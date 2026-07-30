"""Unit tests for Stage 4 model capability registry."""

from __future__ import annotations

import pytest

from fictional_world.application.models.capability_registry import (
    EndpointHealth,
    EndpointProviderKind,
    LoadedState,
    ModelCapabilityRegistry,
    ModelEndpointCapability,
    PrivacyPolicy,
)
from fictional_world.application.models.roles import ModelRole


def _endpoint(
    *,
    endpoint_id: str = "halo-a-text-1",
    roles: tuple[ModelRole, ...] = (ModelRole.CHARACTER_DECISION,),
    health: EndpointHealth = "healthy",
    loaded_state: LoadedState = "loaded",
    privacy_policy: PrivacyPolicy = "local_private",
    context_limit: int = 32768,
) -> ModelEndpointCapability:
    return ModelEndpointCapability(
        endpoint_id=endpoint_id,
        host_id="strix-halo-a",
        provider_kind=EndpointProviderKind.LOCAL_OPENAI_COMPAT,
        base_url="http://strix-halo-a:8000",
        model_id="local-gguf",
        model_hash="sha256:demo",
        roles=roles,
        context_limit=context_limit,
        structured_output_mode="JSON_OBJECT_PROMPTED",
        quantization="Q5_K_M",
        max_concurrency=4,
        health=health,
        loaded_state=loaded_state,
        software_versions=(("llamacpp", "b1"),),
        privacy_policy=privacy_policy,
        cost_class="local_gpu",
    )


@pytest.mark.unit
def test_registry_requires_explicit_roles() -> None:
    registry = ModelCapabilityRegistry()
    with pytest.raises(ValueError, match="advertise"):
        registry.upsert(
            ModelEndpointCapability(
                endpoint_id="empty",
                host_id="strix-halo-a",
                provider_kind=EndpointProviderKind.LOCAL_OPENAI_COMPAT,
                base_url="http://strix-halo-a:8000",
                model_id="x",
                model_hash=None,
                roles=(),
                context_limit=8192,
                structured_output_mode="JSON_OBJECT_PROMPTED",
                quantization=None,
                max_concurrency=1,
                health="healthy",
                loaded_state="loaded",
                software_versions=(),
                privacy_policy="local_private",
                cost_class="local_gpu",
            )
        )


@pytest.mark.unit
def test_registry_filters_by_role_health_and_privacy() -> None:
    registry = ModelCapabilityRegistry()
    registry.upsert(_endpoint(endpoint_id="a-ok"))
    registry.upsert(_endpoint(endpoint_id="a-unhealthy", health="unhealthy"))
    registry.upsert(
        _endpoint(
            endpoint_id="b-reaction",
            roles=(ModelRole.CHARACTER_REACTION,),
        )
    )
    registry.upsert(
        _endpoint(
            endpoint_id="openrouter-emergency",
            privacy_policy="allow_openrouter_emergency",
        )
    )

    decisions = registry.endpoints_for_role(ModelRole.CHARACTER_DECISION)
    assert [ep.endpoint_id for ep in decisions] == ["a-ok", "openrouter-emergency"]

    private = registry.endpoints_for_role(
        ModelRole.CHARACTER_DECISION,
        privacy_policy="local_private",
    )
    assert [ep.endpoint_id for ep in private] == ["a-ok"]

    emergency = registry.endpoints_for_role(
        ModelRole.CHARACTER_DECISION,
        privacy_policy="allow_openrouter_emergency",
    )
    assert [ep.endpoint_id for ep in emergency] == ["openrouter-emergency"]

    reactions = registry.endpoints_for_role(ModelRole.CHARACTER_REACTION)
    assert [ep.endpoint_id for ep in reactions] == ["b-reaction"]


@pytest.mark.unit
def test_mark_health_updates_probe_timestamp() -> None:
    registry = ModelCapabilityRegistry()
    registry.upsert(_endpoint())
    updated = registry.mark_health("halo-a-text-1", health="degraded", queue_depth=3)
    assert updated.health == "degraded"
    assert updated.queue_depth == 3
    assert updated.last_probe_at is not None
