"""Injuries, recovery, and death gates (S3-RULES-003 / handbook ``10`` §8-12).

No HP abstraction: harm is injury/condition/life-status based.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.common.result import ValidationIssue, ValidationResult
from fictional_world.domain.rules.scale import STAT_MAX, STAT_MIN, clamp_unit, clamp_world_scale


class LifeStatus(StrEnum):
    HEALTHY = "healthy"
    IMPAIRED = "impaired"
    CRITICAL = "critical"
    UNCONSCIOUS = "unconscious"
    DYING = "dying"
    DEAD = "dead"


class BodyRegion(StrEnum):
    HEAD = "head"
    NECK = "neck"
    TORSO = "torso"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_HAND = "left_hand"
    RIGHT_HAND = "right_hand"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    INTERNAL = "internal"
    GENERAL = "general"


class InjuryType(StrEnum):
    BLUNT_TRAUMA = "blunt_trauma"
    CUT = "cut"
    PUNCTURE = "puncture"
    BURN = "burn"
    FRACTURE = "fracture"
    SPRAIN = "sprain"
    DISLOCATION = "dislocation"
    CRUSH = "crush"
    INTERNAL_TRAUMA = "internal_trauma"
    MAGICAL_DAMAGE = "magical_damage"
    TOXIC = "toxic"
    FROST = "frost"
    OTHER = "other"


class InjuryState(StrictContract):
    injury_id: UUID
    character_id: UUID
    body_region: str = Field(min_length=1, max_length=100)
    injury_type: str = Field(min_length=1, max_length=100)
    severity: float = Field(ge=STAT_MIN, le=STAT_MAX)
    bleeding: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    pain: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    mobility_effect: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    consciousness_risk: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    infection_risk: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    healing_progress: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    treatment_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    permanent_consequence: bool = False
    status: str = Field(default="active", min_length=1, max_length=50)
    idempotency_key: str | None = Field(default=None, max_length=200)
    version: int = Field(default=0, ge=0)


class InjuryApplication(StrictContract):
    character_id: UUID
    body_region: str = Field(min_length=1, max_length=100)
    injury_type: str = Field(min_length=1, max_length=100)
    severity: float = Field(ge=STAT_MIN, le=STAT_MAX)
    bleeding: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    pain: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    mobility_effect: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    consciousness_risk: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    infection_risk: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    injury_id: UUID | None = None
    idempotency_key: str | None = Field(default=None, max_length=200)


class RecoveryStep(StrictContract):
    rest_quality: float = Field(default=0.5, ge=0.0, le=1.0)
    treatment_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    healer_skill: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    phases_elapsed: int = Field(default=1, ge=1, le=240)
    continued_exertion: float = Field(default=0.0, ge=0.0, le=1.0)
    magical_aid: float = Field(default=0.0, ge=0.0, le=1.0)


class DeathValidationContext(StrictContract):
    life_status: LifeStatus
    injuries: tuple[InjuryState, ...] = ()
    lethal_condition_terminal: bool = False
    catastrophic_injury_criteria_met: bool = False
    resolver_lethal_envelope: bool = False
    deity_override: bool = False
    high_impact_authorized: bool = False
    schema_role: str = Field(default="resolver", min_length=1, max_length=100)


class ReturnFromDeathContext(StrictContract):
    life_status: LifeStatus
    mechanism: str = Field(min_length=1, max_length=200)
    lore_rule_id: str = Field(min_length=1, max_length=200)
    lore_allows_return: bool = False
    high_impact_authorized: bool = False
    schema_role: str = Field(default="resolver", min_length=1, max_length=100)
    cost_acknowledged: bool = False


_CONVERSATION_SCHEMAS: frozenset[str] = frozenset(
    {
        "resolver_conversation",
        "conversation",
        "ordinary_conversation",
    }
)

# Ordinary healing cannot fully resolve a fracture/critical wound in one rest phase.
_MAX_HEALING_PER_PHASE = 12.0


def apply_injury(
    application: InjuryApplication,
    *,
    existing: tuple[InjuryState, ...] = (),
) -> InjuryState:
    """Create or return an existing injury idempotently by injury_id / idempotency_key."""

    if application.idempotency_key:
        for injury in existing:
            if injury.idempotency_key == application.idempotency_key:
                return injury
    if application.injury_id is not None:
        for injury in existing:
            if injury.injury_id == application.injury_id:
                return injury

    injury_id = application.injury_id or uuid4()
    # Guard against duplicate id colliding with different payload.
    for injury in existing:
        if injury.injury_id == injury_id:
            return injury

    return InjuryState(
        injury_id=injury_id,
        character_id=application.character_id,
        body_region=application.body_region,
        injury_type=application.injury_type,
        severity=clamp_world_scale(application.severity),
        bleeding=clamp_world_scale(application.bleeding),
        pain=clamp_world_scale(application.pain),
        mobility_effect=clamp_world_scale(application.mobility_effect),
        consciousness_risk=clamp_world_scale(application.consciousness_risk),
        infection_risk=clamp_world_scale(application.infection_risk),
        healing_progress=0.0,
        idempotency_key=application.idempotency_key,
        status="active",
        version=0,
    )


def progress_recovery(injury: InjuryState, step: RecoveryStep) -> InjuryState:
    """Advance healing deterministically; never instant full recovery for serious wounds."""

    if injury.status in {"healed", "resolved"}:
        return injury
    if injury.healing_progress >= STAT_MAX:
        return injury.model_copy(update={"status": "healed"})

    severity_factor = 1.0 / (1.0 + injury.severity / 40.0)
    treatment = max(clamp_unit(injury.treatment_quality), clamp_unit(step.treatment_quality))
    rest = clamp_unit(step.rest_quality)
    healer = clamp_unit(step.healer_skill / STAT_MAX)
    magic = clamp_unit(step.magical_aid)
    exertion_penalty = clamp_unit(step.continued_exertion)

    per_phase = (
        (2.0 + 6.0 * rest + 5.0 * treatment + 4.0 * healer + 3.0 * magic)
        * severity_factor
        * (1.0 - 0.7 * exertion_penalty)
    )
    # Hard cap prevents narrating a fracture away in one ordinary rest phase.
    per_phase = min(per_phase, _MAX_HEALING_PER_PHASE)
    if injury.severity >= 60.0 and step.phases_elapsed <= 1 and treatment < 0.8:
        per_phase = min(per_phase, 6.0)

    gain = per_phase * float(step.phases_elapsed)
    # Serious injuries require multiple phases even with strong treatment.
    if injury.severity >= 36.0:
        max_total_from_this_step = STAT_MAX * 0.45 * float(step.phases_elapsed) / 3.0
        gain = min(gain, max_total_from_this_step)

    new_progress = clamp_world_scale(injury.healing_progress + max(0.0, gain))
    new_bleeding = clamp_world_scale(
        injury.bleeding * (1.0 - 0.15 * treatment * float(step.phases_elapsed))
    )
    new_pain = clamp_world_scale(injury.pain * (1.0 - 0.08 * rest * float(step.phases_elapsed)))
    status = injury.status
    if new_progress >= STAT_MAX:
        status = "healed"
        new_progress = STAT_MAX

    return injury.model_copy(
        update={
            "healing_progress": new_progress,
            "bleeding": new_bleeding,
            "pain": new_pain,
            "treatment_quality": treatment,
            "status": status,
            "version": injury.version + 1,
        }
    )


def injury_action_penalty(injuries: tuple[InjuryState, ...] | list[InjuryState]) -> float:
    """Aggregate functional penalty in ``0..1`` from active injuries (no HP)."""

    active = [i for i in injuries if i.status == "active"]
    if not active:
        return 0.0
    severity = sum(i.severity for i in active) / STAT_MAX
    mobility = sum(i.mobility_effect for i in active) / STAT_MAX
    pain = sum(i.pain for i in active) / STAT_MAX
    raw = 0.5 * severity + 0.3 * mobility + 0.2 * pain
    return clamp_unit(raw / max(1.0, len(active) * 0.65))


def validate_death_prerequisites(ctx: DeathValidationContext) -> ValidationResult:
    """Death requires lethal criteria and high-impact authorization; never conversation schema."""

    issues: list[ValidationIssue] = []
    if ctx.schema_role in _CONVERSATION_SCHEMAS:
        issues.append(
            ValidationIssue(
                code="death_unavailable_in_conversation",
                message="MARK_DEATH is unavailable in ordinary conversation schema",
                path="schema_role",
            )
        )
    if not ctx.high_impact_authorized and not ctx.deity_override:
        issues.append(
            ValidationIssue(
                code="high_impact_required",
                message="death requires high-impact resolution authorization",
                path="high_impact_authorized",
            )
        )
    if ctx.life_status is LifeStatus.DEAD:
        issues.append(
            ValidationIssue(
                code="already_dead",
                message="entity is already dead",
                path="life_status",
            )
        )

    lethal = (
        ctx.lethal_condition_terminal
        or ctx.catastrophic_injury_criteria_met
        or ctx.resolver_lethal_envelope
        or ctx.deity_override
    )
    if not lethal:
        issues.append(
            ValidationIssue(
                code="lethal_criteria_unmet",
                message=(
                    "death requires terminal condition, catastrophic injury criteria, "
                    "lethal envelope, or deity override"
                ),
                path="lethal_criteria",
            )
        )
    return ValidationResult(issues=tuple(issues))


def validate_return_from_death(ctx: ReturnFromDeathContext) -> ValidationResult:
    """Return-from-death is privileged and lore-constrained; never conversation schema."""

    issues: list[ValidationIssue] = []
    if ctx.schema_role in _CONVERSATION_SCHEMAS:
        issues.append(
            ValidationIssue(
                code="return_unavailable_in_conversation",
                message="RETURN_FROM_DEATH is unavailable in ordinary conversation schema",
                path="schema_role",
            )
        )
    if ctx.life_status is not LifeStatus.DEAD:
        issues.append(
            ValidationIssue(
                code="not_dead",
                message="return-from-death requires life_status=dead",
                path="life_status",
            )
        )
    if not ctx.lore_allows_return:
        issues.append(
            ValidationIssue(
                code="lore_forbids_return",
                message=f"lore rule {ctx.lore_rule_id} does not permit return",
                path="lore_allows_return",
            )
        )
    if not ctx.high_impact_authorized:
        issues.append(
            ValidationIssue(
                code="high_impact_required",
                message="return-from-death requires high-impact authorization",
                path="high_impact_authorized",
            )
        )
    if not ctx.cost_acknowledged:
        issues.append(
            ValidationIssue(
                code="cost_not_acknowledged",
                message="return-from-death cost must be acknowledged",
                path="cost_acknowledged",
            )
        )
    if not ctx.mechanism.strip():
        raise InvalidAction("return-from-death mechanism is required")
    return ValidationResult(issues=tuple(issues))
