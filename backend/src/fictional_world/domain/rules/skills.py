"""Skill evidence accumulation and bounded progression (S3-RULES-001 / handbook ``10`` §4)."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.rules.scale import STAT_MAX, STAT_MIN, clamp_unit, clamp_world_scale
from fictional_world.domain.rules.seeded import seeded_unit_float


class SkillState(StrictContract):
    character_id: UUID
    skill_id: UUID
    proficiency: float = Field(ge=STAT_MIN, le=STAT_MAX)
    dynamic_potential_cap: float = Field(ge=STAT_MIN, le=STAT_MAX)
    growth_rate: float = Field(ge=0.0, le=1.0)
    practice_evidence_total: float = Field(default=0.0, ge=0.0)
    version: int = Field(default=0, ge=0)


class SkillProgressEvidence(StrictContract):
    character_id: UUID
    skill_id: UUID
    difficulty: float = Field(ge=0.0, le=1.0)
    practice_quality: float = Field(ge=0.0, le=1.0)
    duration_weight: float = Field(default=1.0, ge=0.0)
    novelty: float = Field(default=0.5, ge=0.0, le=1.0)
    feedback_quality: float = Field(default=0.5, ge=0.0, le=1.0)
    success_factor: float = Field(default=0.5, ge=0.0, le=1.0)
    recovery_factor: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_units: float = Field(gt=0.0)
    source_event_id: UUID | None = None
    teacher_bonus: float = Field(default=0.0, ge=0.0, le=1.0)
    trivial_repetition_count: int = Field(default=0, ge=0)


class SkillProgressProposal(StrictContract):
    """Bounded proficiency increment proposal; requires evidence, never a free leap."""

    character_id: UUID
    skill_id: UUID
    proficiency_delta: float = Field(ge=0.0, le=STAT_MAX)
    evidence_consumed: float = Field(ge=0.0)
    remaining_evidence: float = Field(ge=0.0)
    extraordinary: bool = False
    rejected_reason: str | None = None


def accumulate_skill_evidence(
    state: SkillState,
    evidence: SkillProgressEvidence,
    *,
    prior_trivial_count: int | None = None,
) -> tuple[SkillState, float]:
    """Accumulate practice evidence with diminishing returns for trivial repetition.

    Attributes do not substitute for skills: this function never reads base stats.
    Returns ``(new_state, units_added)``.
    """

    if evidence.character_id != state.character_id or evidence.skill_id != state.skill_id:
        raise InvalidAction("skill evidence subject does not match skill state")

    trivial_count = (
        prior_trivial_count
        if prior_trivial_count is not None
        else evidence.trivial_repetition_count
    )
    # Trivial / repeated low-difficulty practice yields diminishing evidence.
    triviality = 1.0 / (1.0 + max(0, trivial_count) * 0.35)
    if evidence.difficulty < 0.2:
        triviality *= 0.5 + 0.5 * evidence.difficulty / 0.2

    units = (
        evidence.evidence_units
        * clamp_unit(evidence.practice_quality)
        * (0.4 + 0.6 * clamp_unit(evidence.difficulty))
        * max(0.0, evidence.duration_weight)
        * (0.5 + 0.5 * clamp_unit(evidence.novelty))
        * (0.5 + 0.5 * clamp_unit(evidence.feedback_quality))
        * (0.35 + 0.65 * clamp_unit(evidence.success_factor))
        * clamp_unit(evidence.recovery_factor)
        * (1.0 + 0.25 * clamp_unit(evidence.teacher_bonus))
        * triviality
    )
    units = max(0.0, units)
    new_total = state.practice_evidence_total + units
    return (
        state.model_copy(
            update={
                "practice_evidence_total": new_total,
                "version": state.version + 1,
            }
        ),
        units,
    )


def propose_skill_progress(
    state: SkillState,
    *,
    extraordinary_event: bool = False,
    extraordinary_authorized: bool = False,
    seed: int | None = None,
    evidence_threshold: float = 5.0,
    max_ordinary_delta: float = 1.5,
) -> SkillProgressProposal:
    """Propose a bounded proficiency increase gated by accumulated evidence.

    Ordinary progression cannot leap; extraordinary leaps require both an
    extraordinary event flag and high-impact authorization.
    """

    headroom = max(0.0, state.dynamic_potential_cap - state.proficiency)
    if headroom <= 0.0:
        return SkillProgressProposal(
            character_id=state.character_id,
            skill_id=state.skill_id,
            proficiency_delta=0.0,
            evidence_consumed=0.0,
            remaining_evidence=state.practice_evidence_total,
            rejected_reason="at_potential_cap",
        )

    if extraordinary_event:
        if not extraordinary_authorized:
            return SkillProgressProposal(
                character_id=state.character_id,
                skill_id=state.skill_id,
                proficiency_delta=0.0,
                evidence_consumed=0.0,
                remaining_evidence=state.practice_evidence_total,
                extraordinary=True,
                rejected_reason="extraordinary_not_authorized",
            )
        # Still bounded: at most 10% of remaining headroom or 8 points.
        leap = min(8.0, headroom * 0.10, state.practice_evidence_total * 0.5)
        if seed is not None:
            leap *= 0.85 + 0.15 * seeded_unit_float(seed, "skill_leap", str(state.skill_id))
        leap = clamp_world_scale(leap, minimum=0.0, maximum=headroom)
        return SkillProgressProposal(
            character_id=state.character_id,
            skill_id=state.skill_id,
            proficiency_delta=leap,
            evidence_consumed=min(state.practice_evidence_total, leap * 2.0),
            remaining_evidence=max(0.0, state.practice_evidence_total - leap * 2.0),
            extraordinary=True,
        )

    if state.practice_evidence_total < evidence_threshold:
        return SkillProgressProposal(
            character_id=state.character_id,
            skill_id=state.skill_id,
            proficiency_delta=0.0,
            evidence_consumed=0.0,
            remaining_evidence=state.practice_evidence_total,
            rejected_reason="insufficient_evidence",
        )

    raw = (
        state.practice_evidence_total
        * state.growth_rate
        * (headroom / STAT_MAX)
        * (1.0 / (1.0 + state.proficiency / 40.0))
    )
    if seed is not None:
        raw *= 0.9 + 0.2 * seeded_unit_float(seed, "skill_progress", str(state.skill_id))

    delta = min(raw, max_ordinary_delta, headroom)
    delta = clamp_world_scale(delta, minimum=0.0, maximum=headroom)
    consumed = min(state.practice_evidence_total, evidence_threshold + delta * 2.0)
    return SkillProgressProposal(
        character_id=state.character_id,
        skill_id=state.skill_id,
        proficiency_delta=delta,
        evidence_consumed=consumed,
        remaining_evidence=max(0.0, state.practice_evidence_total - consumed),
    )


def apply_skill_progress(state: SkillState, proposal: SkillProgressProposal) -> SkillState:
    """Apply an accepted progress proposal to skill proficiency and evidence totals."""

    if proposal.character_id != state.character_id or proposal.skill_id != state.skill_id:
        raise InvalidAction("progress proposal subject does not match skill state")
    if proposal.proficiency_delta <= 0.0:
        return (
            state.model_copy(update={"practice_evidence_total": proposal.remaining_evidence})
            if proposal.rejected_reason is None
            else state
        )

    new_prof = clamp_world_scale(
        state.proficiency + proposal.proficiency_delta,
        minimum=STAT_MIN,
        maximum=min(STAT_MAX, state.dynamic_potential_cap),
    )
    return state.model_copy(
        update={
            "proficiency": new_prof,
            "practice_evidence_total": proposal.remaining_evidence,
            "version": state.version + 1,
        }
    )
