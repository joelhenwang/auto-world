"""Reusable Stage 0 test fakes and helpers."""

from fictional_world.testing.fake_clock import FakeClock
from fictional_world.testing.fake_model import (
    FakeEmbedRequest,
    FakeEmbedResult,
    FakeModelGateway,
    FakeResponseKind,
    FakeTextRequest,
    FakeTextResult,
    ModelGatewayPort,
)
from fictional_world.testing.network import block_network
from fictional_world.testing.seeded_random import SeededRandom
from fictional_world.testing.stage1_model import Stage1FakeModelGateway

__all__ = [
    "FakeClock",
    "FakeEmbedRequest",
    "FakeEmbedResult",
    "FakeModelGateway",
    "FakeResponseKind",
    "FakeTextRequest",
    "FakeTextResult",
    "ModelGatewayPort",
    "SeededRandom",
    "Stage1FakeModelGateway",
    "block_network",
]
