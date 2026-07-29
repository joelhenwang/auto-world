"""Model profile registry tests (S0-MODEL-001)."""

from __future__ import annotations

import pytest

from fictional_world.application.models import (
    ModelProfileRegistry,
    ModelRole,
    sampling_for_role,
)
from fictional_world.application.models.profiles import ModelProfileError
from fictional_world.config import settings_from_profile


@pytest.mark.unit
def test_stage0_profiles_load_and_select() -> None:
    settings = settings_from_profile("stage0")
    registry = ModelProfileRegistry.from_settings(settings)
    profile = registry.select(ModelRole.CHARACTER_DECISION)
    assert profile.enabled
    assert profile.profile_id != "default"
    embed = registry.select(ModelRole.EMBEDDING)
    assert embed.embedding_dimensions == 2048
    registry.validate(expected_embedding_dimensions=2048)


@pytest.mark.unit
def test_sampling_defaults() -> None:
    samp = sampling_for_role(ModelRole.SEMANTIC_VALIDATOR)
    assert samp.temperature == 0.10
    assert samp.max_output_tokens == 700


@pytest.mark.unit
def test_missing_role_raises() -> None:
    settings = settings_from_profile("stage0")
    registry = ModelProfileRegistry.from_settings(settings)
    # director exists in defaults only when using _default_profiles; toml may omit it
    # Ensure get unknown fails:
    with pytest.raises(ModelProfileError):
        registry.get("no-such-profile")
