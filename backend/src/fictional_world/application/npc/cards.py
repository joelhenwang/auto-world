"""Compact NPC identity cards — never include director-only content."""

from __future__ import annotations

from collections.abc import Sequence

from fictional_world.application.knowledge.lookup import DEFAULT_DIRECTOR_ONLY
from fictional_world.application.npc.types import NpcCompactCard, NpcProposalInput


def _scrub(text: str | None, director_only: frozenset[str]) -> str | None:
    if text is None:
        return None
    lowered = text.casefold()
    if any(secret.casefold() in lowered for secret in director_only):
        return None
    return text


def build_compact_card(
    proposal: NpcProposalInput,
    *,
    director_only_texts: Sequence[str] = (),
) -> NpcCompactCard:
    """Build a public compact card from a proposal, scrubbing director-only text."""

    director_only = frozenset(director_only_texts) | DEFAULT_DIRECTOR_ONLY
    purpose = _scrub(proposal.narrative_purpose, director_only) or "supporting local figure"
    return NpcCompactCard(
        display_name=proposal.proposed_name,
        role_tags=tuple(proposal.role_tags),
        traits=tuple(proposal.traits),
        location_key=proposal.location_key,
        narrative_purpose=purpose,
        category=proposal.category,
        appearance=_scrub(proposal.appearance, director_only),
        personality=_scrub(proposal.personality, director_only),
        source_hook_key=proposal.source_hook_key,
    )


def compact_card_as_json(card: NpcCompactCard) -> dict[str, object]:
    """Serialize a card for ``npc_profile.compact_card`` JSONB storage."""

    return {
        "display_name": card.display_name,
        "role_tags": list(card.role_tags),
        "traits": list(card.traits),
        "location_key": card.location_key,
        "narrative_purpose": card.narrative_purpose,
        "category": card.category,
        "appearance": card.appearance,
        "personality": card.personality,
        "source_hook_key": card.source_hook_key,
    }


__all__ = ["build_compact_card", "compact_card_as_json"]
