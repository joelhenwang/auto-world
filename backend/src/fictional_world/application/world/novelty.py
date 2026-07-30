"""Soft novelty scoring for Director proposals (S3-WORLD-002).

Cooldown reduces proposal score; it is not a hard ban. When causality genuinely
requires recurrence (``causality_forced=True``), the score is floored so a
forced rematch remains selectable.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from uuid import UUID, uuid4

from fictional_world.application.director.types import DirectorProposal
from fictional_world.application.world.config import NoveltyScoringConfig
from fictional_world.application.world.pacing import (
    compute_pacing_metrics,
    participant_combo_key,
)
from fictional_world.application.world.types import (
    NoveltyHistory,
    NoveltyScoreBreakdown,
    NoveltyScoreResult,
)
from fictional_world.domain.stage3.persistence import (
    NoveltySignaturePersistenceRecord,
    TropeUsagePersistenceRecord,
)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def normalize_trope_tag(tag: str) -> str:
    return tag.strip().upper()


def trope_cooldown_phases(tag: str, *, config: NoveltyScoringConfig) -> int:
    normalized = normalize_trope_tag(tag)
    return config.trope_cooldowns.get(normalized, config.default_trope_cooldown_phases)


def build_novelty_signature(
    *,
    world_id: UUID,
    signature_kind: str,
    phase_index: int,
    day_index: int,
    normalized_text: str | None = None,
    participant_ids: Sequence[UUID] = (),
    location_id: UUID | None = None,
    action_family: str | None = None,
    signature_id: UUID | None = None,
) -> NoveltySignaturePersistenceRecord:
    """Build a novelty signature record with a deterministic content hash."""
    parts = [
        signature_kind.strip().lower(),
        (normalized_text or "").strip().lower(),
        participant_combo_key(participant_ids),
        str(location_id) if location_id is not None else "",
        (action_family or "").strip().lower(),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return NoveltySignaturePersistenceRecord(
        id=signature_id or uuid4(),
        world_id=world_id,
        signature_kind=signature_kind.strip().lower(),
        signature_hash=digest,
        normalized_text=normalized_text,
        phase_index=phase_index,
        day_index=day_index,
        participant_ids=tuple(participant_ids),
        location_id=location_id,
        action_family=action_family.strip().lower() if action_family else None,
    )


def record_trope_usage(
    *,
    world_id: UUID,
    trope_tag: str,
    phase_index: int,
    day_index: int,
    config: NoveltyScoringConfig | None = None,
    scene_id: UUID | None = None,
    participant_ids: Sequence[UUID] = (),
    location_id: UUID | None = None,
    content_hash: str | None = None,
    usage_id: UUID | None = None,
) -> TropeUsagePersistenceRecord:
    """Create a trope usage row with cooldown_until_phase populated."""
    cfg = config or NoveltyScoringConfig()
    tag = normalize_trope_tag(trope_tag)
    cooldown = trope_cooldown_phases(tag, config=cfg)
    return TropeUsagePersistenceRecord(
        id=usage_id or uuid4(),
        world_id=world_id,
        trope_tag=tag,
        phase_index=phase_index,
        day_index=day_index,
        scene_id=scene_id,
        participant_ids=tuple(participant_ids),
        location_id=location_id,
        cooldown_until_phase=phase_index + cooldown,
        content_hash=content_hash,
    )


def score_director_proposal_with_novelty(
    proposal: DirectorProposal,
    history: NoveltyHistory,
    *,
    config: NoveltyScoringConfig | None = None,
    causality_forced: bool = False,
    action_family: str | None = None,
    signature_hashes: Sequence[str] = (),
    base_score: float | None = None,
) -> NoveltyScoreResult:
    """Score a Director proposal with soft anti-repetition penalties.

    Parameters
    ----------
    causality_forced:
        When True, cooldown / repetition cannot suppress the proposal below
        ``causality_forced_floor`` — recurrence remains allowed when required.
    """
    cfg = config or NoveltyScoringConfig()
    baseline = (
        _clamp(base_score, cfg.min_score, cfg.max_score)
        if base_score is not None
        else _clamp(float(proposal.urgency) * 0.5 + float(proposal.confidence) * 0.5, 0.0, 1.0)
    )

    inferred_action = action_family
    if inferred_action is None and proposal.proposed_effect_types:
        inferred_action = proposal.proposed_effect_types[0]

    # Derive signature hashes from proposal text when caller does not supply them.
    derived_hashes = list(signature_hashes)
    if not derived_hashes and (proposal.title or proposal.intent):
        derived = build_novelty_signature(
            world_id=proposal.world_id,
            signature_kind="proposal",
            phase_index=history.current_phase_index,
            day_index=max(0, history.current_phase_index // 10),
            normalized_text=f"{proposal.proposal_kind}:{proposal.title}:{proposal.intent}",
            participant_ids=proposal.involved_entity_ids,
            location_id=proposal.target_location_ids[0] if proposal.target_location_ids else None,
            action_family=inferred_action,
        )
        derived_hashes.append(derived.signature_hash)

    metrics = compute_pacing_metrics(
        history,
        proposal_trope_tags=proposal.trope_tags,
        proposal_location_ids=proposal.target_location_ids,
        proposal_participant_ids=proposal.involved_entity_ids,
        proposal_action_family=inferred_action,
        proposal_signature_hashes=derived_hashes,
        config=cfg,
    )

    trope_penalty = 0.0
    if metrics.tropes_in_cooldown:
        trope_penalty = min(1.0, cfg.trope_cooldown_penalty * len(metrics.tropes_in_cooldown))

    location_penalty = (
        cfg.location_repetition_penalty * metrics.location_repetition_ratio
        if metrics.location_repetition_ratio >= cfg.repetition_ratio_threshold
        else cfg.location_repetition_penalty * metrics.location_repetition_ratio * 0.5
    )
    participant_penalty = (
        cfg.participant_combo_penalty * metrics.participant_combo_ratio
        if metrics.participant_combo_ratio >= cfg.repetition_ratio_threshold
        else cfg.participant_combo_penalty * metrics.participant_combo_ratio * 0.5
    )
    action_penalty = (
        cfg.action_family_penalty * metrics.action_family_ratio
        if metrics.action_family_ratio >= cfg.repetition_ratio_threshold
        else cfg.action_family_penalty * metrics.action_family_ratio * 0.5
    )
    balance_penalty = cfg.quiet_dramatic_imbalance_penalty * (1.0 - metrics.quiet_dramatic_balance)
    signature_penalty = cfg.signature_hash_penalty if metrics.matching_signature_hashes else 0.0
    disruptive_penalty = cfg.disruptive_kinds_extra_penalty if proposal.is_disruptive else 0.0

    raw = (
        baseline
        - trope_penalty
        - location_penalty
        - participant_penalty
        - action_penalty
        - balance_penalty
        - signature_penalty
        - disruptive_penalty
    )
    causality_applied = False
    if causality_forced and raw < cfg.causality_forced_floor:
        raw = cfg.causality_forced_floor
        causality_applied = True

    final = _clamp(raw, cfg.min_score, cfg.max_score)

    reasons: list[str] = []
    if metrics.tropes_in_cooldown:
        reasons.append(f"trope_cooldown:{','.join(metrics.tropes_in_cooldown)}")
    if metrics.location_repetition_ratio >= cfg.repetition_ratio_threshold:
        reasons.append("location_repetition")
    if metrics.participant_combo_ratio >= cfg.repetition_ratio_threshold:
        reasons.append("participant_combo_repetition")
    if metrics.action_family_ratio >= cfg.repetition_ratio_threshold:
        reasons.append("action_family_repetition")
    if metrics.quiet_dramatic_balance < 0.5:
        reasons.append("quiet_dramatic_imbalance")
    if metrics.matching_signature_hashes:
        reasons.append("novelty_signature_repeat")
    if causality_applied:
        reasons.append("causality_forced_floor")

    breakdown = NoveltyScoreBreakdown(
        base_score=baseline,
        trope_penalty=_clamp(trope_penalty, 0.0, 1.0),
        location_penalty=_clamp(location_penalty, 0.0, 1.0),
        participant_penalty=_clamp(participant_penalty, 0.0, 1.0),
        action_family_penalty=_clamp(action_penalty, 0.0, 1.0),
        balance_penalty=_clamp(balance_penalty, 0.0, 1.0),
        signature_penalty=_clamp(signature_penalty, 0.0, 1.0),
        disruptive_penalty=_clamp(disruptive_penalty, 0.0, 1.0),
        causality_boost_applied=causality_applied,
        final_score=final,
    )

    return NoveltyScoreResult(
        score=final,
        metrics=metrics,
        breakdown=breakdown,
        allowed_despite_cooldown=causality_forced and bool(metrics.tropes_in_cooldown),
        reasons=tuple(reasons),
    )
