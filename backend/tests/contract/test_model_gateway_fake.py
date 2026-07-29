"""Contract tests for fake model gateway adapter (S0-MODEL-002)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    ModelMessage,
    ProviderRoutingOptions,
    SamplingOptions,
    TextGenerationRequest,
)
from fictional_world.infrastructure.model_gateway.fake import (
    FakeModelGatewayAdapter,
    FakeScriptKind,
)


class OkSchema(BaseModel):
    ok: bool = Field(...)


def _text_request(*, request_id: str, role: str = "character_decision") -> TextGenerationRequest:
    return TextGenerationRequest(
        request_id=request_id,
        role=role,
        model_profile_id="stage0-character-decision-v1",
        messages=(ModelMessage(role="user", content="hello"),),
        output_schema=OkSchema,
        sampling=SamplingOptions(temperature=0.2, top_p=0.9, max_output_tokens=100),
        routing=ProviderRoutingOptions(),
        metadata={},
    )


@pytest.mark.contract
@pytest.mark.model_fake
@pytest.mark.asyncio
async def test_fake_generate_valid() -> None:
    gateway = FakeModelGatewayAdapter(valid_payload='{"ok": true}')
    result = await gateway.generate(_text_request(request_id="r-ok"))
    assert result.parsed is not None
    assert result.parsed.model_dump() == {"ok": True}
    assert result.provider_name == "fake"


@pytest.mark.contract
@pytest.mark.model_fake
@pytest.mark.asyncio
async def test_fake_generate_malformed_and_schema() -> None:
    gateway = FakeModelGatewayAdapter()
    gateway.script(key="bad", kind=FakeScriptKind.MALFORMED_JSON)
    with pytest.raises(ModelGatewayError) as malformed:
        await gateway.generate(_text_request(request_id="bad"))
    assert malformed.value.code is ModelGatewayErrorCode.MALFORMED_RESPONSE

    gateway.script(key="schema", kind=FakeScriptKind.SCHEMA_INVALID)
    with pytest.raises(ModelGatewayError) as schema_err:
        await gateway.generate(_text_request(request_id="schema"))
    assert schema_err.value.code is ModelGatewayErrorCode.SCHEMA_VALIDATION_ERROR


@pytest.mark.contract
@pytest.mark.model_fake
@pytest.mark.asyncio
async def test_fake_generate_429() -> None:
    gateway = FakeModelGatewayAdapter()
    gateway.script(key="rl", kind=FakeScriptKind.RATE_LIMITED)
    with pytest.raises(ModelGatewayError) as err:
        await gateway.generate(_text_request(request_id="rl"))
    assert err.value.code is ModelGatewayErrorCode.RATE_LIMIT_ERROR
    assert err.value.retry_after_seconds == 1.0


@pytest.mark.contract
@pytest.mark.model_fake
@pytest.mark.asyncio
async def test_fake_embed_dimension_mismatch() -> None:
    gateway = FakeModelGatewayAdapter(embed_dimensions=2048)
    gateway.script(key="emb", kind=FakeScriptKind.EMBED_DIM_MISMATCH)
    with pytest.raises(ModelGatewayError) as err:
        await gateway.embed(
            EmbeddingRequest(
                request_id="emb",
                model_profile_id="stage0-embedding-v1",
                texts=("passage: hello",),
                input_type="passage",
                dimensions=2048,
                metadata={},
            )
        )
    assert err.value.code is ModelGatewayErrorCode.EMBEDDING_DIMENSION_ERROR
