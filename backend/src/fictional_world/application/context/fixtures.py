"""Stage 1 relationship and belief fixtures for context assembly."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fictional_world.domain.seed.ids import seed_uuid

# Handbook 23 §19 — directional Mira↔Dain only for Stage 1 active cast.
STAGE1_RELATIONSHIPS: tuple[dict[str, Any], ...] = (
    {
        "source": "character/mira-talren",
        "target": "character/dain-arcen",
        "familiarity": 0.24,
        "trust": 0.12,
        "affection": 0.06,
        "attraction": 0.0,
        "respect": 0.18,
        "fear": 0.0,
        "resentment": 0.0,
        "dependency": 0.0,
        "loyalty": 0.02,
        "perceived_reciprocity": 0.08,
        "basis": "They have crossed paths on two courier escorts.",
    },
    {
        "source": "character/dain-arcen",
        "target": "character/mira-talren",
        "familiarity": 0.27,
        "trust": 0.16,
        "affection": 0.09,
        "attraction": 0.0,
        "respect": 0.22,
        "fear": 0.0,
        "resentment": 0.0,
        "dependency": 0.0,
        "loyalty": 0.03,
        "perceived_reciprocity": 0.04,
        "basis": "He considers her observant and unnecessarily willing to travel alone.",
    },
)

STAGE1_PRIVATE_BELIEFS: tuple[dict[str, Any], ...] = (
    {
        "owner": "character/mira-talren",
        "proposition": (
            "Her father's disappearance may be connected to a falsified north-route report."
        ),
        "confidence": 0.42,
        "objective_status": "unresolved",
    },
    {
        "owner": "character/dain-arcen",
        "proposition": (
            "His probationary captain cares more about clean reports than uncertain warnings."
        ),
        "confidence": 0.58,
        "objective_status": "partially_supported",
    },
)

DIRECTOR_ONLY_FACTS: tuple[str, ...] = (
    "the old beacon contains an Ashfall-era pattern recorder, not a weapon",
    "Mira's father hook is not required to connect to the first month's event",
)

STAGE1_GOALS: tuple[dict[str, Any], ...] = (
    {
        "owner": "character/mira-talren",
        "title": "Complete the east-bridge route annotation contract",
        "horizon": "short",
        "priority": 72,
    },
    {
        "owner": "character/mira-talren",
        "title": "Learn what happened to her father",
        "horizon": "long",
        "priority": 80,
    },
    {
        "owner": "character/dain-arcen",
        "title": "Finish probationary Warden posting without scandal",
        "horizon": "short",
        "priority": 78,
    },
    {
        "owner": "character/dain-arcen",
        "title": "Prove reliable judgment under incomplete information",
        "horizon": "long",
        "priority": 70,
    },
)

STAGE1_LOCAL_MAP: tuple[dict[str, str], ...] = (
    {
        "key": "location/veycross/cinder-lantern-inn",
        "name": "Cinder Lantern Inn",
    },
    {
        "key": "location/veycross/market-square",
        "name": "Market Square",
    },
    {
        "key": "location/veycross/east-bridge",
        "name": "East Bridge",
    },
)


def relationship_edges_for(observer_seed_key: str) -> list[dict[str, Any]]:
    """Return only outgoing edges owned by the observer (directional isolation)."""

    edges: list[dict[str, Any]] = []
    for edge in STAGE1_RELATIONSHIPS:
        if edge["source"] != observer_seed_key:
            continue
        item = dict(edge)
        item["source_id"] = str(seed_uuid(edge["source"]))
        item["target_id"] = str(seed_uuid(edge["target"]))
        edges.append(item)
    return edges


def private_beliefs_for(owner_seed_key: str) -> list[dict[str, Any]]:
    return [dict(b) for b in STAGE1_PRIVATE_BELIEFS if b["owner"] == owner_seed_key]


def goals_for(owner_seed_key: str) -> list[dict[str, Any]]:
    return [dict(g) for g in STAGE1_GOALS if g["owner"] == owner_seed_key]


def seed_key_for_character_id(character_id: UUID) -> str | None:
    mapping: dict[UUID, str] = {
        seed_uuid("character/mira-talren"): "character/mira-talren",
        seed_uuid("character/dain-arcen"): "character/dain-arcen",
    }
    return mapping.get(character_id)
