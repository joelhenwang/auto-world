"""Stats, temporary modifiers, and derived capabilities (S3-RULES-001 / handbook ``10`` §2-3)."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.rules.scale import STAT_MAX, STAT_MIN, clamp_unit, clamp_world_scale
from fictional_world.domain.rules.seeded import seeded_unit_float


class StatType(StrEnum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    STAMINA = "stamina"
    INTELLIGENCE = "intelligence"
    PERCEPTION = "perception"
    CHARISMA = "charisma"


class CapabilityKind(StrEnum):
    INITIATIVE = "initiative"
    PHYSICAL_POWER = "physical_power"
    EVASION = "evasion"
    SOCIAL_PRESSURE = "social_pressure"
    ANALYSIS = "analysis"


class TemporaryModifier(StrictContract):
    """Temporary stat modifier; never mutates ``base_value``."""

    source_effect_id: UUID | None = None
    stat_type: StatType
    delta: float = 0.0
    multiplier: float = Field(default=1.0, gt=0)
    stacking_group: str = Field(default="default", min_length=1, max_length=100)
    priority: int = 0
    starts_at_phase: int = Field(default=0, ge=0)
    expires_at_phase: int | None = Field(default=None, ge=0)


class StatState(StrictContract):
    character_id: UUID
    stat_type: StatType
    base_value: float = Field(ge=STAT_MIN, le=STAT_MAX)
    dynamic_potential_cap: float = Field(ge=STAT_MIN, le=STAT_MAX)
    growth_rate: float = Field(ge=0.0, le=1.0)
    adaptability: float = Field(default=0.5, ge=0.0, le=1.0)
    temporary_modifiers: tuple[TemporaryModifier, ...] = ()
    version: int = Field(default=0, ge=0)


class EffectiveStat(StrictContract):
    """Effective (modified) value with unchanged base retained separately."""

    stat_type: StatType
    base_value: float
    effective_value: float
    potential_cap: float
    applied_delta: float
    applied_multiplier: float


class StatEvidence(StrictContract):
    """Evidence toward base-stat growth; does not auto-level."""

    difficulty: float = Field(ge=0.0, le=1.0)
    practice_quality: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(default=0.5, ge=0.0, le=1.0)
    recovery_factor: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_units: float = Field(gt=0.0)


class DerivedCapabilityInputs(StrictContract):
    stats: dict[StatType, float]
    relevant_skill: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    stamina_ratio: float = Field(default=1.0, ge=0.0, le=1.0)
    leverage_context: float = Field(default=50.0, ge=STAT_MIN, le=STAT_MAX)
    movement_skill: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)
    status_context: float = Field(default=50.0, ge=STAT_MIN, le=STAT_MAX)
    relationship_context: float = Field(default=50.0, ge=STAT_MIN, le=STAT_MAX)
    information_quality: float = Field(default=50.0, ge=STAT_MIN, le=STAT_MAX)
    domain_skill: float = Field(default=0.0, ge=STAT_MIN, le=STAT_MAX)


def clamp_stat(value: float, *, potential_cap: float | None = None) -> float:
    """Clamp a stat to ``0..100``, optionally also to a potential cap."""

    capped = clamp_world_scale(value)
    if potential_cap is not None:
        if potential_cap < STAT_MIN or potential_cap > STAT_MAX:
            raise InvalidAction(f"potential_cap out of world scale: {potential_cap}")
        capped = min(capped, potential_cap)
    return capped


def effective_stat(
    state: StatState,
    *,
    at_phase: int = 0,
) -> EffectiveStat:
    """Compute effective value from base + temporary modifiers without mutating base."""

    active = [
        mod
        for mod in state.temporary_modifiers
        if mod.stat_type == state.stat_type
        and mod.starts_at_phase <= at_phase
        and (mod.expires_at_phase is None or at_phase < mod.expires_at_phase)
    ]
    active.sort(key=lambda mod: (mod.priority, mod.stacking_group))

    # Stacking: one additive sum and one product of multipliers per group, then across groups.
    groups: dict[str, list[TemporaryModifier]] = {}
    for mod in active:
        groups.setdefault(mod.stacking_group, []).append(mod)

    total_delta = 0.0
    total_multiplier = 1.0
    for group_mods in groups.values():
        group_delta = sum(mod.delta for mod in group_mods)
        group_multiplier = 1.0
        for mod in group_mods:
            group_multiplier *= mod.multiplier
        total_delta += group_delta
        total_multiplier *= group_multiplier

    raw = (state.base_value + total_delta) * total_multiplier
    # Temporary modifiers may push effective above potential; still clamp to world scale.
    effective = clamp_world_scale(raw)
    return EffectiveStat(
        stat_type=state.stat_type,
        base_value=state.base_value,
        effective_value=effective,
        potential_cap=state.dynamic_potential_cap,
        applied_delta=total_delta,
        applied_multiplier=total_multiplier,
    )


def apply_stat_evidence(
    state: StatState,
    evidence: StatEvidence,
    *,
    seed: int | None = None,
) -> tuple[StatState, float]:
    """Apply evidence-gated growth to base_value; never leaps past potential.

    Returns ``(new_state, applied_delta)``. Temporary modifiers are preserved unchanged.
    """

    if state.base_value > state.dynamic_potential_cap:
        raise InvalidAction("base_value exceeds dynamic_potential_cap without temporary permit")

    headroom = max(0.0, state.dynamic_potential_cap - state.base_value)
    if headroom <= 0.0:
        return state, 0.0

    # Evidence converts slowly; difficulty near current ability yields more growth.
    diminishing = 1.0 / (1.0 + state.base_value / 50.0)
    units = max(0.0, evidence.evidence_units)
    quality = clamp_unit(evidence.practice_quality)
    difficulty = clamp_unit(evidence.difficulty)
    novelty = clamp_unit(evidence.novelty)
    recovery = clamp_unit(evidence.recovery_factor)

    raw_gain = (
        units
        * state.growth_rate
        * state.adaptability
        * quality
        * (0.35 + 0.65 * difficulty)
        * (0.5 + 0.5 * novelty)
        * recovery
        * diminishing
    )
    # Soft cap: ordinary evidence never awards more than a small fraction of remaining headroom.
    max_ordinary = min(2.0, headroom * 0.15)
    if seed is not None:
        jitter = 0.9 + 0.2 * seeded_unit_float(seed, "stat_evidence", state.stat_type.value)
        raw_gain *= jitter
    applied = clamp_world_scale(raw_gain, minimum=0.0, maximum=max_ordinary)
    if applied <= 0.0:
        return state, 0.0

    new_base = clamp_stat(state.base_value + applied, potential_cap=state.dynamic_potential_cap)
    delta = new_base - state.base_value
    return state.model_copy(update={"base_value": new_base, "version": state.version + 1}), delta


def compute_derived_capability(
    kind: CapabilityKind,
    inputs: DerivedCapabilityInputs,
) -> float:
    """Compute a derived capability score (not an automatic outcome)."""

    stats = inputs.stats

    def _req(stat: StatType) -> float:
        if stat not in stats:
            raise InvalidAction(f"missing required stat {stat.value} for {kind.value}")
        return clamp_stat(stats[stat])

    if kind is CapabilityKind.INITIATIVE:
        score = (
            0.40 * _req(StatType.DEXTERITY)
            + 0.35 * _req(StatType.PERCEPTION)
            + 0.15 * inputs.relevant_skill
            + 0.10 * inputs.stamina_ratio * STAT_MAX
        )
    elif kind is CapabilityKind.PHYSICAL_POWER:
        score = (
            0.65 * _req(StatType.STRENGTH)
            + 0.20 * inputs.relevant_skill
            + 0.15 * inputs.leverage_context
        )
    elif kind is CapabilityKind.EVASION:
        score = (
            0.50 * _req(StatType.DEXTERITY)
            + 0.25 * _req(StatType.PERCEPTION)
            + 0.15 * inputs.movement_skill
            + 0.10 * inputs.stamina_ratio * STAT_MAX
        )
    elif kind is CapabilityKind.SOCIAL_PRESSURE:
        score = (
            0.45 * _req(StatType.CHARISMA)
            + 0.25 * inputs.relevant_skill
            + 0.15 * inputs.status_context
            + 0.15 * inputs.relationship_context
        )
    elif kind is CapabilityKind.ANALYSIS:
        score = (
            0.55 * _req(StatType.INTELLIGENCE)
            + 0.25 * inputs.domain_skill
            + 0.20 * inputs.information_quality
        )
    else:
        raise InvalidAction(f"unsupported capability kind: {kind}")

    return clamp_world_scale(score)
