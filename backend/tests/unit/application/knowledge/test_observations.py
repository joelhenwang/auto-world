"""Observation builder and diverging witnesses (S2-KNOW-001)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.application.knowledge import (
    EventObservationInput,
    ObserverPresence,
    build_observation_for_observer,
    build_observations,
)


@pytest.mark.unit
def test_two_witnesses_diverge_on_same_event() -> None:
    event_id = uuid4()
    actor = uuid4()
    direct_id = uuid4()
    hear_id = uuid4()
    event = EventObservationInput(
        world_event_id=event_id,
        canonical_summary="Sein tampered with the silver cup under his cloak.",
        public_summary="Sein lingered near the silver cup.",
        auditory_summary="Porcelain scraped softly behind you.",
        structured_facts={
            "actor_id": str(actor),
            "item_id": "silver_cup",
            "substance_id": "sleep_tincture",
            "amount": "3_drops",
            "method": "concealed_under_cloak",
            "motive": "disable_target",
            "location_id": str(uuid4()),
            "public_sound": "porcelain_scrape",
        },
    )
    direct = ObserverPresence(
        character_id=direct_id,
        co_located=True,
        line_of_sight=True,
        hearing_range=True,
        close_range=True,
        precise_close=True,
    )
    hearing = ObserverPresence(
        character_id=hear_id,
        co_located=True,
        line_of_sight=False,
        hearing_range=True,
        close_range=False,
    )
    obs_direct = build_observation_for_observer(event, direct)
    obs_hear = build_observation_for_observer(event, hearing)
    assert obs_direct is not None
    assert obs_hear is not None
    assert obs_direct.perceived_summary != obs_hear.perceived_summary
    assert "substance_id" in obs_direct.perceived_facts
    assert "amount" in obs_direct.perceived_facts
    assert "substance_id" not in obs_hear.perceived_facts
    assert "actor_id" not in obs_hear.perceived_facts
    assert "public_sound" in obs_hear.perceived_facts
    assert "motive" in obs_direct.omitted_fact_keys
    assert "motive" in obs_hear.omitted_fact_keys


@pytest.mark.unit
def test_absent_character_gets_no_observation() -> None:
    event = EventObservationInput(
        world_event_id=uuid4(),
        canonical_summary="A cup was moved.",
        structured_facts={"item_id": "cup"},
    )
    absent = ObserverPresence(character_id=uuid4())
    assert build_observation_for_observer(event, absent) is None
    assert build_observations(event, [absent]) == ()
