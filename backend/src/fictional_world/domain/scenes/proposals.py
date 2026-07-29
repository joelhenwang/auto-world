"""Action/reaction proposals and scene resolution contracts."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import (
    ActionFamily,
    ResolutionLevel,
    ResourceKind,
    Visibility,
)
from fictional_world.domain.effects.commands import EffectCommand


class ResourceIntention(StrictContract):
    resource: ResourceKind
    maximum_amount: float = Field(gt=0)


class DesiredOutcome(StrictContract):
    """Non-authoritative outcome requested by an actor."""

    description: str = Field(min_length=1, max_length=1_000)
    target_entity_ids: tuple[UUID, ...] = ()


class FallbackAction(StrictContract):
    action_family: ActionFamily
    description: str = Field(min_length=1, max_length=1_000)


class ActionProposal(StrictContract):
    schema_version: Literal["1.0"] = "1.0"
    decision_request_id: UUID
    actor_id: UUID
    action_family: ActionFamily
    description: str = Field(min_length=1, max_length=2_000)
    utterance: str | None = Field(default=None, max_length=1_000)
    target_entity_ids: tuple[UUID, ...] = ()
    target_location_id: UUID | None = None
    relevant_goal_ids: tuple[UUID, ...] = ()
    continuation_activity_id: UUID | None = None
    visibility: Visibility = Visibility.OBSERVABLE
    estimated_duration_phases: int = Field(default=1, ge=1, le=240)
    interruptible: bool = True
    interruption_conditions: tuple[str, ...] = Field(default=(), max_length=8)
    resource_intentions: tuple[ResourceIntention, ...] = ()
    desired_outcomes: tuple[DesiredOutcome, ...] = Field(default=(), max_length=6)
    fallback: FallbackAction


class ReactionProposal(StrictContract):
    schema_version: Literal["1.0"] = "1.0"
    reaction_request_id: UUID
    scene_id: UUID
    triggering_attempt_id: UUID
    reactor_id: UUID
    action_family: ActionFamily
    description: str = Field(min_length=1, max_length=1_500)
    utterance: str | None = Field(default=None, max_length=1_000)
    target_entity_ids: tuple[UUID, ...] = ()
    resource_intentions: tuple[ResourceIntention, ...] = ()
    desired_outcomes: tuple[DesiredOutcome, ...] = Field(default=(), max_length=4)


class PriorityBreakdown(StrictContract):
    causal_urgency: float = Field(ge=0, le=1)
    immediate_danger: float = Field(ge=0, le=1)
    scheduled_commitment: float = Field(ge=0, le=1)
    unresolved_dependency: float = Field(ge=0, le=1)
    goal_relevance: float = Field(ge=0, le=1)
    starvation_fairness: float = Field(ge=0, le=1)
    narrative_salience: float = Field(ge=0, le=1)
    final_score: float = Field(ge=0, le=1)


class SceneDraft(StrictContract):
    scene_id: UUID
    phase_id: UUID
    snapshot_id: UUID
    location_id: UUID | None
    participant_ids: tuple[UUID, ...] = Field(min_length=1)
    action_proposal_ids: tuple[UUID, ...] = Field(min_length=1)
    shared_entity_ids: tuple[UUID, ...] = ()
    priority: PriorityBreakdown
    beat_budget: int = Field(ge=1, le=12)
    high_impact: bool = False


class NarrationConstraints(StrictContract):
    perspective: str = Field(default="omniscient_limited", max_length=100)
    required_facts: tuple[str, ...] = ()
    forbidden_assertions: tuple[str, ...] = ()
    tone_tags: tuple[str, ...] = ()
    maximum_words: int = Field(default=700, ge=50, le=2_500)


class SceneResolution(StrictContract):
    schema_version: Literal["1.0"] = "1.0"
    resolution_request_id: UUID
    scene_id: UUID
    level: ResolutionLevel
    accepted_attempt_ids: tuple[UUID, ...]
    rejected_assumptions: tuple[str, ...] = ()
    effects: tuple[EffectCommand, ...] = ()
    canonical_summary: str = Field(min_length=1, max_length=2_000)
    narration_constraints: NarrationConstraints
    visual_significance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
