"""Fault tests for health-aware routing (S4-MODEL-002)."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from fictional_world.application.models.capability_registry import (
    EndpointHealth,
    EndpointProviderKind,
    ModelCapabilityRegistry,
    ModelEndpointCapability,
)
from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    ModelMessage,
    ProviderRoutingOptions,
    SamplingOptions,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.application.models.roles import ModelRole
from fictional_world.application.models.routing import HealthAwareModelGateway, spread_replicas
from fictional_world.infrastructure.model_gateway.capabilities import CapabilityMode


def _ep(
    endpoint_id: str,
    *,
    host_id: str = "strix-halo-a",
    health: EndpointHealth = "healthy",
    max_concurrency: int = 2,
    context_limit: int = 32768,
) -> ModelEndpointCapability:
    return ModelEndpointCapability(
        endpoint_id=endpoint_id,
        host_id=host_id,
        provider_kind=EndpointProviderKind.LOCAL_OPENAI_COMPAT,
        base_url=f"http://{host_id}:8000",
        model_id="local-gguf",
        model_hash=None,
        roles=(ModelRole.CHARACTER_DECISION,),
        context_limit=context_limit,
        structured_output_mode="JSON_OBJECT_PROMPTED",
        quantization="Q5_K_M",
        max_concurrency=max_concurrency,
        health=health,
        loaded_state="loaded",
        software_versions=(),
        privacy_policy="local_private",
        cost_class="local_gpu",
    )


@dataclass
class _FakeTextClient:
    endpoint: ModelEndpointCapability
    fail_codes: list[ModelGatewayErrorCode] = field(default_factory=list)
    calls: int = 0

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        self.calls += 1
        if self.fail_codes:
            code = self.fail_codes.pop(0)
            raise ModelGatewayError(code, "injected", request_id=request.request_id, retryable=True)
        return TextGenerationResult(
            provider_request_id=request.request_id,
            resolved_model=self.endpoint.model_id,
            provider_name=f"fake:{self.endpoint.endpoint_id}",
            raw_text='{"ok": true}',
            parsed=None,
            input_tokens=1,
            output_tokens=1,
            finish_reason="stop",
            capability_mode=CapabilityMode.JSON_OBJECT_PROMPTED.value,
            latency_ms=1,
        )


def _request(request_id: str, *, privacy: str = "local_private") -> TextGenerationRequest:
    return TextGenerationRequest(
        request_id=request_id,
        role=ModelRole.CHARACTER_DECISION.value,
        model_profile_id="local-char-v1",
        messages=(ModelMessage(role="user", content="act"),),
        output_schema=None,
        sampling=SamplingOptions(temperature=0.2, top_p=0.9, max_output_tokens=32),
        routing=ProviderRoutingOptions(),
        metadata={"privacy_policy": privacy},
    )


@pytest.mark.fault
@pytest.mark.asyncio
async def test_failover_on_retryable_endpoint_death() -> None:
    registry = ModelCapabilityRegistry()
    a = _ep("halo-a")
    b = _ep("halo-b", host_id="strix-halo-b")
    registry.upsert(a)
    registry.upsert(b)
    clients = {
        "halo-a": _FakeTextClient(endpoint=a, fail_codes=[ModelGatewayErrorCode.NETWORK_ERROR]),
        "halo-b": _FakeTextClient(endpoint=b),
    }
    gateway = HealthAwareModelGateway(registry=registry, text_clients=clients)
    result = await gateway.generate(_request("r1"))
    assert result.provider_name == "fake:halo-b"
    assert clients["halo-a"].calls == 1
    assert clients["halo-b"].calls == 1


@pytest.mark.fault
@pytest.mark.asyncio
async def test_stale_unhealthy_endpoint_skipped() -> None:
    registry = ModelCapabilityRegistry()
    dead = _ep("halo-a", health="unhealthy")
    live = _ep("halo-b", host_id="strix-halo-b")
    registry.upsert(dead)
    registry.upsert(live)
    clients = {
        "halo-a": _FakeTextClient(endpoint=dead),
        "halo-b": _FakeTextClient(endpoint=live),
    }
    gateway = HealthAwareModelGateway(registry=registry, text_clients=clients)
    result = await gateway.generate(_request("r2"))
    assert result.provider_name == "fake:halo-b"
    assert clients["halo-a"].calls == 0


@pytest.mark.fault
@pytest.mark.asyncio
async def test_incompatible_context_filtered() -> None:
    registry = ModelCapabilityRegistry()
    small = _ep("small", context_limit=4096)
    registry.upsert(small)
    gateway = HealthAwareModelGateway(
        registry=registry,
        text_clients={"small": _FakeTextClient(endpoint=small)},
    )
    req = _request("r3")
    req = TextGenerationRequest(
        request_id=req.request_id,
        role=req.role,
        model_profile_id=req.model_profile_id,
        messages=req.messages,
        output_schema=None,
        sampling=req.sampling,
        routing=req.routing,
        metadata={"privacy_policy": "local_private", "min_context_limit": "20000"},
    )
    with pytest.raises(ModelGatewayError) as exc:
        await gateway.generate(req)
    assert exc.value.code is ModelGatewayErrorCode.MODEL_NOT_AVAILABLE


@pytest.mark.fault
@pytest.mark.asyncio
async def test_double_completion_rejected() -> None:
    registry = ModelCapabilityRegistry()
    ep = _ep("halo-a")
    registry.upsert(ep)
    gateway = HealthAwareModelGateway(
        registry=registry,
        text_clients={"halo-a": _FakeTextClient(endpoint=ep)},
    )
    await gateway.generate(_request("dup"))
    with pytest.raises(ModelGatewayError) as exc:
        await gateway.generate(_request("dup"))
    assert "duplicate" in exc.value.message


@pytest.mark.unit
def test_spread_replicas_across_hosts() -> None:
    registry = ModelCapabilityRegistry()
    registry.upsert(_ep("halo-a"))
    registry.upsert(_ep("halo-b", host_id="strix-halo-b"))
    chosen = spread_replicas(registry, role=ModelRole.CHARACTER_DECISION, count=4)
    assert len(chosen) == 4
    assert {ep.endpoint_id for ep in chosen} == {"halo-a", "halo-b"}
