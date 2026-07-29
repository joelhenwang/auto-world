"""Belief confidence updates from observation and claim evidence."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fictional_world.application.knowledge.claims import proposition_key_for
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    ClaimPersistenceRecord,
    ObservationPersistenceRecord,
)
from fictional_world.domain.knowledge.visibility import BeliefEvidenceSourceKind

_ZERO = Decimal("0")
_ONE = Decimal("1")


def clamp_confidence(value: Decimal | float | int | str) -> Decimal:
    """Clamp confidence to the closed interval [0, 1]."""

    conf = Decimal(str(value))
    if conf < _ZERO:
        return _ZERO
    if conf > _ONE:
        return _ONE
    return conf.quantize(Decimal("0.0001"))


def _append_evidence(
    evidence: dict[str, Any],
    *,
    source_kind: BeliefEvidenceSourceKind,
    source_id: UUID,
    signed_weight: Decimal,
) -> dict[str, Any]:
    updated = dict(evidence)
    entries = list(updated.get("sources", []))
    entries.append(
        {
            "source_kind": source_kind.value,
            "source_id": str(source_id),
            "signed_weight": str(signed_weight),
        }
    )
    updated["sources"] = entries
    updated["last_source_kind"] = source_kind.value
    updated["last_source_id"] = str(source_id)
    return updated


def apply_observation_evidence(
    belief: BeliefPersistenceRecord | None,
    *,
    world_id: UUID,
    character_id: UUID,
    observation: ObservationPersistenceRecord,
    proposition_key: str,
    belief_text: str,
    signed_weight: Decimal | float = Decimal("0.15"),
    belief_id: UUID | None = None,
) -> BeliefPersistenceRecord:
    """Create or update a belief from an observation (confidence stays in [0, 1])."""

    weight = clamp_confidence(abs(Decimal(str(signed_weight))))
    signed = weight if Decimal(str(signed_weight)) >= 0 else -weight
    if belief is None:
        return BeliefPersistenceRecord(
            id=belief_id or uuid4(),
            world_id=world_id,
            character_id=character_id,
            proposition_key=proposition_key,
            belief_text=belief_text,
            confidence=clamp_confidence(weight),
            status="active",
            first_source_observation_id=observation.id,
            last_source_event_id=observation.world_event_id,
            evidence_summary=_append_evidence(
                {},
                source_kind=BeliefEvidenceSourceKind.OBSERVATION,
                source_id=observation.id,
                signed_weight=signed,
            ),
            version=0,
        )

    new_conf = clamp_confidence(belief.confidence + signed)
    evidence = _append_evidence(
        dict(belief.evidence_summary),
        source_kind=BeliefEvidenceSourceKind.OBSERVATION,
        source_id=observation.id,
        signed_weight=signed,
    )
    first_obs = belief.first_source_observation_id or observation.id
    return belief.model_copy(
        update={
            "confidence": new_conf,
            "belief_text": belief_text,
            "first_source_observation_id": first_obs,
            "last_source_event_id": observation.world_event_id,
            "evidence_summary": evidence,
            "version": belief.version + 1,
            "status": "active",
        }
    )


def apply_claim_evidence(
    belief: BeliefPersistenceRecord | None,
    *,
    world_id: UUID,
    character_id: UUID,
    claim: ClaimPersistenceRecord,
    signed_weight: Decimal | float = Decimal("0.10"),
    belief_id: UUID | None = None,
    rumour_provenance: dict[str, Any] | None = None,
) -> BeliefPersistenceRecord:
    """Update belief confidence from a heard claim (including rumours)."""

    weight = clamp_confidence(abs(Decimal(str(signed_weight))))
    # Lies assessed false still update belief — listener may believe the lie.
    signed = weight if Decimal(str(signed_weight)) >= 0 else -weight
    prop_key = claim.proposition_key or proposition_key_for(claim.proposition_text)
    if belief is None:
        evidence = _append_evidence(
            {},
            source_kind=BeliefEvidenceSourceKind.CLAIM,
            source_id=claim.id,
            signed_weight=signed,
        )
        if rumour_provenance is not None:
            evidence["rumour_provenance"] = rumour_provenance
        return BeliefPersistenceRecord(
            id=belief_id or uuid4(),
            world_id=world_id,
            character_id=character_id,
            proposition_key=prop_key,
            belief_text=claim.proposition_text,
            confidence=clamp_confidence(weight),
            status="active",
            last_source_event_id=claim.source_event_id,
            evidence_summary=evidence,
            version=0,
        )

    new_conf = clamp_confidence(belief.confidence + signed)
    evidence = _append_evidence(
        dict(belief.evidence_summary),
        source_kind=BeliefEvidenceSourceKind.CLAIM,
        source_id=claim.id,
        signed_weight=signed,
    )
    if rumour_provenance is not None:
        evidence["rumour_provenance"] = rumour_provenance
    return belief.model_copy(
        update={
            "confidence": new_conf,
            "belief_text": claim.proposition_text,
            "last_source_event_id": claim.source_event_id,
            "evidence_summary": evidence,
            "version": belief.version + 1,
            "status": "active",
        }
    )


__all__ = [
    "apply_claim_evidence",
    "apply_observation_evidence",
    "clamp_confidence",
]
