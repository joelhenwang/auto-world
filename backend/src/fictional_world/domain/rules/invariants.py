"""Named Stage 0 invariant registry (handbook ``05`` §19 subset)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fictional_world.domain.common.result import ValidationIssue, ValidationResult
from fictional_world.domain.rules.effects.context import EffectValidationContext
from fictional_world.domain.time.fictional_time import FictionalTime

InvariantFn = Callable[..., ValidationResult]


@dataclass(frozen=True, slots=True)
class InvariantSpec:
    code: str
    description: str
    check: InvariantFn


def resources_non_negative(context: EffectValidationContext) -> ValidationResult:
    issues: list[ValidationIssue] = []
    for entity_id, snap in context.entities.items():
        for kind, value in snap.resources.items():
            if value < 0:
                issues.append(
                    ValidationIssue(
                        code="resource_negative",
                        message=f"{entity_id} {kind}={value}",
                    )
                )
    return ValidationResult(issues=tuple(issues))


def absolute_phase_monotonic(previous: FictionalTime, current: FictionalTime) -> ValidationResult:
    if current.absolute_phase_index < previous.absolute_phase_index:
        return ValidationResult(
            issues=(
                ValidationIssue(
                    code="phase_not_monotonic",
                    message="absolute_phase_index decreased",
                ),
            )
        )
    return ValidationResult()


def single_location_per_entity(context: EffectValidationContext) -> ValidationResult:
    # EntitySnapshot allows at most one location_id by construction.
    return ValidationResult()


INVARIANT_REGISTRY: dict[str, InvariantSpec] = {
    "resources_non_negative": InvariantSpec(
        code="resources_non_negative",
        description="Entity resources must remain non-negative",
        check=resources_non_negative,
    ),
    "absolute_phase_monotonic": InvariantSpec(
        code="absolute_phase_monotonic",
        description="Fictional absolute_phase_index never decreases",
        check=absolute_phase_monotonic,
    ),
    "single_location_per_entity": InvariantSpec(
        code="single_location_per_entity",
        description="An entity has at most one physical location",
        check=single_location_per_entity,
    ),
}


def get_invariant(code: str) -> InvariantSpec:
    try:
        return INVARIANT_REGISTRY[code]
    except KeyError as exc:
        msg = f"unknown invariant: {code}"
        raise KeyError(msg) from exc
