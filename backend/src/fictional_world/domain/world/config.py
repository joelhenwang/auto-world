"""Configurable Stage 3 world-slot and background-simulation defaults."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

DEFAULT_PLOT_ARMOUR_BIAS: Decimal = Decimal("0")
MAX_ACTIVE_MAJOR_ARCS: int = 1
MAX_ACTIVE_SECONDARY_HOOKS: int = 2


@dataclass(frozen=True, slots=True)
class WorldSlotConfig:
    """Active arc / hook slot budgets (handbook ``09`` §4.3 / Stage 3)."""

    max_active_major_arcs: int = MAX_ACTIVE_MAJOR_ARCS
    max_active_secondary_hooks: int = MAX_ACTIVE_SECONDARY_HOOKS


@dataclass(frozen=True, slots=True)
class FactionDailyConfig:
    """Low-resolution daily faction aggregate update defaults."""

    # Clamp indicator values after applying deltas.
    indicator_min: Decimal = Decimal("-1")
    indicator_max: Decimal = Decimal("1")
    # Resource numeric values are not hard-clamped unless configured.
    resource_min: Decimal = Decimal("0")
