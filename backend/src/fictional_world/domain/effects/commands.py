"""Typed effect commands (handbook ``05`` §7 + Stage-0 ASSUMP-S0-001 + Stage 3 §4.2)."""

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
    injury_id: UUID | None = None
    idempotency_key: str | None = Field(default=None, max_length=200)


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
    causal_injury_ids: tuple[UUID, ...] = ()
    causal_condition_ids: tuple[UUID, ...] = ()


# --- Stage 3 additive kinds (handbook 28 §4.2) ---


class UpdateInjuryEffect(EffectBase):
    kind: Literal["update_injury"] = "update_injury"
    injury_id: UUID
    entity_id: UUID
    severity: float | None = Field(default=None, ge=0, le=100)
    bleeding: float | None = Field(default=None, ge=0, le=100)
    pain: float | None = Field(default=None, ge=0, le=100)
    mobility_penalty: float | None = Field(default=None, ge=0, le=100)
    healing_progress: float | None = Field(default=None, ge=0, le=100)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    permanent_consequence: bool | None = None


class RemoveConditionEffect(EffectBase):
    kind: Literal["remove_condition"] = "remove_condition"
    condition_id: UUID
    entity_id: UUID
    reason: str = Field(min_length=1, max_length=500)


class CreateItemEffect(EffectBase):
    kind: Literal["create_item"] = "create_item"
    item_id: UUID
    world_id: UUID
    name: str = Field(min_length=1, max_length=200)
    item_kind: str = Field(min_length=1, max_length=100)
    owner_character_id: UUID | None = None
    quantity: int = Field(default=1, ge=1)
    item_code: str | None = Field(default=None, max_length=100)


class DestroyItemEffect(EffectBase):
    kind: Literal["destroy_item"] = "destroy_item"
    item_id: UUID
    reason: str = Field(min_length=1, max_length=500)


class UpdateSkillEvidenceEffect(EffectBase):
    kind: Literal["update_skill_evidence"] = "update_skill_evidence"
    character_id: UUID
    skill_id: UUID
    evidence_delta: float = Field(gt=0)
    difficulty: float = Field(ge=0, le=1)
    practice_quality: float = Field(ge=0, le=1)
    source_event_id: UUID | None = None


class AwardSkillProgressEffect(EffectBase):
    kind: Literal["award_skill_progress"] = "award_skill_progress"
    character_id: UUID
    skill_id: UUID
    proficiency_delta: float = Field(gt=0, le=100)
    evidence_event_ids: tuple[UUID, ...] = Field(min_length=1)
    extraordinary: bool = False


class RevealSecretEffect(EffectBase):
    kind: Literal["reveal_secret"] = "reveal_secret"
    secret_memory_id: UUID
    revealer_id: UUID
    listener_ids: tuple[UUID, ...] = Field(min_length=1)
    disclosure_level: str = Field(default="partial", min_length=1, max_length=50)


class UpdateFactionStateEffect(EffectBase):
    kind: Literal["update_faction_state"] = "update_faction_state"
    faction_id: UUID
    indicator_key: str = Field(min_length=1, max_length=100)
    indicator_value: float
    reason: str = Field(min_length=1, max_length=500)


class UpdateFactionRelationEffect(EffectBase):
    kind: Literal["update_faction_relation"] = "update_faction_relation"
    source_faction_id: UUID
    target_faction_id: UUID
    relation_delta: float = Field(ge=-1, le=1)
    dimension: str = Field(default="stance", min_length=1, max_length=100)


class UpdateSettlementIndicatorEffect(EffectBase):
    kind: Literal["update_settlement_indicator"] = "update_settlement_indicator"
    settlement_location_id: UUID
    indicator_key: str = Field(min_length=1, max_length=100)
    indicator_value: float
    reason: str = Field(min_length=1, max_length=500)


