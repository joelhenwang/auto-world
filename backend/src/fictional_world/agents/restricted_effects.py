"""Task-role restricted effect schemas (S2-GRAPH-001).

Graphs and resolvers must never receive the universal effect-command union.
Each task role exposes only the kinds it is privileged to propose or accept.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fictional_world.domain.effects.commands import EFFECT_COMMAND_TYPES


class GraphTaskRole(StrEnum):
    """Bounded agent / resolver task roles that own an effect privilege set."""

    CHARACTER_DECISION = "character_decision"
    CHARACTER_REACTION = "character_reaction"
    RESOLVER = "resolver"
    RESOLVER_CONVERSATION = "resolver_conversation"
    RESOLVER_TRAVEL = "resolver_travel"
    DIRECTOR_PROPOSAL = "director_proposal"
    NPC_SCENE = "npc_scene"
    MEMORY_CONSOLIDATION = "memory_consolidation"


def _kind_from_type(effect_type: type[Any]) -> str:
    annotation = effect_type.model_fields["kind"].annotation
    args = getattr(annotation, "__args__", ())
    if args:
        return str(args[0])
    return str(effect_type.model_fields["kind"].default)


_ALL_EFFECT_KINDS: frozenset[str] = frozenset(_kind_from_type(t) for t in EFFECT_COMMAND_TYPES)

# Stage 1 scene resolver envelope (handbook 26 / existing SceneResolutionGraph).
STAGE1_RESOLVER_EFFECT_KINDS: frozenset[str] = frozenset(
    {
        "wait",
        "observe",
        "rest",
        "move_entity",
        "spend_resource",
        "advance_activity",
        "create_claim",
        "create_recent_memory",
        "schedule_effect",
    }
)

_CONVERSATION_EFFECT_KINDS: frozenset[str] = frozenset(
    {
        "wait",
        "create_claim",
        "relationship_evidence",
        "create_recent_memory",
        "schedule_effect",
    }
)

_TRAVEL_EFFECT_KINDS: frozenset[str] = frozenset(
    {
        "wait",
        "rest",
        "move_entity",
        "spend_resource",
        "advance_activity",
        "apply_condition",
        "schedule_effect",
    }
)

# Director proposals may *name* effect types for later resolver commit — never apply them.
_DIRECTOR_PROPOSED_EFFECT_KINDS: frozenset[str] = frozenset(
    {
        "observe",
        "create_claim",
        "schedule_effect",
        "register_npc",
        "relationship_evidence",
    }
)

# NPC scene actors: Stage 1 social/movement envelope without high-impact / creation.
_NPC_SCENE_EFFECT_KINDS: frozenset[str] = frozenset(
    {
        "wait",
        "observe",
        "rest",
        "move_entity",
        "create_claim",
        "create_recent_memory",
        "spend_resource",
        "advance_activity",
        "schedule_effect",
    }
)

# Character decision/reaction and memory consolidation emit proposals / records, not effects.
_EMPTY: frozenset[str] = frozenset()

_ROLE_EFFECT_KINDS: dict[GraphTaskRole, frozenset[str]] = {
    GraphTaskRole.CHARACTER_DECISION: _EMPTY,
    GraphTaskRole.CHARACTER_REACTION: _EMPTY,
    GraphTaskRole.RESOLVER: STAGE1_RESOLVER_EFFECT_KINDS,
    GraphTaskRole.RESOLVER_CONVERSATION: _CONVERSATION_EFFECT_KINDS,
    GraphTaskRole.RESOLVER_TRAVEL: _TRAVEL_EFFECT_KINDS,
    GraphTaskRole.DIRECTOR_PROPOSAL: _DIRECTOR_PROPOSED_EFFECT_KINDS,
    GraphTaskRole.NPC_SCENE: _NPC_SCENE_EFFECT_KINDS & _ALL_EFFECT_KINDS,
    GraphTaskRole.MEMORY_CONSOLIDATION: _EMPTY,
}


def restricted_effect_kinds(role: GraphTaskRole) -> frozenset[str]:
    """Return the effect-command kinds allowed for a task role."""

    try:
        return _ROLE_EFFECT_KINDS[role]
    except KeyError as exc:
        raise KeyError(f"unknown graph task role: {role}") from exc


def effect_kind_allowed(kind: str, role: GraphTaskRole) -> bool:
    """True when ``kind`` is in the role's restricted privilege set."""

    return kind in restricted_effect_kinds(role)


def restricted_effect_schema(role: GraphTaskRole) -> dict[str, Any]:
    """Build a minimal JSON Schema fragment listing only allowed effect kinds.

    Resolvers and prompt envelopes should pass this (or its ``enum``) rather than
    the universal ``EffectCommand`` union.
    """

    kinds = sorted(restricted_effect_kinds(role))
    return {
        "title": f"RestrictedEffectKinds:{role.value}",
        "description": (
            "Task-specific effect-command kinds only. Unrelated kinds are excluded "
            "as both a reliability and privilege boundary."
        ),
        "type": "string",
        "enum": kinds,
        "role": role.value,
        "allows_effects": bool(kinds),
    }


def assert_no_unrelated_effects(kinds: frozenset[str] | set[str], role: GraphTaskRole) -> None:
    """Raise when any supplied kind is outside the role privilege set."""

    allowed = restricted_effect_kinds(role)
    extras = frozenset(kinds) - allowed
    if extras:
        raise ValueError(
            f"effect kinds {sorted(extras)} are outside restricted schema for {role.value}"
        )


__all__ = [
    "STAGE1_RESOLVER_EFFECT_KINDS",
    "GraphTaskRole",
    "assert_no_unrelated_effects",
    "effect_kind_allowed",
    "restricted_effect_kinds",
    "restricted_effect_schema",
]
