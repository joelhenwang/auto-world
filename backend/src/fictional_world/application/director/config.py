"""Configurable thresholds for deterministic Director trigger evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DirectorTriggerConfig:
    """Stage 2 defaults; handbook 09 §8.1 weights + Stage 2 event budget."""

    stagnation_score_threshold: float = 0.45
    meaningful_choice_stale_phases: int = 8
    goal_progress_stagnation_ceiling: float = 0.05
    repetition_ratio_threshold: float = 0.6
    repetition_min_samples: int = 3
    emotional_flat_range: float = 0.12
    unresolved_hook_soft_count: int = 2
    disruptive_cooldown_phases: int = 10
    weight_no_meaningful_decision: float = 0.25
    weight_no_goal_progress: float = 0.20
    weight_location_repetition: float = 0.15
    weight_participant_repetition: float = 0.15
    weight_action_repetition: float = 0.10
    weight_flat_emotional_trend: float = 0.10
    weight_unresolved_hooks: float = 0.05
