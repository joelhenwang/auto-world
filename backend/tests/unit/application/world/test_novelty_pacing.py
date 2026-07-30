"""Unit tests for Stage 3 pacing / novelty scoring (S3-WORLD-002)."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from fictional_world.application.director.types import DirectorProposal
from fictional_world.application.world import (
    NoveltyHistory,
    NoveltyScoringConfig,
    build_novelty_signature,
    record_trope_usage,
    score_director_proposal_with_novelty,
)


@pytest.fixture
def world_id() -> UUID:
    return uuid4()


@pytest.fixture
def phase_id() -> UUID:
    return uuid4()


def _proposal(
    world_id: UUID,
    phase_id: UUID,
    *,
    trope_tags: tuple[str, ...] = (),
    location_ids: tuple[UUID, ...] = (),
    participant_ids: tuple[UUID, ...] = (),
    is_disruptive: bool = False,
    kind: str = "SOCIAL_OPPORTUNITY",
    urgency: float = 0.8,
    confidence: float = 0.8,
) -> DirectorProposal:
    return DirectorProposal(
        proposal_id=uuid4(),
        phase_id=phase_id,
        world_id=world_id,
        trigger_type="STAGNATION_RISK",
        proposal_kind=kind,
        title="Quiet invitation",
        intent="Invite a focus character to dinner with a trade contact.",
        causal_basis_event_ids=(uuid4(),),
        involved_entity_ids=participant_ids,
        target_location_ids=location_ids,
        proposed_effect_types=("talk",),
        trope_tags=trope_tags,
        is_disruptive=is_disruptive,
        urgency=urgency,
        confidence=confidence,
    )


def test_trope_cooldown_softens_score_not_hard_ban(world_id: UUID, phase_id: UUID) -> None:
    usage = record_trope_usage(
        world_id=world_id,
        trope_tag="SURPRISE_ATTACK",
        phase_index=10,
        day_index=1,
    )
    assert usage.cooldown_until_phase is not None
    assert usage.cooldown_until_phase > 10

    history = NoveltyHistory(
        world_id=world_id,
        current_phase_index=15,
        trope_usages=(usage,),
    )
    proposal = _proposal(
        world_id,
        phase_id,
        trope_tags=("SURPRISE_ATTACK",),
        kind="ENVIRONMENTAL_EVENT",
        is_disruptive=True,
    )
    baseline = score_director_proposal_with_novelty(
        _proposal(world_id, phase_id, trope_tags=()),
        NoveltyHistory(world_id=world_id, current_phase_index=15),
    )
    cooled = score_director_proposal_with_novelty(proposal, history)

    assert cooled.score < baseline.score
    assert cooled.breakdown.trope_penalty > 0
    assert "SURPRISE_ATTACK" in cooled.metrics.tropes_in_cooldown
    # Soft penalty: score remains in range; not rejected/banned.
    assert 0.0 <= cooled.score <= 1.0
    assert cooled.allowed_despite_cooldown is False


def test_causality_forced_allows_recurrence_during_cooldown(world_id: UUID, phase_id: UUID) -> None:
    usage = record_trope_usage(
        world_id=world_id,
        trope_tag="BETRAYAL_REVEAL",
        phase_index=5,
        day_index=0,
    )
    loc = uuid4()
    participants = (uuid4(), uuid4())
    history = NoveltyHistory(
        world_id=world_id,
        current_phase_index=12,
        trope_usages=(usage,),
        recent_location_ids=(loc, loc, loc, loc, loc),
        recent_participant_combos=(
            f"{participants[0]}|{participants[1]}",
            f"{participants[0]}|{participants[1]}",
            f"{participants[0]}|{participants[1]}",
        ),
        recent_action_families=("talk", "talk", "talk", "talk"),
        recent_proposal_kinds=(
            "ENVIRONMENTAL_EVENT",
            "ENVIRONMENTAL_EVENT",
            "ENVIRONMENTAL_EVENT",
        ),
    )
    proposal = _proposal(
        world_id,
        phase_id,
        trope_tags=("BETRAYAL_REVEAL",),
        location_ids=(loc,),
        participant_ids=participants,
        is_disruptive=True,
        kind="ENVIRONMENTAL_EVENT",
    )
    soft = score_director_proposal_with_novelty(proposal, history)
    forced = score_director_proposal_with_novelty(proposal, history, causality_forced=True)

    assert soft.score < NoveltyScoringConfig().causality_forced_floor
    assert forced.score >= NoveltyScoringConfig().causality_forced_floor
    assert forced.breakdown.causality_boost_applied is True
    assert forced.allowed_despite_cooldown is True
    assert "causality_forced_floor" in forced.reasons


def test_pacing_metrics_track_location_participant_action_balance(
    world_id: UUID, phase_id: UUID
) -> None:
    loc = uuid4()
    history = NoveltyHistory(
        world_id=world_id,
        current_phase_index=30,
        recent_location_ids=(loc, loc, loc, loc),
        recent_participant_combos=("a|b", "a|b", "a|b", "c|d"),
        recent_action_families=("fight", "fight", "fight", "travel"),
        recent_proposal_kinds=(
            "ENVIRONMENTAL_EVENT",
            "ENVIRONMENTAL_EVENT",
            "SOCIAL_OPPORTUNITY",
            "DISCOVERY",
        ),
    )
    proposal = _proposal(
        world_id,
        phase_id,
        location_ids=(loc,),
        kind="ENVIRONMENTAL_EVENT",
    )
    result = score_director_proposal_with_novelty(proposal, history)
    assert result.metrics.location_repetition_ratio >= 0.5
    assert result.metrics.participant_combo_ratio > 0
    assert result.metrics.action_family_ratio > 0
    assert 0.0 <= result.metrics.quiet_dramatic_balance <= 1.0


def test_novelty_signature_repeat_penalizes(world_id: UUID, phase_id: UUID) -> None:
    proposal = _proposal(world_id, phase_id)
    sig = build_novelty_signature(
        world_id=world_id,
        signature_kind="proposal",
        phase_index=1,
        day_index=0,
        normalized_text=f"{proposal.proposal_kind}:{proposal.title}:{proposal.intent}",
        participant_ids=proposal.involved_entity_ids,
        action_family="talk",
    )
    history = NoveltyHistory(
        world_id=world_id,
        current_phase_index=20,
        signatures=(sig,),
    )
    scored = score_director_proposal_with_novelty(proposal, history, action_family="talk")
    assert scored.breakdown.signature_penalty > 0
    assert sig.signature_hash in scored.metrics.matching_signature_hashes
