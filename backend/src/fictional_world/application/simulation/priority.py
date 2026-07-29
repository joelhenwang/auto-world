"""Deterministic scene-priority and intra-scene initiative scoring."""

from __future__ import annotations

from fictional_world.domain.scenes.proposals import PriorityBreakdown

CAUSAL_URGENCY_WEIGHT = 0.25
IMMEDIATE_DANGER_WEIGHT = 0.20
SCHEDULED_COMMITMENT_WEIGHT = 0.15
UNRESOLVED_DEPENDENCY_WEIGHT = 0.15
GOAL_RELEVANCE_WEIGHT = 0.10
STARVATION_FAIRNESS_WEIGHT = 0.10
NARRATIVE_SALIENCE_WEIGHT = 0.05

PREPARATION_WEIGHT = 0.20
SURPRISE_WEIGHT = 0.15
DEXTERITY_WEIGHT = 0.15
PERCEPTION_WEIGHT = 0.15
RELEVANT_SKILL_WEIGHT = 0.15
STAMINA_WEIGHT = 0.10
TERRAIN_WEIGHT = 0.05
SEEDED_RANDOM_WEIGHT = 0.05


def score_priority(
    *,
    causal_urgency: float = 0.0,
    immediate_danger: float = 0.0,
    scheduled_commitment: float = 0.0,
    unresolved_dependency: float = 0.0,
    goal_relevance: float = 0.0,
    starvation_fairness: float = 0.0,
) -> PriorityBreakdown:
    """Build a weighted priority; narrative salience stays zero without a model."""

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


def score_initiative(
    *,
    preparation: float = 0.0,
    surprise: float = 0.0,
    dexterity: float = 0.0,
    perception: float = 0.0,
    relevant_skill: float = 0.0,
    current_stamina: float = 0.0,
    terrain_advantage: float = 0.0,
    seeded_randomness: float = 0.0,
    injury_penalty: float = 0.0,
) -> float:
    """Intra-scene initiative (handbook ``05`` §9.5); independent of scene priority.

    All positive factors are normalized ``0..1``. ``injury_penalty`` is subtracted
    after weighting and must be ``>= 0``.
    """

    if injury_penalty < 0.0:
        raise ValueError("injury_penalty cannot be negative")
    score = (
        PREPARATION_WEIGHT * _normalized("preparation", preparation)
        + SURPRISE_WEIGHT * _normalized("surprise", surprise)
        + DEXTERITY_WEIGHT * _normalized("dexterity", dexterity)
        + PERCEPTION_WEIGHT * _normalized("perception", perception)
        + RELEVANT_SKILL_WEIGHT * _normalized("relevant_skill", relevant_skill)
        + STAMINA_WEIGHT * _normalized("current_stamina", current_stamina)
        + TERRAIN_WEIGHT * _normalized("terrain_advantage", terrain_advantage)
        + SEEDED_RANDOM_WEIGHT * _normalized("seeded_randomness", seeded_randomness)
        - float(injury_penalty)
    )
    return score


def _normalized(name: str, value: float) -> float:
    normalized = float(value)
    if not 0.0 <= normalized <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


__all__ = [
    "CAUSAL_URGENCY_WEIGHT",
    "DEXTERITY_WEIGHT",
    "GOAL_RELEVANCE_WEIGHT",
    "IMMEDIATE_DANGER_WEIGHT",
    "NARRATIVE_SALIENCE_WEIGHT",
    "PERCEPTION_WEIGHT",
    "PREPARATION_WEIGHT",
    "RELEVANT_SKILL_WEIGHT",
    "SCHEDULED_COMMITMENT_WEIGHT",
    "SEEDED_RANDOM_WEIGHT",
    "STAMINA_WEIGHT",
    "STARVATION_FAIRNESS_WEIGHT",
    "SURPRISE_WEIGHT",
    "TERRAIN_WEIGHT",
    "UNRESOLVED_DEPENDENCY_WEIGHT",
    "score_initiative",
    "score_priority",
]