class CreateArcEffect(EffectBase):
    kind: Literal["create_arc"] = "create_arc"
    arc_id: UUID
    world_id: UUID
    arc_key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    arc_scope: str = Field(default="major", min_length=1, max_length=50)
    premise: str = Field(min_length=1, max_length=2_000)
    objective: str = Field(min_length=1, max_length=2_000)


class UpdateArcEffect(EffectBase):
    kind: Literal["update_arc"] = "update_arc"
    arc_id: UUID
    progress: float | None = Field(default=None, ge=0, le=1)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    milestone_key: str | None = Field(default=None, max_length=100)


class CloseArcEffect(EffectBase):
    kind: Literal["close_arc"] = "close_arc"
    arc_id: UUID
    closure_reason: str = Field(min_length=1, max_length=500)
    outcome: str = Field(min_length=1, max_length=100)


class CreateHookEffect(EffectBase):
    kind: Literal["create_hook"] = "create_hook"
    hook_id: UUID
    world_id: UUID
    hook_key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    premise: str = Field(min_length=1, max_length=2_000)
    status: str = Field(default="dormant", min_length=1, max_length=50)


class UpdateHookEffect(EffectBase):
    kind: Literal["update_hook"] = "update_hook"
    hook_id: UUID
    status: str | None = Field(default=None, min_length=1, max_length=50)
    progress_note: str | None = Field(default=None, max_length=1_000)


class CloseHookEffect(EffectBase):
    kind: Literal["close_hook"] = "close_hook"
    hook_id: UUID
    closure_reason: str = Field(min_length=1, max_length=500)


class ReturnFromDeathEffect(EffectBase):
    kind: Literal["return_from_death"] = "return_from_death"
    entity_id: UUID
    mechanism: str = Field(min_length=1, max_length=200)
    lore_rule_id: str = Field(min_length=1, max_length=200)
    cost_summary: str = Field(min_length=1, max_length=1_000)
    high_impact_authorized: bool = False


class AlterCharacterCardEffect(EffectBase):
    kind: Literal["alter_character_card"] = "alter_character_card"
    character_id: UUID
    field_path: str = Field(min_length=1, max_length=200)
    new_value_summary: str = Field(min_length=1, max_length=2_000)
    evidence_event_ids: tuple[UUID, ...] = Field(min_length=1)
    high_impact_authorized: bool = False


class AlterWorldLoreEffect(EffectBase):
    kind: Literal["alter_world_lore"] = "alter_world_lore"
    world_id: UUID
    lore_key: str = Field(min_length=1, max_length=200)
    change_summary: str = Field(min_length=1, max_length=2_000)
    permission_grant: str = Field(min_length=1, max_length=200)
    high_impact_authorized: bool = False


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
    | MarkDeathEffect
    | UpdateInjuryEffect
    | RemoveConditionEffect
    | CreateItemEffect
    | DestroyItemEffect
    | UpdateSkillEvidenceEffect
    | AwardSkillProgressEffect
    | RevealSecretEffect
    | UpdateFactionStateEffect
    | UpdateFactionRelationEffect
    | UpdateSettlementIndicatorEffect
    | CreateArcEffect
    | UpdateArcEffect
    | CloseArcEffect
    | CreateHookEffect
    | UpdateHookEffect
    | CloseHookEffect
    | ReturnFromDeathEffect
    | AlterCharacterCardEffect
    | AlterWorldLoreEffect,
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
    UpdateInjuryEffect,
    RemoveConditionEffect,
    CreateItemEffect,
    DestroyItemEffect,
    UpdateSkillEvidenceEffect,
    AwardSkillProgressEffect,
    RevealSecretEffect,
    UpdateFactionStateEffect,
    UpdateFactionRelationEffect,
    UpdateSettlementIndicatorEffect,
    CreateArcEffect,
    UpdateArcEffect,
    CloseArcEffect,
    CreateHookEffect,
    UpdateHookEffect,
    CloseHookEffect,
    ReturnFromDeathEffect,
    AlterCharacterCardEffect,
    AlterWorldLoreEffect,
)
