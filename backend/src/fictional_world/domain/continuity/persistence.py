"""Stage 2 continuity persistence records (goals, plans, travel, hooks, NPCs)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, Any]


class RoutePersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    origin_location_id: UUID
    destination_location_id: UUID
    is_bidirectional: bool = True
    distance_units: Decimal
    base_duration_phases: int = Field(ge=1)
    allowed_travel_modes: tuple[str, ...] = ()
    terrain_tags: tuple[str, ...] = ()
    danger_level: Decimal = Field(default=Decimal("0"))
    seasonal_modifiers: JsonObject = Field(default_factory=dict)
    status: str = Field(default="active", min_length=1, max_length=50)
    created_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)


class GoalPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    description: str = Field(min_length=1, max_length=2_000)
    category: str = Field(min_length=1, max_length=100)
    priority: Decimal = Field(default=Decimal("0.5"))
    status: str = Field(default="active", min_length=1, max_length=50)
    horizon: str | None = Field(default=None, max_length=100)
    success_conditions: JsonObject = Field(default_factory=dict)
    failure_conditions: JsonObject = Field(default_factory=dict)
    allows_alternative_plans: bool = False
    source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlanPersistenceRecord(StrictContract):
    id: UUID
    goal_id: UUID
    world_id: UUID
    owner_character_id: UUID
    title: str = Field(min_length=1, max_length=500)
    status: str = Field(default="active", min_length=1, max_length=50)
    is_primary: bool = True
    expected_horizon: str | None = Field(default=None, max_length=100)
    commitment_level: Decimal = Field(default=Decimal("0.5"))
    revision_number: int = Field(default=1, ge=1)
    source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlanStepPersistenceRecord(StrictContract):
    id: UUID
    plan_id: UUID
    step_index: int = Field(ge=0)
    description: str = Field(min_length=1, max_length=2_000)
    status: str = Field(default="pending", min_length=1, max_length=50)
    target_entity_id: UUID | None = None
    target_location_id: UUID | None = None
    activity_id: UUID | None = None
    prerequisites: JsonObject = Field(default_factory=dict)
    expected_duration_phases: int | None = Field(default=None, ge=0)
    version: int = Field(default=0, ge=0)


class CommitmentPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    debtor_character_id: UUID
    beneficiary_character_id: UUID
    description: str = Field(min_length=1, max_length=2_000)
    due_condition: JsonObject = Field(default_factory=dict)
    status: str = Field(default="active", min_length=1, max_length=50)
    created_event_id: UUID | None = None
    fulfilled_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RelationshipEdgePersistenceRecord(StrictContract):
    source_character_id: UUID
    target_character_id: UUID
    world_id: UUID
    familiarity: Decimal = Field(default=Decimal("0"))
    trust: Decimal = Field(default=Decimal("0"))
    affection: Decimal = Field(default=Decimal("0"))
    attraction: Decimal = Field(default=Decimal("0"))
    respect: Decimal = Field(default=Decimal("0"))
    fear: Decimal = Field(default=Decimal("0"))
    resentment: Decimal = Field(default=Decimal("0"))
    dependency: Decimal = Field(default=Decimal("0"))
    loyalty: Decimal = Field(default=Decimal("0"))
    perceived_reciprocity: Decimal = Field(default=Decimal("0"))
    last_meaningful_interaction_phase: int | None = None
    last_source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None


class ActivityPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_entity_id: UUID
    activity_type: str = Field(min_length=1, max_length=100)
    status: str = Field(default="active", min_length=1, max_length=50)
    origin_location_id: UUID | None = None
    destination_location_id: UUID | None = None
    route_id: UUID | None = None
    started_phase_index: int = Field(ge=0)
    expected_end_phase_index: int | None = None
    progress: Decimal = Field(default=Decimal("0"))
    interruption_conditions: JsonObject = Field(default_factory=dict)
    activity_payload: JsonObject = Field(default_factory=dict)
    last_source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)


class TravelProgressPersistenceRecord(StrictContract):
    """Per-activity route progress (``travel_progress`` table)."""

    activity_id: UUID
    route_id: UUID
    distance_completed: Decimal = Field(default=Decimal("0"), ge=0)
    phases_elapsed: int = Field(default=0, ge=0)
    current_segment_index: int = Field(default=0, ge=0)
    last_tick_phase_index: int = Field(ge=0)
    status: str = Field(default="in_progress", min_length=1, max_length=50)
    version: int = Field(default=0, ge=0)


class HookPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    hook_key: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    status: str = Field(default="dormant", min_length=1, max_length=50)
    premise: str = Field(min_length=1, max_length=4_000)
    prerequisites: JsonObject = Field(default_factory=dict)
    scheduled_window: JsonObject | None = None
    involved_entity_ids: tuple[UUID, ...] = ()
    disclosure_state: str = Field(default="hidden", min_length=1, max_length=50)
    cooldown_until_phase: int | None = None
    director_profile_key: str | None = Field(default=None, max_length=200)
    source_event_id: UUID | None = None
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NpcProfilePersistenceRecord(StrictContract):
    character_id: UUID
    world_id: UUID
    display_name: str = Field(min_length=1, max_length=200)
    role_tags: tuple[str, ...] = ()
    compact_card: JsonObject = Field(default_factory=dict)
    source_hook_id: UUID | None = None
    similarity_fingerprint: str = Field(min_length=1, max_length=256)
    version: int = Field(default=0, ge=0)
    created_at: datetime | None = None


class NpcLifecyclePersistenceRecord(StrictContract):
    character_id: UUID
    world_id: UUID
    lifecycle_status: str = Field(min_length=1, max_length=50)
    activated_phase_index: int | None = None
    archive_phase_index: int | None = None
    ttl_until_phase: int | None = None
    relevance_score: Decimal = Field(default=Decimal("0.5"))
    archive_summary: str | None = Field(default=None, max_length=4_000)
    last_scene_phase_index: int | None = None
    version: int = Field(default=0, ge=0)
    updated_at: datetime | None = None


class SummaryPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID | None = None
    summary_type: str = Field(min_length=1, max_length=50)
    start_phase_index: int = Field(ge=0)
    end_phase_index: int = Field(ge=0)
    content: str = Field(min_length=1, max_length=50_000)
    structured_extract: JsonObject = Field(default_factory=dict)
    perspective: str = Field(min_length=1, max_length=50)
    version_number: int = Field(default=1, ge=1)
    content_hash: str = Field(min_length=1, max_length=128)
    model_call_id: UUID | None = None
    created_at: datetime | None = None


class DiaryEntryPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    day_index: int = Field(ge=0)
    content: str = Field(min_length=1, max_length=50_000)
    summary_id: UUID | None = None
    content_hash: str = Field(min_length=1, max_length=128)
    created_at: datetime | None = None
    version: int = Field(default=0, ge=0)


class DayRunPersistenceRecord(StrictContract):
    id: UUID
    world_id: UUID
    day_index: int = Field(ge=0)
    status: str = Field(min_length=1, max_length=50)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    recovery_snapshot_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)
    version: int = Field(default=0, ge=0)


class SummarySourcePersistenceRecord(StrictContract):
    """Provenance link from a summary to an observation/memory/event source."""

    summary_id: UUID
    ordinal: int = Field(ge=0)
    source_kind: str = Field(min_length=1, max_length=50)
    source_id: UUID


class DailyAuditPersistenceRecord(StrictContract):
    """End-of-day memory audit attached to one day_run."""

    id: UUID
    day_run_id: UUID
    world_id: UUID
    hard_violation_count: int = Field(default=0, ge=0)
    soft_violation_count: int = Field(default=0, ge=0)
    findings: list[Any] = Field(default_factory=list)
    created_at: datetime | None = None


class NarrativeMetricPersistenceRecord(StrictContract):
    """Append-only pacing / Director trigger metric sample."""

    id: UUID
    world_id: UUID
    metric_key: str = Field(min_length=1, max_length=200)
    metric_value: Decimal
    window_start_phase: int = Field(ge=0)
    window_end_phase: int = Field(ge=0)
    payload: JsonObject = Field(default_factory=dict)
    recorded_at: datetime | None = None
