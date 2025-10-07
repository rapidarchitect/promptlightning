# LMDB Registry Architecture

Technical architecture documentation for PromptLightning's LMDB-based registry implementation.

## Overview

The LMDB registry provides high-performance template storage using Lightning Memory-Mapped Database (LMDB), delivering 450-4,380x performance improvement over YAML file scanning through O(1) constant-time lookups and zero-copy memory-mapped I/O.

## Architecture Components

### 1. Registry Interface

Abstract base class defining the registry contract:

```python
class RegistryInterface(ABC):
    @abstractmethod
    def load(self, template_id: str) -> TemplateSpec:
        """Load template by ID"""
        pass

    @abstractmethod
    def save(self, template: TemplateSpec) -> None:
        """Save template to registry"""
        pass

    @abstractmethod
    def delete(self, template_id: str) -> None:
        """Delete template from registry"""
        pass

    @abstractmethod
    def list_ids(self) -> list[str]:
        """List all template IDs"""
        pass
```

### 2. LMDB Implementation

The `LMDBRegistry` class implements the registry interface using LMDB:

**File:** `promptlightning/registry/lmdb_registry.py`

**Key Components:**
- LMDB environment management
- Three-database schema
- MessagePack serialization
- Transaction handling
- Version indexing

### 3. Migration Utilities

Automated migration from LocalRegistry to LMDBRegistry:

**File:** `promptlightning/registry/migrate.py`

**Functions:**
- `migrate_local_to_lmdb()`: Batch migration with verification
- `verify_migration()`: Data integrity verification

## LMDB Schema Design

### Database Structure

LMDBRegistry uses three separate LMDB databases within a single environment:

```
templates.lmdb/
├── data.mdb          # Main data file
└── lock.mdb          # Lock file

Internal databases:
1. templates          # Primary template storage
2. metadata           # Registry metadata
3. version_index      # Version-based lookup index
```

### 1. Templates Database

Primary storage for template data.

**Schema:**
```python
Key:   template_id (UTF-8 encoded string)
Value: MessagePack-serialized TemplateSpec
```

**Example:**
```
Key:   b"summarizer"
Value: msgpack.packb({
    "id": "summarizer",
    "version": "1.0.0",
    "description": "Summarize text",
    "template": "Summarize: {{text}}",
    "inputs": {...},
    "metadata": {...}
})
```

**Operations:**
- **Load:** O(1) B+tree lookup by template_id
- **Save:** O(log n) B+tree insertion
- **Delete:** O(log n) B+tree deletion
- **List:** O(n) cursor iteration over all keys

### 2. Metadata Database

Registry-level metadata storage.

**Schema:**
```python
Key:   metadata_key (UTF-8 encoded string)
Value: MessagePack-serialized value
```

**Stored Metadata:**
```python
{
    "count": 42,                    # Total template count
    "last_modified": 1704067200,    # Unix timestamp
}
```

**Operations:**
- **Get count:** O(1) direct key lookup
- **Update metadata:** O(1) direct key update

### 3. Version Index Database

Enables lookup by template ID and version.

**Schema:**
```python
Key:   "{template_id}:{version}" (UTF-8 encoded)
Value: template_id (reference to templates database)
```

**Example:**
```
Key:   b"summarizer:1.0.0"
Value: b"summarizer"

Key:   b"summarizer:2.0.0"
Value: b"summarizer"
```

**Operations:**
- **Load by version:** O(1) index lookup, O(1) template lookup = O(1) total
- **Save:** O(log n) index insertion per version
- **Delete:** O(k × log n) where k = number of versions

## MessagePack Serialization

### Why MessagePack?

MessagePack provides:
- **Compact binary format** (30-40% smaller than JSON)
- **Fast serialization** (2-5x faster than JSON)
- **Type preservation** (no string-to-type conversion)
- **Cross-language compatibility** (future-proof)

### Serialization Process

**Template to bytes:**
```python
import msgpack

template_dict = template.model_dump()
serialized = msgpack.packb(template_dict)
```

**Bytes to template:**
```python
template_dict = msgpack.unpackb(serialized)
template = TemplateSpec(**template_dict)
```

### Size Comparison

Example template with 3 inputs:

| Format | Size | Ratio |
|--------|------|-------|
| YAML | 482 bytes | 1.00x (baseline) |
| JSON | 398 bytes | 0.83x |
| MessagePack | 312 bytes | 0.65x |

**Storage savings:** 35% compared to YAML, 22% compared to JSON.

