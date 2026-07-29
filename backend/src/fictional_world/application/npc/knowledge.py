"""NPC actor knowledge packages — reuse KNOW secrets policy; never omniscient."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fictional_world.application.knowledge.lookup import (
    DEFAULT_DIRECTOR_ONLY,
    lookup_perspective_knowledge,
    npc_restricted_package_beliefs,
)
from fictional_world.application.npc.registry import may_receive_ordinary_actor_task
from fictional_world.application.npc.types import NpcKnowledgePackage, NpcRegistryEntry
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    SecretAccessPersistenceRecord,
)

# Keys/fields that must never appear in an NPC actor package (omniscient Director).
_OMNISCIENT_FORBIDDEN_KEYS: frozenset[str] = frozenset(
    {
        "director_only",
        "director_only_secret",
        "omniscient",
        "omniscient_secret",
        "protected_secret",
        "secret_payload",
        "true_name_revealed",
    }
)


def _strip_omniscient_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k.casefold() not in _OMNISCIENT_FORBIDDEN_KEYS}


def build_npc_knowledge_package(
    entry: NpcRegistryEntry,
    *,
    beliefs: Sequence[BeliefPersistenceRecord],
    secret_access: Sequence[SecretAccessPersistenceRecord],
    director_only_texts: Sequence[str] = (),
    omniscient_secret_texts: Sequence[str] = (),
) -> NpcKnowledgePackage:
    """Assemble an NPC actor package from the NPC's own perspective only.

    Reuses ``lookup_perspective_knowledge`` / ``SecretAccessPolicy`` and
    ``npc_restricted_package_beliefs``. Omniscient Director secrets and
    director-only strings are excluded even if present in inputs.
    """

    director_only = frozenset(director_only_texts) | frozenset(omniscient_secret_texts)
    knowledge = lookup_perspective_knowledge(
        character_id=entry.character_id,
        beliefs=beliefs,
        secret_access=secret_access,
        world_id=entry.world_id,
        director_only_texts=tuple(director_only),
        include_secret_summaries=True,
    )
    restricted = npc_restricted_package_beliefs(
        knowledge,
        director_only_texts=tuple(director_only),
    )
    scrubbed_beliefs = tuple(_strip_omniscient_fields(dict(b)) for b in restricted)
    scrubbed_summaries = tuple(
        _strip_omniscient_fields(dict(s)) for s in knowledge.secret_summaries
    )

    # Defense in depth: never leak default director-only strings into any field.
    banned = DEFAULT_DIRECTOR_ONLY | director_only
    final_beliefs: list[dict[str, Any]] = []
    for belief in scrubbed_beliefs:
        blob = " ".join(str(v) for v in belief.values()).casefold()
        if any(secret.casefold() in blob for secret in banned):
            continue
        final_beliefs.append(belief)

    return NpcKnowledgePackage(
        character_id=entry.character_id,
        compact_card=entry.compact_card,
        beliefs=tuple(final_beliefs),
        secret_keys=knowledge.secret_keys,
        secret_summaries=scrubbed_summaries,
        may_receive_ordinary_actor_task=may_receive_ordinary_actor_task(entry),
    )


def package_contains_forbidden_text(
    package: NpcKnowledgePackage,
    forbidden: Sequence[str],
) -> bool:
    """Test helper: True if any forbidden substring appears in the package."""

    blob_parts: list[str] = [
        package.compact_card.narrative_purpose,
        *(package.compact_card.traits),
        *(str(k) for k in package.secret_keys),
    ]
    for belief in package.beliefs:
        blob_parts.append(str(belief))
    for summary in package.secret_summaries:
        blob_parts.append(str(summary))
    blob = " ".join(blob_parts).casefold()
    return any(text.casefold() in blob for text in forbidden if text)


__all__ = [
    "build_npc_knowledge_package",
    "package_contains_forbidden_text",
]
