"""Build observer-specific ObservationPersistenceRecord values."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.application.knowledge.eligibility import (
    classify_observer_eligibility,
    eligible_observers,
)
from fictional_world.application.knowledge.observable_facts import allowed_observable_facts
from fictional_world.application.knowledge.types import EventObservationInput, ObserverPresence
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.knowledge.visibility import ObserverEligibility

_ELIGIBILITY_CONFIDENCE: dict[ObserverEligibility, Decimal] = {
    ObserverEligibility.DIRECT_WITNESS: Decimal("0.9000"),
    ObserverEligibility.PARTIAL: Decimal("0.5500"),
    ObserverEligibility.HEARING_ONLY: Decimal("0.4500"),
}

_ELIGIBILITY_SENSE: dict[ObserverEligibility, tuple[str, ...]] = {
    ObserverEligibility.DIRECT_WITNESS: ("sight", "hearing"),
    ObserverEligibility.PARTIAL: ("sight",),
    ObserverEligibility.HEARING_ONLY: ("hearing",),
}


def _content_hash(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _summary_for(
    event: EventObservationInput,
    eligibility: ObserverEligibility,
) -> str:
    if eligibility is ObserverEligibility.HEARING_ONLY:
        return event.auditory_summary or f"Heard activity near: {event.canonical_summary[:120]}"
    if eligibility is ObserverEligibility.PARTIAL:
        return event.partial_summary or f"Partially noticed: {event.canonical_summary[:120]}"
    return event.public_summary or event.canonical_summary


def build_observation_for_observer(
    event: EventObservationInput,
    presence: ObserverPresence,
    *,
    observation_id: UUID | None = None,
) -> ObservationPersistenceRecord | None:
    """Create one observation record, or None when the observer is absent."""

    eligibility = classify_observer_eligibility(presence)
    if eligibility is ObserverEligibility.ABSENT:
        return None

    perceived_facts, omitted = allowed_observable_facts(
        event.structured_facts,
        eligibility=eligibility,
        presence=presence,
    )
    summary = _summary_for(event, eligibility)
    obs_id = observation_id or uuid4()
    content_hash = _content_hash(
        {
            "world_event_id": str(event.world_event_id),
            "observer_id": str(presence.character_id),
            "eligibility": eligibility.value,
            "summary": summary,
            "perceived_facts": perceived_facts,
            "omitted": list(omitted),
        }
    )
    return ObservationPersistenceRecord(
        id=obs_id,
        world_event_id=event.world_event_id,
        observer_id=presence.character_id,
        observation_type=eligibility.value,
        perceived_summary=summary[:2_000],
        perceived_facts=perceived_facts,
        omitted_fact_keys=omitted,
        confidence=_ELIGIBILITY_CONFIDENCE[eligibility],
        visibility_reason=eligibility.value,
        source_sense_tags=_ELIGIBILITY_SENSE[eligibility],
        content_hash=content_hash,
    )


def build_observations(
    event: EventObservationInput,
    candidates: Sequence[ObserverPresence],
) -> tuple[ObservationPersistenceRecord, ...]:
    """Build observations for all eligible observers (absent → no record)."""

    records: list[ObservationPersistenceRecord] = []
    for presence, _eligibility in eligible_observers(candidates):
        record = build_observation_for_observer(event, presence)
        if record is not None:
            records.append(record)
    return tuple(records)


__all__ = ["build_observation_for_observer", "build_observations"]
