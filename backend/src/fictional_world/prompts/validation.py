"""Prompt-output convention checks that Pydantic shape validation cannot express."""

from __future__ import annotations

import re
from collections.abc import Iterable

from fictional_world.domain.scenes.proposals import ActionProposal

_OTHER_REACTION_VERBS = (
    "accepts",
    "agrees",
    "answers",
    "apologizes",
    "declines",
    "flinches",
    "follows",
    "laughs",
    "nods",
    "refuses",
    "replies",
    "responds",
    "retreats",
    "smiles",
    "steps aside",
    "turns away",
)


class AuthoredOtherReactionError(ValueError):
    """Raised when an action proposal narrates another character's reaction."""


def validate_no_authored_other_reaction(
    proposal: ActionProposal,
    *,
    other_character_names: Iterable[str],
) -> None:
    """Reject explicit other-character reactions embedded in an actor's proposal.

    The caller supplies display names from the proposal's allow-listed context. This
    conservative lexical convention check complements later semantic graph validation;
    it does not infer identities or query global character state.
    """

    descriptions = (proposal.description, *(item.description for item in proposal.desired_outcomes))
    reaction_alternation = "|".join(re.escape(verb) for verb in _OTHER_REACTION_VERBS)
    for raw_name in other_character_names:
        name = raw_name.strip()
        if not name:
            continue
        pattern = re.compile(
            rf"\b{re.escape(name)}\b\s+(?:{reaction_alternation})\b",
            flags=re.IGNORECASE,
        )
        if any(pattern.search(description) for description in descriptions):
            raise AuthoredOtherReactionError(
                f"proposal authors a reaction for another character: {name}"
            )