## Performance Optimizations

### 1. Memory-Mapped I/O

LMDB uses memory-mapped files for zero-copy reads:

**Traditional I/O:**
```
Application → fread() → Kernel buffer → memcpy() → Application buffer
```

**Memory-mapped I/O:**
```
Application → Direct memory access → OS page cache
```

**Benefits:**
- No data copying (zero-copy reads)
- OS manages memory (no explicit allocation)
- Shared page cache (efficient concurrent access)
- Reduced CPU usage (no memcpy overhead)

### 2. B+Tree Indexing

LMDB uses B+tree data structure for O(log n) insertions and O(1) lookups:

**Lookup complexity:**
```
YAML scanning: O(n) - scan all files
LMDB B+tree:   O(1) - direct page mapping after initial lookup
```

**B+Tree properties:**
- Internal nodes: Keys only (efficient cache usage)
- Leaf nodes: Keys + values (memory-mapped data)
- Sequential access: Cache-friendly leaf node links
- Balanced tree: Guaranteed O(log n) height

### 3. MVCC (Multi-Version Concurrency Control)

LMDB uses MVCC for lock-free concurrent reads:

**Architecture:**
```
Writer: Creates new page versions
Readers: See consistent snapshot (no blocking)
```

**Transaction isolation:**
- Each read transaction sees consistent database snapshot
- Writers don't block readers
- Readers don't block writers
- Single writer at a time (serialized writes)

**Performance impact:**
- Concurrent reads: Near-linear scaling with CPU cores
- Read-heavy workloads: Excellent throughput
- Write-heavy workloads: Single-writer bottleneck

### 4. Write Optimizations

LMDB write performance strategies:

**Writemap mode:**
```python
writemap=True  # Memory-mapped writes (faster)
```
- Writes directly to memory-mapped region
- OS flushes to disk asynchronously
- 20-30% faster than traditional writes

**Metadata sync:**
```python
metasync=False  # Async metadata sync
```
- Metadata synced lazily
- Reduced fsync() calls
- 10-15% faster writes

**Transaction batching:**
```python
# Instead of:
for template in templates:
    registry.save(template)  # N transactions

# Better (future optimization):
registry.save_batch(templates)  # 1 transaction
```

### 5. Read Optimizations

**Read-only transactions:**
```python
with env.begin(write=False) as txn:
    data = txn.get(key)  # No write lock
```
- No write lock acquisition
- No transaction commit overhead
- Minimal CPU usage

**OS read-ahead:**
```python
readahead=True  # Enable OS read-ahead
```
- OS prefetches sequential data
- 15-25% faster for scans
- Automatic cache warming

**Key encoding optimization:**
```python
key = template_id.encode("utf-8")  # Direct encoding, no overhead
```
- No intermediate string allocation
- Minimal CPU for encoding
- Cache-friendly fixed encoding

## Thread Safety Model

### LMDB Guarantees

LMDB provides:
- **Multiple concurrent readers**: Lock-free, no contention
- **Single writer**: LMDB enforces single-writer model
- **ACID transactions**: Atomic, Consistent, Isolated, Durable
- **Crash recovery**: Automatic recovery from crashes

### LMDBRegistry Thread Safety

**Read operations (thread-safe):**
```python
# Multiple threads can read concurrently
def worker(template_id):
    return registry.load(template_id)

with ThreadPoolExecutor(max_workers=20) as executor:
    results = executor.map(worker, template_ids)
```

**Write operations (serialized):**
```python
# LMDB serializes writes internally
def writer(template):
    registry.save(template)  # Thread-safe, but serialized

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(writer, templates)  # Safe, but sequential
```

**Recommendation:**
- Use concurrent workers for reads
- Use single thread for writes
- Batch writes in application code

### Vault Integration

Vault adds an additional caching layer with RLock:

```python
class Vault:
    def __init__(self):
        self._cache_lock = RLock()
        self._template_cache = {}

    def get(self, template_id):
        with self._cache_lock:
            if template_id in self._template_cache:
                return self._template_cache[template_id]
            template = self.registry.load(template_id)
            self._template_cache[template_id] = template
            return template
```

**Thread safety:**
- RLock protects cache dictionary
- Multiple readers with RLock held (reentrant)
- LMDB registry handles database-level concurrency

## Cache Architecture

### Three-Level Caching

PromptLightning uses three cache levels:

```
1. Vault cache (application level)
   ↓ miss
2. LMDB page cache (OS level)
   ↓ miss
3. Disk I/O (storage level)
```

