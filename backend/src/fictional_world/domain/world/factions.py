"""Faction aggregate daily updates (no per-NPC simulation)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.stage3.persistence import FactionPersistenceRecord
from fictional_world.domain.world.config import (
    DEFAULT_PLOT_ARMOUR_BIAS,
    FactionDailyConfig,
)


def default_plot_armour_bias() -> Decimal:
    """Explicit plot-armour configuration default (handbook: outcome bias ``0``)."""
    return DEFAULT_PLOT_ARMOUR_BIAS


def validate_plot_armour_bias(bias: Decimal) -> Decimal:
    """Reject out-of-range plot armour; never silently clamp toward favouritism."""
    if bias < Decimal("-1") or bias > Decimal("1"):
        raise InvalidAction(f"plot_armour_bias must be in [-1, 1]; got {bias}")
    return bias


def with_default_plot_armour(
    faction: FactionPersistenceRecord,
) -> FactionPersistenceRecord:
    """Ensure plot_armour_bias is set to the explicit default when unset/None-like."""
    bias = validate_plot_armour_bias(faction.plot_armour_bias)
    if bias == faction.plot_armour_bias:
        return faction
    return faction.model_copy(update={"plot_armour_bias": bias, "version": faction.version + 1})


class FactionIndicatorDelta(StrictContract):
    indicator_key: str
    previous: Decimal
    delta: Decimal
    next_value: Decimal


@dataclass(frozen=True, slots=True)
class FactionDailyUpdateResult:
    """Result of a deterministic faction daily aggregate update.

    ``promote_causal_event`` is True when background deltas affect focus characters.
    Promotion is a flag only — callers enqueue Director/resolver work; this helper
    never mutates character private state.
    """

    faction: FactionPersistenceRecord
    day_index: int
    indicator_deltas: tuple[FactionIndicatorDelta, ...]
    resource_deltas: dict[str, Decimal]
    promote_causal_event: bool
    affected_focus_character_ids: tuple[UUID, ...]
    notes: str | None = None


def apply_faction_daily_update(
    faction: FactionPersistenceRecord,
    *,
    day_index: int,
    indicator_deltas: Mapping[str, Decimal] | None = None,
    resource_deltas: Mapping[str, Decimal] | None = None,
    previous_indicators: Mapping[str, Decimal] | None = None,
    focus_character_ids: Sequence[UUID] = (),
    membership_character_ids: Sequence[UUID] = (),
    plan_progress_delta: Decimal | None = None,
    config: FactionDailyConfig | None = None,
    notes: str | None = None,
) -> FactionDailyUpdateResult:
    """Apply low-resolution daily faction aggregate changes.

    Produces indicator deltas and optionally flags causal-event promotion when
    focus characters are among faction members affected by the update.
    Does not simulate individual NPCs or write character private memory/intent.
    """
    if day_index < 0:
        raise InvalidAction("day_index must be >= 0")
    if faction.status != "active":
        raise InvalidAction(f"cannot apply daily update to faction status {faction.status!r}")
    cfg = config or FactionDailyConfig()
    bias = validate_plot_armour_bias(faction.plot_armour_bias)

    prev = {str(k): Decimal(str(v)) for k, v in dict(previous_indicators or {}).items()}
    # Seed previous from goals/resources markers when explicit history absent.
    if not prev:
        prev = _indicators_from_goals(faction.goals)

    applied: list[FactionIndicatorDelta] = []
    next_indicators = dict(prev)
    for key, delta in dict(indicator_deltas or {}).items():
        d = Decimal(str(delta))
        before = next_indicators.get(key, Decimal("0"))
        after = _clamp(before + d, cfg.indicator_min, cfg.indicator_max)
        next_indicators[key] = after
        applied.append(
            FactionIndicatorDelta(
                indicator_key=key,
                previous=before,
                delta=after - before,
                next_value=after,
            )
        )

    resources = _as_decimal_map(faction.resources)
    applied_resources: dict[str, Decimal] = {}
    for key, delta in dict(resource_deltas or {}).items():
        d = Decimal(str(delta))
        before = resources.get(key, Decimal("0"))
        after = max(cfg.resource_min, before + d)
        resources[key] = after
        applied_resources[key] = after - before

    plans = dict(faction.plans)
    if plan_progress_delta is not None:
        progress = Decimal(str(plans.get("progress", "0")))
        plans["progress"] = str(
            _clamp(progress + Decimal(str(plan_progress_delta)), Decimal("0"), Decimal("1"))
        )

    goals = dict(faction.goals)
    goals["indicators"] = {k: str(v) for k, v in next_indicators.items()}

    updated = faction.model_copy(
        update={
            "resources": {k: _jsonable(v) for k, v in resources.items()},
            "goals": goals,
            "plans": plans,
            "plot_armour_bias": bias,
            "version": faction.version + 1,
        }
    )

    focus_set = frozenset(focus_character_ids)
    member_set = frozenset(membership_character_ids)
    affected = tuple(sorted(focus_set & member_set, key=str))
    has_material_change = (
        bool(applied) or bool(applied_resources) or plan_progress_delta is not None
    )
    promote = has_material_change and bool(affected)

    return FactionDailyUpdateResult(
        faction=updated,
        day_index=day_index,
        indicator_deltas=tuple(applied),
        resource_deltas=applied_resources,
        promote_causal_event=promote,
        affected_focus_character_ids=affected,
        notes=notes,
    )


def _clamp(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    return max(lo, min(hi, value))


def _indicators_from_goals(goals: Mapping[str, Any]) -> dict[str, Decimal]:
    raw = goals.get("indicators")
    if not isinstance(raw, dict):
        return {}
    typed = cast(dict[str, object], raw)
    seeded: dict[str, Decimal] = {}
    for key, value in typed.items():
        if isinstance(value, (int, float, str, Decimal)):
            seeded[str(key)] = Decimal(str(value))
    return seeded


def _as_decimal_map(raw: Mapping[str, Any] | dict[str, Any]) -> dict[str, Decimal]:
    out: dict[str, Decimal] = {}
    for key, value in dict(raw).items():
        if isinstance(value, (int, float, str, Decimal)):
            out[str(key)] = Decimal(str(value))
    return out


def _jsonable(value: Decimal) -> str:
    return str(value)
