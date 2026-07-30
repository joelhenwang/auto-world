"""SQLAlchemy repositories for Stage 4 image pipeline tables."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.images.persistence import (
    AssetObjectRecord,
    GalleryItemRecord,
    ImageJobRecord,
    VisualProfileRecord,
)
from fictional_world.infrastructure.database.errors import NotFoundError
from fictional_world.infrastructure.database.mappings.image_records import (
    asset_object_to_record,
    gallery_item_to_record,
    image_job_to_record,
    visual_profile_to_record,
)
from fictional_world.infrastructure.database.models.images import (
    AssetObjectRow,
    GalleryItemRow,
    ImageJobRow,
    VisualProfileRow,
)


class SqlAlchemyAssetObjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, asset_id: UUID) -> AssetObjectRecord | None:
        row = await self._session.get(AssetObjectRow, asset_id)
        return asset_object_to_record(row) if row is not None else None

    async def get_by_key(self, bucket: str, object_key: str) -> AssetObjectRecord | None:
        result = await self._session.execute(
            select(AssetObjectRow).where(
                AssetObjectRow.bucket == bucket,
                AssetObjectRow.object_key == object_key,
            )
        )
        row = result.scalar_one_or_none()
        return asset_object_to_record(row) if row is not None else None

    async def insert(self, record: AssetObjectRecord) -> AssetObjectRecord:
        stmt = (
            pg_insert(AssetObjectRow)
            .values(
                id=record.id,
                world_id=record.world_id,
                bucket=record.bucket,
                object_key=record.object_key,
                content_type=record.content_type,
                byte_size=record.byte_size,
                checksum_sha256=record.checksum_sha256,
                width_px=record.width_px,
                height_px=record.height_px,
                asset_class=record.asset_class,
                source_job_id=record.source_job_id,
                status=record.status,
                extra_meta=record.extra_meta,
                version=record.version,
            )
            .on_conflict_do_nothing(constraint="uq_asset_object_bucket_object_key")
            .returning(AssetObjectRow)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one()
        return asset_object_to_record(row)

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        asset_class: str | None = None,
        status: str = "active",
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AssetObjectRecord]:
        q = select(AssetObjectRow).where(
            AssetObjectRow.world_id == world_id,
            AssetObjectRow.status == status,
        )
        if asset_class is not None:
            q = q.where(AssetObjectRow.asset_class == asset_class)
        q = q.order_by(AssetObjectRow.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(q)
        return [asset_object_to_record(r) for r in result.scalars().all()]


class SqlAlchemyImageJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, job_id: UUID) -> ImageJobRecord | None:
        row = await self._session.get(ImageJobRow, job_id)
        return image_job_to_record(row) if row is not None else None

    async def get_by_idempotency_key(
        self, world_id: UUID, idempotency_key: str
    ) -> ImageJobRecord | None:
        result = await self._session.execute(
            select(ImageJobRow).where(
                ImageJobRow.world_id == world_id,
                ImageJobRow.idempotency_key == idempotency_key,
            )
        )
        row = result.scalar_one_or_none()
        return image_job_to_record(row) if row is not None else None

    async def insert(self, record: ImageJobRecord) -> ImageJobRecord:
        row = ImageJobRow(
            id=record.id,
            world_id=record.world_id,
            idempotency_key=record.idempotency_key,
            source_event_id=record.source_event_id,
            source_scene_id=record.source_scene_id,
            asset_class=record.asset_class,
            status=record.status,
            priority=record.priority,
            generation_number=record.generation_number,
            attempt=record.attempt,
            max_attempts=record.max_attempts,
            workflow_profile_id=record.workflow_profile_id,
            workflow_version=record.workflow_version,
            external_prompt_id=record.external_prompt_id,
            seed=record.seed,
            width_px=record.width_px,
            height_px=record.height_px,
            prompt_spec=record.prompt_spec,
            visual_profile_versions=record.visual_profile_versions,
            error_class=record.error_class,
            error_detail=record.error_detail,
            version=record.version,
        )
        self._session.add(row)
        await self._session.flush()
        return image_job_to_record(row)

    async def update_status(
        self,
        job_id: UUID,
        *,
        status: str,
        external_prompt_id: str | None = None,
        error_class: str | None = None,
        error_detail: str | None = None,
        expected_version: int,
    ) -> ImageJobRecord:
        row = await self._session.get(ImageJobRow, job_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="image_job", entity_id=str(job_id))
        if row.version != expected_version:
            raise ValueError(
                f"Optimistic version conflict on image_job {job_id}: "
                f"expected {expected_version}, got {row.version}"
            )
        row.status = status
        row.version = row.version + 1
        if external_prompt_id is not None:
            row.external_prompt_id = external_prompt_id
        if error_class is not None:
            row.error_class = error_class
        if error_detail is not None:
            row.error_detail = error_detail
        await self._session.flush()
        return image_job_to_record(row)

    async def increment_attempt(self, job_id: UUID, *, expected_version: int) -> ImageJobRecord:
        row = await self._session.get(ImageJobRow, job_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="image_job", entity_id=str(job_id))
        if row.version != expected_version:
            raise ValueError(
                f"Optimistic version conflict on image_job {job_id}: "
                f"expected {expected_version}, got {row.version}"
            )
        row.attempt = row.attempt + 1
        row.version = row.version + 1
        await self._session.flush()
        return image_job_to_record(row)

    async def list_by_status(
        self,
        world_id: UUID,
        *,
        status: str,
        limit: int = 50,
    ) -> Sequence[ImageJobRecord]:
        result = await self._session.execute(
            select(ImageJobRow)
            .where(ImageJobRow.world_id == world_id, ImageJobRow.status == status)
            .order_by(ImageJobRow.priority.desc(), ImageJobRow.created_at.asc())
            .limit(limit)
        )
        return [image_job_to_record(r) for r in result.scalars().all()]

    async def list_for_event(
        self, world_id: UUID, source_event_id: UUID
    ) -> Sequence[ImageJobRecord]:
        result = await self._session.execute(
            select(ImageJobRow).where(
                ImageJobRow.world_id == world_id,
                ImageJobRow.source_event_id == source_event_id,
            )
        )
        return [image_job_to_record(r) for r in result.scalars().all()]


class SqlAlchemyVisualProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, profile_id: UUID) -> VisualProfileRecord | None:
        row = await self._session.get(VisualProfileRow, profile_id)
        return visual_profile_to_record(row) if row is not None else None

    async def get_active(
        self, world_id: UUID, subject_type: str, subject_id: UUID
    ) -> VisualProfileRecord | None:
        result = await self._session.execute(
            select(VisualProfileRow)
            .where(
                VisualProfileRow.world_id == world_id,
                VisualProfileRow.subject_type == subject_type,
                VisualProfileRow.subject_id == subject_id,
                VisualProfileRow.status == "active",
            )
            .order_by(VisualProfileRow.profile_version.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return visual_profile_to_record(row) if row is not None else None

    async def insert(self, record: VisualProfileRecord) -> VisualProfileRecord:
        row = VisualProfileRow(
            id=record.id,
            world_id=record.world_id,
            subject_type=record.subject_type,
            subject_id=record.subject_id,
            profile_version=record.profile_version,
            valid_from_event_id=record.valid_from_event_id,
            supersedes_profile_id=record.supersedes_profile_id,
            style_spec=record.style_spec,
            negative_constraints=list(record.negative_constraints),
            reference_asset_ids=[str(aid) for aid in record.reference_asset_ids],
            status=record.status,
            version=record.version,
        )
        self._session.add(row)
        await self._session.flush()
        return visual_profile_to_record(row)

    async def supersede(
        self,
        old_profile_id: UUID,
        *,
        expected_version: int,
    ) -> VisualProfileRecord:
        row = await self._session.get(VisualProfileRow, old_profile_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="visual_profile", entity_id=str(old_profile_id))
        if row.version != expected_version:
            raise ValueError(
                f"Optimistic version conflict on visual_profile {old_profile_id}: "
                f"expected {expected_version}, got {row.version}"
            )
        row.status = "superseded"
        row.version = row.version + 1
        await self._session.flush()
        return visual_profile_to_record(row)


class SqlAlchemyGalleryItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, item_id: UUID) -> GalleryItemRecord | None:
        row = await self._session.get(GalleryItemRow, item_id)
        return gallery_item_to_record(row) if row is not None else None

    async def insert(self, record: GalleryItemRecord) -> GalleryItemRecord:
        row = GalleryItemRow(
            id=record.id,
            world_id=record.world_id,
            image_job_id=record.image_job_id,
            asset_object_id=record.asset_object_id,
            source_event_id=record.source_event_id,
            source_scene_id=record.source_scene_id,
            asset_class=record.asset_class,
            display_status=record.display_status,
            is_canonical_illustration=record.is_canonical_illustration,
            qc_passed=record.qc_passed,
            qc_report=record.qc_report,
            version=record.version,
        )
        self._session.add(row)
        await self._session.flush()
        return gallery_item_to_record(row)

    async def update_display_status(
        self,
        item_id: UUID,
        *,
        display_status: str,
        qc_passed: bool | None = None,
        qc_report: dict[str, object] | None = None,
        expected_version: int,
    ) -> GalleryItemRecord:
        row = await self._session.get(GalleryItemRow, item_id, with_for_update=True)
        if row is None:
            raise NotFoundError(entity="gallery_item", entity_id=str(item_id))
        if row.version != expected_version:
            raise ValueError(
                f"Optimistic version conflict on gallery_item {item_id}: "
                f"expected {expected_version}, got {row.version}"
            )
        row.display_status = display_status
        if qc_passed is not None:
            row.qc_passed = qc_passed
        if qc_report is not None:
            row.qc_report = qc_report  # type: ignore[assignment]
        row.version = row.version + 1
        await self._session.flush()
        return gallery_item_to_record(row)

    async def list_for_world(
        self,
        world_id: UUID,
        *,
        display_status: str | None = None,
        source_event_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[GalleryItemRecord]:
        q = select(GalleryItemRow).where(GalleryItemRow.world_id == world_id)
        if display_status is not None:
            q = q.where(GalleryItemRow.display_status == display_status)
        if source_event_id is not None:
            q = q.where(GalleryItemRow.source_event_id == source_event_id)
        q = q.order_by(GalleryItemRow.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(q)
        return [gallery_item_to_record(r) for r in result.scalars().all()]
