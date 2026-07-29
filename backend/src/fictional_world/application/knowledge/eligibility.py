"""Observer eligibility classification (handbook 11 §4.1)."""

from __future__ import annotations

from collections.abc import Sequence

from fictional_world.application.knowledge.types import ObserverPresence
from fictional_world.domain.knowledge.visibility import ObserverEligibility


def classify_observer_eligibility(presence: ObserverPresence) -> ObserverEligibility:
    """Deterministically classify how an observer may perceive an event.

    Models do not decide presence. Absent characters receive no observation.
    """

    if presence.eligibility_override is not None:
        return presence.eligibility_override

    if not presence.co_located and not presence.hearing_range:
        return ObserverEligibility.ABSENT

    can_see = (
        presence.co_located
        and presence.line_of_sight
        and presence.attention
        and not presence.concealment_blocks_sight
    )
    can_hear = presence.hearing_range and presence.attention

    if can_see and presence.precise_close:
        return ObserverEligibility.DIRECT_WITNESS
    if can_see and not presence.close_range:
        return ObserverEligibility.PARTIAL
    if can_see:
        return ObserverEligibility.DIRECT_WITNESS
    if can_hear:
        return ObserverEligibility.HEARING_ONLY
    if presence.co_located and not presence.attention:
        return ObserverEligibility.PARTIAL
    return ObserverEligibility.ABSENT


def eligible_observers(
    candidates: Sequence[ObserverPresence],
) -> tuple[tuple[ObserverPresence, ObserverEligibility], ...]:
    """Return only non-absent observers with their eligibility class."""

    out: list[tuple[ObserverPresence, ObserverEligibility]] = []
    for presence in candidates:
        eligibility = classify_observer_eligibility(presence)
        if eligibility is ObserverEligibility.ABSENT:
            continue
        out.append((presence, eligibility))
    return tuple(out)


__all__ = ["classify_observer_eligibility", "eligible_observers"]
