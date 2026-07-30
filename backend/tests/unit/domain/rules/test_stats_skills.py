"""Unit/property tests for S3-RULES-001 stats and skills."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.domain.rules.scale import STAT_MAX, STAT_MIN
from fictional_world.domain.rules.seeded import seeded_unit_float
from fictional_world.domain.rules.skills import (
    SkillProgressEvidence,
    SkillState,
    accumulate_skill_evidence,
    apply_skill_progress,
    propose_skill_progress,
)
from fictional_world.domain.rules.stats import (
    CapabilityKind,
    DerivedCapabilityInputs,
    StatEvidence,
    StatState,
    StatType,
    TemporaryModifier,
    apply_stat_evidence,
    clamp_stat,
    compute_derived_capability,
    effective_stat,
)


@pytest.mark.unit
def test_clamp_stat_bounds_and_potential_cap() -> None:
    assert clamp_stat(-5) == STAT_MIN
    assert clamp_stat(150) == STAT_MAX
    assert clamp_stat(80, potential_cap=60) == 60.0
    assert clamp_stat(40, potential_cap=60) == 40.0


@pytest.mark.unit
def test_temporary_modifiers_do_not_overwrite_base() -> None:
    character_id = uuid4()
    state = StatState(
        character_id=character_id,
        stat_type=StatType.STRENGTH,
        base_value=50.0,
        dynamic_potential_cap=70.0,
        growth_rate=0.4,
        temporary_modifiers=(
            TemporaryModifier(
                stat_type=StatType.STRENGTH,
                delta=10.0,
                multiplier=1.1,
                stacking_group="blessing",
            ),
        ),
    )
    effective = effective_stat(state, at_phase=0)
    assert state.base_value == 50.0
    assert effective.base_value == 50.0
    assert effective.effective_value == pytest.approx(66.0)
    assert effective.effective_value != effective.base_value


@pytest.mark.unit
def test_apply_stat_evidence_monotonic_and_capped() -> None:
    state = StatState(
        character_id=uuid4(),
        stat_type=StatType.DEXTERITY,
        base_value=40.0,
        dynamic_potential_cap=55.0,
        growth_rate=0.6,
        adaptability=0.7,
    )
    evidence = StatEvidence(
        difficulty=0.7,
        practice_quality=0.8,
        novelty=0.6,
        recovery_factor=1.0,
        evidence_units=3.0,
    )
    new_state, delta = apply_stat_evidence(state, evidence, seed=7)
    assert delta >= 0.0
    assert new_state.base_value >= state.base_value
    assert new_state.base_value <= state.dynamic_potential_cap
    # No sudden leap: ordinary evidence is tightly capped.
    assert delta <= 2.0


@pytest.mark.property
def test_stat_evidence_seeded_determinism() -> None:
    character_id = uuid4()
    state = StatState(
        character_id=character_id,
        stat_type=StatType.INTELLIGENCE,
        base_value=45.0,
        dynamic_potential_cap=80.0,
        growth_rate=0.5,
    )
    evidence = StatEvidence(
        difficulty=0.5,
        practice_quality=0.5,
        evidence_units=2.0,
    )
    a, da = apply_stat_evidence(state, evidence, seed=99)
    b, db = apply_stat_evidence(state, evidence, seed=99)
    c, dc = apply_stat_evidence(state, evidence, seed=100)
    assert a.base_value == b.base_value
    assert da == db
    assert seeded_unit_float(99, "stat_evidence", "intelligence") == seeded_unit_float(
        99, "stat_evidence", "intelligence"
    )
    # Different seeds may differ; at minimum helper is deterministic per seed.
    assert isinstance(dc, float)
    assert c.base_value >= state.base_value


@pytest.mark.unit
def test_derived_capability_uses_stats_not_as_skills() -> None:
    inputs = DerivedCapabilityInputs(
        stats={
            StatType.STRENGTH: 70.0,
            StatType.DEXTERITY: 40.0,
            StatType.PERCEPTION: 40.0,
        },
        relevant_skill=20.0,
        leverage_context=50.0,
    )
    power = compute_derived_capability(CapabilityKind.PHYSICAL_POWER, inputs)
    assert 0.0 <= power <= 100.0
    # High strength alone with low skill is not maxed.
    assert power < 95.0


@pytest.mark.unit
def test_skill_evidence_accumulation_diminishing_for_trivial() -> None:
    skill_id = uuid4()
    character_id = uuid4()
    state = SkillState(
        character_id=character_id,
        skill_id=skill_id,
        proficiency=30.0,
        dynamic_potential_cap=70.0,
        growth_rate=0.5,
    )
    fresh = SkillProgressEvidence(
        character_id=character_id,
        skill_id=skill_id,
        difficulty=0.1,
        practice_quality=0.9,
        evidence_units=2.0,
        trivial_repetition_count=0,
    )
    repeated = fresh.model_copy(update={"trivial_repetition_count": 8})
    _, units_fresh = accumulate_skill_evidence(state, fresh)
    _, units_repeated = accumulate_skill_evidence(state, repeated)
    assert units_fresh > units_repeated


@pytest.mark.unit
def test_propose_skill_progress_evidence_gated_no_leap() -> None:
    skill_id = uuid4()
    character_id = uuid4()
    low_evidence = SkillState(
        character_id=character_id,
        skill_id=skill_id,
        proficiency=20.0,
        dynamic_potential_cap=80.0,
        growth_rate=0.6,
        practice_evidence_total=1.0,
    )
    blocked = propose_skill_progress(low_evidence, seed=1)
    assert blocked.proficiency_delta == 0.0
    assert blocked.rejected_reason == "insufficient_evidence"

    ready = low_evidence.model_copy(update={"practice_evidence_total": 20.0})
    proposal = propose_skill_progress(ready, seed=1)
    assert proposal.proficiency_delta > 0.0
    assert proposal.proficiency_delta <= 1.5
    applied = apply_skill_progress(ready, proposal)
    assert applied.proficiency == pytest.approx(ready.proficiency + proposal.proficiency_delta)

    leap = propose_skill_progress(
        ready,
        extraordinary_event=True,
        extraordinary_authorized=False,
    )
    assert leap.proficiency_delta == 0.0
    assert leap.rejected_reason == "extraordinary_not_authorized"
