"""Unit tests for S3-RULES-003 combat, injuries, recovery, and death."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.agents.restricted_effects import (
    GraphTaskRole,
    effect_kind_allowed,
    restricted_effect_kinds,
)
from fictional_world.domain.effects.commands import EFFECT_COMMAND_TYPES
from fictional_world.domain.rules.combat import (
    CombatantSnapshot,
    CombatExchangeInput,
    CombatOutcomeClass,
    resolve_combat_exchange,
)
from fictional_world.domain.rules.injuries import (
    DeathValidationContext,
    InjuryApplication,
    LifeStatus,
    RecoveryStep,
    ReturnFromDeathContext,
    apply_injury,
    injury_action_penalty,
    progress_recovery,
    validate_death_prerequisites,
    validate_return_from_death,
)


def _combatant(**overrides: object) -> CombatantSnapshot:
    base: dict[str, object] = {
        "character_id": uuid4(),
        "capability": 50.0,
        "skill": 50.0,
        "preparation": 0.2,
        "terrain_advantage": 0.0,
        "teamwork": 0.0,
        "morale": 0.5,
        "injury_penalty": 0.0,
        "surprise": 0.0,
        "stamina_ratio": 1.0,
    }
    base.update(overrides)
    return CombatantSnapshot.model_validate(base)


@pytest.mark.unit
def test_weaker_prepared_may_win_within_envelope() -> None:
    weaker = _combatant(capability=35.0, skill=40.0, preparation=0.85, surprise=0.6)
    stronger = _combatant(capability=75.0, skill=70.0, preparation=0.05, surprise=0.0)
    result = resolve_combat_exchange(
        CombatExchangeInput(attacker=weaker, defender=stronger, seed=11)
    )
    assert CombatOutcomeClass.SUCCESS_WITH_COST in result.allowed_outcomes
    # Clean success may or may not be allowed depending on margin; costly success is.
    assert not result.rejected
    win = resolve_combat_exchange(
        CombatExchangeInput(
            attacker=weaker,
            defender=stronger,
            seed=11,
            proposed_outcome=CombatOutcomeClass.SUCCESS_WITH_COST,
        )
    )
    assert not win.rejected
    assert win.outcome is CombatOutcomeClass.SUCCESS_WITH_COST


@pytest.mark.unit
def test_impossible_outcome_rejected() -> None:
    weak = _combatant(capability=20.0, skill=15.0, preparation=0.0, surprise=0.0)
    strong = _combatant(capability=90.0, skill=85.0, preparation=0.8)
    result = resolve_combat_exchange(
        CombatExchangeInput(
            attacker=weak,
            defender=strong,
            seed=3,
            proposed_outcome=CombatOutcomeClass.CLEAN_SUCCESS,
        )
    )
    assert result.rejected
    assert result.rejection_reason == "outcome_outside_feasible_envelope"
    assert CombatOutcomeClass.CLEAN_SUCCESS not in result.allowed_outcomes


@pytest.mark.unit
def test_combat_seeded_determinism() -> None:
    attacker = _combatant(capability=55.0, skill=60.0, preparation=0.4)
    defender = _combatant(capability=50.0, skill=45.0, preparation=0.3)
    a = resolve_combat_exchange(CombatExchangeInput(attacker=attacker, defender=defender, seed=99))
    b = resolve_combat_exchange(CombatExchangeInput(attacker=attacker, defender=defender, seed=99))
    assert a == b


@pytest.mark.unit
def test_duplicate_injury_idempotent_by_key_and_id() -> None:
    character_id = uuid4()
    injury_id = uuid4()
    key = "exchange:scene-1:injury-a"
    first = apply_injury(
        InjuryApplication(
            character_id=character_id,
            body_region="left_leg",
            injury_type="fracture",
            severity=55.0,
            bleeding=10.0,
            pain=40.0,
            mobility_effect=60.0,
            injury_id=injury_id,
            idempotency_key=key,
        )
    )
    duplicate_key = apply_injury(
        InjuryApplication(
            character_id=character_id,
            body_region="left_leg",
            injury_type="fracture",
            severity=90.0,
            injury_id=uuid4(),
            idempotency_key=key,
        ),
        existing=(first,),
    )
    duplicate_id = apply_injury(
        InjuryApplication(
            character_id=character_id,
            body_region="torso",
            injury_type="cut",
            severity=10.0,
            injury_id=injury_id,
            idempotency_key="other-key",
        ),
        existing=(first,),
    )
    assert duplicate_key.injury_id == first.injury_id
    assert duplicate_key.severity == first.severity
    assert duplicate_id.severity == first.severity


@pytest.mark.unit
def test_recovery_not_instant_for_serious_injury() -> None:
    injury = apply_injury(
        InjuryApplication(
            character_id=uuid4(),
            body_region="left_leg",
            injury_type="fracture",
            severity=70.0,
            bleeding=20.0,
            pain=50.0,
            mobility_effect=70.0,
        )
    )
    after_one = progress_recovery(
        injury,
        RecoveryStep(
            rest_quality=1.0,
            treatment_quality=0.9,
            healer_skill=80.0,
            phases_elapsed=1,
        ),
    )
    assert after_one.healing_progress < 100.0
    assert after_one.status == "active"
    # Severe injury still impairs action after one phase.
    penalty = injury_action_penalty((after_one,))
    assert penalty > 0.2


@pytest.mark.unit
def test_death_not_via_conversation_schema() -> None:
    conversation = validate_death_prerequisites(
        DeathValidationContext(
            life_status=LifeStatus.CRITICAL,
            catastrophic_injury_criteria_met=True,
            high_impact_authorized=True,
            schema_role="resolver_conversation",
        )
    )
    assert not conversation.ok
    assert any(i.code == "death_unavailable_in_conversation" for i in conversation.issues)

    allowed = validate_death_prerequisites(
        DeathValidationContext(
            life_status=LifeStatus.DYING,
            catastrophic_injury_criteria_met=True,
            high_impact_authorized=True,
            schema_role="resolver_high_impact",
        )
    )
    assert allowed.ok

    kinds = restricted_effect_kinds(GraphTaskRole.RESOLVER_CONVERSATION)
    assert "mark_death" not in kinds
    assert "return_from_death" not in kinds
    assert not effect_kind_allowed("mark_death", GraphTaskRole.RESOLVER_CONVERSATION)


@pytest.mark.unit
def test_return_from_death_lore_constrained() -> None:
    denied = validate_return_from_death(
        ReturnFromDeathContext(
            life_status=LifeStatus.DEAD,
            mechanism="resonance_anchor",
            lore_rule_id="caldris.no_cheap_resurrection",
            lore_allows_return=False,
            high_impact_authorized=True,
            cost_acknowledged=True,
        )
    )
    assert not denied.ok
    assert any(i.code == "lore_forbids_return" for i in denied.issues)

    ok = validate_return_from_death(
        ReturnFromDeathContext(
            life_status=LifeStatus.DEAD,
            mechanism="deity_compact",
            lore_rule_id="caldris.deity_exception",
            lore_allows_return=True,
            high_impact_authorized=True,
            cost_acknowledged=True,
            schema_role="resolver_high_impact",
        )
    )
    assert ok.ok


@pytest.mark.unit
def test_stage3_effect_kinds_present_additively() -> None:
    kinds = {t.model_fields["kind"].default for t in EFFECT_COMMAND_TYPES}
    required = {
        "apply_injury",
        "update_injury",
        "apply_condition",
        "remove_condition",
        "transfer_item",
        "create_item",
        "destroy_item",
        "update_skill_evidence",
        "award_skill_progress",
        "reveal_secret",
        "update_faction_state",
        "update_faction_relation",
        "update_settlement_indicator",
        "create_arc",
        "update_arc",
        "close_arc",
        "create_hook",
        "update_hook",
        "close_hook",
        "mark_death",
        "return_from_death",
        "alter_character_card",
        "alter_world_lore",
        # Frozen Stage 0/1 kinds retained
        "wait",
        "move_entity",
        "skill_progress_evidence",
    }
    assert required <= kinds
