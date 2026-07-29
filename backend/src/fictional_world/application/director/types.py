"""Director proposal and trigger contracts (StrictContract)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from fictional_world.domain.common.base import StrictContract

ALLOWED_PROPOSAL_KINDS: frozenset[str] = frozenset(
    {
        "ENVIRONMENTAL_EVENT",
        "SOCIAL_OPPORTUNITY",
        "DISCOVERY",
        "MYSTERY_HOOK",
        "RELATIONSHIP_OPPORTUNITY",
        "PERSONAL_DILEMMA",
        "QUEST_HOOK",
        "NEW_LOCATION_DETAIL",
        "NPC_BLUEPRINT",
    }
)

DISCLOSURE_PATHS: frozenset[str] = frozenset(
    {
        "witnessed_event",
        "direct_speech",
        "claim_transmission",
        "discoverable_object",
        "environmental_clue",
        "authorized_briefing",
    }
)

FORBIDDEN_PUBLIC_SECRET_FIELDS: frozenset[str] = frozenset(
    {
        "secret_key",
        "secret_keys",
        "protected_secret",
        "director_only_secret",
    }
)


class TriggerMetricsSnapshot(StrictContract):
    """Normalized metric snapshot returned with every trigger decision."""

    phases_since_meaningful_choice: int = Field(ge=0)
    repeated_location_ratio: float = Field(ge=0, le=1)
    repeated_participant_ratio: float = Field(ge=0, le=1)
    repeated_action_ratio: float = Field(ge=0, le=1)
    goal_progress_stagnation: float = Field(ge=0, le=1)
    unresolved_hook_count: int = Field(ge=0)
    emotional_intensity_trend: float = Field(ge=-1, le=1)
    recent_disruptive_event_cooldown: int = Field(ge=0)
    stagnation_score: float = Field(ge=0, le=1)


class TriggerDecision(StrictContract):
    should_call: bool
    reasons: tuple[str, ...] = ()
    metrics: TriggerMetricsSnapshot


class DirectorWorldSnapshot(StrictContract):
    """Omniscient read model inputs for trigger evaluation (not character context)."""

    world_id: UUID
    current_phase_index: int = Field(ge=0)
    phases_since_meaningful_choice: int = Field(ge=0)
    recent_location_keys: tuple[str, ...] = ()
    recent_participant_keys: tuple[str, ...] = ()
    recent_action_families: tuple[str, ...] = ()
    goal_progress_delta: float = Field(ge=0, le=1)
    unresolved_hook_count: int = Field(ge=0)
    emotional_intensity_history: tuple[float, ...] = ()
    last_disruptive_event_phase: int | None = None
    protected_secret_keys: tuple[str, ...] = ()
    recent_trope_tags: tuple[str, ...] = ()
    trope_cooldown_remaining: int = Field(default=0, ge=0)


class ProposedHookStub(StrictContract):
    hook_key: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=500)
    premise: str = Field(min_length=1, max_length=4_000)
    status: Literal["active", "dormant"] = "dormant"
    disclosure_state: Literal["hidden", "hinted", "partial", "public"] = "hidden"


class ProposedNpcStub(StrictContract):
    """Compact NPC blueprint only — full registry is S2-WORLD-002."""

    proposed_name: str = Field(min_length=1, max_length=200)
    role_tags: tuple[str, ...] = ()
    narrative_purpose: str = Field(min_length=1, max_length=1_000)
    location_key: str | None = Field(default=None, max_length=200)


class SecretHandlingPlan(StrictContract):
    """Public secret-handling plan — never embeds secret keys."""

    reveals_secret: bool = False
    disclosure_path: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("disclosure_path")
    @classmethod
    def _normalize_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower()


class DirectorProposal(StrictContract):
    """Restricted Director proposal. Proposals only — no direct canon commit."""

    schema_version: Literal["1.0"] = "1.0"
    proposal_id: UUID
    phase_id: UUID
    world_id: UUID
    trigger_type: str = Field(min_length=1, max_length=100)
    proposal_kind: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    intent: str = Field(min_length=1, max_length=2_000)
    causal_basis_event_ids: tuple[UUID, ...] = ()
    involved_entity_ids: tuple[UUID, ...] = ()
    target_location_ids: tuple[UUID, ...] = ()
    prerequisites: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    proposed_hooks: tuple[ProposedHookStub, ...] = ()
    proposed_event_facts: tuple[str, ...] = ()
    proposed_npc_stubs: tuple[ProposedNpcStub, ...] = ()
    proposed_effect_types: tuple[str, ...] = ()
    observability_plan: tuple[str, ...] = ()
    secret_handling: SecretHandlingPlan = Field(default_factory=SecretHandlingPlan)
    expected_horizon: str = Field(default="same_day", max_length=100)
    urgency: float = Field(default=0.5, ge=0, le=1)
    narrative_dimensions: tuple[str, ...] = ()
    novelty_tags: tuple[str, ...] = ()
    trope_tags: tuple[str, ...] = ()
    fallback_or_expiry: str | None = Field(default=None, max_length=500)
    confidence: float = Field(default=0.5, ge=0, le=1)
    is_disruptive: bool = False
    guarantees_romance: bool = False
    public_payload: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("proposal_kind")
    @classmethod
    def _kind_upper(cls, value: str) -> str:
        return value.strip().upper()


class NoEventFallback(StrictContract):
    """Safe quiet-phase outcome when validation fails or Director abstains."""

    reason: str = Field(min_length=1, max_length=500)
    validation_issue_codes: tuple[str, ...] = ()
    proposal_id: UUID | None = None
