# Migration Guide: YAML to LMDB

This guide covers migrating from YAML-based template storage to LMDB-based storage for improved performance.

## Why Migrate?

LMDB provides significant performance advantages over YAML file scanning:

| Metric | YAML Registry | LMDB Registry | Improvement |
|--------|--------------|---------------|-------------|
| 10 templates (50 lookups) | 86ms | 0.2ms | 451x faster |
| 50 templates (200 lookups) | 1,595ms | 0.7ms | 2,275x faster |
| 100 templates (500 lookups) | 7,817ms | 1.8ms | 4,380x faster |

**Key Benefits:**
- O(1) constant-time lookups regardless of template count
- Zero-copy memory-mapped reads for maximum efficiency
- Thread-safe MVCC architecture for concurrent access
- ACID-compliant storage for production reliability
- Reduced memory footprint with MessagePack serialization

## Before You Begin

### 1. Backup Your Templates

Always backup your YAML templates before migration:

```bash
# Create timestamped backup
tar -czf templates-backup-$(date +%Y%m%d-%H%M%S).tar.gz prompts/

# Or copy to backup directory
cp -r prompts/ prompts-backup/
```

### 2. Verify Template Integrity

Ensure all YAML templates are valid:

```bash
# List all templates
promptlightning list

# If this command succeeds, your templates are valid
```

### 3. Check Dependencies

Ensure you have the latest version with LMDB support:

```bash
pip install --upgrade promptlightning

# Or for development
git pull
uv sync
```

## Migration Steps

### Option 1: CLI Migration (Recommended)

The simplest migration method using the built-in CLI command:

```bash
# Basic migration
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb

# With custom map size (for large template collections)
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --map-size 500

# Overwrite existing database
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --overwrite

# Quiet mode (no progress output)
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --quiet
```

**Output:**
```
Migrating templates from ./prompts to ./templates.lmdb
  ✓ Migrated: summarizer
  ✓ Migrated: greeting
  ✓ Migrated: code_review

Migration complete:
  Migrated: 3
  Failed: 0
```

### Option 2: Python Script

For programmatic migration with custom logic:

```python
from promptlightning.registry.migrate import migrate_local_to_lmdb

result = migrate_local_to_lmdb(
    prompt_dir="./prompts",
    db_path="./templates.lmdb",
    map_size=100 * 1024 * 1024,  # 100MB (default)
    overwrite=False,              # Don't overwrite existing DB
    verbose=True                  # Show progress
)

print(f"Success: {result['success']}")
print(f"Migrated: {result['migrated']} templates")
print(f"Failed: {result['failed']} templates")

if result['failed_ids']:
    print(f"Failed IDs: {result['failed_ids']}")
```

### Option 3: Hybrid Approach (Gradual Migration)

Migrate templates on-demand as they're accessed:

```python
from promptlightning.registry.local import LocalRegistry
from promptlightning.registry.lmdb_registry import LMDBRegistry
from promptlightning.exceptions import TemplateNotFoundError

class HybridRegistry:
    def __init__(self, local_dir, lmdb_path):
        self.local = LocalRegistry(prompt_dir=local_dir)
        self.lmdb = LMDBRegistry(db_path=lmdb_path)

    def load(self, template_id):
        try:
            # Try LMDB first (fast)
            return self.lmdb.load(template_id)
        except TemplateNotFoundError:
            # Fall back to YAML and migrate
            template = self.local.load(template_id)
            self.lmdb.save(template)
            return template

    def list_ids(self):
        # Return combined list
        return list(set(self.local.list_ids()) | set(self.lmdb.list_ids()))

# Use hybrid registry
registry = HybridRegistry("./prompts", "./templates.lmdb")
```

## Verification

### Automatic Verification

The CLI migration includes automatic verification:

```bash
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --verify
```

### Manual Verification

Verify migration integrity using Python:

```python
from promptlightning.registry.migrate import verify_migration

result = verify_migration(
    prompt_dir="./prompts",
    db_path="./templates.lmdb",
    verbose=True
)

print(f"Verified: {result['verified']} templates")
print(f"Mismatches: {result['mismatches']}")
print(f"Missing in LMDB: {result['missing_in_lmdb']}")
print(f"Extra in LMDB: {result['extra_in_lmdb']}")

if not result['success']:
    print("Verification failed!")
    print(f"Mismatch IDs: {result['mismatch_ids']}")
```

### Compare Template Content

Manually compare individual templates:

