"""Action/scene/reaction/stream ORM tables (Stage 1 / S1-DB-001)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
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
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class ActionProposalRow(Base):
    __tablename__ = "action_proposal"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        CheckConstraint(
            "proposal_kind IN ('primary', 'fallback', 'continuation')",
            name="proposal_kind",
        ),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'rejected')",
            name="validation_status",
        ),
        CheckConstraint(
            "risk_tolerance >= 0 AND risk_tolerance <= 1",
            name="risk_tolerance_range",
        ),
        CheckConstraint(
            "estimated_duration_phases >= 1 AND estimated_duration_phases <= 240",
            name="duration_range",
        ),
        CheckConstraint("generation >= 0", name="generation_nonneg"),
        Index(
            "uq_action_proposal_primary_actor_phase",
            "phase_run_id",
            "actor_id",
            unique=True,
            postgresql_where=text("proposal_kind = 'primary'"),
        ),
        Index("ix_action_proposal_snapshot", "snapshot_id"),
        Index("ix_action_proposal_phase", "phase_run_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    phase_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=False,
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_snapshot.id"),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    proposal_kind: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'primary'")
    )
    action_family: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    utterance: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    visibility: Mapped[str] = mapped_column(Text, nullable=False)
    risk_tolerance: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.5000")
    )
    estimated_duration_phases: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("1")
    )
    continuation_activity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    desired_effects: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    fallback_action: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    validation_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    validation_errors: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    generation: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ActionTargetRow(Base):
    __tablename__ = "action_target"
    __table_args__ = (
        CheckConstraint("ordinal >= 0", name="ordinal_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    action_proposal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.action_proposal.id"),
        primary_key=True,
    )
    target_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        primary_key=True,
    )
    target_role: Mapped[str] = mapped_column(Text, primary_key=True)
    ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))


class SceneRow(Base):
    __tablename__ = "scene"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 1",
            name="priority_score_range",
        ),
        CheckConstraint("beat_budget >= 1 AND beat_budget <= 12", name="beat_budget_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_scene_phase_run", "phase_run_id"),
        Index("ix_scene_snapshot", "snapshot_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    phase_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=False,
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_snapshot.id"),
        nullable=False,
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    scene_type: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    priority_breakdown: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    beat_budget: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    high_impact: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    mutable_aggregate_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=True
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class SceneActionRow(Base):
    __tablename__ = "scene_action"
    __table_args__ = (
        CheckConstraint(
            "role IN ('initiator', 'co_intent', 'conflicting_intent', 'background')",
            name="scene_action_role",
        ),
        CheckConstraint("ordinal >= 0", name="ordinal_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        primary_key=True,
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.action_proposal.id"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))


class SceneParticipantRow(Base):
    __tablename__ = "scene_participant"
    __table_args__ = (
        CheckConstraint("joined_at_beat >= 0", name="joined_beat_nonneg"),
        CheckConstraint(
            "left_at_beat IS NULL OR left_at_beat >= joined_at_beat",
            name="left_beat_order",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        primary_key=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        primary_key=True,
    )
    participant_role: Mapped[str] = mapped_column(Text, nullable=False)
    reaction_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    knowledge_scope_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    joined_at_beat: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    left_at_beat: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)


class ReactionProposalRow(Base):
    __tablename__ = "reaction_proposal"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        UniqueConstraint("scene_id", "reactor_id", "beat_index", "triggering_attempt_id"),
        CheckConstraint("beat_index >= 0 AND beat_index <= 12", name="beat_index_range"),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'rejected')",
            name="validation_status",
        ),
        CheckConstraint(
            "source_kind IN ('model', 'deterministic', 'player', 'engine')",
            name="source_kind",
        ),
        Index("ix_reaction_proposal_scene", "scene_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        nullable=False,
    )
    phase_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=False,
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_snapshot.id"),
        nullable=False,
    )
    triggering_attempt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.action_proposal.id"),
        nullable=False,
    )
    reactor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    beat_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    action_family: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    utterance: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_entity_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=True
    )
    resource_intentions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    desired_outcomes: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    validation_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    validation_errors: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    source_kind: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'model'"))
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SceneResolutionRow(Base):
    __tablename__ = "scene_resolution"
    __table_args__ = (
        UniqueConstraint("scene_id"),
        UniqueConstraint("idempotency_key"),
        UniqueConstraint("commit_event_id"),
        CheckConstraint(
            "visual_significance >= 0 AND visual_significance <= 1",
            name="visual_significance_range",
        ),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'committed', 'rejected')",
            name="validation_status",
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        nullable=False,
    )
    resolution_level: Mapped[str] = mapped_column(Text, nullable=False)
    accepted_attempt_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=True
    )
    rejected_assumptions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    proposed_effects: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    delayed_effects: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    observation_seeds: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    narration_constraints: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    visual_significance: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    resolver_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_profile.id"),
        nullable=True,
    )
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    expected_aggregate_versions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    validation_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    commit_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    canonical_summary: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SceneRunRow(Base):
    __tablename__ = "scene_run"
    __table_args__ = (
        UniqueConstraint("scene_id"),
        UniqueConstraint("idempotency_key"),
        CheckConstraint("beat_count >= 0", name="beat_count_nonneg"),
        CheckConstraint("beat_budget >= 1 AND beat_budget <= 12", name="beat_budget_range"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_scene_run_phase", "phase_run_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        nullable=False,
    )
    phase_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    beat_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    beat_budget: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    high_impact: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    resolution_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene_resolution.id"),
        nullable=True,
    )
    committed_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    attempt_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_detail: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class NarrationRow(Base):
    __tablename__ = "narration"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        UniqueConstraint("scene_id", "perspective", "content_hash"),
        Index("ix_narration_world_event", "world_event_id"),
        Index("ix_narration_scene", "scene_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        nullable=False,
    )
    world_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=False,
    )
    perspective: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StreamEventRow(Base):
    __tablename__ = "stream_event"
    __table_args__ = (
        UniqueConstraint("world_id", "sequence"),
        UniqueConstraint("idempotency_key"),
        CheckConstraint("sequence >= 1", name="sequence_positive"),
        Index("ix_stream_event_world_seq", "world_id", "sequence"),
        Index("ix_stream_event_type", "event_type"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fictional_time: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    payload: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    schema_version: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'1'"))
    phase_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=True,
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.scene.id"),
        nullable=True,
    )
    world_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    perspective_scope: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'world'")
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PlayerControlSessionRow(Base):
    __tablename__ = "player_control_session"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        CheckConstraint(
            "status IN ('active', 'waiting_input', 'released', 'expired')",
            name="player_control_status",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index(
            "uq_player_control_one_active_per_character",
            "character_id",
            unique=True,
            postgresql_where=text("status IN ('active', 'waiting_input')"),
        ),
        Index("ix_player_control_world", "world_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"),
        nullable=False,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    controller_id: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    waiting_input: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    phase_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.phase_run.id"),
        nullable=True,
    )
    last_command_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.user_command.id"),
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
