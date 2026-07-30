"""Unit tests for FakeObjectStore (S4-STORAGE-001)."""

from __future__ import annotations

import hashlib

import pytest

from fictional_world.application.ports.storage import (
    StorageConflictError,
    StorageNotFoundError,
)
from fictional_world.infrastructure.storage.fake import FakeObjectStore


@pytest.mark.unit
@pytest.mark.asyncio
async def test_put_and_get_roundtrip() -> None:
    store = FakeObjectStore()
    data = b"hello world"
    result = await store.put("bucket-a", "key/foo.txt", data)
    assert result.byte_size == len(data)
    assert result.checksum_sha256 == hashlib.sha256(data).hexdigest()
    retrieved = await store.get("bucket-a", "key/foo.txt")
    assert retrieved == data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_put_idempotent_same_content() -> None:
    store = FakeObjectStore()
    data = b"same content"
    r1 = await store.put("b", "k", data)
    r2 = await store.put("b", "k", data)
    assert r1.checksum_sha256 == r2.checksum_sha256


@pytest.mark.unit
@pytest.mark.asyncio
async def test_put_conflict_different_content() -> None:
    store = FakeObjectStore()
    await store.put("b", "k", b"original")
    with pytest.raises(StorageConflictError):
        await store.put("b", "k", b"different")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_missing_raises() -> None:
    store = FakeObjectStore()
    with pytest.raises(StorageNotFoundError):
        await store.get("no-bucket", "no-key")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_head_returns_metadata() -> None:
    store = FakeObjectStore()
    data = b"metadata test"
    await store.put("b", "k", data, content_type="image/png")
    meta = await store.head("b", "k")
    assert meta.byte_size == len(data)
    assert meta.content_type == "image/png"
    assert len(meta.checksum_sha256) == 64


@pytest.mark.unit
@pytest.mark.asyncio
async def test_head_missing_raises() -> None:
    store = FakeObjectStore()
    with pytest.raises(StorageNotFoundError):
        await store.head("b", "missing")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_removes_object() -> None:
    store = FakeObjectStore()
    await store.put("b", "k", b"data")
    assert await store.exists("b", "k")
    await store.delete("b", "k")
    assert not await store.exists("b", "k")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_missing_is_noop() -> None:
    store = FakeObjectStore()
    await store.delete("b", "ghost")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_ensure_bucket_creates() -> None:
    store = FakeObjectStore()
    await store.ensure_bucket("new-bucket")
    assert store.key_count("new-bucket") == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_keys() -> None:
    store = FakeObjectStore()
    await store.put("b", "a", b"1")
    await store.put("b", "b", b"2")
    keys = store.list_keys("b")
    assert set(keys) == {"a", "b"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reset_clears_all() -> None:
    store = FakeObjectStore()
    await store.put("b", "k", b"x")
    store.reset()
    assert store.key_count("b") == 0
