"""Claims: lies are not facts; rumours are sourced (S2-KNOW-001)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.application.knowledge import (
    claim_is_not_objective_fact,
    create_lie_claim,
    rumour_provenance,
    transmit_rumour,
)
from fictional_world.domain.knowledge import ClaimIntentClass, ClaimTruthStatus


@pytest.mark.unit
def test_lie_produces_claim_not_objective_fact() -> None:
    world_id = uuid4()
    event_id = uuid4()
    speaker = uuid4()
    listener = uuid4()
    claim = create_lie_claim(
        world_id=world_id,
        source_event_id=event_id,
        speaker_id=speaker,
        listener_ids=(listener,),
        proposition_text="The north beacon is empty and harmless.",
    )
    assert claim.intent_class == ClaimIntentClass.LIE.value
    assert claim.truth_status == ClaimTruthStatus.FALSE.value
    assert claim_is_not_objective_fact(claim)
    # No objective-fact storage fields exist on the claim record.
    assert not hasattr(claim, "structured_facts")
    assert claim.proposition_text == "The north beacon is empty and harmless."


@pytest.mark.unit
def test_rumour_creates_new_claim_with_source_linkage() -> None:
    world_id = uuid4()
    original = create_lie_claim(
        world_id=world_id,
        source_event_id=uuid4(),
        speaker_id=uuid4(),
        listener_ids=(uuid4(),),
        proposition_text="Mira carries a sealed Collegium letter.",
    )
    reteller = uuid4()
    new_listeners = (uuid4(),)
    rumour_event = uuid4()
    rumour = transmit_rumour(
        world_id=world_id,
        source_event_id=rumour_event,
        speaker_id=reteller,
        listener_ids=new_listeners,
        source_claim=original,
    )
    assert rumour.id != original.id
    assert rumour.intent_class == ClaimIntentClass.RUMOUR.value
    assert rumour.proposition_key == original.proposition_key
    assert rumour.speaker_id == reteller
    assert rumour.listener_ids == new_listeners
    provenance = rumour_provenance(original, rumour)
    assert provenance["source_claim_id"] == str(original.id)
    assert provenance["rumour_claim_id"] == str(rumour.id)
    assert provenance["source_kind"] == "claim"
