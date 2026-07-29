"""Deterministic Stage 1 scene-priority scoring."""

from __future__ import annotations

from fictional_world.domain.scenes.proposals import PriorityBreakdown

CAUSAL_URGENCY_WEIGHT = 0.25
IMMEDIATE_DANGER_WEIGHT = 0.20
SCHEDULED_COMMITMENT_WEIGHT = 0.15
UNRESOLVED_DEPENDENCY_WEIGHT = 0.15
GOAL_RELEVANCE_WEIGHT = 0.10
STARVATION_FAIRNESS_WEIGHT = 0.10
NARRATIVE_SALIENCE_WEIGHT = 0.05


def score_priority(
    *,
    causal_urgency: float = 0.0,
    immediate_danger: float = 0.0,
    scheduled_commitment: float = 0.0,
    unresolved_dependency: float = 0.0,
    goal_relevance: float = 0.0,
    starvation_fairness: float = 0.0,
) -> PriorityBreakdown:
    """Build a weighted priority; Stage 1 never requests narrative scoring."""

    factors = {
        "causal_urgency": _normalized("causal_urgency", causal_urgency),
        "immediate_danger": _normalized("immediate_danger", immediate_danger),
        "scheduled_commitment": _normalized("scheduled_commitment", scheduled_commitment),
        "unresolved_dependency": _normalized("unresolved_dependency", unresolved_dependency),
        "goal_relevance": _normalized("goal_relevance", goal_relevance),
        "starvation_fairness": _normalized("starvation_fairness", starvation_fairness),
    }
    narrative_salience = 0.0
    final_score = (
        CAUSAL_URGENCY_WEIGHT * factors["causal_urgency"]
        + IMMEDIATE_DANGER_WEIGHT * factors["immediate_danger"]
        + SCHEDULED_COMMITMENT_WEIGHT * factors["scheduled_commitment"]
        + UNRESOLVED_DEPENDENCY_WEIGHT * factors["unresolved_dependency"]
        + GOAL_RELEVANCE_WEIGHT * factors["goal_relevance"]
        + STARVATION_FAIRNESS_WEIGHT * factors["starvation_fairness"]
        + NARRATIVE_SALIENCE_WEIGHT * narrative_salience
    )
    return PriorityBreakdown(
        causal_urgency=factors["causal_urgency"],
        immediate_danger=factors["immediate_danger"],
        scheduled_commitment=factors["scheduled_commitment"],
        unresolved_dependency=factors["unresolved_dependency"],
        goal_relevance=factors["goal_relevance"],
        starvation_fairness=factors["starvation_fairness"],
        narrative_salience=narrative_salience,
        final_score=final_score,
    )


def _normalized(name: str, value: float) -> float:
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


__all__ = [
    "CAUSAL_URGENCY_WEIGHT",
    "GOAL_RELEVANCE_WEIGHT",
    "IMMEDIATE_DANGER_WEIGHT",
    "NARRATIVE_SALIENCE_WEIGHT",
    "SCHEDULED_COMMITMENT_WEIGHT",
    "STARVATION_FAIRNESS_WEIGHT",
    "UNRESOLVED_DEPENDENCY_WEIGHT",
    "score_priority",
]
