"""Directional relationship evidence aggregation (Stage 2)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from fictional_world.domain.common.enums import RelationshipDimension
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.continuity.config import (
    DIMENSION_NORMAL_SCENE_MAX_ABS_DELTA,
    DIMINISHING_RETURNS_RATE,
    EXPLICIT_ATTRACTION_TAGS,
    FAMILIARITY_MAX,
    FAMILIARITY_MIN,
    GENERIC_KINDNESS_TAGS,
    NORMAL_SCENE_MAX_ABS_DELTA,
    SIGNED_DIMENSION_MAX,
    SIGNED_DIMENSION_MIN,
)
from fictional_world.domain.continuity.evidence import RelationshipEvidenceInput
from fictional_world.domain.continuity.persistence import RelationshipEdgePersistenceRecord

_SUPPORTED_DIMENSIONS: frozenset[str] = frozenset(
    {dimension.value for dimension in RelationshipDimension} | {"perceived_reciprocity"}
)

_DIMENSION_FIELDS: frozenset[str] = frozenset(
    {
        "familiarity",
        "trust",
        "affection",
        "attraction",
        "respect",
        "fear",
        "resentment",
        "dependency",
        "loyalty",
        "perceived_reciprocity",
    }
)


def apply_relationship_evidence(
    edge: RelationshipEdgePersistenceRecord,
    evidence: RelationshipEvidenceInput,
    *,
    prior_same_sign_count: int = 0,
    max_abs_delta: Decimal | None = None,
    diminishing_rate: Decimal = DIMINISHING_RETURNS_RATE,
) -> tuple[RelationshipEdgePersistenceRecord, Decimal]:
    """Apply one evidence row to a directional edge.

    Returns ``(new_edge, capped_delta)`` where ``capped_delta`` is the signed
    change actually applied after diminishing returns and normal-scene clamps.
    """
    if edge.source_character_id == edge.target_character_id:
        raise InvalidAction("relationship edge cannot be reflexive")

    dimension = evidence.dimension.strip().lower()
    if dimension not in _SUPPORTED_DIMENSIONS or dimension not in _DIMENSION_FIELDS:
        raise InvalidAction(f"unsupported relationship dimension {evidence.dimension!r}")

    if not evidence.perceived:
        return edge, Decimal("0")

    raw = Decimal(evidence.signed_strength)
    if _blocks_attraction_from_kindness(dimension=dimension, evidence=evidence, raw=raw):
        return edge, Decimal("0")

    scaled = _apply_diminishing_returns(
        raw,
        prior_same_sign_count=prior_same_sign_count,
        diminishing_rate=diminishing_rate,
    )
    cap = max_abs_delta
    if cap is None:
        cap = DIMENSION_NORMAL_SCENE_MAX_ABS_DELTA.get(dimension, NORMAL_SCENE_MAX_ABS_DELTA)
    capped = _clamp_abs(scaled, cap)

    current = Decimal(getattr(edge, dimension))
    proposed = current + capped
    bounded = _clamp_dimension(dimension, proposed)
    applied = bounded - current

    updates: dict[str, Any] = {
        dimension: bounded,
        "version": edge.version + 1,
    }
    if evidence.source_event_id is not None:
        updates["last_source_event_id"] = evidence.source_event_id
    if evidence.phase_index is not None:
        updates["last_meaningful_interaction_phase"] = evidence.phase_index

    return edge.model_copy(update=updates), applied


def empty_relationship_edge(
    *,
    world_id: UUID,
    source_character_id: UUID,
    target_character_id: UUID,
) -> RelationshipEdgePersistenceRecord:
    """Seed-compatible edge with zeroed dimensions (no evidence rows required)."""
    if source_character_id == target_character_id:
        raise InvalidAction("relationship edge cannot be reflexive")
    return RelationshipEdgePersistenceRecord(
        source_character_id=source_character_id,
        target_character_id=target_character_id,
        world_id=world_id,
        version=0,
    )


def _blocks_attraction_from_kindness(
    *,
    dimension: str,
    evidence: RelationshipEvidenceInput,
    raw: Decimal,
) -> bool:
    """Generic kindness must not raise attraction unless explicitly tagged."""
    if dimension != RelationshipDimension.ATTRACTION.value:
        return False
    if raw <= 0:
        return False
    tags = {tag.strip().lower() for tag in evidence.evidence_tags}
    if tags & EXPLICIT_ATTRACTION_TAGS:
        return False
    return bool(tags & GENERIC_KINDNESS_TAGS)


def _apply_diminishing_returns(
    raw: Decimal,
    *,
    prior_same_sign_count: int,
    diminishing_rate: Decimal,
) -> Decimal:
    if raw <= 0 or prior_same_sign_count <= 0:
        return raw
    scale = Decimal("1") / (Decimal("1") + Decimal(prior_same_sign_count) * diminishing_rate)
    return raw * scale


def _clamp_abs(value: Decimal, max_abs: Decimal) -> Decimal:
    if value > max_abs:
        return max_abs
    if value < -max_abs:
        return -max_abs
    return value


def _clamp_dimension(dimension: str, value: Decimal) -> Decimal:
    if dimension == RelationshipDimension.FAMILIARITY.value:
        return min(FAMILIARITY_MAX, max(FAMILIARITY_MIN, value))
    return min(SIGNED_DIMENSION_MAX, max(SIGNED_DIMENSION_MIN, value))
