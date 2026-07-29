"""Typed effect commands (handbook ``05`` §7 + Stage-0 ASSUMP-S0-001)."""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import (
    MemoryKind,
    ObservationChannel,
    RelationshipDimension,
    ResourceKind,
)


class EffectBase(StrictContract):
    effect_key: str = Field(min_length=1, max_length=100)
    source_attempt_ids: tuple[UUID, ...] = ()
    justification: str = Field(min_length=1, max_length=1_000)


# --- Stage 0 additive kinds (ASSUMP-S0-001; required by 25 §2) ---


class WaitEffect(EffectBase):
    kind: Literal["wait"] = "wait"
    entity_id: UUID
    phases: int = Field(default=1, ge=1, le=240)


class ObserveEffect(EffectBase):
    kind: Literal["observe"] = "observe"
    observer_id: UUID
    target_entity_ids: tuple[UUID, ...] = ()
    channels: tuple[ObservationChannel, ...] = ()


class RestEffect(EffectBase):
    kind: Literal["rest"] = "rest"
    entity_id: UUID
    stamina_recovery: float = Field(default=0.0, ge=0)


class CreateRecentMemoryEffect(EffectBase):
    kind: Literal["create_recent_memory"] = "create_recent_memory"
    owner_character_id: UUID
    memory_kind: MemoryKind
    text: str = Field(min_length=1, max_length=4_000)
    salience: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    source_event_ids: tuple[UUID, ...] = ()
    source_observation_ids: tuple[UUID, ...] = ()


# --- Handbook §7 effect kinds ---


class MoveEntityEffect(EffectBase):
    kind: Literal["move_entity"] = "move_entity"
    entity_id: UUID
    from_location_id: UUID
    to_location_id: UUID


class SpendResourceEffect(EffectBase):
    kind: Literal["spend_resource"] = "spend_resource"
    entity_id: UUID
    resource: ResourceKind
    amount: float = Field(gt=0)


class ApplyInjuryEffect(EffectBase):
    kind: Literal["apply_injury"] = "apply_injury"
    entity_id: UUID
    body_region: str = Field(min_length=1, max_length=100)
    injury_type: str = Field(min_length=1, max_length=100)
    severity: int = Field(ge=1, le=5)
    bleeding: int = Field(default=0, ge=0, le=5)
    pain: int = Field(default=0, ge=0, le=5)
    mobility_impact: int = Field(default=0, ge=0, le=5)
    consciousness_impact: int = Field(default=0, ge=0, le=5)
    potentially_permanent: bool = False


class ApplyConditionEffect(EffectBase):
    kind: Literal["apply_condition"] = "apply_condition"
    entity_id: UUID
    condition_type: str = Field(min_length=1, max_length=100)
    intensity: int = Field(ge=1, le=5)
    duration_phases: int | None = Field(default=None, ge=1)


class TransferItemEffect(EffectBase):
    kind: Literal["transfer_item"] = "transfer_item"
    item_id: UUID
    from_owner_id: UUID
    to_owner_id: UUID
    quantity: int = Field(default=1, ge=1)


class RelationshipEvidenceEffect(EffectBase):
    kind: Literal["relationship_evidence"] = "relationship_evidence"
    source_character_id: UUID
    target_character_id: UUID
    dimension: RelationshipDimension
    evidence_strength: float = Field(ge=-1, le=1)
    perceived_by_source: bool = True


class CreateClaimEffect(EffectBase):
    kind: Literal["create_claim"] = "create_claim"
    speaker_id: UUID
    listener_ids: tuple[UUID, ...] = Field(min_length=1)
    proposition: str = Field(min_length=1, max_length=2_000)
    referenced_entity_ids: tuple[UUID, ...] = ()


class AdvanceActivityEffect(EffectBase):
    kind: Literal["advance_activity"] = "advance_activity"
    activity_id: UUID
    progress_delta: float = Field(gt=0, le=1)
    completed: bool = False


class SkillProgressEvidenceEffect(EffectBase):
    kind: Literal["skill_progress_evidence"] = "skill_progress_evidence"
    character_id: UUID
    skill_id: UUID
    evidence_strength: float = Field(gt=0, le=1)
    difficulty: float = Field(ge=0, le=1)


class ScheduleEffect(EffectBase):
    kind: Literal["schedule_effect"] = "schedule_effect"
    due_absolute_phase_index: int = Field(ge=0)
    effect_type: str = Field(min_length=1, max_length=100)
    target_entity_ids: tuple[UUID, ...] = ()
    payload: dict[str, str | int | float | bool | None]


class RegisterNpcEffect(EffectBase):
    kind: Literal["register_npc"] = "register_npc"
    proposed_name: str = Field(min_length=1, max_length=200)
    location_id: UUID
    narrative_purpose: str = Field(min_length=1, max_length=1_000)
    persistence_horizon_days: int = Field(ge=1, le=120)


class MarkDeathEffect(EffectBase):
    kind: Literal["mark_death"] = "mark_death"
    entity_id: UUID
    cause: str = Field(min_length=1, max_length=1_000)


EffectCommand = Annotated[
    WaitEffect
    | ObserveEffect
    | RestEffect
    | CreateRecentMemoryEffect
    | MoveEntityEffect
    | SpendResourceEffect
    | ApplyInjuryEffect
    | ApplyConditionEffect
    | TransferItemEffect
    | RelationshipEvidenceEffect
    | CreateClaimEffect
    | AdvanceActivityEffect
    | SkillProgressEvidenceEffect
    | ScheduleEffect
    | RegisterNpcEffect
    | MarkDeathEffect,
    Field(discriminator="kind"),
]

EFFECT_COMMAND_TYPES: tuple[type[EffectBase], ...] = (
    WaitEffect,
    ObserveEffect,
    RestEffect,
    CreateRecentMemoryEffect,
    MoveEntityEffect,
    SpendResourceEffect,
    ApplyInjuryEffect,
    ApplyConditionEffect,
    TransferItemEffect,
    RelationshipEvidenceEffect,
    CreateClaimEffect,
    AdvanceActivityEffect,
    SkillProgressEvidenceEffect,
    ScheduleEffect,
    RegisterNpcEffect,
    MarkDeathEffect,
)
