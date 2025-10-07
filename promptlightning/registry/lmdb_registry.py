from __future__ import annotations
from typing import Iterable
from pathlib import Path
import time
import lmdb
import msgpack
from ..model import TemplateSpec
from ..exceptions import TemplateNotFound, RegistryError
from .base import Registry

class LMDBRegistry(Registry):
    def __init__(self, db_path: str | Path, map_size: int = 100 * 1024 * 1024) -> None:
        self.db_path = Path(db_path).resolve()
        self.map_size = map_size
        self._env = None
        self._templates_db = None
        self._metadata_db = None
        self._version_index_db = None
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        if self._env is not None:
            return

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self._env = lmdb.open(
                str(self.db_path),
                map_size=self.map_size,
                max_dbs=10,
                writemap=True,
                metasync=False,
                sync=True,
                map_async=False,
                readahead=True,
                meminit=False,
                lock=True
            )

            self._templates_db = self._env.open_db(b'templates')
            self._metadata_db = self._env.open_db(b'metadata')
            self._version_index_db = self._env.open_db(b'version_index')

        except lmdb.Error as e:
            raise RegistryError(f"Failed to initialize LMDB: {e}")

    def list_ids(self) -> Iterable[str]:
        self._ensure_initialized()
        try:
            with self._env.begin(db=self._templates_db, write=False) as txn:
                cursor = txn.cursor()
                for key in cursor.iternext(keys=True, values=False):
                    yield key.decode('utf-8')
        except lmdb.Error as e:
            raise RegistryError(f"Failed to list template IDs: {e}")

    def load(self, template_id: str) -> TemplateSpec:
        self._ensure_initialized()
        try:
            with self._env.begin(db=self._templates_db, write=False) as txn:
                key = template_id.encode('utf-8')
                value = txn.get(key)

                if value is None:
                    raise TemplateNotFound(template_id)

                data = msgpack.unpackb(value, raw=False, strict_map_key=False)
                return TemplateSpec.model_validate(data)

        except TemplateNotFound:
            raise
        except lmdb.Error as e:
            raise RegistryError(f"LMDB error loading template '{template_id}': {e}")
        except Exception as e:
            raise RegistryError(f"Failed to load template '{template_id}': {e}")

    def save(self, spec: TemplateSpec) -> None:
        self._ensure_initialized()
        try:
            data = spec.model_dump()
            packed = msgpack.packb(data, use_bin_type=True)
            template_key = spec.id.encode('utf-8')
            version_key = f"{spec.id}:{spec.version}".encode('utf-8')

            with self._env.begin(write=True) as txn:
                txn.put(template_key, packed, db=self._templates_db)
                txn.put(version_key, template_key, db=self._version_index_db)

                count_key = b"count"
                current_count = txn.get(count_key, db=self._metadata_db)
                if current_count is None:
                    new_count = 1
                else:
                    new_count = msgpack.unpackb(current_count, raw=False) + 1
                txn.put(count_key, msgpack.packb(new_count), db=self._metadata_db)

                timestamp_key = b"last_modified"
                timestamp = int(time.time())
                txn.put(timestamp_key, msgpack.packb(timestamp), db=self._metadata_db)

        except lmdb.Error as e:
            raise RegistryError(f"LMDB error saving template '{spec.id}': {e}")
        except Exception as e:
            raise RegistryError(f"Failed to save template '{spec.id}': {e}")

    def delete(self, template_id: str) -> None:
        self._ensure_initialized()
        try:
            template_key = template_id.encode('utf-8')

            with self._env.begin(write=True) as txn:
                value = txn.get(template_key, db=self._templates_db)
                if value is None:
                    raise TemplateNotFound(template_id)

                data = msgpack.unpackb(value, raw=False, strict_map_key=False)
                version = data.get('version', '0.1.0')
                version_key = f"{template_id}:{version}".encode('utf-8')

                txn.delete(template_key, db=self._templates_db)
                txn.delete(version_key, db=self._version_index_db)

                count_key = b"count"
                current_count = txn.get(count_key, db=self._metadata_db)
                if current_count is not None:
                    new_count = max(0, msgpack.unpackb(current_count, raw=False) - 1)
                    txn.put(count_key, msgpack.packb(new_count), db=self._metadata_db)

                timestamp_key = b"last_modified"
                timestamp = int(time.time())
                txn.put(timestamp_key, msgpack.packb(timestamp), db=self._metadata_db)

        except TemplateNotFound:
            raise
        except lmdb.Error as e:
            raise RegistryError(f"LMDB error deleting template '{template_id}': {e}")
        except Exception as e:
            raise RegistryError(f"Failed to delete template '{template_id}': {e}")

    def get_by_version(self, template_id: str, version: str) -> TemplateSpec:
        self._ensure_initialized()
        try:
            with self._env.begin(db=self._version_index_db, write=False) as txn:
                version_key = f"{template_id}:{version}".encode('utf-8')
                template_key = txn.get(version_key)

                if template_key is None:
                    raise TemplateNotFound(f"{template_id}:{version}")

            return self.load(template_key.decode('utf-8'))

        except TemplateNotFound:
            raise
        except lmdb.Error as e:
            raise RegistryError(f"LMDB error loading template '{template_id}:{version}': {e}")
        except Exception as e:
            raise RegistryError(f"Failed to load template '{template_id}:{version}': {e}")

    def get_metadata(self) -> dict:
        self._ensure_initialized()
        try:
            with self._env.begin(db=self._metadata_db, write=False) as txn:
                count_val = txn.get(b"count")
                timestamp_val = txn.get(b"last_modified")

                return {
                    "count": msgpack.unpackb(count_val, raw=False) if count_val else 0,
                    "last_modified": msgpack.unpackb(timestamp_val, raw=False) if timestamp_val else None
                }
        except lmdb.Error as e:
            raise RegistryError(f"Failed to get metadata: {e}")

    def close(self) -> None:
        if self._env is not None:
            self._env.close()
            self._env = None
            self._templates_db = None
            self._metadata_db = None
            self._version_index_db = None

    def __enter__(self):
        self._ensure_initialized()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()
