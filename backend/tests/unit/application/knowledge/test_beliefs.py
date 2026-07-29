"""Belief confidence bounds and evidence updates (S2-KNOW-001)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from fictional_world.application.knowledge import (
    apply_claim_evidence,
    apply_observation_evidence,
    clamp_confidence,
    create_claim,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (-1, Decimal("0.0000")),
        (0, Decimal("0.0000")),
        (0.5, Decimal("0.5000")),
        (1, Decimal("1.0000")),
        (2.5, Decimal("1.0000")),
        ("0.12345", Decimal("0.1234")),
    ],
)
def test_clamp_confidence_bounds(raw: object, expected: Decimal) -> None:
    assert clamp_confidence(raw) == expected  # type: ignore[arg-type]


@pytest.mark.unit
def test_observation_evidence_updates_confidence_with_provenance() -> None:
    world_id = uuid4()
    character_id = uuid4()
    observation = ObservationPersistenceRecord(
        id=uuid4(),
        world_event_id=uuid4(),
        observer_id=character_id,
        observation_type="direct_witness",
        perceived_summary="Saw the cup move.",
        perceived_facts={"item_id": "cup"},
        omitted_fact_keys=("motive",),
        confidence=Decimal("0.9000"),
        visibility_reason="direct_witness",
        source_sense_tags=("sight",),
        content_hash="abc",
    )
    belief = apply_observation_evidence(
        None,
        world_id=world_id,
        character_id=character_id,
        observation=observation,
        proposition_key="cup_moved",
        belief_text="Someone moved the cup.",
        signed_weight=Decimal("0.20"),
    )
    assert belief.confidence == Decimal("0.2000")
    assert belief.first_source_observation_id == observation.id
    assert belief.evidence_summary["last_source_kind"] == "observation"

    boosted = apply_observation_evidence(
        belief,
        world_id=world_id,
        character_id=character_id,
        observation=observation,
        proposition_key="cup_moved",
        belief_text="Someone moved the cup.",
        signed_weight=Decimal("0.95"),
    )
    assert boosted.confidence == Decimal("1.0000")
    assert boosted.version == 1
    assert len(boosted.evidence_summary["sources"]) == 2


@pytest.mark.unit
def test_claim_evidence_can_reduce_but_not_below_zero() -> None:
    world_id = uuid4()
    character_id = uuid4()
    claim = create_claim(
        world_id=world_id,
        source_event_id=uuid4(),
        speaker_id=uuid4(),
        listener_ids=(character_id,),
        proposition_text="The bridge is unsafe tonight.",
    )
    belief = apply_claim_evidence(
        None,
        world_id=world_id,
        character_id=character_id,
        claim=claim,
        signed_weight=Decimal("0.05"),
    )
    reduced = apply_claim_evidence(
        belief,
        world_id=world_id,
        character_id=character_id,
        claim=claim,
        signed_weight=Decimal("-0.80"),
    )
    assert reduced.confidence == Decimal("0.0000")
