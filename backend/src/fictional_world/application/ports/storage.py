"""Object storage port — S3-compatible put/get/head/delete with checksums.

Handbook: 29 S4-STORAGE-001; 16 §14.  Adapters: FakeObjectStore (tests),
MinioObjectStore (production).  Protocol methods are async to support
non-blocking I/O; application logic must not call them while a DB transaction
is open (handbook §4.3 / §11).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ObjectMetadata:
    """Lightweight stat result returned by ``head``."""

    bucket: str
    key: str
    byte_size: int
    content_type: str
    checksum_sha256: str
    extra_meta: dict[str, str]


@dataclass(frozen=True)
class PutResult:
    """Confirmation returned by ``put``."""

    bucket: str
    key: str
    byte_size: int
    checksum_sha256: str


class ObjectStoragePort(Protocol):
    """Port for content-addressed object storage (handbook §4.1 non-canon boundary)."""

    async def put(
        self,
        bucket: str,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
        extra_meta: dict[str, str] | None = None,
    ) -> PutResult:
        """Upload ``data`` to ``bucket/key``.

        Returns computed checksum for idempotent verification.
        Raises ``StorageConflictError`` if the key already exists with a
        different checksum (immutable-object policy).
        """
        ...

    async def get(self, bucket: str, key: str) -> bytes:
        """Download and return the full object bytes.

        Raises ``StorageNotFoundError`` if the object does not exist.
        """
        ...

    async def head(self, bucket: str, key: str) -> ObjectMetadata:
        """Return metadata without downloading the body.

        Raises ``StorageNotFoundError`` if the object does not exist.
        """
        ...

    async def delete(self, bucket: str, key: str) -> None:
        """Delete the object.  No-op if already absent."""
        ...

    async def exists(self, bucket: str, key: str) -> bool:
        """Return True if the object exists."""
        ...

    async def ensure_bucket(self, bucket: str) -> None:
        """Create the bucket if it does not exist."""
        ...


class StorageNotFoundError(Exception):
    """Raised when an object key does not exist in the store."""

    def __init__(self, bucket: str, key: str) -> None:
        super().__init__(f"Object not found: {bucket}/{key}")
        self.bucket = bucket
        self.key = key


class StorageConflictError(Exception):
    """Raised when a put would overwrite an immutable object with different content."""

    def __init__(self, bucket: str, key: str) -> None:
        super().__init__(f"Immutable object conflict: {bucket}/{key}")
        self.bucket = bucket
        self.key = key
