"""Bounded agent graphs (Stage 1+; protocols may appear earlier).

Stage 2 adds Director / MemoryConsolidation / NPCScene thin wrappers plus
task-role restricted effect schemas. All graphs return proposals or derived
records only — none commit canonical domain state.
"""

from fictional_world.agents.restricted_effects import (
    STAGE1_RESOLVER_EFFECT_KINDS,
    GraphTaskRole,
    assert_no_unrelated_effects,
    effect_kind_allowed,
    restricted_effect_kinds,
    restricted_effect_schema,
)

__all__ = [
    "STAGE1_RESOLVER_EFFECT_KINDS",
    "GraphTaskRole",
    "assert_no_unrelated_effects",
    "effect_kind_allowed",
    "restricted_effect_kinds",
    "restricted_effect_schema",
]
