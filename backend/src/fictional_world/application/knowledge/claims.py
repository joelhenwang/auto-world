"""Claim creation from statements, lies, and rumour transmission."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.domain.knowledge.persistence import ClaimPersistenceRecord
from fictional_world.domain.knowledge.visibility import ClaimIntentClass, ClaimTruthStatus

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def proposition_key_for(text: str) -> str:
    """Stable short key for a claim/belief proposition (matches seed importer style)."""

    digest = hashlib.sha256(text.encode()).hexdigest()[:12]
    slug = _SLUG_RE.sub("-", text.casefold()).strip("-")[:40] or digest
    return f"{slug}-{digest}"


def create_claim(
    *,
    world_id: UUID,
    source_event_id: UUID,
    speaker_id: UUID,
    listener_ids: tuple[UUID, ...],
    proposition_text: str,
    intent_class: ClaimIntentClass = ClaimIntentClass.STATEMENT,
    truth_status: ClaimTruthStatus = ClaimTruthStatus.UNKNOWN,
    confidence_expressed: Decimal | None = None,
    claim_id: UUID | None = None,
    proposition_key: str | None = None,
) -> ClaimPersistenceRecord:
    """Create a ClaimPersistenceRecord.

    Claims are never written to objective fact tables. ``truth_status`` is an
    omniscient assessor label only; default remains ``unknown``.
    """

    if not listener_ids:
        msg = "claim requires at least one listener"
        raise ValueError(msg)
    text = proposition_text.strip()
    if not text:
        msg = "proposition_text must be non-empty"
        raise ValueError(msg)

    # Lies must not be auto-promoted to true facts.
    if intent_class is ClaimIntentClass.LIE and truth_status is ClaimTruthStatus.TRUE:
        truth_status = ClaimTruthStatus.FALSE

    return ClaimPersistenceRecord(
        id=claim_id or uuid4(),
        world_id=world_id,
        source_event_id=source_event_id,
        speaker_id=speaker_id,
        proposition_key=proposition_key or proposition_key_for(text),
        proposition_text=text[:4_000],
        truth_status=truth_status.value,
        intent_class=intent_class.value,
        confidence_expressed=confidence_expressed,
        listener_ids=listener_ids,
    )


def create_lie_claim(
    *,
    world_id: UUID,
    source_event_id: UUID,
    speaker_id: UUID,
    listener_ids: tuple[UUID, ...],
    proposition_text: str,
    assessor_knows_false: bool = True,
    claim_id: UUID | None = None,
) -> ClaimPersistenceRecord:
    """Speaker lie → claim (not an objective fact)."""

    truth = ClaimTruthStatus.FALSE if assessor_knows_false else ClaimTruthStatus.UNKNOWN
    return create_claim(
        world_id=world_id,
        source_event_id=source_event_id,
        speaker_id=speaker_id,
        listener_ids=listener_ids,
        proposition_text=proposition_text,
        intent_class=ClaimIntentClass.LIE,
        truth_status=truth,
        claim_id=claim_id,
    )


def transmit_rumour(
    *,
    world_id: UUID,
    source_event_id: UUID,
    speaker_id: UUID,
    listener_ids: tuple[UUID, ...],
    source_claim: ClaimPersistenceRecord,
    proposition_text: str | None = None,
    claim_id: UUID | None = None,
) -> ClaimPersistenceRecord:
    """Create a NEW rumour claim linked to a prior claim via provenance fields.

    The prior claim is not mutated. Linkage lives on the new claim's
    ``proposition_key`` lineage and is returned with provenance metadata that
    callers may store in belief evidence_summary.
    """

    text = (proposition_text or source_claim.proposition_text).strip()
    rumour = create_claim(
        world_id=world_id,
        source_event_id=source_event_id,
        speaker_id=speaker_id,
        listener_ids=listener_ids,
        proposition_text=text,
        intent_class=ClaimIntentClass.RUMOUR,
        truth_status=ClaimTruthStatus.UNKNOWN,
        claim_id=claim_id,
        proposition_key=source_claim.proposition_key,
    )
    return rumour


def rumour_provenance(
    source_claim: ClaimPersistenceRecord, rumour: ClaimPersistenceRecord
) -> dict[str, str | None]:
    """Provenance blob for belief evidence / audit when a rumour is transmitted."""

    return {
        "source_kind": "claim",
        "source_claim_id": str(source_claim.id),
        "rumour_claim_id": str(rumour.id),
        "source_speaker_id": str(source_claim.speaker_id),
        "rumour_speaker_id": str(rumour.speaker_id),
        "intent_class": ClaimIntentClass.RUMOUR.value,
        "proposition_key": rumour.proposition_key,
    }


def claim_is_not_objective_fact(claim: ClaimPersistenceRecord) -> bool:
    """Invariant helper: claims remain non-canonical regardless of truth_status."""

    return claim.intent_class is not None and claim.truth_status in {
        ClaimTruthStatus.UNKNOWN.value,
        ClaimTruthStatus.TRUE.value,
        ClaimTruthStatus.FALSE.value,
        ClaimTruthStatus.MIXED.value,
    }


__all__ = [
    "claim_is_not_objective_fact",
    "create_claim",
    "create_lie_claim",
    "proposition_key_for",
    "rumour_provenance",
    "transmit_rumour",
]
