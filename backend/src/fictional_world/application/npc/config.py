"""Configurable NPC registry budgets and TTL defaults (handbook 09 §15.5-15.6)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NpcBudgetConfig:
    """Stage 2 defaults from handbook 09 §15.5 / 27 S2-WORLD-002."""

    max_detailed_per_scene: int = 6
    max_active_in_region: int = 24
    max_new_named_per_day: int = 3


@dataclass(frozen=True, slots=True)
class NpcTtlConfig:
    """TTL defaults for temporary named NPCs (phases; ~10 phases/day)."""

    default_ttl_phases: int = 20
    meaningful_scene_extension_phases: int = 10
