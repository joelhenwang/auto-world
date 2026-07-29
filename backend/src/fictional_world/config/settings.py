"""Application settings groups (handbook ``19`` §15)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ApiSettings(_StrictModel):
    bind_host: str = "127.0.0.1"
    bind_port: int = Field(default=8000, ge=1, le=65535)


class DatabaseSettings(_StrictModel):
    host: str = "127.0.0.1"
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = "fictional_world"
    user: str = "fictional_world"
    password: str = "change-me-local"  # noqa: S105 — local placeholder only


class AuthSettings(_StrictModel):
    enabled: bool = False
    local_admin_password: str = ""
    allow_insecure_public_bind: bool = False


class ModelGatewaySettings(_StrictModel):
    provider_mode: Literal["fake", "openrouter", "disabled"] = "fake"
    embeddings_enabled: bool = False
    expected_embedding_dimensions: int = Field(default=2048, ge=1)


class OpenRouterSettings(_StrictModel):
    api_key: str = ""
    base_url: str = "https://openrouter.ai/api/v1"
    text_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    embedding_model: str = "nvidia/nemotron-3-embed-1b:free"
    live_test_max_requests: int = Field(default=3, ge=0)


class MemorySettings(_StrictModel):
    embedding_dimensions: int = Field(default=2048, ge=1)
    long_term_enabled: bool = False


class FeatureFlags(_StrictModel):
    director: bool = False
    long_term_memory: bool = False
    magic: bool = False
    combat: bool = False
    images: bool = False
    temporal: bool = False
    macro_simulation: bool = False


class ObservabilitySettings(_StrictModel):
    log_level: str = "INFO"
    otel_enabled: bool = False


class AppSettings(BaseSettings):
    """Layered application settings: defaults < profile < environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        frozen=True,
    )

    environment: Literal["development", "test", "staging", "production"] = "development"
    profile: str = Field(default="stage0", validation_alias="APP_PROFILE")
    api: ApiSettings = Field(default_factory=ApiSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    model_gateway: ModelGatewaySettings = Field(default_factory=ModelGatewaySettings)
    openrouter: OpenRouterSettings = Field(default_factory=OpenRouterSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    @field_validator("profile")
    @classmethod
    def _profile_nonempty(cls, value: str) -> str:
        if not value.strip():
            msg = "APP_PROFILE must be non-empty"
            raise ValueError(msg)
        return value.strip()


def repo_root() -> Path:
    """Return repository root (…/ containing pyproject.toml)."""

    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    msg = "could not locate repository root with pyproject.toml"
    raise RuntimeError(msg)
