from pathlib import Path
import tempfile
import shutil
from promptlightning.registry.lmdb_registry import LMDBRegistry
from promptlightning.model import TemplateSpec, InputSpec

def main():
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "example.lmdb"

    try:
        print("LMDB Registry Example")
        print("=" * 60)

        with LMDBRegistry(db_path=db_path) as registry:
            print("\n1. Creating templates...")

            summarizer = TemplateSpec(
                id="summarizer",
                version="1.0.0",
                description="Summarize text",
                template="Summarize the following text:\n\n{{input_text}}",
                inputs={
                    "input_text": InputSpec(type="string", required=True)
                }
            )

            translator = TemplateSpec(
                id="translator",
                version="1.0.0",
                description="Translate text",
                template="Translate to {{target_language}}:\n\n{{text}}",
                inputs={
                    "text": InputSpec(type="string", required=True),
                    "target_language": InputSpec(type="string", default="Spanish")
                }
            )

            registry.save(summarizer)
            registry.save(translator)
            print("  ✓ Saved 2 templates")

            print("\n2. Listing templates...")
            for template_id in registry.list_ids():
                print(f"  - {template_id}")

            print("\n3. Loading templates...")
            loaded = registry.load("summarizer")
            print(f"  ✓ Loaded: {loaded.id} (v{loaded.version})")
            print(f"    Description: {loaded.description}")

            print("\n4. Getting metadata...")
            metadata = registry.get_metadata()
            print(f"  Template count: {metadata['count']}")
            print(f"  Last modified: {metadata['last_modified']}")

            print("\n5. Updating template...")
            summarizer.version = "1.1.0"
            summarizer.description = "Summarize text with improved prompt"
            registry.save(summarizer)
            print(f"  ✓ Updated to version {summarizer.version}")

            print("\n6. Version lookup...")
            v1 = registry.get_by_version("summarizer", "1.0.0")
            v2 = registry.get_by_version("summarizer", "1.1.0")
            print(f"  v1.0.0: {v1.description}")
            print(f"  v1.1.0: {v2.description}")

            print("\n7. Deleting template...")
            registry.delete("translator")
            print(f"  ✓ Deleted translator")
            print(f"  Remaining: {list(registry.list_ids())}")

        print("\n" + "=" * 60)
        print("Example complete!")
        print(f"Database size: {db_path.stat().st_size:,} bytes")

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
