"""Image pipeline repository ports (S4-STORAGE-001, S4-IMG-001/002/003)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from fictional_world.domain.images.persistence import (
    AssetObjectRecord,
    GalleryItemRecord,
    ImageJobRecord,
    VisualProfileRecord,
)


class AssetObjectRepository(Protocol):
    async def get(self, asset_id: UUID) -> AssetObjectRecord | None: ...

    async def get_by_key(self, bucket: str, object_key: str) -> AssetObjectRecord | None: ...

    async def insert(self, record: AssetObjectRecord) -> AssetObjectRecord: ...

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        asset_class: str | None = None,
        status: str = "active",
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AssetObjectRecord]: ...


class ImageJobRepository(Protocol):
    async def get(self, job_id: UUID) -> ImageJobRecord | None: ...

    async def get_by_idempotency_key(
        self, world_id: UUID, idempotency_key: str
    ) -> ImageJobRecord | None: ...

    async def insert(self, record: ImageJobRecord) -> ImageJobRecord: ...

    async def update_status(
        self,
        job_id: UUID,
        *,
        status: str,
        external_prompt_id: str | None = None,
        error_class: str | None = None,
        error_detail: str | None = None,
        expected_version: int,
    ) -> ImageJobRecord: ...

    async def increment_attempt(self, job_id: UUID, *, expected_version: int) -> ImageJobRecord: ...

    async def list_by_status(
        self,
        world_id: UUID,
        *,
        status: str,
        limit: int = 50,
    ) -> Sequence[ImageJobRecord]: ...

    async def list_for_event(
        self, world_id: UUID, source_event_id: UUID
    ) -> Sequence[ImageJobRecord]: ...


class VisualProfileRepository(Protocol):
    async def get(self, profile_id: UUID) -> VisualProfileRecord | None: ...

    async def get_active(
        self, world_id: UUID, subject_type: str, subject_id: UUID
    ) -> VisualProfileRecord | None: ...

    async def insert(self, record: VisualProfileRecord) -> VisualProfileRecord: ...

    async def supersede(
        self, old_profile_id: UUID, *, expected_version: int
    ) -> VisualProfileRecord: ...


class GalleryItemRepository(Protocol):
    async def get(self, item_id: UUID) -> GalleryItemRecord | None: ...

    async def insert(self, record: GalleryItemRecord) -> GalleryItemRecord: ...

    async def update_display_status(
        self,
        item_id: UUID,
        *,
        display_status: str,
        qc_passed: bool | None = None,
        qc_report: dict[str, object] | None = None,
        expected_version: int,
    ) -> GalleryItemRecord: ...

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        display_status: str | None = None,
        source_event_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[GalleryItemRecord]: ...
