"""World domain package — aggregates, slots, and Stage 3 arc/faction helpers."""

from fictional_world.domain.world.arcs import activate_arc, advance_arc_progress, close_arc
from fictional_world.domain.world.config import (
    DEFAULT_PLOT_ARMOUR_BIAS,
    MAX_ACTIVE_MAJOR_ARCS,
    MAX_ACTIVE_SECONDARY_HOOKS,
    FactionDailyConfig,
    WorldSlotConfig,
)
from fictional_world.domain.world.factions import (
    FactionDailyUpdateResult,
    FactionIndicatorDelta,
    apply_faction_daily_update,
    default_plot_armour_bias,
    validate_plot_armour_bias,
    with_default_plot_armour,
)
from fictional_world.domain.world.hooks import activate_hook, close_hook, expire_hook
from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)
from fictional_world.domain.world.settlement import apply_settlement_indicator_update
from fictional_world.domain.world.slots import (
    can_activate_major_arc,
    can_activate_secondary_hook,
    count_active_major_arcs,
    count_active_secondary_hooks,
)
from fictional_world.domain.world.statuses import (
    ACTIVE_HOOK_STATUS,
    ARC_TERMINAL_STATUSES,
    ArcScope,
    ArcStatus,
    HookStatus,
)

__all__ = [
    "ACTIVE_HOOK_STATUS",
    "ARC_TERMINAL_STATUSES",
    "DEFAULT_PLOT_ARMOUR_BIAS",
    "MAX_ACTIVE_MAJOR_ARCS",
    "MAX_ACTIVE_SECONDARY_HOOKS",
    "AggregateVersionRecord",
    "ArcScope",
    "ArcStatus",
    "FactionDailyConfig",
    "FactionDailyUpdateResult",
    "FactionIndicatorDelta",
    "HookStatus",
    "WorldClockRecord",
    "WorldRecord",
    "WorldSlotConfig",
    "activate_arc",
    "activate_hook",
    "advance_arc_progress",
    "apply_faction_daily_update",
    "apply_settlement_indicator_update",
    "can_activate_major_arc",
    "can_activate_secondary_hook",
    "close_arc",
    "close_hook",
    "count_active_major_arcs",
    "count_active_secondary_hooks",
    "default_plot_armour_bias",
    "expire_hook",
    "validate_plot_armour_bias",
    "with_default_plot_armour",
]