```python
from promptlightning.registry.local import LocalRegistry
from promptlightning.registry.lmdb_registry import LMDBRegistry

local = LocalRegistry(prompt_dir="./prompts")
lmdb = LMDBRegistry(db_path="./templates.lmdb")

template_id = "summarizer"

local_template = local.load(template_id)
lmdb_template = lmdb.load(template_id)

# Compare dictionaries
assert local_template.model_dump() == lmdb_template.model_dump()

lmdb.close()
```

## Update Configuration

After successful migration, update `promptlightning.yaml`:

### Before (YAML):
```yaml
registry: local
prompt_dir: ./prompts
logging:
  enabled: true
  backend: sqlite
  db_path: ./promptlightning.db
```

### After (LMDB):
```yaml
registry: lmdb
db_path: ./templates.lmdb
logging:
  enabled: true
  backend: sqlite
  db_path: ./promptlightning.db
```

## Update Application Code

### Vault Initialization

Update Vault creation to use LMDB:

**Before:**
```python
from promptlightning import Vault

vault = Vault(prompt_dir="./prompts")
```

**After:**
```python
from promptlightning import Vault

vault = Vault(db_path="./templates.lmdb")
```

### Direct Registry Usage

**Before:**
```python
from promptlightning.registry.local import LocalRegistry

registry = LocalRegistry(prompt_dir="./prompts")
template = registry.load("my_template")
```

**After:**
```python
from promptlightning.registry.lmdb_registry import LMDBRegistry

registry = LMDBRegistry(db_path="./templates.lmdb")
template = registry.load("my_template")
registry.close()  # Important: Close when done
```

### Context Manager Pattern

Use context managers to ensure proper cleanup:

```python
from promptlightning.registry.lmdb_registry import LMDBRegistry

with LMDBRegistry(db_path="./templates.lmdb") as registry:
    template = registry.load("my_template")
    # Registry automatically closes
```

## Troubleshooting

### Migration Fails with "Database exists"

**Problem:** Target database already exists and `overwrite=False`

**Solution:**
```bash
# Option 1: Use --overwrite flag
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --overwrite

# Option 2: Delete existing database
rm -rf ./templates.lmdb
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb

# Option 3: Use different path
promptlightning migrate --prompt-dir ./prompts --db-path ./templates-new.lmdb
```

### Some Templates Fail to Migrate

**Problem:** Individual templates fail during migration

**Solution:**
1. Check the failed template IDs from migration output
2. Validate YAML syntax:
```bash
python -c "import yaml; yaml.safe_load(open('prompts/failed_template.yaml'))"
```
3. Fix YAML errors and retry migration

### "Map size exceeded" Error

**Problem:** Database map size too small for template collection

**Solution:**
```bash
# Increase map size (e.g., 500MB)
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --map-size 500
```

**Map size recommendations:**
- Small projects (<100 templates): 100MB (default)
- Medium projects (100-1000 templates): 500MB
- Large projects (>1000 templates): 1GB+

### Permission Errors

**Problem:** Cannot create database file

**Solution:**
```bash
# Ensure write permissions
chmod 755 /path/to/db/directory

# Check disk space
df -h /path/to/db/directory
```

### Verification Shows Mismatches

**Problem:** Template content differs between YAML and LMDB

**Solution:**
1. Check specific mismatches:
```python
from promptlightning.registry.migrate import verify_migration
result = verify_migration("./prompts", "./templates.lmdb", verbose=True)
print(result['mismatch_ids'])
```

2. Re-migrate specific templates:
```python
from promptlightning.registry.local import LocalRegistry
from promptlightning.registry.lmdb_registry import LMDBRegistry

local = LocalRegistry(prompt_dir="./prompts")
lmdb = LMDBRegistry(db_path="./templates.lmdb")

for template_id in result['mismatch_ids']:
    template = local.load(template_id)
    lmdb.save(template)  # Overwrite

lmdb.close()
```

## Rollback Procedure

If you need to rollback to YAML-based storage:

### 1. Restore Configuration

Revert `promptlightning.yaml` to YAML registry:

```yaml
registry: local
prompt_dir: ./prompts
```

### 2. Restore Backup

```bash
# Extract backup
tar -xzf templates-backup-YYYYMMDD-HHMMSS.tar.gz

# Or copy from backup directory
cp -r prompts-backup/ prompts/
```

### 3. Remove LMDB Database (Optional)

```bash
rm -rf ./templates.lmdb
```

### 4. Verify Rollback

```bash
promptlightning list
```

## Best Practices

