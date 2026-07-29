"""Model profile and call ORM tables (handbook ``06`` §16)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class ModelProfileRow(Base):
    __tablename__ = "model_profile"
    __table_args__ = (
        CheckConstraint("context_limit > 0", name="context_limit_positive"),
        CheckConstraint("application_input_limit > 0", name="app_input_limit_positive"),
        CheckConstraint("max_output_tokens >= 0", name="max_output_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    profile_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    logical_role: Mapped[str] = mapped_column(Text, nullable=False)
    provider_adapter: Mapped[str] = mapped_column(Text, nullable=False)
    model_slug: Mapped[str] = mapped_column(Text, nullable=False)
    endpoint_type: Mapped[str] = mapped_column(Text, nullable=False)
    context_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    application_input_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    sampling_configuration: Mapped[object] = mapped_column(JSONB, nullable=False)
    structured_output_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    privacy_classification: Mapped[str] = mapped_column(Text, nullable=False)
    capability_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    active_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    active_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ModelCallRow(Base):
    __tablename__ = "model_call"
    __table_args__ = (
        CheckConstraint("attempt_number >= 1", name="attempt_positive"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=True,
    )
    phase_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=True,
    )
    task_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.task_run.id", use_alter=True),
        nullable=True,
    )
    model_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_profile.id"),
        nullable=False,
    )
    prompt_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    context_manifest: Mapped[object] = mapped_column(JSONB, nullable=False)
    request_hash: Mapped[str] = mapped_column(Text, nullable=False)
    response_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_request_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_request_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
