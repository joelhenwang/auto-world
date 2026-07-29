"""Stage 2 continuity ORM tables (goals, plans, activities, travel, hooks, NPCs)."""

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
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
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


class RouteRow(Base):
    __tablename__ = "route"
    __table_args__ = (
        CheckConstraint("distance_units > 0", name="distance_units_positive"),
        CheckConstraint("base_duration_phases > 0", name="base_duration_phases_positive"),
        CheckConstraint("danger_level >= 0 AND danger_level <= 1", name="danger_level_range"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index(
            "uq_route_active_identity",
            "world_id",
            "origin_location_id",
            "destination_location_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_route_world", "world_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    origin_location_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=False,
    )
    destination_location_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=False,
    )
    is_bidirectional: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    distance_units: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    base_duration_phases: Mapped[int] = mapped_column(Integer, nullable=False)
    allowed_travel_modes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    terrain_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    danger_level: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    seasonal_modifiers: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    created_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class GoalRow(Base):
    __tablename__ = "goal"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_goal_owner", "world_id", "owner_character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, server_default=text("0.5000")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    horizon: Mapped[str | None] = mapped_column(Text, nullable=True)
    success_conditions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    failure_conditions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    allows_alternative_plans: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PlanRow(Base):
    __tablename__ = "plan"
    __table_args__ = (
        CheckConstraint(
            "commitment_level >= 0 AND commitment_level <= 1",
            name="commitment_level_range",
        ),
        CheckConstraint("revision_number >= 1", name="revision_number_positive"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index(
            "uq_plan_one_active_primary_per_goal",
            "goal_id",
            unique=True,
            postgresql_where=text("is_primary AND status = 'active'"),
        ),
        Index("ix_plan_goal", "goal_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.goal.id"), nullable=False
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    expected_horizon: Mapped[str | None] = mapped_column(Text, nullable=True)
    commitment_level: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.5000")
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PlanStepRow(Base):
    __tablename__ = "plan_step"
    __table_args__ = (
        UniqueConstraint("plan_id", "step_index"),
        CheckConstraint("step_index >= 0", name="step_index_nonneg"),
        CheckConstraint(
            "expected_duration_phases IS NULL OR expected_duration_phases >= 0",
            name="expected_duration_nonneg",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.plan.id"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    target_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"), nullable=True
    )
    target_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.activity.id", use_alter=True),
        nullable=True,
    )
    prerequisites: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    expected_duration_phases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class CommitmentRow(Base):
    __tablename__ = "commitment"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_commitment_debtor", "world_id", "debtor_character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    debtor_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    beneficiary_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_condition: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    created_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    fulfilled_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RelationshipEdgeRow(Base):
    __tablename__ = "relationship_edge"
    __table_args__ = (
        CheckConstraint(
            "source_character_id <> target_character_id",
            name="source_ne_target",
        ),
        CheckConstraint("familiarity >= 0 AND familiarity <= 1", name="familiarity_range"),
        CheckConstraint("trust >= -1 AND trust <= 1", name="trust_range"),
        CheckConstraint("affection >= -1 AND affection <= 1", name="affection_range"),
        CheckConstraint("attraction >= -1 AND attraction <= 1", name="attraction_range"),
        CheckConstraint("respect >= -1 AND respect <= 1", name="respect_range"),
        CheckConstraint("fear >= -1 AND fear <= 1", name="fear_range"),
        CheckConstraint("resentment >= -1 AND resentment <= 1", name="resentment_range"),
        CheckConstraint("dependency >= -1 AND dependency <= 1", name="dependency_range"),
        CheckConstraint("loyalty >= -1 AND loyalty <= 1", name="loyalty_range"),
        CheckConstraint(
            "perceived_reciprocity >= -1 AND perceived_reciprocity <= 1",
            name="perceived_reciprocity_range",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_relationship_edge_world_source", "world_id", "source_character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    source_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    target_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    familiarity: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    trust: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    affection: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    attraction: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    respect: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    fear: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    resentment: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    dependency: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    loyalty: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    perceived_reciprocity: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    last_meaningful_interaction_phase: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class RelationshipEvidenceRow(Base):
    __tablename__ = "relationship_evidence"
    __table_args__ = (
        CheckConstraint(
            "signed_strength >= -1 AND signed_strength <= 1",
            name="signed_strength_range",
        ),
        ForeignKeyConstraint(
            ["source_character_id", "target_character_id"],
            [
                f"{WORLDSIM_SCHEMA}.relationship_edge.source_character_id",
                f"{WORLDSIM_SCHEMA}.relationship_edge.target_character_id",
            ],
        ),
        Index("ix_relationship_evidence_edge", "source_character_id", "target_character_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    source_character_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_character_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=False,
    )
    dimension: Mapped[str] = mapped_column(Text, nullable=False)
    signed_strength: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    perceived: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    decay_policy: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'default'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ActivityRow(Base):
    __tablename__ = "activity"
    __table_args__ = (
        CheckConstraint("progress >= 0 AND progress <= 1", name="progress_range"),
        CheckConstraint(
            "(activity_type <> 'travel') OR (route_id IS NOT NULL)",
            name="travel_requires_route",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index(
            "uq_activity_one_active_per_owner",
            "owner_entity_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_activity_world_owner", "world_id", "owner_entity_id"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"), nullable=False
    )
    activity_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    origin_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    destination_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.location.entity_id"),
        nullable=True,
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.route.id"), nullable=True
    )
    started_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_end_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    progress: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.0000")
    )
    interruption_conditions: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    activity_payload: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    last_source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class ActivityParticipantRow(Base):
    __tablename__ = "activity_participant"
    __table_args__ = (
        CheckConstraint("joined_phase_index >= 0", name="joined_phase_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.activity.id"),
        primary_key=True,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.entity.id"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    joined_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    left_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class TravelProgressRow(Base):
    __tablename__ = "travel_progress"
    __table_args__ = (
        CheckConstraint("distance_completed >= 0", name="distance_completed_nonneg"),
        CheckConstraint("phases_elapsed >= 0", name="phases_elapsed_nonneg"),
        CheckConstraint("current_segment_index >= 0", name="current_segment_index_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    activity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.activity.id"),
        primary_key=True,
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.route.id"), nullable=False
    )
    distance_completed: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, server_default=text("0")
    )
    phases_elapsed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    current_segment_index: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    last_tick_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'in_progress'"))
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class HookRow(Base):
    __tablename__ = "hook"
    __table_args__ = (
        UniqueConstraint("world_id", "hook_key"),
        CheckConstraint(
            "status IN ('active', 'dormant', 'resolved', 'abandoned')",
            name="status",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        Index("ix_hook_world_status", "world_id", "status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    hook_key: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'dormant'"))
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisites: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    scheduled_window: Mapped[object | None] = mapped_column(JSONB, nullable=True)
    involved_entity_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(Uuid(as_uuid=True)), nullable=False, server_default=text("'{}'::uuid[]")
    )
    disclosure_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'hidden'")
    )
    cooldown_until_phase: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    director_profile_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NarrativeMetricRow(Base):
    __tablename__ = "narrative_metric"
    __table_args__ = (
        Index("ix_narrative_metric_world_key_recorded", "world_id", "metric_key", "recorded_at"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    metric_key: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(16, 6), nullable=False)
    window_start_phase: Mapped[int] = mapped_column(BigInteger, nullable=False)
    window_end_phase: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payload: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NpcProfileRow(Base):
    __tablename__ = "npc_profile"
    __table_args__ = (
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    role_tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    compact_card: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source_hook_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.hook.id"), nullable=True
    )
    similarity_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class NpcLifecycleRow(Base):
    __tablename__ = "npc_lifecycle"
    __table_args__ = (
        CheckConstraint(
            "lifecycle_status IN ('proposed', 'active', 'archived', 'retained')",
            name="lifecycle_status",
        ),
        CheckConstraint(
            "lifecycle_status <> 'archived' OR archive_phase_index IS NOT NULL",
            name="archived_requires_archive_phase",
        ),
        CheckConstraint(
            "relevance_score >= 0 AND relevance_score <= 1",
            name="relevance_score_range",
        ),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        primary_key=True,
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    lifecycle_status: Mapped[str] = mapped_column(Text, nullable=False)
    activated_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    archive_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ttl_until_phase: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    relevance_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default=text("0.5000")
    )
    archive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_scene_phase_index: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SummaryRow(Base):
    __tablename__ = "summary"
    __table_args__ = (
        CheckConstraint("version_number >= 1", name="version_number_positive"),
        CheckConstraint("end_phase_index >= start_phase_index", name="phase_range"),
        Index(
            "uq_summary_owned_identity",
            "world_id",
            "owner_character_id",
            "summary_type",
            "start_phase_index",
            "end_phase_index",
            "version_number",
            unique=True,
            postgresql_where=text("owner_character_id IS NOT NULL"),
        ),
        Index(
            "uq_summary_unowned_identity",
            "world_id",
            "summary_type",
            "start_phase_index",
            "end_phase_index",
            "version_number",
            unique=True,
            postgresql_where=text("owner_character_id IS NULL"),
        ),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=True,
    )
    summary_type: Mapped[str] = mapped_column(Text, nullable=False)
    start_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    end_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_extract: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    perspective: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    model_call_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.model_call.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SummarySourceRow(Base):
    __tablename__ = "summary_source"
    __table_args__ = (
        CheckConstraint("ordinal >= 0", name="ordinal_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    summary_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.summary.id"),
        primary_key=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class DiaryEntryRow(Base):
    __tablename__ = "diary_entry"
    __table_args__ = (
        UniqueConstraint("world_id", "owner_character_id", "day_index"),
        CheckConstraint("day_index >= 0", name="day_index_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    owner_character_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.character.entity_id"),
        nullable=False,
    )
    day_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.summary.id"), nullable=True
    )
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class DayRunRow(Base):
    __tablename__ = "day_run"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        UniqueConstraint("world_id", "day_index"),
        CheckConstraint("day_index >= 0", name="day_index_nonneg"),
        CheckConstraint("version >= 0", name="version_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    day_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recovery_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, nullable=False, server_default=text("0"))


class DailyAuditRow(Base):
    __tablename__ = "daily_audit"
    __table_args__ = (
        UniqueConstraint("day_run_id"),
        CheckConstraint("hard_violation_count >= 0", name="hard_violation_count_nonneg"),
        CheckConstraint("soft_violation_count >= 0", name="soft_violation_count_nonneg"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    day_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.day_run.id"), nullable=False
    )
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    hard_violation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    soft_violation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    findings: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScheduledEffectRow(Base):
    __tablename__ = "scheduled_effect"
    __table_args__ = (
        UniqueConstraint("idempotency_key"),
        CheckConstraint("due_phase_index >= 0", name="due_phase_index_nonneg"),
        Index("ix_scheduled_effect_due", "world_id", "due_phase_index", "status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey(f"{WORLDSIM_SCHEMA}.world.id"), nullable=False
    )
    due_phase_index: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"))
    effect_payload: Mapped[object] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    applied_event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(f"{WORLDSIM_SCHEMA}.world_event.id"),
        nullable=True,
    )
