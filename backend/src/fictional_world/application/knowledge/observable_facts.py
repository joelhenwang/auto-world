"""Map committed structured facts to observer-allowed fact keys."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fictional_world.application.knowledge.types import ObserverPresence
from fictional_world.domain.knowledge.fact_policy import (
    ALWAYS_OMITTED_FACT_KEYS,
    visibility_for_fact_key,
)
from fictional_world.domain.knowledge.visibility import (
    FactVisibilityRequirement,
    ObserverEligibility,
)


def _requirement_met(
    requirement: FactVisibilityRequirement,
    *,
    eligibility: ObserverEligibility,
    presence: ObserverPresence,
) -> bool:
    if requirement is FactVisibilityRequirement.NEVER:
        return False
    if requirement is FactVisibilityRequirement.ALWAYS_PUBLIC:
        return eligibility is not ObserverEligibility.ABSENT
    if requirement is FactVisibilityRequirement.HEARING_CHANNEL:
        return eligibility in {
            ObserverEligibility.DIRECT_WITNESS,
            ObserverEligibility.HEARING_ONLY,
            ObserverEligibility.PARTIAL,
        } and (presence.hearing_range or presence.line_of_sight)
    if requirement is FactVisibilityRequirement.ACTOR_SEEN:
        return eligibility is ObserverEligibility.DIRECT_WITNESS and presence.line_of_sight
    if requirement is FactVisibilityRequirement.ITEM_SEEN:
        return eligibility is ObserverEligibility.DIRECT_WITNESS and (
            presence.line_of_sight or presence.close_range
        )
    if requirement is FactVisibilityRequirement.CLOSE_VISUAL_OR_KNOWN_MAGIC:
        return eligibility is ObserverEligibility.DIRECT_WITNESS and (
            presence.close_range or presence.known_magic_sense
        )
    if requirement is FactVisibilityRequirement.PRECISE_CLOSE_OBSERVATION:
        return (
            eligibility is ObserverEligibility.DIRECT_WITNESS
            and presence.precise_close
            and presence.close_range
        )
    return False


def allowed_observable_facts(
    structured_facts: Mapping[str, Any],
    *,
    eligibility: ObserverEligibility,
    presence: ObserverPresence,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Return (perceived_facts, omitted_fact_keys) for one observer.

    Omitted keys include both ineligible fields and always-private keys present
    in the canonical payload. Absent observers should not call this — they get
    no observation record at all.
    """

    if eligibility is ObserverEligibility.ABSENT:
        return {}, tuple(sorted(structured_facts.keys()))

    perceived: dict[str, Any] = {}
    omitted: list[str] = []
    for key, value in structured_facts.items():
        if key in ALWAYS_OMITTED_FACT_KEYS:
            omitted.append(key)
            continue
        requirement = visibility_for_fact_key(key)
        if _requirement_met(requirement, eligibility=eligibility, presence=presence):
            # Partial witnesses lose precise keys even when requirement is looser.
            if eligibility is ObserverEligibility.PARTIAL and requirement in {
                FactVisibilityRequirement.CLOSE_VISUAL_OR_KNOWN_MAGIC,
                FactVisibilityRequirement.PRECISE_CLOSE_OBSERVATION,
                FactVisibilityRequirement.ACTOR_SEEN,
            }:
                omitted.append(key)
                continue
            if eligibility is ObserverEligibility.HEARING_ONLY and requirement not in {
                FactVisibilityRequirement.ALWAYS_PUBLIC,
                FactVisibilityRequirement.HEARING_CHANNEL,
            }:
                omitted.append(key)
                continue
            perceived[key] = value
        else:
            omitted.append(key)
    return perceived, tuple(sorted(omitted))


__all__ = ["allowed_observable_facts"]
