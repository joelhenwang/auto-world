"""Phase run and snapshot ORM tables (handbook ``06`` §8)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA

_PHASE_TERMINAL = "('completed', 'failed', 'cancelled')"


class PhaseRunRow(Base):
    __tablename__ = "phase_run"
    __table_args__ = (
        UniqueConstraint("world_id", "absolute_phase_index"),
        UniqueConstraint("idempotency_key"),
        CheckConstraint("absolute_phase_index >= 0", name="absolute_phase_nonneg"),
        CheckConstraint("expected_character_count >= 0", name="expected_character_nonneg"),
        CheckConstraint("completed_character_count >= 0", name="completed_character_nonneg"),
        CheckConstraint("completed_scene_count >= 0", name="completed_scene_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        CheckConstraint(
            "resolution_mode IN ('detailed', 'day', 'week', 'month', 'year')",
            name="resolution_mode",
        ),
        Index(
            "uq_phase_run_one_nonterminal_per_world",
            "world_id",
            unique=True,
            postgresql_where=text(f"state NOT IN {_PHASE_TERMINAL}"),
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    absolute_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    phase_name: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_mode: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    expected_character_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    completed_character_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    expected_scene_count: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    completed_scene_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    request_reservation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class PhaseSnapshotRow(Base):
    __tablename__ = "phase_snapshot"
    __table_args__ = ({"schema": WORLDSIM_SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    phase_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=False,
        unique=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    source_event_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    world_clock_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state_manifest: Mapped[object] = mapped_column(JSONB, nullable=False)
    state_hash: Mapped[str] = mapped_column(Text, nullable=False)
    sealed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PhaseSnapshotCharacterRow(Base):
    __tablename__ = "phase_snapshot_character"
    __table_args__ = ({"schema": WORLDSIM_SCHEMA},)

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_snapshot.id"),
        primary_key=True,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    character_state_version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    card_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character_card_version.id"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    active_activity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    context_source_hash: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_status: Mapped[str] = mapped_column(Text, nullable=False)
    eligibility_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
