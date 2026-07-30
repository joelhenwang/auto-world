"""Pure pacing metric helpers for Stage 3 anti-repetition."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from uuid import UUID

from fictional_world.application.world.config import NoveltyScoringConfig
from fictional_world.application.world.types import NoveltyHistory, PacingMetricsSnapshot
from fictional_world.domain.stage3.persistence import TropeUsagePersistenceRecord


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def repetition_ratio(samples: Sequence[str], *, threshold: float) -> float:
    """Mode frequency among samples; softens below threshold."""
    if not samples:
        return 0.0
    counts = Counter(samples)
    mode_count = counts.most_common(1)[0][1]
    ratio = mode_count / len(samples)
    if ratio >= threshold:
        return _clamp01(ratio)
    return _clamp01(ratio * 0.5)


def participant_combo_key(participant_ids: Sequence[UUID]) -> str:
    """Stable hash key for a participant combination."""
    return "|".join(sorted(str(pid) for pid in participant_ids))


def tropes_in_cooldown(
    usages: Sequence[TropeUsagePersistenceRecord],
    *,
    current_phase_index: int,
    tags: Sequence[str],
) -> tuple[str, ...]:
    """Return proposal trope tags still inside a recorded cooldown window."""
    wanted = {tag.strip().upper() for tag in tags if tag.strip()}
    if not wanted:
        return ()
    cooling: set[str] = set()
    for usage in usages:
        tag = usage.trope_tag.strip().upper()
        if tag not in wanted:
            continue
        until = usage.cooldown_until_phase
        if until is not None and current_phase_index < until:
            cooling.add(tag)
    return tuple(sorted(cooling))


def quiet_dramatic_shares(
    recent_kinds: Sequence[str],
    *,
    config: NoveltyScoringConfig,
) -> tuple[float, float, float]:
    """Return (quiet_share, dramatic_share, balance) where balance=1 is even."""
    if not recent_kinds:
        return 0.0, 0.0, 1.0
    quiet = sum(1 for k in recent_kinds if k.upper() in config.quiet_proposal_kinds)
    dramatic = sum(1 for k in recent_kinds if k.upper() in config.dramatic_proposal_kinds)
    total = len(recent_kinds)
    quiet_share = quiet / total
    dramatic_share = dramatic / total
    # Perfect balance when quiet≈dramatic among classified kinds; unclassified ignored.
    classified = quiet + dramatic
    if classified == 0:
        return quiet_share, dramatic_share, 1.0
    skew = abs(quiet - dramatic) / classified
    balance = _clamp01(1.0 - skew)
    return _clamp01(quiet_share), _clamp01(dramatic_share), balance


def compute_pacing_metrics(
    history: NoveltyHistory,
    *,
    proposal_trope_tags: Sequence[str] = (),
    proposal_location_ids: Sequence[UUID] = (),
    proposal_participant_ids: Sequence[UUID] = (),
    proposal_action_family: str | None = None,
    proposal_signature_hashes: Sequence[str] = (),
    config: NoveltyScoringConfig | None = None,
) -> PacingMetricsSnapshot:
    """Compute rolling location / participant / action / quiet-dramatic metrics."""
    cfg = config or NoveltyScoringConfig()
    window = max(1, cfg.repetition_window)

    loc_samples = tuple(
        str(loc) for loc in history.recent_location_ids[-window:] if loc is not None
    )
    if proposal_location_ids:
        loc_samples = (
            *loc_samples,
            *(str(loc) for loc in proposal_location_ids),
        )

    part_samples = history.recent_participant_combos[-window:]
    if proposal_participant_ids:
        part_samples = (
            *part_samples,
            participant_combo_key(proposal_participant_ids),
        )

    action_samples = history.recent_action_families[-window:]
    if proposal_action_family:
        action_samples = (*action_samples, proposal_action_family.strip().lower())

    quiet_share, dramatic_share, balance = quiet_dramatic_shares(
        history.recent_proposal_kinds[-window:],
        config=cfg,
    )

    cooling = tropes_in_cooldown(
        history.trope_usages,
        current_phase_index=history.current_phase_index,
        tags=proposal_trope_tags,
    )

    wanted_hashes = {h for h in proposal_signature_hashes if h}
    matching = tuple(
        sorted(
            {
                sig.signature_hash
                for sig in history.signatures
                if sig.signature_hash in wanted_hashes
            }
        )
    )

    return PacingMetricsSnapshot(
        location_repetition_ratio=repetition_ratio(
            loc_samples, threshold=cfg.repetition_ratio_threshold
        ),
        participant_combo_ratio=repetition_ratio(
            part_samples, threshold=cfg.repetition_ratio_threshold
        ),
        action_family_ratio=repetition_ratio(
            action_samples, threshold=cfg.repetition_ratio_threshold
        ),
        quiet_share=quiet_share,
        dramatic_share=dramatic_share,
        quiet_dramatic_balance=balance,
        tropes_in_cooldown=cooling,
        matching_signature_hashes=matching,
    )
