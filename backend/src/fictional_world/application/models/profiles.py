"""Model profile registry (handbook ``12`` §5)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fictional_world.application.models.roles import ModelRole
from fictional_world.application.models.sampling import DEFAULT_SAMPLING
from fictional_world.config.settings import AppSettings, repo_root

ProviderKind = Literal["fake", "openrouter", "local", "disabled"]


@dataclass(frozen=True, slots=True)
class ModelProfile:
    profile_id: str
    provider_kind: ProviderKind
    model_slug: str
    role: ModelRole
    enabled: bool
    context_limit: int
    application_input_limit: int
    max_output_tokens: int
    supports_json_schema: bool
    supports_tools: bool
    supports_seed: bool
    supports_streaming: bool
    supports_embeddings: bool
    embedding_dimensions: int | None
    sampling_profile_id: str
    privacy_class: str
    capability_probe_version: str


class ModelProfileError(ValueError):
    """Invalid or missing model profile configuration."""


def _default_profiles(settings: AppSettings) -> dict[str, ModelProfile]:
    text_slug = settings.openrouter.text_model
    embed_slug = settings.openrouter.embedding_model
    dims = settings.model_gateway.expected_embedding_dimensions
    provider: ProviderKind = (
        "fake"
        if settings.model_gateway.provider_mode == "fake"
        else settings.model_gateway.provider_mode
    )
    profiles: dict[str, ModelProfile] = {}
    for role, sampling in DEFAULT_SAMPLING.items():
        pid = f"stage0-{role.value}-v1"
        profiles[pid] = ModelProfile(
            profile_id=pid,
            provider_kind=provider,
            model_slug=text_slug,
            role=role,
            enabled=True,
            context_limit=262_144,
            application_input_limit=32_768,
            max_output_tokens=sampling.max_output_tokens,
            supports_json_schema=True,
            supports_tools=False,
            supports_seed=True,
            supports_streaming=False,
            supports_embeddings=False,
            embedding_dimensions=None,
            sampling_profile_id=sampling.profile_id,
            privacy_class="synthetic_fiction",
            capability_probe_version="stage0-1",
        )
    embed_id = "stage0-embedding-v1"
    profiles[embed_id] = ModelProfile(
        profile_id=embed_id,
        provider_kind=provider,
        model_slug=embed_slug,
        role=ModelRole.EMBEDDING,
        enabled=settings.model_gateway.embeddings_enabled
        or settings.model_gateway.provider_mode == "fake",
        context_limit=8192,
        application_input_limit=8192,
        max_output_tokens=0,
        supports_json_schema=False,
        supports_tools=False,
        supports_seed=False,
        supports_streaming=False,
        supports_embeddings=True,
        embedding_dimensions=dims,
        sampling_profile_id="samp-embedding-none",
        privacy_class="synthetic_fiction",
        capability_probe_version="stage0-1",
    )
    return profiles


def load_profiles_from_toml(path: Path) -> dict[str, ModelProfile]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    profiles: dict[str, ModelProfile] = {}
    for item in raw.get("profiles", []):
        role = ModelRole(str(item["role"]))
        pid = str(item["profile_id"])
        if pid == "default":
            raise ModelProfileError("mutable profile_id 'default' is forbidden")
        profiles[pid] = ModelProfile(
            profile_id=pid,
            provider_kind=item.get("provider_kind", "fake"),
            model_slug=str(item["model_slug"]),
            role=role,
            enabled=bool(item.get("enabled", True)),
            context_limit=int(item.get("context_limit", 32_768)),
            application_input_limit=int(item.get("application_input_limit", 32_768)),
            max_output_tokens=int(item.get("max_output_tokens", 1200)),
            supports_json_schema=bool(item.get("supports_json_schema", True)),
            supports_tools=bool(item.get("supports_tools", False)),
            supports_seed=bool(item.get("supports_seed", True)),
            supports_streaming=bool(item.get("supports_streaming", False)),
            supports_embeddings=bool(item.get("supports_embeddings", False)),
            embedding_dimensions=item.get("embedding_dimensions"),
            sampling_profile_id=str(item.get("sampling_profile_id", f"samp-{role.value}-v1")),
            privacy_class=str(item.get("privacy_class", "synthetic_fiction")),
            capability_probe_version=str(item.get("capability_probe_version", "stage0-1")),
        )
    return profiles


class ModelProfileRegistry:
    def __init__(self, profiles: dict[str, ModelProfile]) -> None:
        if not profiles:
            raise ModelProfileError("profile registry is empty")
        self._profiles = dict(profiles)

    @classmethod
    def from_settings(cls, settings: AppSettings) -> ModelProfileRegistry:
        path = repo_root() / "config" / "model_profiles" / "stage0.toml"
        if path.is_file():
            return cls(load_profiles_from_toml(path))
        return cls(_default_profiles(settings))

    def get(self, profile_id: str) -> ModelProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ModelProfileError(f"unknown profile_id: {profile_id}") from exc

    def select(self, role: ModelRole, *, require_enabled: bool = True) -> ModelProfile:
        matches = [p for p in self._profiles.values() if p.role is role]
        if require_enabled:
            matches = [p for p in matches if p.enabled]
        if not matches:
            raise ModelProfileError(f"no enabled profile for role {role}")
        return matches[0]

    def validate(self, *, expected_embedding_dimensions: int = 2048) -> None:
        for profile in self._profiles.values():
            if (
                profile.supports_embeddings
                and profile.embedding_dimensions != expected_embedding_dimensions
            ):
                raise ModelProfileError(
                    f"profile {profile.profile_id} embedding_dimensions="
                    f"{profile.embedding_dimensions}, expected {expected_embedding_dimensions}"
                )
