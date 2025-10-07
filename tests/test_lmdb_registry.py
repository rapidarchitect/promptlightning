from __future__ import annotations
import tempfile
import shutil
from pathlib import Path
import pytest
from promptlightning.registry.lmdb_registry import LMDBRegistry
from promptlightning.model import TemplateSpec, InputSpec
from promptlightning.exceptions import TemplateNotFound, RegistryError

@pytest.fixture
def temp_db_path():
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test.lmdb"
    yield db_path
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

@pytest.fixture
def sample_template():
    return TemplateSpec(
        id="test_template",
        version="1.0.0",
        description="Test template",
        template="Hello {{name}}!",
        inputs={
            "name": InputSpec(type="string", required=True, default="World")
        },
        metadata={"author": "test"}
    )

def test_lmdb_registry_initialization(temp_db_path):
    registry = LMDBRegistry(db_path=temp_db_path)
    assert registry.db_path.resolve() == temp_db_path.resolve()
    assert registry.map_size == 100 * 1024 * 1024
    registry.close()

def test_save_and_load_template(temp_db_path, sample_template):
    registry = LMDBRegistry(db_path=temp_db_path)

    registry.save(sample_template)
    loaded = registry.load("test_template")

    assert loaded.id == sample_template.id
    assert loaded.version == sample_template.version
    assert loaded.description == sample_template.description
    assert loaded.template == sample_template.template
    assert loaded.inputs == sample_template.inputs
    assert loaded.metadata == sample_template.metadata

    registry.close()

def test_list_ids(temp_db_path, sample_template):
    registry = LMDBRegistry(db_path=temp_db_path)

    template2 = TemplateSpec(
        id="another_template",
        version="2.0.0",
        template="Test {{input}}"
    )

    registry.save(sample_template)
    registry.save(template2)

    ids = list(registry.list_ids())
    assert len(ids) == 2
    assert "test_template" in ids
    assert "another_template" in ids

    registry.close()

def test_delete_template(temp_db_path, sample_template):
    registry = LMDBRegistry(db_path=temp_db_path)

    registry.save(sample_template)
    assert "test_template" in list(registry.list_ids())

    registry.delete("test_template")
    assert "test_template" not in list(registry.list_ids())

    with pytest.raises(TemplateNotFound):
        registry.load("test_template")

    registry.close()

def test_delete_nonexistent_template(temp_db_path):
    registry = LMDBRegistry(db_path=temp_db_path)

    with pytest.raises(TemplateNotFound):
        registry.delete("nonexistent")

    registry.close()

def test_load_nonexistent_template(temp_db_path):
    registry = LMDBRegistry(db_path=temp_db_path)

    with pytest.raises(TemplateNotFound):
        registry.load("nonexistent")

    registry.close()

def test_get_by_version(temp_db_path, sample_template):
    registry = LMDBRegistry(db_path=temp_db_path)

    registry.save(sample_template)
    loaded = registry.get_by_version("test_template", "1.0.0")

    assert loaded.id == sample_template.id
    assert loaded.version == sample_template.version

    registry.close()

def test_get_by_version_nonexistent(temp_db_path):
    registry = LMDBRegistry(db_path=temp_db_path)

    with pytest.raises(TemplateNotFound):
        registry.get_by_version("test_template", "1.0.0")

    registry.close()

def test_get_metadata(temp_db_path, sample_template):
    registry = LMDBRegistry(db_path=temp_db_path)

    initial_metadata = registry.get_metadata()
    assert initial_metadata["count"] == 0
    assert initial_metadata["last_modified"] is None

    registry.save(sample_template)

    metadata = registry.get_metadata()
    assert metadata["count"] == 1
    assert metadata["last_modified"] is not None

    registry.close()

def test_context_manager(temp_db_path, sample_template):
    with LMDBRegistry(db_path=temp_db_path) as registry:
        registry.save(sample_template)
        loaded = registry.load("test_template")
        assert loaded.id == sample_template.id

def test_update_template(temp_db_path, sample_template):
    registry = LMDBRegistry(db_path=temp_db_path)

    registry.save(sample_template)

    updated = TemplateSpec(
        id="test_template",
        version="2.0.0",
        description="Updated template",
        template="Hi {{name}}!",
        inputs=sample_template.inputs
    )
    registry.save(updated)

    loaded = registry.load("test_template")
    assert loaded.version == "2.0.0"
    assert loaded.description == "Updated template"
    assert loaded.template == "Hi {{name}}!"

    registry.close()

def test_large_template_data(temp_db_path):
    registry = LMDBRegistry(db_path=temp_db_path)

    large_template = TemplateSpec(
        id="large_template",
        version="1.0.0",
        template="x" * 10000,
        metadata={"data": "y" * 5000}
    )

    registry.save(large_template)
    loaded = registry.load("large_template")

    assert len(loaded.template) == 10000
    assert len(loaded.metadata["data"]) == 5000

    registry.close()

def test_concurrent_operations(temp_db_path, sample_template):
    registry1 = LMDBRegistry(db_path=temp_db_path)
    registry2 = LMDBRegistry(db_path=temp_db_path)

    registry1.save(sample_template)
    loaded = registry2.load("test_template")

    assert loaded.id == sample_template.id

    registry1.close()
    registry2.close()
