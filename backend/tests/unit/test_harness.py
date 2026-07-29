"""Harness self-tests (S0-QA-001)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from fictional_world.testing import (
    FakeClock,
    FakeEmbedRequest,
    FakeModelGateway,
    FakeResponseKind,
    FakeTextRequest,
    SeededRandom,
    block_network,
)


@pytest.mark.unit
def test_fake_clock_advances(fake_clock: FakeClock) -> None:
    start = fake_clock.now()
    later = fake_clock.advance(minutes=5)
    assert later > start
    fake_clock.set(datetime(2030, 1, 1, tzinfo=UTC))
    assert fake_clock.now().year == 2030


@pytest.mark.unit
def test_seeded_random_script(seeded_random: SeededRandom) -> None:
    assert seeded_random.random() == 0.1
    assert seeded_random.random() == 0.2
    assert seeded_random.random() == 0.3
    assert seeded_random.random() == 0.5  # fallback


@pytest.mark.unit
@pytest.mark.model_fake
@pytest.mark.asyncio
async def test_fake_model_gateway_scripts(fake_model_gateway: FakeModelGateway) -> None:
    fake_model_gateway.script(key="character", kind=FakeResponseKind.MALFORMED_JSON)
    result = await fake_model_gateway.generate_text(
        FakeTextRequest(role="character", request_id="r1", prompt="hi")
    )
    assert result.kind is FakeResponseKind.MALFORMED_JSON
    fake_model_gateway.script(key="emb-1", kind=FakeResponseKind.EMBED_DIM_MISMATCH)
    embed = await fake_model_gateway.embed(
        FakeEmbedRequest(request_id="emb-1", texts=("passage: hello",))
    )
    assert embed.kind is FakeResponseKind.EMBED_DIM_MISMATCH
    assert embed.dimensions != 2048
    assert len(fake_model_gateway.calls) == 2


@pytest.mark.unit
def test_block_network_raises() -> None:
    with block_network(), pytest.raises(RuntimeError, match="network disabled"):
        import socket

        socket.socket()


@pytest.mark.unit
def test_scenario_harness_skeleton_loads() -> None:
    from tools.scenario_harness import load_scenario, run_scenario_skeleton

    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample_scenario.toml"
    spec = load_scenario(fixture)
    assert spec.scenario_id == "stage0-harness-smoke-v1"
    result = run_scenario_skeleton(spec)
    assert result.scenario_id == spec.scenario_id
    assert result.passed is False
