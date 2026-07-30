"""Object storage adapters (S4-STORAGE-001)."""

from fictional_world.infrastructure.storage.fake import FakeObjectStore
from fictional_world.infrastructure.storage.minio_adapter import MinioObjectStore

__all__ = ["FakeObjectStore", "MinioObjectStore"]
