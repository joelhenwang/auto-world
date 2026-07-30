"""Resonance magic spell resolution (S3-RULES-002 / handbook ``10`` §6)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import ResolutionLevel
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.common.result import ValidationIssue, ValidationResult
from fictional_world.domain.rules.scale import STAT_MAX, STAT_MIN, clamp_unit, clamp_world_scale
from fictional_world.domain.rules.seeded import SeededRng


class CastTimeClass(StrEnum):
    INSTANT = "instant"
    SWIFT = "swift"
    STANDARD = "standard"
    RITUAL = "ritual"


class SpellOutcomeClass(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    INTERRUPTED = "interrupted"
    INVALID = "invalid"


class SpellTargetRules(StrictContract):
    max_targets: int = Field(default=1, ge=1, le=20)
    requires_line_of_sight: bool = True
    allows_self: bool = True
    allows_hostile: bool = True
    allows_ally: bool = True
    max_range_units: float = Field(default=1.0, ge=0.0)


class SpellPrerequisites(StrictContract):
    required_schools: tuple[str, ...] = ()
    required_elements: tuple[str, ...] = ()
    minimum_mana_control: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    minimum_magic_sensitivity: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    material_tags: tuple[str, ...] = ()
    known_spell_required: bool = True


class SpellDefinition(StrictContract):
    """Registered spell definition; unknown spells cannot be cast."""

    spell_id: UUID
    spell_code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    school: str = Field(min_length=1, max_length=100)
    elements: tuple[str, ...] = ()
    minimum_proficiency: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    mana_cost_min: float = Field(ge=0.0, le=STAT_MAX)
    mana_cost_max: float = Field(ge=0.0, le=STAT_MAX)
    cast_time_class: CastTimeClass = CastTimeClass.STANDARD
    cast_time_beats: int = Field(default=1, ge=0, le=100)
    range_class: str = Field(default="touch", min_length=1, max_length=50)
    target_rules: SpellTargetRules = Field(default_factory=SpellTargetRules)
    prerequisites: SpellPrerequisites = Field(default_factory=SpellPrerequisites)
    failure_modes: tuple[str, ...] = ("fizzle", "backlash")
    counters: tuple[str, ...] = ()
    visibility: str = Field(default="public", min_length=1, max_length=50)
    world_rule_version: str = Field(default="stage3-v1", min_length=1, max_length=100)


class MagicState(StrictContract):
    character_id: UUID
    mana_current: float = Field(ge=STAT_MIN, le=STAT_MAX)
    mana_capacity: float = Field(ge=STAT_MIN, le=STAT_MAX)
    mana_control: float = Field(default=40.0, ge=STAT_MIN, le=STAT_MAX)
    magic_sensitivity: float = Field(default=40.0, ge=STAT_MIN, le=STAT_MAX)
    casting_speed: float = Field(default=40.0, ge=STAT_MIN, le=STAT_MAX)
    spell_stability: float = Field(default=40.0, ge=STAT_MIN, le=STAT_MAX)
    school_affinities: dict[str, float] = Field(default_factory=dict)
    element_affinities: dict[str, float] = Field(default_factory=dict)


class KnownSpell(StrictContract):
    character_id: UUID
    spell_id: UUID
    proficiency: float = Field(ge=STAT_MIN, le=STAT_MAX)
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)


class SpellAttempt(StrictContract):
    caster_id: UUID
    spell_id: UUID
    target_ids: tuple[UUID, ...] = ()
    improvised: bool = False
    interrupted: bool = False
    counter_tags: tuple[str, ...] = ()
    available_material_tags: tuple[str, ...] = ()
    line_of_sight: bool = True
    range_units: float = Field(default=0.0, ge=0.0)
    target_relations: dict[str, str] = Field(default_factory=dict)
    # relation values: self | ally | hostile | other
    concentration_ok: bool = True
    seed: int = 0


class SpellResolution(StrictContract):
    outcome: SpellOutcomeClass
    resolution_level: ResolutionLevel
    mana_spent: float = Field(ge=0.0)
    mana_remaining: float = Field(ge=STAT_MIN, le=STAT_MAX)
    cast_beats_used: int = Field(ge=0)
    failure_mode: str | None = None
    justification: str = Field(min_length=1, max_length=1_000)
    issues: tuple[ValidationIssue, ...] = ()


def validate_spell_prerequisites(
    definition: SpellDefinition,
    magic: MagicState,
    known: KnownSpell | None,
    attempt: SpellAttempt,
) -> ValidationResult:
    """Check prerequisites, registration, and targeting without spending mana."""

    issues: list[ValidationIssue] = []

    if attempt.improvised:
        issues.append(
            ValidationIssue(
                code="improvised_not_enabled",
                message=(
                    "improvisation requires a high-uncertainty envelope "
                    "not enabled for Stage 3 seed spells"
                ),
                path="improvised",
            )
        )
        return ValidationResult(issues=tuple(issues))

    if definition.prerequisites.known_spell_required and known is None:
        issues.append(
            ValidationIssue(
                code="unknown_spell",
                message="spell is not in the caster's known spell registry",
                path="spell_id",
            )
        )
    if known is not None and known.spell_id != definition.spell_id:
        issues.append(
            ValidationIssue(
                code="spell_mismatch",
                message="known spell does not match definition",
                path="spell_id",
            )
        )
    if known is not None and known.proficiency < definition.minimum_proficiency:
        issues.append(
            ValidationIssue(
                code="insufficient_proficiency",
                message=(
                    f"proficiency {known.proficiency} below minimum "
                    f"{definition.minimum_proficiency}"
                ),
                path="proficiency",
            )
        )

    prereq = definition.prerequisites
    if magic.mana_control < prereq.minimum_mana_control:
        issues.append(
            ValidationIssue(
                code="mana_control_prerequisite",
                message="mana control below spell prerequisite",
                path="mana_control",
            )
        )
    if magic.magic_sensitivity < prereq.minimum_magic_sensitivity:
        issues.append(
            ValidationIssue(
                code="sensitivity_prerequisite",
                message="magic sensitivity below spell prerequisite",
                path="magic_sensitivity",
            )
        )
    for school in prereq.required_schools:
        if magic.school_affinities.get(school, 0.0) <= 0.0:
            issues.append(
                ValidationIssue(
                    code="school_prerequisite",
                    message=f"missing school affinity {school}",
                    path="school_affinities",
                )
            )
    for element in prereq.required_elements:
        if magic.element_affinities.get(element, 0.0) <= 0.0:
            issues.append(
                ValidationIssue(
                    code="element_prerequisite",
                    message=f"missing element affinity {element}",
                    path="element_affinities",
                )
            )
    missing_materials = [
        tag for tag in prereq.material_tags if tag not in attempt.available_material_tags
    ]
    if missing_materials:
        issues.append(
            ValidationIssue(
                code="material_prerequisite",
                message=f"missing materials: {', '.join(missing_materials)}",
                path="material_tags",
            )
        )

    issues.extend(_target_issues(definition, attempt))
    return ValidationResult(issues=tuple(issues))


def resolve_spell_attempt(
    *,
    definition: SpellDefinition | None,
    magic: MagicState,
    known: KnownSpell | None,
    attempt: SpellAttempt,
    registered_spell_ids: frozenset[UUID] | set[UUID],
) -> SpellResolution:
    """Resolve a cast attempt inside the feasible mana/prerequisite envelope.

    Cannot invent unknown spells or spend more mana than available (no infinite mana).
    """

    if definition is None or definition.spell_id not in registered_spell_ids:
        return SpellResolution(
            outcome=SpellOutcomeClass.INVALID,
            resolution_level=ResolutionLevel.INVALIDATED,
            mana_spent=0.0,
            mana_remaining=magic.mana_current,
            cast_beats_used=0,
            failure_mode="unknown_spell",
            justification="spell is not registered in the world spell registry",
            issues=(
                ValidationIssue(
                    code="unregistered_spell",
                    message="only registered spell definitions may be cast",
                    path="spell_id",
                ),
            ),
        )

    if definition.mana_cost_min > definition.mana_cost_max:
        raise InvalidAction("spell mana_cost_min exceeds mana_cost_max")

    prereq_result = validate_spell_prerequisites(definition, magic, known, attempt)
    if not prereq_result.ok:
        return SpellResolution(
            outcome=SpellOutcomeClass.INVALID,
            resolution_level=ResolutionLevel.INVALIDATED,
            mana_spent=0.0,
            mana_remaining=magic.mana_current,
            cast_beats_used=0,
            failure_mode="prerequisite_failed",
            justification="spell prerequisites or targeting failed validation",
            issues=prereq_result.issues,
        )

    if attempt.interrupted:
        # Partial cast cost for non-instant spells; instant fizzles free if interrupted.
        partial_cost = 0.0
        if definition.cast_time_class is not CastTimeClass.INSTANT:
            partial_cost = min(
                magic.mana_current,
                definition.mana_cost_min * 0.25,
            )
        return SpellResolution(
            outcome=SpellOutcomeClass.INTERRUPTED,
            resolution_level=ResolutionLevel.INTERRUPTED,
            mana_spent=partial_cost,
            mana_remaining=clamp_world_scale(magic.mana_current - partial_cost),
            cast_beats_used=max(0, definition.cast_time_beats // 2),
            failure_mode="interrupted",
            justification="cast interrupted before completion",
        )

    rng = SeededRng(seed=attempt.seed, salt=f"spell:{definition.spell_id}")
    cost = _select_mana_cost(definition, magic, known, rng)
    if cost > magic.mana_current:
        return SpellResolution(
            outcome=SpellOutcomeClass.FAILURE,
            resolution_level=ResolutionLevel.FAILURE,
            mana_spent=0.0,
            mana_remaining=magic.mana_current,
            cast_beats_used=0,
            failure_mode="insufficient_mana",
            justification="mana cost exceeds available mana; overdraw is not permitted",
        )

    # Counters present in attempt that match definition counters force failure/partial.
    matched_counters = [c for c in attempt.counter_tags if c in definition.counters]
    if matched_counters:
        return SpellResolution(
            outcome=SpellOutcomeClass.FAILURE,
            resolution_level=ResolutionLevel.FAILURE,
            mana_spent=cost,
            mana_remaining=clamp_world_scale(magic.mana_current - cost),
            cast_beats_used=definition.cast_time_beats,
            failure_mode=f"countered:{matched_counters[0]}",
            justification=f"spell countered by {matched_counters[0]}",
        )

    reliability = known.reliability if known is not None else 0.35
    stability = clamp_unit(magic.spell_stability / STAT_MAX)
    roll = rng.unit()
    # Higher reliability/stability widens the success band (roll in [0, p_success)).
    p_success = clamp_unit(0.20 + 0.55 * reliability + 0.20 * stability)
    p_partial = clamp_unit(min(0.95, p_success + 0.20))

    if roll < p_success:
        return SpellResolution(
            outcome=SpellOutcomeClass.SUCCESS,
            resolution_level=ResolutionLevel.SUCCESS,
            mana_spent=cost,
            mana_remaining=clamp_world_scale(magic.mana_current - cost),
            cast_beats_used=definition.cast_time_beats,
            justification="spell resolved successfully within registered envelope",
        )
    if roll < p_partial:
        partial_cost = min(cost, max(definition.mana_cost_min, cost * 0.75))
        return SpellResolution(
            outcome=SpellOutcomeClass.PARTIAL,
            resolution_level=ResolutionLevel.PARTIAL_SUCCESS,
            mana_spent=partial_cost,
            mana_remaining=clamp_world_scale(magic.mana_current - partial_cost),
            cast_beats_used=definition.cast_time_beats,
            failure_mode=definition.failure_modes[0] if definition.failure_modes else "partial",
            justification="spell partially manifested with reduced effect",
        )

    fail_mode = definition.failure_modes[0] if definition.failure_modes else "fizzle"
    # Failed casts still spend a fraction of the cost (never more than available).
    spent = min(magic.mana_current, cost * 0.5)
    return SpellResolution(
        outcome=SpellOutcomeClass.FAILURE,
        resolution_level=ResolutionLevel.FAILURE,
        mana_spent=spent,
        mana_remaining=clamp_world_scale(magic.mana_current - spent),
        cast_beats_used=definition.cast_time_beats,
        failure_mode=fail_mode,
        justification=f"spell failed ({fail_mode})",
    )


def _select_mana_cost(
    definition: SpellDefinition,
    magic: MagicState,
    known: KnownSpell | None,
    rng: SeededRng,
) -> float:
    """Pick a cost inside the spell's declared range; never invent infinite mana."""

    low = definition.mana_cost_min
    high = definition.mana_cost_max
    proficiency = known.proficiency if known is not None else 0.0
    # Higher control/proficiency biases toward the low end of the cost range.
    bias = clamp_unit((magic.mana_control + proficiency) / (2.0 * STAT_MAX))
    base = low + (high - low) * (1.0 - 0.7 * bias)
    jitter = rng.uniform(-0.05, 0.05) * (high - low + 1.0)
    return clamp_world_scale(base + jitter, minimum=low, maximum=high)


