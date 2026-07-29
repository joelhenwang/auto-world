"""Perspective-restricted knowledge lookup for character context packages."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from fictional_world.application.knowledge.secrets import SecretAccessPolicy
from fictional_world.application.knowledge.types import PerspectiveKnowledge
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    SecretAccessPersistenceRecord,
)

# Texts that must never appear in actor / NPC packages.
DEFAULT_DIRECTOR_ONLY: frozenset[str] = frozenset(
    {
        "the old beacon contains an Ashfall-era pattern recorder, not a weapon",
        "Mira's father hook is not required to connect to the first month's event",
    }
)


def _contains_director_only(text: str, director_only: frozenset[str]) -> bool:
    lowered = text.casefold()
    return any(secret.casefold() in lowered for secret in director_only)


def _belief_to_dict(belief: BeliefPersistenceRecord) -> dict[str, Any]:
    return {
        "belief_id": str(belief.id),
        "proposition_key": belief.proposition_key,
        "proposition": belief.belief_text,
        "confidence": str(belief.confidence),
        "status": belief.status,
        "owner_character_id": str(belief.character_id),
    }


def lookup_perspective_knowledge(
    *,
    character_id: UUID,
    beliefs: Sequence[BeliefPersistenceRecord],
    secret_access: Sequence[SecretAccessPersistenceRecord],
    world_id: UUID | None = None,
    director_only_texts: Sequence[str] = (),
    include_secret_summaries: bool = True,
) -> PerspectiveKnowledge:
    """Return only beliefs/secrets the character is allowed to see.

    - Own active beliefs only (no other character's private beliefs).
    - Secrets only when ``secret_access`` grants the holder.
    - Director-only strings are stripped even if present in belief text.
    """

    director_only = frozenset(director_only_texts) | DEFAULT_DIRECTOR_ONLY
    policy = SecretAccessPolicy(secret_access)
    held_keys = policy.held_secret_keys(character_id, world_id=world_id)

    allowed_beliefs: list[dict[str, Any]] = []
    for belief in beliefs:
        if belief.character_id != character_id:
            continue
        if belief.status.casefold() not in {"active", "believed_true", "uncertain", "leaning_true"}:
            continue
        if _contains_director_only(belief.belief_text, director_only):
            continue
        allowed_beliefs.append(_belief_to_dict(belief))

    secret_summaries: list[dict[str, Any]] = []
    if include_secret_summaries:
        for row in policy.active_rows_for_holder(character_id, world_id=world_id):
            secret_summaries.append(
                {
                    "secret_key": row.secret_key,
                    "access_level": row.access_level,
                    "owner_character_id": str(row.owner_character_id),
                }
            )

    return PerspectiveKnowledge(
        character_id=character_id,
        beliefs=tuple(allowed_beliefs),
        secret_keys=tuple(sorted(held_keys)),
        secret_summaries=tuple(secret_summaries),
    )


def npc_restricted_package_beliefs(
    knowledge: PerspectiveKnowledge,
    *,
    director_only_texts: Sequence[str] = (),
) -> tuple[dict[str, Any], ...]:
    """NPC-style projection: beliefs only, never director-only content."""

    director_only = frozenset(director_only_texts) | DEFAULT_DIRECTOR_ONLY
    out: list[dict[str, Any]] = []
    for belief in knowledge.beliefs:
        prop = str(belief.get("proposition", ""))
        if _contains_director_only(prop, director_only):
            continue
        out.append(dict(belief))
    return tuple(out)


__all__ = [
    "DEFAULT_DIRECTOR_ONLY",
    "lookup_perspective_knowledge",
    "npc_restricted_package_beliefs",
]
