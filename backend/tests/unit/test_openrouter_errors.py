"""Unit tests for OpenRouter error mapping and live smoke marker."""

from __future__ import annotations

import os

import pytest

from fictional_world.application.models.errors import ModelGatewayErrorCode
from fictional_world.infrastructure.model_gateway.capabilities import (
    CapabilityMode,
    CapabilityProbeStub,
)
from fictional_world.infrastructure.model_gateway.errors import (
    map_http_error,
    map_openrouter_error_body,
)


@pytest.mark.unit
def test_map_http_429_and_402() -> None:
    rate = map_http_error(429, message="slow down", retry_after_seconds=2.5)
    assert rate.code is ModelGatewayErrorCode.RATE_LIMIT_ERROR
    assert rate.retryable is True
    assert rate.retry_after_seconds == 2.5
    credit = map_http_error(402, message="no credit")
    assert credit.code is ModelGatewayErrorCode.CREDIT_LIMIT_ERROR
    assert credit.retryable is False


@pytest.mark.unit
def test_map_openrouter_error_body() -> None:
    err = map_openrouter_error_body(
        401,
        {"error": {"message": "bad key", "code": "auth"}},
        request_id="req-1",
    )
    assert err.code is ModelGatewayErrorCode.AUTHENTICATION_ERROR
    assert err.provider_code == "auth"
    assert err.request_id == "req-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_capability_probe_stub() -> None:
    stub = CapabilityProbeStub(default_mode=CapabilityMode.NATIVE_BEST_EFFORT)
    text = await stub.probe_text_profile("stage0-character-decision-v1")
    assert text.mode is CapabilityMode.NATIVE_BEST_EFFORT
    embed = await stub.probe_embedding_profile("stage0-embedding-v1")
    assert embed.embedding_dimensions == 2048


@pytest.mark.openrouter_live
@pytest.mark.asyncio
async def test_openrouter_live_smoke_opt_in() -> None:
    """Opt-in smoke; skipped unless OPENROUTER_API_KEY is set and marker selected."""

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    # Import lazily so ordinary suites never construct a live client.
    import httpx

    from fictional_world.application.models.messages import (
        ModelMessage,
        ProviderRoutingOptions,
        SamplingOptions,
        TextGenerationRequest,
    )
    from fictional_world.application.models.profiles import ModelProfile
    from fictional_world.application.models.roles import ModelRole
    from fictional_world.infrastructure.model_gateway.openrouter import OpenRouterGateway

    profile = ModelProfile(
        profile_id="live-smoke-v1",
        provider_kind="openrouter",
        model_slug=os.environ.get(
            "OPENROUTER_TEXT_MODEL", "nvidia/nemotron-3-super-120b-a12b:free"
        ),
        role=ModelRole.CHARACTER_DECISION,
        enabled=True,
        context_limit=8192,
        application_input_limit=2048,
        max_output_tokens=64,
        supports_json_schema=False,
        supports_tools=False,
        supports_seed=False,
        supports_streaming=False,
        supports_embeddings=False,
        embedding_dimensions=None,
        sampling_profile_id="samp-live",
        privacy_class="synthetic_fiction",
        capability_probe_version="stage0-live",
    )
    gateway = OpenRouterGateway(
        api_key=api_key,
        profiles={profile.profile_id: profile},
        http_client=httpx.AsyncClient(timeout=60.0),
    )
    try:
        result = await gateway.generate(
            TextGenerationRequest(
                request_id="live-smoke-1",
                role=profile.role.value,
                model_profile_id=profile.profile_id,
                messages=(
                    ModelMessage(
                        role="user",
                        content='Reply with exactly: {"ok": true}',
                    ),
                ),
                output_schema=None,
                sampling=SamplingOptions(temperature=0.0, top_p=1.0, max_output_tokens=64),
                routing=ProviderRoutingOptions(require_parameters=False),
                metadata={"privacy": "synthetic"},
            )
        )
        assert result.raw_text
        assert result.provider_name == "openrouter"
    finally:
        await gateway.aclose()
