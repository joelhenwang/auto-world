"""Map Stage 4 image ORM rows to domain persistence records."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from fictional_world.domain.images.persistence import (
    AssetObjectRecord,
    GalleryItemRecord,
    ImageJobRecord,
    VisualProfileRecord,
)
from fictional_world.infrastructure.database.models.images import (
    AssetObjectRow,
    GalleryItemRow,
    ImageJobRow,
    VisualProfileRow,
)


def _as_dict(value: object | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def _as_uuid_list(value: object | None) -> list[UUID]:
    if isinstance(value, list):
        return [UUID(str(v)) if not isinstance(v, UUID) else v for v in cast(list[Any], value)]
    return []


def _as_str_list(value: object | None) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in cast(list[Any], value)]
    return []


def asset_object_to_record(row: AssetObjectRow) -> AssetObjectRecord:
    return AssetObjectRecord(
        id=row.id,
        world_id=row.world_id,
        bucket=row.bucket,
        object_key=row.object_key,
        content_type=row.content_type,
        byte_size=row.byte_size,
        checksum_sha256=row.checksum_sha256,
        width_px=row.width_px,
        height_px=row.height_px,
        asset_class=row.asset_class,
        source_job_id=row.source_job_id,
        status=row.status,
        extra_meta=_as_dict(row.extra_meta),
        created_at=row.created_at,
        version=row.version,
    )


def image_job_to_record(row: ImageJobRow) -> ImageJobRecord:
    return ImageJobRecord(
        id=row.id,
        world_id=row.world_id,
        idempotency_key=row.idempotency_key,
        source_event_id=row.source_event_id,
        source_scene_id=row.source_scene_id,
        asset_class=row.asset_class,
        status=row.status,
        priority=row.priority,
        generation_number=row.generation_number,
        attempt=row.attempt,
        max_attempts=row.max_attempts,
        workflow_profile_id=row.workflow_profile_id,
        workflow_version=row.workflow_version,
        external_prompt_id=row.external_prompt_id,
        seed=row.seed,
        width_px=row.width_px,
        height_px=row.height_px,
        prompt_spec=_as_dict(row.prompt_spec),
        visual_profile_versions=_as_dict(row.visual_profile_versions),
        error_class=row.error_class,
        error_detail=row.error_detail,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
        version=row.version,
    )


def visual_profile_to_record(row: VisualProfileRow) -> VisualProfileRecord:
    return VisualProfileRecord(
        id=row.id,
        world_id=row.world_id,
        subject_type=row.subject_type,
        subject_id=row.subject_id,
        profile_version=row.profile_version,
        valid_from_event_id=row.valid_from_event_id,
        supersedes_profile_id=row.supersedes_profile_id,
        style_spec=_as_dict(row.style_spec),
        negative_constraints=_as_str_list(row.negative_constraints),
        reference_asset_ids=_as_uuid_list(row.reference_asset_ids),
        status=row.status,
        created_at=row.created_at,
        version=row.version,
    )


def gallery_item_to_record(row: GalleryItemRow) -> GalleryItemRecord:
    return GalleryItemRecord(
        id=row.id,
        world_id=row.world_id,
        image_job_id=row.image_job_id,
        asset_object_id=row.asset_object_id,
        source_event_id=row.source_event_id,
        source_scene_id=row.source_scene_id,
        asset_class=row.asset_class,
        display_status=row.display_status,
        is_canonical_illustration=row.is_canonical_illustration,
        qc_passed=row.qc_passed,
        qc_report=_as_dict(row.qc_report),
        created_at=row.created_at,
        version=row.version,
    )
