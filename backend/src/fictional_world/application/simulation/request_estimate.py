"""Estimate mandatory remote model requests before a phase (S2-SIM-001)."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import Field

from fictional_world.application.simulation.activation import (
    ActivationDecision,
    ActivationResult,
)
from fictional_world.domain.common.base import StrictContract


class PhaseRequestEstimate(StrictContract):
    """Upper-bound request budget needed to finish a phase safely."""

    character_decision_requests: int = Field(ge=0)
    director_requests: int = Field(ge=0)
    resolver_requests: int = Field(ge=0)
    optional_narration_requests: int = Field(default=0, ge=0)
    optional_embedding_requests: int = Field(default=0, ge=0)
    total_mandatory: int = Field(ge=0)
    total_with_optional: int = Field(ge=0)


def estimate_phase_model_requests(
    activations: Sequence[ActivationResult],
    *,
    director_call_planned: bool = False,
    ambiguous_scene_count: int = 0,
    include_optional_narration: bool = False,
    include_optional_embeddings: bool = False,
    eligible_character_count: int | None = None,
) -> PhaseRequestEstimate:
    """Estimate max remote calls required before advancing the clock.

    Characters decided as SLEEP / CONTINUE_ACTIVITY / SKIP do not consume a
    character-decision request. Optional narration/embeddings are tracked
    separately and never block starting a phase.
    """

    if ambiguous_scene_count < 0:
        raise ValueError("ambiguous_scene_count must be >= 0")

    decisions = sum(1 for item in activations if item.decision is ActivationDecision.FULL_DECISION)
    if eligible_character_count is not None:
        decisions = max(decisions, eligible_character_count)

    director = 1 if director_call_planned else 0
    resolver = max(0, ambiguous_scene_count)
    narration = decisions if include_optional_narration else 0
    embeddings = 1 if include_optional_embeddings else 0
    mandatory = decisions + director + resolver
    return PhaseRequestEstimate(
        character_decision_requests=decisions,
        director_requests=director,
        resolver_requests=resolver,
        optional_narration_requests=narration,
        optional_embedding_requests=embeddings,
        total_mandatory=mandatory,
        total_with_optional=mandatory + narration + embeddings,
    )


__all__ = [
    "PhaseRequestEstimate",
    "estimate_phase_model_requests",
]