### 1. Vault Cache

**Implementation:** Python dictionary with RLock

**Characteristics:**
- In-process memory cache
- Unlimited size (constrained by memory)
- Template objects cached
- Invalidation via `invalidate_cache()`

**Performance:**
```python
# First access: LMDB lookup (~0.02ms)
template = vault.get("summarizer")

# Second access: Cache hit (<0.001ms)
template = vault.get("summarizer")
```

**Speedup:** 20-50x for repeated access

### 2. LMDB Page Cache

**Implementation:** OS page cache (memory-mapped files)

**Characteristics:**
- OS-managed memory
- Shared across processes
- LRU eviction by OS
- Automatic warmup via read-ahead

**Performance:**
- Hot data: <0.005ms (memory access)
- Cold data: 0.5-5ms (disk I/O)

**Speedup:** 100-1000x for hot data

### 3. Disk I/O

**Implementation:** SSD/HDD storage

**Characteristics:**
- Persistent storage
- Slowest tier
- Required for cold data
- Sequential access optimized by LMDB

**Performance:**
- SSD: 0.1-1ms
- HDD: 5-20ms

## Data Flow

### Read Operation

```
Application
    ↓
Vault.get(template_id)
    ↓
Check vault cache → HIT → Return cached template
    ↓ MISS
Registry.load(template_id)
    ↓
LMDB transaction (read-only)
    ↓
B+tree lookup (O(1) with memory mapping)
    ↓
Page cache → HIT → Memory access
    ↓ MISS
Disk I/O → Read data file
    ↓
MessagePack deserialization
    ↓
TemplateSpec object
    ↓
Cache in vault
    ↓
Return to application
```

**Latency breakdown:**
- Vault cache hit: <0.001ms
- LMDB page cache hit: 0.005ms
- Cold read (SSD): 0.5-1ms
- Cold read (HDD): 5-20ms

### Write Operation

```
Application
    ↓
Registry.save(template)
    ↓
MessagePack serialization
    ↓
LMDB transaction (write)
    ↓
Acquire write lock (single writer)
    ↓
B+tree insertion (O(log n))
    ↓
Update version index
    ↓
Update metadata
    ↓
Commit transaction
    ↓
Invalidate vault cache
    ↓
Return to application
```

**Latency breakdown:**
- Serialization: 0.05ms
- LMDB write: 0.1-0.2ms
- Total: ~0.15-0.25ms

## Error Handling

### LMDB Error Categories

**1. Environment errors:**
- Map size exceeded
- Disk full
- Permission denied

**2. Transaction errors:**
- Read transaction too long
- Write conflict
- Transaction abort

**3. Data errors:**
- Key not found
- Corruption detected
- Invalid data format

### Error Recovery

**Map size exceeded:**
```python
try:
    registry.save(template)
except lmdb.MapFullError:
    # Increase map_size and retry
    registry.close()
    registry = LMDBRegistry(db_path=path, map_size=new_size)
    registry.save(template)
```

**Corruption detection:**
```python
try:
    template = registry.load(template_id)
except msgpack.UnpackException:
    # Data corruption - restore from backup
    restore_from_backup()
```

**Transaction timeout:**
```python
try:
    with env.begin(write=False) as txn:
        # Long-running read transaction
        data = process_large_dataset(txn)
except lmdb.Error:
    # Restart transaction
    with env.begin(write=False) as txn:
        data = process_large_dataset(txn)
```

## Comparison with LocalRegistry

### LocalRegistry Architecture

**File-based storage:**
```
prompts/
├── summarizer.yaml
├── greeting.yaml
└── code_review.yaml
```

**Load operation:**
1. Scan directory (O(n) files)
2. Find matching filename
3. Read YAML file
4. Parse YAML
5. Validate with Pydantic
6. Return TemplateSpec

**Characteristics:**
- O(n) lookup time
- Human-readable YAML
- Easy to edit
- Version control friendly
- Slow for large collections

### LMDBRegistry Architecture

**Database storage:**
```
templates.lmdb/
├── data.mdb
└── lock.mdb
```

**Load operation:**
1. B+tree lookup (O(1) with memory mapping)
2. Deserialize MessagePack
3. Validate with Pydantic
4. Return TemplateSpec

**Characteristics:**
- O(1) lookup time
- Binary MessagePack
- Requires migration for editing
- Not directly version controllable
- Fast for any collection size

### When to Use Each

**LocalRegistry (Development):**
- Small template collections (<100)
- Frequent manual editing
- Version control integration important
- Development/prototyping
- Human readability required

