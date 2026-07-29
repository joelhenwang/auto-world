"""Scene/action/reaction persistence records (Stage 1 / S1-DB-001)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract

JsonObject = dict[str, Any]


class ActionTargetRecord(StrictContract):
    action_proposal_id: UUID
    target_entity_id: UUID
    target_role: str = Field(min_length=1, max_length=50)
    ordinal: int = Field(ge=0, le=32_767)


class ActionProposalRecord(StrictContract):
    id: UUID
    phase_run_id: UUID
    snapshot_id: UUID
    actor_id: UUID
    proposal_kind: str = Field(default="primary", min_length=1, max_length=50)
    action_family: str = Field(min_length=1, max_length=50)
    intent: str = Field(min_length=1, max_length=2_000)
    utterance: str | None = Field(default=None, max_length=1_000)
    target_location_id: UUID | None = None
    visibility: str = Field(min_length=1, max_length=50)
    risk_tolerance: Decimal = Field(default=Decimal("0.5"))
    estimated_duration_phases: int = Field(default=1, ge=1, le=240)
    continuation_activity_id: UUID | None = None
    desired_effects: JsonObject = Field(default_factory=dict)
    fallback_action: JsonObject = Field(default_factory=dict)
    validation_status: str = Field(default="pending", min_length=1, max_length=50)
    validation_errors: JsonObject | None = None
    model_call_id: UUID | None = None
    generation: int = Field(default=0, ge=0)
    idempotency_key: str = Field(min_length=1, max_length=200)
    created_at: datetime | None = None
    targets: tuple[ActionTargetRecord, ...] = ()


class SceneActionRecord(StrictContract):
    scene_id: UUID
    proposal_id: UUID
    role: str = Field(min_length=1, max_length=50)
    ordinal: int = Field(ge=0, le=32_767)


class SceneParticipantRecord(StrictContract):
    scene_id: UUID
    entity_id: UUID
    participant_role: str = Field(min_length=1, max_length=50)
    reaction_eligible: bool = True
    knowledge_scope_hash: str | None = Field(default=None, max_length=128)
    joined_at_beat: int = Field(default=0, ge=0)
    left_at_beat: int | None = Field(default=None, ge=0)


class SceneRecord(StrictContract):
    id: UUID
    phase_run_id: UUID
    snapshot_id: UUID
    location_id: UUID | None = None
    scene_type: str = Field(min_length=1, max_length=50)
    state: str = Field(min_length=1, max_length=50)
    priority_score: Decimal = Field(default=Decimal("0"))
    priority_breakdown: JsonObject = Field(default_factory=dict)
    beat_budget: int = Field(ge=1, le=12)
    high_impact: bool = False
    mutable_aggregate_ids: tuple[UUID, ...] = ()
    idempotency_key: str = Field(min_length=1, max_length=200)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    version: int = Field(default=0, ge=0)
    continuation_id: UUID | None = None
    director_hook_id: UUID | None = None
    observer_eligibility: JsonObject = Field(default_factory=dict)
    actions: tuple[SceneActionRecord, ...] = ()
    participants: tuple[SceneParticipantRecord, ...] = ()


class ReactionProposalRecord(StrictContract):
    id: UUID
    scene_id: UUID
    phase_run_id: UUID
    snapshot_id: UUID
    triggering_attempt_id: UUID
    reactor_id: UUID
    beat_index: int = Field(ge=0, le=12)
    action_family: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=1_500)
    utterance: str | None = Field(default=None, max_length=1_000)
    target_entity_ids: tuple[UUID, ...] = ()
    resource_intentions: JsonObject = Field(default_factory=dict)
    desired_outcomes: JsonObject = Field(default_factory=dict)
    validation_status: str = Field(default="pending", min_length=1, max_length=50)
    validation_errors: JsonObject | None = None
    model_call_id: UUID | None = None
    source_kind: str = Field(default="model", min_length=1, max_length=50)
    idempotency_key: str = Field(min_length=1, max_length=200)
    created_at: datetime | None = None


class SceneResolutionRecord(StrictContract):
    id: UUID
    scene_id: UUID
    resolution_level: str = Field(min_length=1, max_length=50)
    accepted_attempt_ids: tuple[UUID, ...] = ()
    rejected_assumptions: JsonObject = Field(default_factory=dict)
    proposed_effects: JsonObject = Field(default_factory=dict)
    delayed_effects: JsonObject = Field(default_factory=dict)
    observation_seeds: JsonObject = Field(default_factory=dict)
    narration_constraints: JsonObject = Field(default_factory=dict)
    visual_significance: Decimal = Field(default=Decimal("0"))
    confidence: Decimal = Field(default=Decimal("0"))
    resolver_profile_id: UUID | None = None
    model_call_id: UUID | None = None
    expected_aggregate_versions: JsonObject = Field(default_factory=dict)
    validation_status: str = Field(default="pending", min_length=1, max_length=50)
    commit_event_id: UUID | None = None
    canonical_summary: str = Field(min_length=1, max_length=2_000)
    idempotency_key: str = Field(min_length=1, max_length=200)
    created_at: datetime | None = None


class SceneRunRecord(StrictContract):
    id: UUID
    scene_id: UUID
    phase_run_id: UUID
    status: str = Field(min_length=1, max_length=50)
    stage: str = Field(min_length=1, max_length=50)
    beat_count: int = Field(default=0, ge=0)
    beat_budget: int = Field(ge=1, le=12)
    high_impact: bool = False
    resolution_id: UUID | None = None
    committed_event_id: UUID | None = None
    attempt_count: int = Field(default=0, ge=0)
    error_code: str | None = None
    error_detail: JsonObject | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    version: int = Field(default=0, ge=0)


class NarrationRecord(StrictContract):
    id: UUID
    world_id: UUID
    scene_id: UUID
    world_event_id: UUID
    perspective: str = Field(default="omniscient_limited", min_length=1, max_length=100)
    body: str = Field(min_length=1, max_length=8_000)
    source_kind: str = Field(min_length=1, max_length=50)
    model_call_id: UUID | None = None
    is_fallback: bool = False
    content_hash: str = Field(min_length=1, max_length=128)
    idempotency_key: str = Field(min_length=1, max_length=200)
    created_at: datetime | None = None


class StreamEventRecord(StrictContract):
    id: UUID
    world_id: UUID
    sequence: int = Field(ge=1)
    event_type: str = Field(min_length=1, max_length=100)
    occurred_at: datetime
    fictional_time: JsonObject = Field(default_factory=dict)
    payload: JsonObject = Field(default_factory=dict)
    schema_version: str = Field(default="1", min_length=1, max_length=20)
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    world_event_id: UUID | None = None
    perspective_scope: str = Field(default="world", min_length=1, max_length=50)
    idempotency_key: str = Field(min_length=1, max_length=200)
    created_at: datetime | None = None


class PlayerControlSessionRecord(StrictContract):
    id: UUID
    world_id: UUID
    character_id: UUID
    controller_id: str = Field(min_length=1, max_length=200)
    status: str = Field(min_length=1, max_length=50)
    acquired_at: datetime
    released_at: datetime | None = None
    waiting_input: bool = False
    phase_run_id: UUID | None = None
    last_command_id: UUID | None = None
    idempotency_key: str = Field(min_length=1, max_length=200)
    version: int = Field(default=0, ge=0)
