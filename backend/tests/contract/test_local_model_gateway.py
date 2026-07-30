"""Contract tests for local OpenAI-compatible gateway (offline MockTransport)."""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel

from fictional_world.application.models.capability_registry import (
    EndpointProviderKind,
    ModelEndpointCapability,
)
from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    ModelMessage,
    ProviderRoutingOptions,
    SamplingOptions,
    TextGenerationRequest,
)
from fictional_world.application.models.roles import ModelRole
from fictional_world.infrastructure.model_gateway.local import LocalOpenAICompatibleGateway


class _TinySchema(BaseModel):
    ok: bool


def _text_endpoint(
    *,
    roles: tuple[ModelRole, ...] = (ModelRole.CHARACTER_DECISION,),
) -> ModelEndpointCapability:
    return ModelEndpointCapability(
        endpoint_id="halo-a-text-1",
        host_id="strix-halo-a",
        provider_kind=EndpointProviderKind.LOCAL_OPENAI_COMPAT,
        base_url="http://local-test",
        model_id="local-gguf",
        model_hash="sha256:demo",
        roles=roles,
        context_limit=32768,
        structured_output_mode="JSON_OBJECT_PROMPTED",
        quantization="Q5_K_M",
        max_concurrency=4,
        health="healthy",
        loaded_state="loaded",
        software_versions=(("llamacpp", "b1"),),
        privacy_policy="local_private",
        cost_class="local_gpu",
        supports_embeddings=True,
        embedding_dimensions=8,
    )


@pytest.mark.contract
@pytest.mark.asyncio
async def test_local_gateway_generate_and_reject_unadvertised_role() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        body = {
            "id": "local-1",
            "model": "local-gguf",
            "choices": [{"message": {"content": '{"ok": true}'}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 3},
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://local-test")
    gateway = LocalOpenAICompatibleGateway(endpoint=_text_endpoint(), http_client=client)
    result = await gateway.generate(
        TextGenerationRequest(
            request_id="req-1",
            role=ModelRole.CHARACTER_DECISION.value,
            model_profile_id="local-char-v1",
            messages=(ModelMessage(role="user", content="hi"),),
            output_schema=_TinySchema,
            sampling=SamplingOptions(temperature=0.2, top_p=0.9, max_output_tokens=64),
            routing=ProviderRoutingOptions(),
            metadata={},
        )
    )
    assert result.parsed is not None
    assert result.provider_name == "local:halo-a-text-1"
    assert result.capability_mode == "JSON_OBJECT_PROMPTED"

    with pytest.raises(ModelGatewayError) as exc:
        await gateway.generate(
            TextGenerationRequest(
                request_id="req-2",
                role=ModelRole.RESOLVER.value,
                model_profile_id="local-char-v1",
                messages=(ModelMessage(role="user", content="hi"),),
                output_schema=None,
                sampling=SamplingOptions(temperature=0.2, top_p=0.9, max_output_tokens=64),
                routing=ProviderRoutingOptions(),
                metadata={},
            )
        )
    assert exc.value.code is ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR
    await gateway.aclose()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_local_gateway_embeddings() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        payload = json.loads(request.content.decode("utf-8"))
        assert payload["input"] == ["alpha", "beta"]
        return httpx.Response(
            200,
            json={
                "model": "local-gguf",
                "data": [
                    {"embedding": [0.1] * 8},
                    {"embedding": [0.2] * 8},
                ],
                "usage": {"prompt_tokens": 4},
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="http://local-test")
    gateway = LocalOpenAICompatibleGateway(endpoint=_text_endpoint(), http_client=client)
    result = await gateway.embed(
        EmbeddingRequest(
            request_id="emb-1",
            model_profile_id="local-embed-v1",
            texts=("alpha", "beta"),
            input_type="passage",
            dimensions=8,
            metadata={},
        )
    )
    assert result.dimensions == 8
    assert len(result.vectors) == 2
    await gateway.aclose()
