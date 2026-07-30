"""Unit tests for object-storage prefix policy (S4-STORAGE-001)."""

from __future__ import annotations

import uuid

import pytest

from fictional_world.application.images.prefix import (
    character_reference_key,
    event_image_key,
    event_image_prefix,
    location_reference_key,
    workflow_key,
)


@pytest.mark.unit
def test_event_image_key_format() -> None:
    world = uuid.uuid4()
    event = uuid.uuid4()
    job = uuid.uuid4()
    asset = uuid.uuid4()
    key = event_image_key(world, event, job, asset)
    assert key.startswith(f"worlds/{world}/events/{event}/images/{job}/")
    assert key.endswith(".webp")


@pytest.mark.unit
def test_event_image_prefix() -> None:
    world = uuid.uuid4()
    event = uuid.uuid4()
    job = uuid.uuid4()
    prefix = event_image_prefix(world, event, job)
    assert str(world) in prefix
    assert str(event) in prefix
    assert str(job) in prefix


@pytest.mark.unit
def test_character_reference_key() -> None:
    world = uuid.uuid4()
    char = uuid.uuid4()
    asset = uuid.uuid4()
    key = character_reference_key(world, char, asset)
    assert f"worlds/{world}/references/characters/{char}/" in key


@pytest.mark.unit
def test_location_reference_key() -> None:
    world = uuid.uuid4()
    loc = uuid.uuid4()
    asset = uuid.uuid4()
    key = location_reference_key(world, loc, asset)
    assert f"worlds/{world}/references/locations/{loc}/" in key


@pytest.mark.unit
def test_workflow_key() -> None:
    key = workflow_key("stub_v1", "stub_v1.json")
    assert key == "workflows/comfyui/stub_v1/stub_v1.json"
