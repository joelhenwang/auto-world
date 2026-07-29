"""Settings and profile validation tests (S0-ENG-002)."""

from __future__ import annotations

import pytest

from fictional_world.config import (
    SettingsValidationError,
    settings_from_profile,
    validate_settings,
)
from fictional_world.config.settings import (
    ApiSettings,
    AppSettings,
    AuthSettings,
    MemorySettings,
    ModelGatewaySettings,
)


@pytest.mark.unit
def test_stage0_profile_loads_and_validates() -> None:
    settings = settings_from_profile("stage0")
    assert settings.profile == "stage0"
    assert settings.api.bind_host == "127.0.0.1"
    assert settings.memory.embedding_dimensions == 2048
    validate_settings(settings)


@pytest.mark.unit
def test_test_profile_loads() -> None:
    settings = settings_from_profile("test")
    assert settings.environment == "test"
    validate_settings(settings)


@pytest.mark.unit
def test_public_bind_without_auth_rejected() -> None:
    settings = AppSettings(
        api=ApiSettings(bind_host="0.0.0.0", bind_port=8000),  # noqa: S104 — intentional unsafe case
        auth=AuthSettings(enabled=False, allow_insecure_public_bind=False),
    )
    with pytest.raises(SettingsValidationError, match="unsafe public bind"):
        validate_settings(settings)


@pytest.mark.unit
def test_public_bind_allowed_with_override() -> None:
    settings = AppSettings(
        api=ApiSettings(bind_host="0.0.0.0", bind_port=8000),  # noqa: S104 — intentional unsafe case
        auth=AuthSettings(enabled=False, allow_insecure_public_bind=True),
    )
    validate_settings(settings)


@pytest.mark.unit
def test_embedding_dimension_mismatch_rejected() -> None:
    settings = AppSettings(
        model_gateway=ModelGatewaySettings(
            embeddings_enabled=True, expected_embedding_dimensions=2048
        ),
        memory=MemorySettings(embedding_dimensions=768, long_term_enabled=False),
    )
    with pytest.raises(SettingsValidationError, match="embedding dimension mismatch"):
        validate_settings(settings)
