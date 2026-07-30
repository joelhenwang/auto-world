"""Unit tests for visual prompt compiler (S4-IMG-002)."""

from __future__ import annotations

import uuid

import pytest

from fictional_world.application.images.prompt_compiler import (
    ParticipantSpec,
    ScenePromptInput,
    compile_prompt,
)


def _make_input(**kwargs: object) -> ScenePromptInput:
    base: dict[str, object] = {
        "world_id": uuid.uuid4(),
        "source_event_id": uuid.uuid4(),
        "source_scene_id": uuid.uuid4(),
        "asset_class": "EVENT_CG",
        "location_name": "Embervale Tavern",
        "location_notes": "firelit interior",
        "time_of_day": "evening",
        "weather": "clear",
    }
    base.update(kwargs)
    return ScenePromptInput(**base)  # type: ignore[arg-type]


@pytest.mark.unit
def test_compile_returns_positive_and_negative() -> None:
    spec = compile_prompt(_make_input())
    assert "positive_prompt" in spec
    assert "negative_prompt" in spec
    assert isinstance(spec["positive_prompt"], str)
    assert isinstance(spec["negative_prompt"], str)


@pytest.mark.unit
def test_compile_includes_location() -> None:
    spec = compile_prompt(_make_input(location_name="Dragon Keep"))
    assert "Dragon Keep" in spec["positive_prompt"]


@pytest.mark.unit
def test_compile_includes_participant_name() -> None:
    participant = ParticipantSpec(
        entity_id=uuid.uuid4(),
        name="Alaric",
        role="primary",
        expression="determined",
    )
    spec = compile_prompt(_make_input(participants=[participant]))
    assert "Alaric" in spec["positive_prompt"]


@pytest.mark.unit
def test_compile_includes_prohibited_in_negative() -> None:
    spec = compile_prompt(_make_input(prohibited_additions=["extra characters"]))
    assert "extra characters" in spec["negative_prompt"]


@pytest.mark.unit
def test_compile_provenance_contains_world_id() -> None:
    world_id = uuid.uuid4()
    spec = compile_prompt(_make_input(world_id=world_id))
    assert str(world_id) in spec["provenance"]["world_id"]


@pytest.mark.unit
def test_compile_negative_contains_defaults() -> None:
    spec = compile_prompt(_make_input())
    assert "low quality" in spec["negative_prompt"]


@pytest.mark.unit
def test_compile_includes_action_outcome() -> None:
    spec = compile_prompt(_make_input(action_outcome="sword raised in victory"))
    assert "sword raised in victory" in spec["positive_prompt"]


@pytest.mark.unit
def test_compile_source_ids_in_spec() -> None:
    event_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    spec = compile_prompt(_make_input(source_event_id=event_id, source_scene_id=scene_id))
    assert str(event_id) == spec["source_event_id"]
    assert str(scene_id) == spec["source_scene_id"]