### 1. Test Migration in Development First

Always test migration in development environment before production:

```bash
# Development migration
promptlightning migrate --prompt-dir ./prompts --db-path ./templates-dev.lmdb

# Verify
promptlightning migrate --prompt-dir ./prompts --db-path ./templates-dev.lmdb --verify

# If successful, migrate production
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb
```

### 2. Version Control YAML Templates

Keep YAML templates in version control even after migration:

```bash
# .gitignore
templates.lmdb/
templates-*.lmdb/
*.lmdb

# Keep YAML in version control
!prompts/*.yaml
```

This allows:
- Easy template editing and review
- Version history tracking
- Rollback capability
- Re-migration if needed

### 3. Periodic Re-Migration

If YAML templates are updated, re-migrate:

```bash
# Re-migrate with overwrite
promptlightning migrate --prompt-dir ./prompts --db-path ./templates.lmdb --overwrite --verify
```

### 4. Monitor Database Size

Check LMDB database size periodically:

```bash
# Actual disk usage (LMDB uses sparse files)
du -h templates.lmdb

# If approaching map size, increase it:
# 1. Export templates to YAML
# 2. Delete LMDB database
# 3. Re-migrate with larger map size
```

### 5. Database Backup Strategy

Backup LMDB database for production systems:

```bash
# Stop application first (LMDB should be closed)
systemctl stop myapp

# Backup database
cp -r templates.lmdb templates.lmdb.backup-$(date +%Y%m%d-%H%M%S)

# Restart application
systemctl start myapp
```

## Performance Tuning

After migration, optimize performance:

### 1. Adjust Map Size

Set appropriate map size based on template count:

```python
from promptlightning.registry.lmdb_registry import LMDBRegistry

# Large template collection
registry = LMDBRegistry(
    db_path="./templates.lmdb",
    map_size=1024 * 1024 * 1024  # 1GB
)
```

### 2. Enable Vault Caching

Vault caching works seamlessly with LMDB:

```python
from promptlightning import Vault

vault = Vault(db_path="./templates.lmdb")

# First access: LMDB lookup (~0.02ms)
template = vault.get("summarizer")

# Second access: Vault cache hit (~0.001ms)
template = vault.get("summarizer")
```

### 3. Concurrent Access

LMDB supports thread-safe concurrent reads:

```python
from concurrent.futures import ThreadPoolExecutor
from promptlightning.registry.lmdb_registry import LMDBRegistry

registry = LMDBRegistry(db_path="./templates.lmdb")

def load_template(template_id):
    return registry.load(template_id)

template_ids = ["summarizer", "greeting", "code_review"]

with ThreadPoolExecutor(max_workers=10) as executor:
    templates = list(executor.map(load_template, template_ids))

registry.close()
```

## FAQ

**Q: Can I use both YAML and LMDB registries simultaneously?**

A: Yes, use the hybrid approach (Option 3) to maintain both registries during transition.

**Q: Will my existing code break after migration?**

A: No, the Vault API is identical. Only configuration changes are needed.

**Q: Can I edit templates in LMDB directly?**

A: No, LMDB stores binary data. Edit YAML templates and re-migrate, or use the Playground UI.

**Q: How do I add new templates after migration?**

A: Add to YAML prompts directory and re-migrate with `--overwrite`, or use the registry API:
```python
from promptlightning.registry.lmdb_registry import LMDBRegistry
from promptlightning.model import TemplateSpec

registry = LMDBRegistry(db_path="./templates.lmdb")
registry.save(new_template_spec)
registry.close()
```

**Q: What happens to template versioning?**

A: LMDB maintains full version history via the `version_index` database.

**Q: Can I migrate back to YAML?**

A: Yes, use the rollback procedure above. YAML templates serve as the source of truth.

**Q: Does LMDB work on Windows/Mac/Linux?**

A: Yes, LMDB is cross-platform and included in the `lmdb` Python package.

**Q: How much faster is LMDB really?**

A: 450-4,380x faster depending on template count. See [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for benchmarks.

## Next Steps

After successful migration:

1. Review [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for performance optimization tips
2. Check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for LMDB implementation details
3. Update deployment documentation with new configuration
4. Monitor application performance metrics
5. Consider removing YAML templates from production (keep in version control)

## Support

If you encounter issues during migration:

- Check existing GitHub issues: https://github.com/bogdan-pistol/promptlightning/issues
- Join Discord community: https://discord.gg/QSRRcFjzE8
- Create detailed bug report with migration logs
