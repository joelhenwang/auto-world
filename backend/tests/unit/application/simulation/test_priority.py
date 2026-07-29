"""Unit tests for priority weights and beat-budget bounds."""

from __future__ import annotations

import pytest

from fictional_world.application.simulation.beat_budget import SceneType, beat_budget_for
from fictional_world.application.simulation.priority import score_priority


def test_priority_uses_documented_weights_without_model_salience() -> None:
    priority = score_priority(
        causal_urgency=1.0,
        immediate_danger=0.5,
        scheduled_commitment=0.25,
        unresolved_dependency=0.75,
        goal_relevance=0.4,
        starvation_fairness=0.8,
    )

    expected = (0.25 * 1.0) + (0.20 * 0.5) + (0.15 * 0.25) + (0.15 * 0.75)
    expected += (0.10 * 0.4) + (0.10 * 0.8)
    assert priority.final_score == pytest.approx(expected)
    assert priority.narrative_salience == 0.0


@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_priority_rejects_non_normalized_inputs(value: float) -> None:
    with pytest.raises(ValueError, match="causal_urgency"):
        score_priority(causal_urgency=value)


def test_beat_budgets_cover_stage1_defaults_and_clamp() -> None:
    assert beat_budget_for(SceneType.SOLO_ACTION, 1) == 1
    assert beat_budget_for(SceneType.SOCIAL_INTERACTION, 2) == 4
    assert beat_budget_for(SceneType.NEGOTIATION, 20) == 12
    assert beat_budget_for(SceneType.TRAVEL, 0) == 1
