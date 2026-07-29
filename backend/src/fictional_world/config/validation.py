"""Startup validation for AppSettings (handbook ``19`` §15.3)."""

from __future__ import annotations

from fictional_world.config.settings import AppSettings

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
EXPECTED_EMBEDDING_DIMENSIONS = 2048


class SettingsValidationError(ValueError):
    """Raised when settings fail startup safety checks."""


def validate_settings(settings: AppSettings) -> None:
    """Fail fast on unsafe or incompatible configuration."""

    errors: list[str] = []

    if (
        settings.api.bind_host not in LOOPBACK_HOSTS
        and not settings.auth.enabled
        and not settings.auth.allow_insecure_public_bind
    ):
        errors.append(
            "unsafe public bind: APP bind_host is not loopback while auth is disabled "
            "(set auth.enabled=true or auth.allow_insecure_public_bind=true)"
        )

    if settings.model_gateway.embeddings_enabled or settings.features.long_term_memory:
        dims = settings.memory.embedding_dimensions
        expected = settings.model_gateway.expected_embedding_dimensions
        if dims != EXPECTED_EMBEDDING_DIMENSIONS:
            errors.append(
                f"embedding dimension mismatch: memory.embedding_dimensions={dims} "
                f"(schema expects {EXPECTED_EMBEDDING_DIMENSIONS})"
            )
        if expected != EXPECTED_EMBEDDING_DIMENSIONS:
            errors.append(
                f"embedding dimension mismatch: model_gateway.expected_embedding_dimensions="
                f"{expected} (schema expects {EXPECTED_EMBEDDING_DIMENSIONS})"
            )
        if dims != expected:
            errors.append(
                f"embedding dimension mismatch between memory ({dims}) and gateway ({expected})"
            )

    if settings.model_gateway.provider_mode == "openrouter" and not settings.openrouter.api_key:
        errors.append("OPENROUTER_API_KEY required when model_gateway.provider_mode=openrouter")

    if settings.features.temporal and settings.environment == "production":
        # Temporal remains Stage 4; Stage 0 profile must keep it off.
        errors.append("features.temporal must remain false until Stage 4")

    if errors:
        raise SettingsValidationError("; ".join(errors))
