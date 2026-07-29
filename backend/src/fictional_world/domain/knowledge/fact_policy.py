"""Default structured-fact visibility policies (handbook 11 §4.3)."""

from __future__ import annotations

from fictional_world.domain.knowledge.visibility import FactVisibilityRequirement

# Canonical / common fact keys → visibility requirement.
DEFAULT_FACT_VISIBILITY: dict[str, FactVisibilityRequirement] = {
    "location_id": FactVisibilityRequirement.ALWAYS_PUBLIC,
    "event_type": FactVisibilityRequirement.ALWAYS_PUBLIC,
    "public_sound": FactVisibilityRequirement.HEARING_CHANNEL,
    "utterance_heard": FactVisibilityRequirement.HEARING_CHANNEL,
    "actor_id": FactVisibilityRequirement.ACTOR_SEEN,
    "method": FactVisibilityRequirement.ACTOR_SEEN,
    "item_id": FactVisibilityRequirement.ITEM_SEEN,
    "target_entity_id": FactVisibilityRequirement.ITEM_SEEN,
    "substance_id": FactVisibilityRequirement.CLOSE_VISUAL_OR_KNOWN_MAGIC,
    "amount": FactVisibilityRequirement.PRECISE_CLOSE_OBSERVATION,
    "motive": FactVisibilityRequirement.NEVER,
    "director_notes": FactVisibilityRequirement.NEVER,
    "secret_payload": FactVisibilityRequirement.NEVER,
}

# Keys that must never appear in character observations regardless of eligibility.
ALWAYS_OMITTED_FACT_KEYS: frozenset[str] = frozenset(
    {
        "motive",
        "director_notes",
        "secret_payload",
        "director_only",
        "omniscient_truth",
    }
)


def visibility_for_fact_key(fact_key: str) -> FactVisibilityRequirement:
    """Return the visibility requirement for a structured fact key."""

    if fact_key in ALWAYS_OMITTED_FACT_KEYS:
        return FactVisibilityRequirement.NEVER
    return DEFAULT_FACT_VISIBILITY.get(fact_key, FactVisibilityRequirement.ACTOR_SEEN)


__all__ = [
    "ALWAYS_OMITTED_FACT_KEYS",
    "DEFAULT_FACT_VISIBILITY",
    "visibility_for_fact_key",
]
