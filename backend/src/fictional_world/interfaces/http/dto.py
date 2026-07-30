"""HTTP response/request DTOs for Stage 0 API."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HealthLiveResponse(ApiModel):
    status: str = "ok"


class HealthReadyResponse(ApiModel):
    status: str
    database: str
    detail: str | None = None


class WorldRead(ApiModel):
    id: UUID
    slug: str
    name: str
    status: str
    current_event_sequence: int
    version: int


class ClockRead(ApiModel):
    world_id: UUID
    generation_number: int
    year: int
    month: int
    day: int
    phase_name: str
    phase_ordinal: int
    absolute_day_index: int
    absolute_phase_index: int
    resolution_mode: str
    version: int


class PhaseRead(ApiModel):
    id: UUID
    world_id: UUID
    absolute_phase_index: int
    phase_name: str
    state: str
    resolution_mode: str
    expected_character_count: int
    completed_character_count: int
    version: int
    started_at: datetime | None = None
    completed_at: datetime | None = None


class EventRead(ApiModel):
    id: UUID
    world_id: UUID
    sequence_number: int
    absolute_phase_index: int
    phase_run_id: UUID | None
    event_type: str
    canonical_summary: str
    structured_facts: dict[str, Any] = Field(default_factory=dict)
    importance: Decimal
    visibility_class: str
    source_kind: str
    idempotency_key: str
    committed_at: datetime | None = None


class AdvancePhaseResponse(ApiModel):
    phase_run_id: UUID
    absolute_phase_index: int
    phase_name: str
    already_completed: bool
    snapshot_id: UUID | None
    event_ids: list[UUID]


class ReconcileResponse(ApiModel):
    world_id: UUID
    active_phase_id: UUID | None
    tasks_created: int
    phase_completed: bool
    notes: list[str]


class PauseWorldRequest(ApiModel):
    mode: Literal["after_safe_boundary", "immediate"] = "after_safe_boundary"


class RuntimeCommandResponse(ApiModel):
    world_id: UUID
    status: str
    phase: AdvancePhaseResponse | None = None


class StreamEventRead(ApiModel):
    id: UUID
    world_id: UUID
    sequence: int
    event_type: str
    occurred_at: datetime
    fictional_time: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)
    schema_version: str
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    world_event_id: UUID | None = None
    perspective_scope: str


class SceneSummaryRead(ApiModel):
    id: UUID
    phase_run_id: UUID
    snapshot_id: UUID
    location_id: UUID | None
    scene_type: str
    state: str
    priority_score: Decimal
    beat_budget: int
    participant_ids: list[UUID]
    resolution_level: str | None = None
    canonical_summary: str | None = None
    narration: str | None = None


class CharacterSummaryRead(ApiModel):
    id: UUID
    name: str
    location_id: UUID | None
    life_status: str
    stamina: Decimal
    energy: Decimal
    pain: Decimal
    stress: Decimal
    active_activity_id: UUID | None
    state_version: int


class AcquirePlayerControlRequest(ApiModel):
    controller_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)


class ReleasePlayerControlRequest(ApiModel):
    controller_id: str = Field(min_length=1, max_length=200)
    session_id: UUID


class PlayerControlRead(ApiModel):
    id: UUID
    world_id: UUID
    character_id: UUID
    controller_id: str
    status: str
    acquired_at: datetime
    released_at: datetime | None
    waiting_input: bool
    phase_run_id: UUID | None
    version: int


class PlayerActionRequest(ApiModel):
    session_id: UUID
    controller_id: str = Field(min_length=1, max_length=200)
    idempotency_key: str = Field(min_length=1, max_length=200)
    action_family: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=2_000)
    utterance: str | None = Field(default=None, max_length=1_000)
    target_entity_ids: list[UUID] = Field(default_factory=list)
    target_location_id: UUID | None = None


class PlayerActionResponse(ApiModel):
    command_id: UUID
    status: str
    already_existed: bool


class DayRunRead(ApiModel):
    id: UUID
    world_id: UUID
    day_index: int
    status: str
    recovery_snapshot_id: UUID | None = None
    version: int


class DayProgressRead(ApiModel):
    world_id: UUID
    day_index: int
    phase_name: str
    phase_ordinal: int
    absolute_phase_index: int
    resolution_mode: str
    clock_version: int
    day_run: DayRunRead | None = None
    completed_day_count: int = 0


class LocationMapRead(ApiModel):
    id: UUID
    name: str
    location_type: str
    region_code: str
    parent_location_id: UUID | None = None
    coordinate_x: Decimal | None = None
    coordinate_y: Decimal | None = None
    environment_tags: list[str] = Field(default_factory=list)


class RouteMapRead(ApiModel):
    id: UUID
    origin_location_id: UUID
    destination_location_id: UUID
    is_bidirectional: bool
    distance_units: Decimal
    base_duration_phases: int
    status: str
    danger_level: Decimal


class TravelProgressSummaryRead(ApiModel):
    activity_id: UUID
    owner_entity_id: UUID
    route_id: UUID | None
    origin_location_id: UUID | None
    destination_location_id: UUID | None
    status: str
    progress: Decimal
    started_phase_index: int
    expected_end_phase_index: int | None = None


class MapStateRead(ApiModel):
    locations: list[LocationMapRead]
    routes: list[RouteMapRead]
    travel_progress: list[TravelProgressSummaryRead]


class GoalRead(ApiModel):
    id: UUID
    description: str
    category: str
    priority: Decimal
    status: str
    horizon: str | None = None
    allows_alternative_plans: bool = False


class PlanRead(ApiModel):
    id: UUID
    goal_id: UUID
    title: str
    status: str
    is_primary: bool
    commitment_level: Decimal
    revision_number: int


class CommitmentRead(ApiModel):
    id: UUID
    debtor_character_id: UUID
    beneficiary_character_id: UUID
    description: str
    status: str


class CharacterDetailRead(ApiModel):
    id: UUID
    name: str
    character_kind: str | None = None
    location_id: UUID | None
    life_status: str
    stamina: Decimal
    energy: Decimal
    pain: Decimal
    stress: Decimal
    active_activity_id: UUID | None
    state_version: int
    goals: list[GoalRead] = Field(default_factory=list)
    plans: list[PlanRead] = Field(default_factory=list)
    commitments: list[CommitmentRead] = Field(default_factory=list)


class BeliefRead(ApiModel):
    id: UUID
    character_id: UUID
    proposition_key: str
    belief_text: str
    confidence: Decimal
    status: str
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    version: int


class RelationshipEdgeRead(ApiModel):
    source_character_id: UUID
    target_character_id: UUID
    familiarity: Decimal
    trust: Decimal
    affection: Decimal
    attraction: Decimal
    respect: Decimal
    fear: Decimal
    resentment: Decimal
    dependency: Decimal
    loyalty: Decimal
    perceived_reciprocity: Decimal
    last_meaningful_interaction_phase: int | None = None
    version: int


class NpcLifecycleRead(ApiModel):
    character_id: UUID
    lifecycle_status: str
    activated_phase_index: int | None = None
    archive_phase_index: int | None = None
    ttl_until_phase: int | None = None
    relevance_score: Decimal
    archive_summary: str | None = None
    last_scene_phase_index: int | None = None
    version: int


class NpcSummaryRead(ApiModel):
    character_id: UUID
    display_name: str
    role_tags: list[str] = Field(default_factory=list)
    lifecycle: NpcLifecycleRead | None = None


class NpcDetailRead(NpcSummaryRead):
    compact_card: dict[str, Any] = Field(default_factory=dict)
    source_hook_id: UUID | None = None
    similarity_fingerprint: str


class DiaryEntryRead(ApiModel):
    id: UUID
    owner_character_id: UUID
    day_index: int
    content: str
    summary_id: UUID | None = None
    version: int


class SummaryRead(ApiModel):
    id: UUID
    owner_character_id: UUID | None
    summary_type: str
    start_phase_index: int
    end_phase_index: int
    content: str
    perspective: str
    version_number: int


class CharacterDiaryBundleRead(ApiModel):
    character_id: UUID
    diaries: list[DiaryEntryRead]
    summaries: list[SummaryRead]


class DirectorHookRead(ApiModel):
    id: UUID
    hook_key: str
    title: str
    status: str
    premise: str
    disclosure_state: str
    cooldown_until_phase: int | None = None
    involved_entity_ids: list[UUID] = Field(default_factory=list)
    version: int


class NarrativeMetricRead(ApiModel):
    id: UUID
    metric_key: str
    metric_value: Decimal
    window_start_phase: int
    window_end_phase: int
    payload: dict[str, Any] = Field(default_factory=dict)


class DirectorHooksMetricsRead(ApiModel):
    hooks: list[DirectorHookRead]
    metrics: list[NarrativeMetricRead]


class TaskFailureRead(ApiModel):
    id: UUID
    task_type: str
    state: str
    attempt_count: int
    error_code: str | None = None
    error_detail: dict[str, Any] | None = None
    phase_run_id: UUID | None = None
    created_at: datetime
    completed_at: datetime | None = None


class PhaseAdvanceSummaryRead(ApiModel):
    phase_run_id: UUID
    absolute_phase_index: int
    phase_name: str
    already_completed: bool


class DayAdvanceResponse(ApiModel):
    world_id: UUID
    day_index: int
    day_run_id: UUID | None
    recovery_snapshot_id: UUID | None
    already_finalized: bool
    hard_audit_violations: int
    phase_results: list[PhaseAdvanceSummaryRead]


class RunUntilDayRequest(ApiModel):
    target_day_index: int = Field(ge=0)


class RunUntilDayResponse(ApiModel):
    world_id: UUID
    target_day_index: int
    days: list[DayAdvanceResponse]


class ProposeDirectorEventRequest(ApiModel):
    idempotency_key: str = Field(min_length=1, max_length=200)
    proposal_kind: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=2_000)
    public_payload: dict[str, Any] = Field(default_factory=dict)


class ProposeDirectorEventResponse(ApiModel):
    command_id: UUID
    status: str
    already_existed: bool


class MonthRunRead(ApiModel):
    id: UUID
    world_id: UUID
    month_index: int
    status: str
    start_day_index: int
    end_day_index: int
    metrics: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime | None = None


class LongTermMemoryRead(ApiModel):
    id: UUID
    world_id: UUID
    owner_character_id: UUID
    memory_type: str
    content: str
    salience: Decimal
    confidence: Decimal
    emotional_weight: Decimal
    visibility: str
    occurred_phase_index: int
    created_phase_index: int
    status: str
    decay_score: Decimal


class ArcRead(ApiModel):
    id: UUID
    world_id: UUID
    arc_key: str
    title: str
    arc_scope: str
    status: str
    premise: str
    objective: str
    progress: Decimal
    participant_entity_ids: list[UUID] = Field(default_factory=list)
    dominant_genres: list[str] = Field(default_factory=list)
    version: int


class FactionRead(ApiModel):
    id: UUID
    world_id: UUID
    faction_key: str
    name: str
    faction_type: str
    status: str
    territory_location_ids: list[UUID] = Field(default_factory=list)
    plot_armour_bias: Decimal
    version: int


class ExportListRead(ApiModel):
    items: list[dict[str, Any]] = Field(default_factory=list)


class MonthFinalizeSummaryRead(ApiModel):
    month_index: int
    month_run_id: UUID | None
    already_finalized: bool
    chapter_count: int = 0
    reflection_count: int = 0


class RunThirtyDaysResponse(ApiModel):
    world_id: UUID
    days_completed: int
    day_results: list[DayAdvanceResponse]
    month: MonthFinalizeSummaryRead | None = None


class WebSocketEnvelopeRead(ApiModel):
    """Documented WebSocket message shapes (additive Stage 2 event types)."""

    type: Literal[
        "stream_event",
        "replay_complete",
        "pong",
        "error",
        "day.finalized",
        "director.metric",
        "day.progress",
    ]
    sequence: int | None = None
    last_sequence: int | None = None
    detail: str | None = None
    event: StreamEventRead | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
