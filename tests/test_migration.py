from __future__ import annotations
import tempfile
import shutil
from pathlib import Path
import yaml
import pytest
from promptlightning.registry.migrate import migrate_local_to_lmdb, verify_migration
from promptlightning.registry.lmdb_registry import LMDBRegistry
from promptlightning.exceptions import RegistryError

@pytest.fixture
def temp_dirs():
    prompt_dir = Path(tempfile.mkdtemp())
    db_dir = Path(tempfile.mkdtemp())
    db_path = db_dir / "test.lmdb"

    yield prompt_dir, db_path

    if prompt_dir.exists():
        shutil.rmtree(prompt_dir)
    if db_dir.exists():
        shutil.rmtree(db_dir)

def create_test_template(prompt_dir: Path, template_id: str):
    template_file = prompt_dir / f"{template_id}.yaml"
    data = {
        "id": template_id,
        "version": "1.0.0",
        "description": f"Test template {template_id}",
        "template": f"Hello {{{{name}}}}! This is {template_id}.",
        "inputs": {
            "name": {
                "type": "string",
                "required": True,
                "default": "World"
            }
        },
        "metadata": {"test": True}
    }
    template_file.write_text(yaml.dump(data))

def test_migrate_local_to_lmdb(temp_dirs):
    prompt_dir, db_path = temp_dirs

    create_test_template(prompt_dir, "template1")
    create_test_template(prompt_dir, "template2")
    create_test_template(prompt_dir, "template3")

    result = migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    assert result["success"] is True
    assert result["migrated"] == 3
    assert result["failed"] == 0
    assert len(result["failed_ids"]) == 0

def test_verify_migration(temp_dirs):
    prompt_dir, db_path = temp_dirs

    create_test_template(prompt_dir, "template1")
    create_test_template(prompt_dir, "template2")

    migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    result = verify_migration(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    assert result["success"] is True
    assert result["verified"] == 2
    assert result["mismatches"] == 0
    assert len(result["missing_in_lmdb"]) == 0
    assert len(result["extra_in_lmdb"]) == 0

def test_migrate_overwrite_protection(temp_dirs):
    prompt_dir, db_path = temp_dirs

    create_test_template(prompt_dir, "template1")

    migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    with pytest.raises(RegistryError, match="already exists"):
        migrate_local_to_lmdb(
            prompt_dir=prompt_dir,
            db_path=db_path,
            verbose=False,
            overwrite=False
        )

def test_migrate_with_overwrite(temp_dirs):
    prompt_dir, db_path = temp_dirs

    create_test_template(prompt_dir, "template1")

    migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    result = migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False,
        overwrite=True
    )

    assert result["success"] is True
    assert result["migrated"] == 1

def test_migrate_empty_directory(temp_dirs):
    prompt_dir, db_path = temp_dirs

    result = migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    assert result["success"] is True
    assert result["migrated"] == 0

def test_migrate_nonexistent_directory():
    db_path = Path(tempfile.mkdtemp()) / "test.lmdb"

    with pytest.raises(RegistryError, match="not found"):
        migrate_local_to_lmdb(
            prompt_dir="/nonexistent/path",
            db_path=db_path,
            verbose=False
        )

    shutil.rmtree(db_path.parent)

def test_verify_missing_template(temp_dirs):
    prompt_dir, db_path = temp_dirs

    create_test_template(prompt_dir, "template1")
    create_test_template(prompt_dir, "template2")

    migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    (prompt_dir / "template3.yaml").write_text(yaml.dump({
        "id": "template3",
        "version": "1.0.0",
        "template": "Test"
    }))

    result = verify_migration(
        prompt_dir=prompt_dir,
        db_path=db_path,
        verbose=False
    )

    assert result["success"] is False
    assert "template3" in result["missing_in_lmdb"]

def test_migration_with_custom_map_size(temp_dirs):
    prompt_dir, db_path = temp_dirs

    create_test_template(prompt_dir, "template1")

    custom_map_size = 200 * 1024 * 1024

    result = migrate_local_to_lmdb(
        prompt_dir=prompt_dir,
        db_path=db_path,
        map_size=custom_map_size,
        verbose=False
    )

    assert result["success"] is True

    registry = LMDBRegistry(db_path=db_path, map_size=custom_map_size)
    assert registry.map_size == custom_map_size
    registry.close()
