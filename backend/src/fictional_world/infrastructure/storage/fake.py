"""In-memory object store for offline tests (S4-STORAGE-001).

Thread-safe for the same event loop; does NOT persist across process restarts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fictional_world.application.ports.storage import (
    ObjectMetadata,
    PutResult,
    StorageConflictError,
    StorageNotFoundError,
)


@dataclass
class _Entry:
    data: bytes
    content_type: str
    checksum_sha256: str
    extra_meta: dict[str, str]


class FakeObjectStore:
    """Deterministic in-memory adapter — satisfies ObjectStoragePort."""

    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, _Entry]] = {}

    # ------------------------------------------------------------------
    # ObjectStoragePort implementation
    # ------------------------------------------------------------------

    async def put(
        self,
        bucket: str,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        extra_meta: dict[str, str] | None = None,
    ) -> PutResult:
        checksum = hashlib.sha256(data).hexdigest()
        bucket_store = self._buckets.setdefault(bucket, {})
        existing = bucket_store.get(key)
        if existing is not None and existing.checksum_sha256 != checksum:
            raise StorageConflictError(bucket, key)
        bucket_store[key] = _Entry(
            data=data,
            content_type=content_type,
            checksum_sha256=checksum,
            extra_meta=dict(extra_meta or {}),
        )
        return PutResult(
            bucket=bucket,
            key=key,
            byte_size=len(data),
            checksum_sha256=checksum,
        )

    async def get(self, bucket: str, key: str) -> bytes:
        entry = self._buckets.get(bucket, {}).get(key)
        if entry is None:
            raise StorageNotFoundError(bucket, key)
        return entry.data

    async def head(self, bucket: str, key: str) -> ObjectMetadata:
        entry = self._buckets.get(bucket, {}).get(key)
        if entry is None:
            raise StorageNotFoundError(bucket, key)
        return ObjectMetadata(
            bucket=bucket,
            key=key,
            byte_size=len(entry.data),
            content_type=entry.content_type,
            checksum_sha256=entry.checksum_sha256,
            extra_meta=dict(entry.extra_meta),
        )

    async def delete(self, bucket: str, key: str) -> None:
        self._buckets.get(bucket, {}).pop(key, None)

    async def exists(self, bucket: str, key: str) -> bool:
        return key in self._buckets.get(bucket, {})

    async def ensure_bucket(self, bucket: str) -> None:
        self._buckets.setdefault(bucket, {})

    # ------------------------------------------------------------------
    # Introspection helpers for tests
    # ------------------------------------------------------------------

    def list_keys(self, bucket: str) -> list[str]:
        """Return all keys in *bucket*; empty list if bucket absent."""
        return list(self._buckets.get(bucket, {}).keys())

    def key_count(self, bucket: str) -> int:
        return len(self._buckets.get(bucket, {}))

    def reset(self) -> None:
        """Clear all buckets — useful between tests."""
        self._buckets.clear()
