"""Validate Stage 0 effect commands against a minimal context."""

from __future__ import annotations

from fictional_world.domain.common.result import ValidationIssue, ValidationResult
from fictional_world.domain.effects.commands import (
    CreateRecentMemoryEffect,
    EffectBase,
    MoveEntityEffect,
    ObserveEffect,
    RestEffect,
    SpendResourceEffect,
    WaitEffect,
)
from fictional_world.domain.rules.effects.context import EffectValidationContext

_STAGE0_KINDS = frozenset(
    {"wait", "observe", "rest", "move_entity", "spend_resource", "create_recent_memory"}
)


def validate_effect(
    effect: EffectBase,
    *,
    context: EffectValidationContext | None = None,
) -> ValidationResult:
    ctx = context or EffectValidationContext()
    kind = getattr(effect, "kind", None)
    if kind not in _STAGE0_KINDS:
        return ValidationResult(
            issues=(
                ValidationIssue(
                    code="unsupported_effect_kind",
                    message=f"effect kind {kind!r} is not enabled for Stage 0 validators",
                    path="kind",
                ),
            )
        )
    if isinstance(effect, WaitEffect):
        return _validate_wait(effect, ctx)
    if isinstance(effect, ObserveEffect):
        return _validate_observe(effect, ctx)
    if isinstance(effect, RestEffect):
        return _validate_rest(effect, ctx)
    if isinstance(effect, MoveEntityEffect):
        return _validate_move(effect, ctx)
    if isinstance(effect, SpendResourceEffect):
        return _validate_spend(effect, ctx)
    if isinstance(effect, CreateRecentMemoryEffect):
        return _validate_memory(effect, ctx)
    return ValidationResult(
        issues=(ValidationIssue(code="unknown_effect", message="unhandled effect type"),)
    )


def validate_effects(
    effects: tuple[EffectBase, ...],
    *,
    context: EffectValidationContext | None = None,
) -> ValidationResult:
    issues: list[ValidationIssue] = []
    for effect in effects:
        issues.extend(validate_effect(effect, context=context).issues)
    return ValidationResult(issues=tuple(issues))


def _entity_known(ctx: EffectValidationContext, entity_id: object) -> bool:
    return entity_id in ctx.entities or entity_id in ctx.known_character_ids


def _validate_wait(effect: WaitEffect, ctx: EffectValidationContext) -> ValidationResult:
    if (
        ctx.entities
        and effect.entity_id not in ctx.entities
        and not _entity_known(ctx, effect.entity_id)
    ):
        return ValidationResult(
            issues=(
                ValidationIssue(
                    code="unknown_entity",
                    message="wait entity is unknown",
                    path="entity_id",
                ),
            )
        )
    snap = ctx.entities.get(effect.entity_id)
    if snap is not None and not snap.alive:
        return ValidationResult(
            issues=(ValidationIssue(code="entity_dead", message="dead entity cannot wait"),)
        )
    return ValidationResult()


def _validate_observe(effect: ObserveEffect, ctx: EffectValidationContext) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if (
        ctx.known_character_ids
        and effect.observer_id not in ctx.known_character_ids
        and effect.observer_id not in ctx.entities
    ):
        issues.append(
            ValidationIssue(
                code="unknown_observer", message="observer unknown", path="observer_id"
            )
        )
    for target in effect.target_entity_ids:
        if ctx.entities and target not in ctx.entities and target not in ctx.known_character_ids:
            issues.append(
                ValidationIssue(
                    code="unknown_observe_target",
                    message=f"observe target {target} unknown",
                    path="target_entity_ids",
                )
            )
    return ValidationResult(issues=tuple(issues))


def _validate_rest(effect: RestEffect, ctx: EffectValidationContext) -> ValidationResult:
    snap = ctx.entities.get(effect.entity_id)
    if snap is not None and not snap.alive:
        return ValidationResult(
            issues=(ValidationIssue(code="entity_dead", message="dead entity cannot rest"),)
        )
    return ValidationResult()


def _validate_move(effect: MoveEntityEffect, ctx: EffectValidationContext) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if effect.from_location_id == effect.to_location_id:
        issues.append(
            ValidationIssue(
                code="move_same_location",
                message="from_location_id and to_location_id must differ",
            )
        )
    if ctx.known_location_ids:
        if effect.from_location_id not in ctx.known_location_ids:
            issues.append(
                ValidationIssue(code="unknown_from_location", message="from location unknown")
            )
        if effect.to_location_id not in ctx.known_location_ids:
            issues.append(
                ValidationIssue(code="unknown_to_location", message="to location unknown")
            )
    snap = ctx.entities.get(effect.entity_id)
    if snap is not None:
        if not snap.alive:
            issues.append(ValidationIssue(code="entity_dead", message="dead entity cannot move"))
        if snap.location_id is not None and snap.location_id != effect.from_location_id:
            issues.append(
                ValidationIssue(
                    code="move_from_mismatch",
                    message="from_location_id does not match entity location",
                )
            )
    return ValidationResult(issues=tuple(issues))


def _validate_spend(effect: SpendResourceEffect, ctx: EffectValidationContext) -> ValidationResult:
    snap = ctx.entities.get(effect.entity_id)
    if snap is None:
        return ValidationResult()
    available = snap.resources.get(effect.resource, 0.0)
    if effect.amount > available:
        return ValidationResult(
            issues=(
                ValidationIssue(
                    code="insufficient_resource",
                    message=f"need {effect.amount} {effect.resource}, have {available}",
                ),
            )
        )
    return ValidationResult()


def _validate_memory(
    effect: CreateRecentMemoryEffect, ctx: EffectValidationContext
) -> ValidationResult:
    if (
        ctx.known_character_ids
        and effect.owner_character_id not in ctx.known_character_ids
        and effect.owner_character_id not in ctx.entities
    ):
        return ValidationResult(
            issues=(
                ValidationIssue(
                    code="unknown_memory_owner",
                    message="memory owner unknown",
                    path="owner_character_id",
                ),
            )
        )
    if not effect.text.strip():
        return ValidationResult(
            issues=(ValidationIssue(code="empty_memory_text", message="memory text empty"),)
        )
    return ValidationResult()
