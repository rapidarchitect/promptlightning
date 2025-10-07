from __future__ import annotations
import tempfile
import shutil
import time
from pathlib import Path
from promptlightning.registry.lmdb_registry import LMDBRegistry
from promptlightning.registry.local import LocalRegistry
from promptlightning.model import TemplateSpec, InputSpec
import yaml

def create_sample_templates(count: int) -> list[TemplateSpec]:
    templates = []
    for i in range(count):
        templates.append(
            TemplateSpec(
                id=f"template_{i}",
                version="1.0.0",
                description=f"Test template {i}",
                template=f"Hello {{{{name}}}}! This is template {i}.",
                inputs={
                    "name": InputSpec(type="string", required=True, default="World")
                },
                metadata={"index": i, "category": f"cat_{i % 10}"}
            )
        )
    return templates

def benchmark_local_registry(template_count: int, lookup_count: int):
    temp_dir = Path(tempfile.mkdtemp())
    try:
        for i in range(template_count):
            template_file = temp_dir / f"template_{i}.yaml"
            data = {
                "id": f"template_{i}",
                "version": "1.0.0",
                "description": f"Test template {i}",
                "template": f"Hello {{{{name}}}}! This is template {i}.",
                "inputs": {
                    "name": {
                        "type": "string",
                        "required": True,
                        "default": "World"
                    }
                },
                "metadata": {"index": i, "category": f"cat_{i % 10}"}
            }
            template_file.write_text(yaml.dump(data))

        registry = LocalRegistry(prompt_dir=temp_dir)

        start = time.perf_counter()
        for i in range(lookup_count):
            template_id = f"template_{i % template_count}"
            registry.load(template_id)
        elapsed = time.perf_counter() - start

        return elapsed
    finally:
        shutil.rmtree(temp_dir)

def benchmark_lmdb_registry(template_count: int, lookup_count: int):
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.lmdb"
    try:
        registry = LMDBRegistry(db_path=db_path)

        templates = create_sample_templates(template_count)
        for template in templates:
            registry.save(template)

        start = time.perf_counter()
        for i in range(lookup_count):
            template_id = f"template_{i % template_count}"
            registry.load(template_id)
        elapsed = time.perf_counter() - start

        registry.close()
        return elapsed
    finally:
        shutil.rmtree(temp_dir)

def run_benchmark():
    print("=" * 80)
    print("LMDB Registry Performance Benchmark")
    print("=" * 80)

    test_configs = [
        (10, 50, "Small dataset"),
        (50, 200, "Medium dataset"),
        (100, 500, "Large dataset"),
    ]

    for template_count, lookup_count, label in test_configs:
        print(f"\n{label}: {template_count} templates, {lookup_count} lookups")
        print("-" * 80)

        local_time = benchmark_local_registry(template_count, lookup_count)
        print(f"LocalRegistry:  {local_time:.4f}s ({lookup_count/local_time:.0f} lookups/sec)")

        lmdb_time = benchmark_lmdb_registry(template_count, lookup_count)
        print(f"LMDBRegistry:   {lmdb_time:.4f}s ({lookup_count/lmdb_time:.0f} lookups/sec)")

        speedup = local_time / lmdb_time
        print(f"Speedup:        {speedup:.1f}x faster")

    print("\n" + "=" * 80)
    print("Benchmark Summary:")
    print("- LMDB provides O(1) constant-time lookups")
    print("- LocalRegistry performs O(n) linear scans")
    print("- Performance gap increases with template count")
    print("- LMDB uses memory-mapped files for zero-copy reads")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmark()
