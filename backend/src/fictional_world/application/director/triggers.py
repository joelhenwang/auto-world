"""Deterministic Narrative Director trigger evaluation."""

from __future__ import annotations

from collections import Counter

from fictional_world.application.director.config import DirectorTriggerConfig
from fictional_world.application.director.types import (
    DirectorWorldSnapshot,
    TriggerDecision,
    TriggerMetricsSnapshot,
)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _repetition_ratio(samples: tuple[str, ...], *, min_samples: int, threshold: float) -> float:
    if len(samples) < min_samples:
        return 0.0
    counts = Counter(samples)
    mode_count = counts.most_common(1)[0][1]
    ratio = mode_count / len(samples)
    return _clamp01(ratio if ratio >= threshold else ratio * 0.5)


def _emotional_trend(history: tuple[float, ...], *, flat_range: float) -> tuple[float, float]:
    """Return (trend in [-1,1], flatness term in [0,1])."""
    if len(history) < 2:
        return 0.0, 1.0
    first = history[0]
    last = history[-1]
    span = max(history) - min(history)
    magnitude = _clamp01(abs(last - first))
    trend = magnitude if last >= first else -magnitude
    flatness = 1.0 if span <= flat_range else _clamp01(1.0 - span)
    return max(-1.0, min(1.0, trend)), flatness


def evaluate_director_trigger(
    snapshot: DirectorWorldSnapshot,
    *,
    config: DirectorTriggerConfig | None = None,
) -> TriggerDecision:
    """Compute stagnation metrics and decide whether to call the Director.

    Pure / deterministic: no I/O, no model calls.
    """
    cfg = config or DirectorTriggerConfig()

    choice_term = _clamp01(
        snapshot.phases_since_meaningful_choice / max(1, cfg.meaningful_choice_stale_phases)
    )
    ceiling = cfg.goal_progress_stagnation_ceiling
    if snapshot.goal_progress_delta <= ceiling:
        goal_stagnation = 1.0
    else:
        goal_stagnation = _clamp01(
            1.0 - (snapshot.goal_progress_delta - ceiling) / max(1e-9, 1.0 - ceiling)
        )

    loc_rep = _repetition_ratio(
        snapshot.recent_location_keys,
        min_samples=cfg.repetition_min_samples,
        threshold=cfg.repetition_ratio_threshold,
    )
    part_rep = _repetition_ratio(
        snapshot.recent_participant_keys,
        min_samples=cfg.repetition_min_samples,
        threshold=cfg.repetition_ratio_threshold,
    )
    action_rep = _repetition_ratio(
        snapshot.recent_action_families,
        min_samples=cfg.repetition_min_samples,
        threshold=cfg.repetition_ratio_threshold,
    )

    emotion_trend, flatness = _emotional_trend(
        snapshot.emotional_intensity_history,
        flat_range=cfg.emotional_flat_range,
    )
    hook_term = _clamp01(snapshot.unresolved_hook_count / max(1, cfg.unresolved_hook_soft_count))

    if snapshot.last_disruptive_event_phase is None:
        cooldown_remaining = 0
    else:
        elapsed = snapshot.current_phase_index - snapshot.last_disruptive_event_phase
        cooldown_remaining = max(0, cfg.disruptive_cooldown_phases - elapsed)

    stagnation = _clamp01(
        cfg.weight_no_meaningful_decision * choice_term
        + cfg.weight_no_goal_progress * goal_stagnation
        + cfg.weight_location_repetition * loc_rep
        + cfg.weight_participant_repetition * part_rep
        + cfg.weight_action_repetition * action_rep
        + cfg.weight_flat_emotional_trend * flatness
        + cfg.weight_unresolved_hooks * hook_term
    )

    metrics = TriggerMetricsSnapshot(
        phases_since_meaningful_choice=snapshot.phases_since_meaningful_choice,
        repeated_location_ratio=loc_rep,
        repeated_participant_ratio=part_rep,
        repeated_action_ratio=action_rep,
        goal_progress_stagnation=goal_stagnation,
        unresolved_hook_count=snapshot.unresolved_hook_count,
        emotional_intensity_trend=emotion_trend,
        recent_disruptive_event_cooldown=cooldown_remaining,
        stagnation_score=stagnation,
    )

    reasons: list[str] = []
    if choice_term >= 1.0:
        reasons.append("phases_since_meaningful_choice")
    if goal_stagnation >= 1.0:
        reasons.append("goal_progress_stagnation")
    if loc_rep >= cfg.repetition_ratio_threshold:
        reasons.append("repeated_location_pattern")
    if part_rep >= cfg.repetition_ratio_threshold:
        reasons.append("repeated_participant_pattern")
    if action_rep >= cfg.repetition_ratio_threshold:
        reasons.append("repeated_action_pattern")
    if flatness >= 1.0 and len(snapshot.emotional_intensity_history) >= 2:
        reasons.append("emotional_intensity_flat")
    if snapshot.unresolved_hook_count >= cfg.unresolved_hook_soft_count:
        reasons.append("unresolved_hook_count")
    if cooldown_remaining > 0:
        reasons.append("recent_disruptive_event_cooldown")

    should_call = stagnation >= cfg.stagnation_score_threshold
    if should_call and "stagnation_risk" not in reasons:
        reasons.insert(0, "stagnation_risk")

    return TriggerDecision(
        should_call=should_call,
        reasons=tuple(reasons),
        metrics=metrics,
    )