def _target_issues(definition: SpellDefinition, attempt: SpellAttempt) -> list[ValidationIssue]:
    rules = definition.target_rules
    issues: list[ValidationIssue] = []
    if len(attempt.target_ids) > rules.max_targets:
        issues.append(
            ValidationIssue(
                code="too_many_targets",
                message=f"at most {rules.max_targets} targets allowed",
                path="target_ids",
            )
        )
    if rules.requires_line_of_sight and not attempt.line_of_sight and attempt.target_ids:
        issues.append(
            ValidationIssue(
                code="no_line_of_sight",
                message="line of sight required",
                path="line_of_sight",
            )
        )
    if attempt.range_units > rules.max_range_units:
        issues.append(
            ValidationIssue(
                code="out_of_range",
                message="target beyond spell range",
                path="range_units",
            )
        )
    if not attempt.concentration_ok:
        issues.append(
            ValidationIssue(
                code="concentration_broken",
                message="caster concentration requirements not met",
                path="concentration_ok",
            )
        )
    for target_id in attempt.target_ids:
        relation = attempt.target_relations.get(str(target_id), "other")
        if relation == "self" and not rules.allows_self:
            issues.append(
                ValidationIssue(
                    code="self_not_allowed",
                    message="spell cannot target self",
                    path="target_relations",
                )
            )
        if relation == "hostile" and not rules.allows_hostile:
            issues.append(
                ValidationIssue(
                    code="hostile_not_allowed",
                    message="spell cannot target hostiles",
                    path="target_relations",
                )
            )
        if relation == "ally" and not rules.allows_ally:
            issues.append(
                ValidationIssue(
                    code="ally_not_allowed",
                    message="spell cannot target allies",
                    path="target_relations",
                )
            )
    return issues
