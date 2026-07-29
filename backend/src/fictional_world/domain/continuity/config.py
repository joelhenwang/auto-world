"""Bounded relationship aggregation configuration (Stage 2)."""

from __future__ import annotations

from decimal import Decimal

from fictional_world.domain.common.enums import RelationshipDimension

# Packet example: trust normal-scene cap 0.08 (handbook ordinary was 0.05).
NORMAL_SCENE_MAX_ABS_DELTA: Decimal = Decimal("0.08")

DIMENSION_NORMAL_SCENE_MAX_ABS_DELTA: dict[str, Decimal] = {
    RelationshipDimension.FAMILIARITY.value: Decimal("0.08"),
    RelationshipDimension.TRUST.value: Decimal("0.08"),
    RelationshipDimension.AFFECTION.value: Decimal("0.08"),
    RelationshipDimension.ATTRACTION.value: Decimal("0.08"),
    RelationshipDimension.RESPECT.value: Decimal("0.08"),
    RelationshipDimension.FEAR.value: Decimal("0.08"),
    RelationshipDimension.RESENTMENT.value: Decimal("0.08"),
    RelationshipDimension.DEPENDENCY.value: Decimal("0.08"),
    RelationshipDimension.LOYALTY.value: Decimal("0.08"),
    "perceived_reciprocity": Decimal("0.08"),
}

DIMINISHING_RETURNS_RATE: Decimal = Decimal("0.75")
GENERIC_KINDNESS_TAGS: frozenset[str] = frozenset({"kindness", "generic_kindness"})
EXPLICIT_ATTRACTION_TAGS: frozenset[str] = frozenset(
    {"attraction", "romantic", "romance", "attraction_evidence"}
)
FAMILIARITY_MIN: Decimal = Decimal("0")
FAMILIARITY_MAX: Decimal = Decimal("1")
SIGNED_DIMENSION_MIN: Decimal = Decimal("-1")
SIGNED_DIMENSION_MAX: Decimal = Decimal("1")
GOAL_PRIORITY_MIN: Decimal = Decimal("0")
GOAL_PRIORITY_MAX: Decimal = Decimal("1")
MAX_ACTIVE_GOALS_IN_CONTEXT: int = 3
