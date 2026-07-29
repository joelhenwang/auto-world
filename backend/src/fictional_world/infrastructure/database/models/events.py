"""Canonical event ORM tables (handbook ``06`` §10)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class WorldEventRow(Base):
    __tablename__ = "world_event"
    __table_args__ = (
        UniqueConstraint("world_id", "sequence_number"),
        UniqueConstraint("idempotency_key"),
        CheckConstraint("sequence_number >= 1", name="sequence_positive"),
        CheckConstraint("absolute_phase_index >= 0", name="absolute_phase_nonneg"),
        CheckConstraint("importance >= 0 AND importance <= 1", name="importance_range"),
        Index(
            "ix_world_event_timeline",
            "world_id",
            "absolute_phase_index",
            "sequence_number",
        ),
        Index("ix_world_event_type", "event_type"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    absolute_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    phase_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id", use_alter=True),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    initiator_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        nullable=True,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    canonical_summary: Mapped[str] = mapped_column(Text, nullable=False)
    structured_facts: Mapped[object] = mapped_column(JSONB, nullable=False)
    importance: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    visibility_class: Mapped[str] = mapped_column(Text, nullable=False)
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    source_model_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_profile.id"),
        nullable=True,
    )
    prompt_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    random_seed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    supersedes_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    consistency_status: Mapped[str] = mapped_column(Text, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EventEffectRow(Base):
    __tablename__ = "event_effect"
    __table_args__ = (
        UniqueConstraint("world_event_id", "effect_index"),
        CheckConstraint("effect_index >= 0", name="effect_index_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=False,
    )
    effect_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    effect_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        nullable=True,
    )
    effect_payload: Mapped[object] = mapped_column(JSONB, nullable=False)
    previous_state: Mapped[object] = mapped_column(JSONB, nullable=False)
    resulting_state: Mapped[object] = mapped_column(JSONB, nullable=False)
    target_version_before: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target_version_after: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_attempt_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=True
    )
    validation_manifest: Mapped[object] = mapped_column(JSONB, nullable=False)
