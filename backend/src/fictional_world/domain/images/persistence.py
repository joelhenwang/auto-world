"""Persistence records for object storage, image jobs, visual profiles, and gallery.

Handbook: 16 §6, §7, §14; 29 §S4-STORAGE-001, S4-IMG-001/002/003.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

# ---------------------------------------------------------------------------
# asset_object — binary asset metadata stored in object storage
# ---------------------------------------------------------------------------

IMAGE_JOB_STATUSES = frozenset(
    {
        "queued",
        "running",
        "succeeded",
        "failed",
        "rejected",
        "approved",
        "cancelled",
        "dead_letter",
    }
)

VISUAL_PROFILE_SUBJECTS = frozenset({"character", "location", "world"})

GALLERY_DISPLAY_STATUSES = frozenset(
    {"auto_selected", "user_selected", "rejected", "hidden", "superseded"}
)


class AssetObjectRecord(StrictContract):
    """Metadata row for a binary asset stored in object storage.

    The binary itself lives at ``bucket/object_key``; PostgreSQL stores only
    the envelope.
    """

    id: UUID
    world_id: UUID
    bucket: str = Field(min_length=1, max_length=200)
    object_key: str = Field(min_length=1, max_length=1000)
    content_type: str = Field(min_length=1, max_length=200)
    byte_size: int = Field(ge=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)
    width_px: int | None = Field(default=None, ge=1)
    height_px: int | None = Field(default=None, ge=1)
    asset_class: str = Field(min_length=1, max_length=80)
    source_job_id: UUID | None = None
    status: str = Field(default="active", min_length=1, max_length=50)
    extra_meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    version: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# image_job — ComfyUI image generation job (handbook 16 §6)
# ---------------------------------------------------------------------------


class ImageJobRecord(StrictContract):
    """One image generation job.  idempotency_key must be unique per world."""

    id: UUID
    world_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=200)
    source_event_id: UUID | None = None
    source_scene_id: UUID | None = None
    asset_class: str = Field(min_length=1, max_length=80)
    status: str = Field(default="queued", min_length=1, max_length=50)
    priority: int = Field(default=50, ge=0, le=100)
    generation_number: int = Field(default=1, ge=1)
    attempt: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    workflow_profile_id: UUID | None = None
    workflow_version: str | None = Field(default=None, max_length=100)
    external_prompt_id: str | None = Field(default=None, max_length=200)
    seed: int | None = None
    width_px: int | None = Field(default=None, ge=1)
    height_px: int | None = Field(default=None, ge=1)
    prompt_spec: dict[str, Any] = Field(default_factory=dict)
    visual_profile_versions: dict[str, Any] = Field(default_factory=dict)
    error_class: str | None = Field(default=None, max_length=100)
    error_detail: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    version: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# visual_profile — versioned style profiles for characters/locations/world
# ---------------------------------------------------------------------------


class VisualProfileRecord(StrictContract):
    """Versioned visual profile for a character, location, or world style.

    ``subject_type`` ∈ {'character', 'location', 'world'}.
    ``subject_id`` references the relevant entity (character entity_id,
    location entity_id, or world id) depending on subject_type.
    """

    id: UUID
    world_id: UUID
    subject_type: str = Field(min_length=1, max_length=50)
    subject_id: UUID
    profile_version: int = Field(ge=1)
    valid_from_event_id: UUID | None = None
    supersedes_profile_id: UUID | None = None
    style_spec: dict[str, Any] = Field(default_factory=dict)
    negative_constraints: list[str] = Field(default_factory=list)
    reference_asset_ids: list[UUID] = Field(default_factory=list)
    status: str = Field(default="active", min_length=1, max_length=50)
    created_at: datetime | None = None
    version: int = Field(default=1, ge=1)


# ---------------------------------------------------------------------------
# gallery_item — resolved display record linking job → asset
# ---------------------------------------------------------------------------


class GalleryItemRecord(StrictContract):
    """Display record connecting an image job to its selected output asset.

    ``display_status`` ∈ {'auto_selected', 'user_selected', 'rejected',
    'hidden', 'superseded'}.
    """

    id: UUID
    world_id: UUID
    image_job_id: UUID
    asset_object_id: UUID
    source_event_id: UUID | None = None
    source_scene_id: UUID | None = None
    asset_class: str = Field(min_length=1, max_length=80)
    display_status: str = Field(default="auto_selected", min_length=1, max_length=50)
    is_canonical_illustration: bool = False
    qc_passed: bool = False
    qc_report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    version: int = Field(default=1, ge=1)
