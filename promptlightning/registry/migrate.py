from __future__ import annotations
from pathlib import Path
from typing import Optional
from .local import LocalRegistry
from .lmdb_registry import LMDBRegistry
from ..exceptions import RegistryError

def migrate_local_to_lmdb(
    prompt_dir: str | Path,
    db_path: str | Path,
    map_size: int = 100 * 1024 * 1024,
    overwrite: bool = False,
    verbose: bool = True
) -> dict:
    prompt_dir = Path(prompt_dir)
    db_path = Path(db_path)

    if db_path.exists() and not overwrite:
        raise RegistryError(
            f"Database already exists at {db_path}. "
            "Set overwrite=True to replace it."
        )

    if not prompt_dir.exists():
        raise RegistryError(f"Prompt directory not found: {prompt_dir}")

    try:
        local_registry = LocalRegistry(prompt_dir=prompt_dir)
        lmdb_registry = LMDBRegistry(db_path=db_path, map_size=map_size)

        migrated_count = 0
        failed_count = 0
        failed_ids = []

        if verbose:
            print(f"Migrating templates from {prompt_dir} to {db_path}")

        for template_id in local_registry.list_ids():
            try:
                template = local_registry.load(template_id)
                lmdb_registry.save(template)
                migrated_count += 1
                if verbose:
                    print(f"  ✓ Migrated: {template_id}")
            except Exception as e:
                failed_count += 1
                failed_ids.append(template_id)
                if verbose:
                    print(f"  ✗ Failed: {template_id} - {e}")

        lmdb_registry.close()

        result = {
            "success": failed_count == 0,
            "migrated": migrated_count,
            "failed": failed_count,
            "failed_ids": failed_ids,
            "db_path": str(db_path.resolve()),
        }

        if verbose:
            print(f"\nMigration complete:")
            print(f"  Migrated: {migrated_count}")
            print(f"  Failed: {failed_count}")

        return result

    except Exception as e:
        raise RegistryError(f"Migration failed: {e}")

def verify_migration(
    prompt_dir: str | Path,
    db_path: str | Path,
    verbose: bool = True
) -> dict:
    try:
        local_registry = LocalRegistry(prompt_dir=prompt_dir)
        lmdb_registry = LMDBRegistry(db_path=db_path)

        local_ids = set(local_registry.list_ids())
        lmdb_ids = set(lmdb_registry.list_ids())

        missing_in_lmdb = local_ids - lmdb_ids
        extra_in_lmdb = lmdb_ids - local_ids

        verified_count = 0
        mismatch_count = 0
        mismatch_ids = []

        if verbose:
            print(f"Verifying migration...")

        for template_id in local_ids & lmdb_ids:
            try:
                local_template = local_registry.load(template_id)
                lmdb_template = lmdb_registry.load(template_id)

                if local_template.model_dump() == lmdb_template.model_dump():
                    verified_count += 1
                    if verbose:
                        print(f"  ✓ Verified: {template_id}")
                else:
                    mismatch_count += 1
                    mismatch_ids.append(template_id)
                    if verbose:
                        print(f"  ✗ Mismatch: {template_id}")
            except Exception as e:
                mismatch_count += 1
                mismatch_ids.append(template_id)
                if verbose:
                    print(f"  ✗ Error: {template_id} - {e}")

        lmdb_registry.close()

        result = {
            "success": (
                len(missing_in_lmdb) == 0 and
                len(extra_in_lmdb) == 0 and
                mismatch_count == 0
            ),
            "verified": verified_count,
            "mismatches": mismatch_count,
            "mismatch_ids": mismatch_ids,
            "missing_in_lmdb": list(missing_in_lmdb),
            "extra_in_lmdb": list(extra_in_lmdb),
        }

        if verbose:
            print(f"\nVerification complete:")
            print(f"  Verified: {verified_count}")
            print(f"  Mismatches: {mismatch_count}")
            print(f"  Missing in LMDB: {len(missing_in_lmdb)}")
            print(f"  Extra in LMDB: {len(extra_in_lmdb)}")

        return result

    except Exception as e:
        raise RegistryError(f"Verification failed: {e}")
