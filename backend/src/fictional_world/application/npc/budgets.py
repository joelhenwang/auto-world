"""Pure NPC budget checks (handbook 09 §15.5)."""

from __future__ import annotations

from fictional_world.application.npc.config import NpcBudgetConfig
from fictional_world.application.npc.types import BudgetSnapshot, BudgetViolation


def check_new_npc_budgets(
    snapshot: BudgetSnapshot,
    *,
    config: NpcBudgetConfig | None = None,
    counts_toward_scene: bool = True,
) -> BudgetViolation | None:
    """Return a violation when registering a *new* detailed NPC would exceed budgets.

    Archived NPCs are assumed already excluded from the snapshot counters.
    """

    cfg = config or NpcBudgetConfig()

    if counts_toward_scene and snapshot.detailed_npcs_in_scene >= cfg.max_detailed_per_scene:
        return BudgetViolation(
            code="scene_detailed_npc_budget",
            message=(
                f"scene already has {snapshot.detailed_npcs_in_scene} detailed NPCs "
                f"(max {cfg.max_detailed_per_scene})"
            ),
        )

    if snapshot.active_detailed_in_region >= cfg.max_active_in_region:
        return BudgetViolation(
            code="region_active_npc_budget",
            message=(
                f"region already has {snapshot.active_detailed_in_region} active detailed NPCs "
                f"(max {cfg.max_active_in_region})"
            ),
        )

    if snapshot.new_named_today >= cfg.max_new_named_per_day:
        return BudgetViolation(
            code="daily_new_named_npc_budget",
            message=(
                f"day already created {snapshot.new_named_today} new named NPCs "
                f"(max {cfg.max_new_named_per_day})"
            ),
        )

    return None


__all__ = ["check_new_npc_budgets"]
