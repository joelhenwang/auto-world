"""ORM models for Stage 4 object storage, image jobs, visual profiles, gallery.

Tables: asset_object, image_job, visual_profile, gallery_item.
Migration: 0007_stage4_img.
Handbook: 16 §6/§14; 29 S4-STORAGE-001, S4-IMG-001/002/003.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class AssetObjectRow(Base):
    """Binary asset envelope; the actual bytes live in object storage."""

    __tablename__ = "asset_object"
    __table_args__ = (
        UniqueConstraint("bucket", "object_key", name="uq_asset_object_bucket_object_key"),
        CheckConstraint(
            "byte_size >= 0",
            name="ck_asset_object_byte_size_nonneg",
        ),
        CheckConstraint(
            "status IN ('active', 'deleted', 'orphan')",
            name="ck_asset_object_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_asset_object_version_pos",
        ),
        Index("ix_asset_object_world_class", "world_id", "asset_class"),
        Index("ix_asset_object_job", "source_job_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    bucket: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    checksum_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    asset_class: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'UNKNOWN'")
    )
    source_job_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    extra_meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class ImageJobRow(Base):
    """ComfyUI image generation job record.  idempotency_key is unique per world."""

    __tablename__ = "image_job"
    __table_args__ = (
        UniqueConstraint(
            "world_id", "idempotency_key", name="uq_image_job_world_idempotency_key"
        ),
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','rejected',"
            "'approved','cancelled','dead_letter')",
            name="ck_image_job_status",
        ),
        CheckConstraint("priority >= 0 AND priority <= 100", name="ck_image_job_priority"),
        CheckConstraint("generation_number >= 1", name="ck_image_job_generation_number_pos"),
        CheckConstraint("attempt >= 0", name="ck_image_job_attempt_nonneg"),
        CheckConstraint("max_attempts >= 1", name="ck_image_job_max_attempts_pos"),
        CheckConstraint("version >= 1", name="ck_image_job_version_pos"),
        Index("ix_image_job_world_status", "world_id", "status"),
        Index("ix_image_job_source_event", "source_event_id"),
        Index("ix_image_job_source_scene", "source_scene_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    source_scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    asset_class: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'EVENT_CG'")
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'queued'")
    )
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("50")
    )
    generation_number: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    max_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("3")
    )
    workflow_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    workflow_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_prompt_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_spec: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    visual_profile_versions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    error_class: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class VisualProfileRow(Base):
    """Versioned visual style profile for a character, location, or world."""

    __tablename__ = "visual_profile"
    __table_args__ = (
        UniqueConstraint(
            "world_id",
            "subject_type",
            "subject_id",
            "profile_version",
            name="uq_visual_profile_world_subject_version",
        ),
        CheckConstraint(
            "subject_type IN ('character', 'location', 'world')",
            name="ck_visual_profile_subject_type",
        ),
        CheckConstraint("profile_version >= 1", name="ck_visual_profile_version_pos"),
        CheckConstraint(
            "status IN ('active', 'superseded', 'draft')",
            name="ck_visual_profile_status",
        ),
        CheckConstraint("version >= 1", name="ck_visual_profile_optimistic_version_pos"),
        Index("ix_visual_profile_world_subject", "world_id", "subject_type", "subject_id"),
        Index(
            "ix_visual_profile_world_subject_active",
            "world_id",
            "subject_type",
            "subject_id",
            "status",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    subject_type: Mapped[str] = mapped_column(Text, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    profile_version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )
    valid_from_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    supersedes_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    style_spec: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    negative_constraints: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    reference_asset_ids: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class GalleryItemRow(Base):
    """Display record linking an image_job to its selected output asset."""

    __tablename__ = "gallery_item"
    __table_args__ = (
        CheckConstraint(
            "display_status IN ('auto_selected','user_selected','rejected','hidden','superseded')",
            name="ck_gallery_item_display_status",
        ),
        CheckConstraint("version >= 1", name="ck_gallery_item_version_pos"),
        Index("ix_gallery_item_world_event", "world_id", "source_event_id"),
        Index("ix_gallery_item_world_status", "world_id", "display_status"),
        Index("ix_gallery_item_job", "image_job_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    image_job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.image_job.id"),
        nullable=False,
    )
    asset_object_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.asset_object.id"),
        nullable=False,
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    source_scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    asset_class: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'EVENT_CG'")
    )
    display_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'auto_selected'")
    )
    is_canonical_illustration: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    qc_passed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    qc_report: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