**LMDBRegistry (Production):**
- Large template collections (>100)
- High-performance requirements
- Production deployments
- Concurrent access needed
- Scalability important

## Future Architecture Enhancements

### 1. Batch Operations

Native batch support for reduced transaction overhead:

```python
# Future API
registry.save_batch(templates)      # Single transaction
registry.delete_batch(template_ids)  # Single transaction
```

**Benefits:**
- Reduced fsync() calls
- Lower transaction overhead
- 5-10x faster for bulk operations

### 2. Read-Only Mode

Immutable registry for maximum read performance:

```python
registry = LMDBRegistry(db_path=path, readonly=True)
```

**Benefits:**
- No write lock overhead
- Faster transaction setup
- Multiple environment instances
- Safe concurrent access

### 3. Compression

Optional template compression for large collections:

```python
registry = LMDBRegistry(db_path=path, compression="zstd")
```

**Benefits:**
- 50-70% size reduction
- Reduced disk I/O
- Lower page cache pressure
- Trade-off: CPU for space

### 4. Sharding

Database sharding for massive template collections:

```python
# Future: Automatic sharding for >100k templates
registry = LMDBRegistry(db_path=path, shards=10)
```

**Benefits:**
- Scalability beyond single database limits
- Parallel write operations
- Reduced lock contention
- Enterprise-scale support

### 5. Async API

Asynchronous registry operations:

```python
async with LMDBRegistry(db_path=path) as registry:
    template = await registry.load_async(template_id)
```

**Benefits:**
- Better integration with async applications
- Non-blocking I/O
- Higher throughput for I/O-bound workloads

## Testing Strategy

### Unit Tests

Test individual components:

```python
def test_lmdb_registry_save_load():
    registry = LMDBRegistry(db_path=tmp_path)
    registry.save(template)
    loaded = registry.load(template.id)
    assert loaded == template
    registry.close()
```

### Integration Tests

Test full workflow:

```python
def test_migration_workflow():
    local = LocalRegistry(prompt_dir="./prompts")
    migrate_local_to_lmdb("./prompts", "./templates.lmdb")
    lmdb = LMDBRegistry(db_path="./templates.lmdb")
    verify_migration("./prompts", "./templates.lmdb")
```

### Performance Tests

Benchmark performance characteristics:

```python
def test_lmdb_performance():
    registry = LMDBRegistry(db_path=tmp_path)
    start = time.perf_counter()
    for _ in range(1000):
        registry.load("template_0")
    elapsed = time.perf_counter() - start
    assert elapsed < 0.01  # <10ms for 1000 lookups
```

### Concurrency Tests

Test thread safety:

```python
def test_concurrent_reads():
    registry = LMDBRegistry(db_path=tmp_path)
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(registry.load, template_ids)
    assert all(r is not None for r in results)
```

## Monitoring and Observability

### Key Metrics

**Performance metrics:**
- Lookup latency (p50, p95, p99)
- Throughput (ops/sec)
- Cache hit rate (vault, page cache)

**Resource metrics:**
- Database file size
- Memory usage (RSS, virtual)
- Disk I/O (read/write bytes)

**Error metrics:**
- Map full errors
- Transaction timeouts
- Corruption events

### Instrumentation

```python
import time
from prometheus_client import Histogram, Counter

# Latency histogram
lookup_latency = Histogram("registry_lookup_seconds", "Template lookup latency")

# Error counter
errors = Counter("registry_errors_total", "Registry errors", ["type"])

class InstrumentedLMDBRegistry(LMDBRegistry):
    def load(self, template_id):
        with lookup_latency.time():
            try:
                return super().load(template_id)
            except Exception as e:
                errors.labels(type=type(e).__name__).inc()
                raise
```

## Conclusion

The LMDB registry architecture provides:
- **450-4,380x performance improvement** over YAML file scanning
- **O(1) constant-time lookups** via B+tree indexing and memory mapping
- **Thread-safe concurrent reads** via MVCC architecture
- **Zero-copy I/O** through memory-mapped files
- **Production-ready reliability** with ACID transactions

Key design decisions:
- Three-database schema for separation of concerns
- MessagePack for compact binary serialization
- Memory-mapped I/O for maximum performance
- MVCC for lock-free concurrent reads
- Single-writer model for consistency

See [PERFORMANCE.md](PERFORMANCE.md) for detailed benchmarks and [../MIGRATION.md](../MIGRATION.md) for migration guide.
