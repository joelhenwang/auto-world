"""Unit tests for S3-RULES-002 Resonance magic resolution."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from fictional_world.domain.common.enums import ResolutionLevel
from fictional_world.domain.rules.magic import (
    CastTimeClass,
    KnownSpell,
    MagicState,
    SpellAttempt,
    SpellDefinition,
    SpellOutcomeClass,
    SpellPrerequisites,
    SpellTargetRules,
    resolve_spell_attempt,
)


def _spell(**overrides: object) -> SpellDefinition:
    base: dict[str, object] = {
        "spell_id": uuid4(),
        "spell_code": "ember_spark",
        "name": "Ember Spark",
        "school": "resonance",
        "elements": ("fire",),
        "minimum_proficiency": 10.0,
        "mana_cost_min": 8.0,
        "mana_cost_max": 14.0,
        "cast_time_class": CastTimeClass.STANDARD,
        "cast_time_beats": 2,
        "target_rules": SpellTargetRules(max_targets=1, max_range_units=5.0),
        "prerequisites": SpellPrerequisites(
            required_schools=("resonance",),
            minimum_mana_control=20.0,
            material_tags=("focus_crystal",),
        ),
        "counters": ("silence",),
    }
    base.update(overrides)
    return SpellDefinition.model_validate(base)


@pytest.mark.unit
def test_unregistered_spell_rejected() -> None:
    spell = _spell()
    magic = MagicState(
        character_id=uuid4(),
        mana_current=50.0,
        mana_capacity=50.0,
        mana_control=40.0,
        school_affinities={"resonance": 30.0},
    )
    result = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=None,
        attempt=SpellAttempt(
            caster_id=magic.character_id,
            spell_id=spell.spell_id,
            available_material_tags=("focus_crystal",),
            seed=1,
        ),
        registered_spell_ids=frozenset(),
    )
    assert result.outcome is SpellOutcomeClass.INVALID
    assert result.mana_spent == 0.0
    assert result.failure_mode == "unknown_spell"


@pytest.mark.unit
def test_insufficient_mana_cannot_overdraw() -> None:
    spell = _spell()
    caster = uuid4()
    magic = MagicState(
        character_id=caster,
        mana_current=3.0,
        mana_capacity=50.0,
        mana_control=40.0,
        school_affinities={"resonance": 40.0},
    )
    known = KnownSpell(character_id=caster, spell_id=spell.spell_id, proficiency=40.0)
    result = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=known,
        attempt=SpellAttempt(
            caster_id=caster,
            spell_id=spell.spell_id,
            available_material_tags=("focus_crystal",),
            seed=2,
        ),
        registered_spell_ids={spell.spell_id},
    )
    assert result.outcome is SpellOutcomeClass.FAILURE
    assert result.failure_mode == "insufficient_mana"
    assert result.mana_spent == 0.0
    assert result.mana_remaining == 3.0


@pytest.mark.unit
def test_prerequisite_and_material_gates() -> None:
    spell = _spell()
    caster = uuid4()
    magic = MagicState(
        character_id=caster,
        mana_current=40.0,
        mana_capacity=40.0,
        mana_control=10.0,
        school_affinities={},
    )
    known = KnownSpell(character_id=caster, spell_id=spell.spell_id, proficiency=40.0)
    result = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=known,
        attempt=SpellAttempt(
            caster_id=caster,
            spell_id=spell.spell_id,
            available_material_tags=(),
            seed=3,
        ),
        registered_spell_ids={spell.spell_id},
    )
    assert result.outcome is SpellOutcomeClass.INVALID
    codes = {issue.code for issue in result.issues}
    assert "mana_control_prerequisite" in codes
    assert "school_prerequisite" in codes
    assert "material_prerequisite" in codes


@pytest.mark.unit
def test_interruption_partial_mana_spend() -> None:
    spell = _spell()
    caster = uuid4()
    magic = MagicState(
        character_id=caster,
        mana_current=40.0,
        mana_capacity=40.0,
        mana_control=50.0,
        school_affinities={"resonance": 50.0},
    )
    known = KnownSpell(character_id=caster, spell_id=spell.spell_id, proficiency=50.0)
    result = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=known,
        attempt=SpellAttempt(
            caster_id=caster,
            spell_id=spell.spell_id,
            available_material_tags=("focus_crystal",),
            interrupted=True,
            seed=4,
        ),
        registered_spell_ids={spell.spell_id},
    )
    assert result.outcome is SpellOutcomeClass.INTERRUPTED
    assert result.resolution_level is ResolutionLevel.INTERRUPTED
    assert 0.0 < result.mana_spent < spell.mana_cost_min
    assert result.mana_remaining == pytest.approx(40.0 - result.mana_spent)


@pytest.mark.unit
def test_successful_cast_spends_bounded_mana_deterministically() -> None:
    spell = _spell(spell_id=UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"))
    caster = UUID("11111111-2222-3333-4444-555555555555")
    magic = MagicState(
        character_id=caster,
        mana_current=80.0,
        mana_capacity=80.0,
        mana_control=70.0,
        spell_stability=70.0,
        school_affinities={"resonance": 60.0},
    )
    known = KnownSpell(
        character_id=caster,
        spell_id=spell.spell_id,
        proficiency=80.0,
        reliability=0.9,
    )
    attempt = SpellAttempt(
        caster_id=caster,
        spell_id=spell.spell_id,
        available_material_tags=("focus_crystal",),
        seed=1,
    )
    first = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=known,
        attempt=attempt,
        registered_spell_ids={spell.spell_id},
    )
    second = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=known,
        attempt=attempt,
        registered_spell_ids={spell.spell_id},
    )
    assert first.outcome is SpellOutcomeClass.SUCCESS
    assert first == second
    assert spell.mana_cost_min <= first.mana_spent <= spell.mana_cost_max
    assert first.mana_remaining == pytest.approx(80.0 - first.mana_spent)


@pytest.mark.unit
def test_counter_forces_failure_with_mana_cost() -> None:
    spell = _spell()
    caster = uuid4()
    magic = MagicState(
        character_id=caster,
        mana_current=50.0,
        mana_capacity=50.0,
        mana_control=60.0,
        school_affinities={"resonance": 50.0},
    )
    known = KnownSpell(character_id=caster, spell_id=spell.spell_id, proficiency=60.0)
    result = resolve_spell_attempt(
        definition=spell,
        magic=magic,
        known=known,
        attempt=SpellAttempt(
            caster_id=caster,
            spell_id=spell.spell_id,
            available_material_tags=("focus_crystal",),
            counter_tags=("silence",),
            seed=5,
        ),
        registered_spell_ids={spell.spell_id},
    )
    assert result.outcome is SpellOutcomeClass.FAILURE
    assert result.failure_mode == "countered:silence"
    assert result.mana_spent > 0.0
