"""Unit tests for FakeComfyUI adapter (S4-IMG-001)."""

from __future__ import annotations

import pytest

from fictional_world.infrastructure.comfyui.fake import FakeComfyUI
from fictional_world.infrastructure.comfyui.protocol import ImageExecutionRequest


def _req(key: str = "idem-key-1") -> ImageExecutionRequest:
    return ImageExecutionRequest(
        idempotency_key=key,
        workflow_version="stub_v1",
        positive_prompt="a test scene",
        negative_prompt="low quality",
        seed=42,
        width=832,
        height=1216,
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_returns_healthy() -> None:
    fake = FakeComfyUI()
    h = await fake.health()
    assert h.healthy is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_returns_unhealthy_when_flag_set() -> None:
    fake = FakeComfyUI()
    fake.healthy = False
    h = await fake.health()
    assert h.healthy is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_returns_prompt_id() -> None:
    fake = FakeComfyUI()
    req = _req()
    sub = await fake.submit(req)
    assert sub.external_prompt_id.startswith("fake-")
    assert fake.submitted_count() == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_idempotent_same_key() -> None:
    fake = FakeComfyUI()
    req = _req()
    s1 = await fake.submit(req)
    s2 = await fake.submit(req)
    assert s1.external_prompt_id == s2.external_prompt_id
    assert fake.submitted_count() == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_submit_raises_when_unavailable() -> None:
    fake = FakeComfyUI()
    fake.healthy = False
    with pytest.raises(RuntimeError, match="unavailable"):
        await fake.submit(_req())


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_status_running_then_succeeded() -> None:
    fake = FakeComfyUI()
    sub = await fake.submit(_req())
    s1 = await fake.get_status(sub.external_prompt_id)
    assert s1.status == "running"
    s2 = await fake.get_status(sub.external_prompt_id)
    assert s2.status == "succeeded"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cancel_marks_failed() -> None:
    fake = FakeComfyUI()
    sub = await fake.submit(_req())
    await fake.cancel(sub.external_prompt_id)
    assert fake.was_cancelled(sub.external_prompt_id)
    s = await fake.get_status(sub.external_prompt_id)
    assert s.status == "failed"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_outputs_returns_asset() -> None:
    fake = FakeComfyUI()
    sub = await fake.submit(_req())
    outputs = await fake.fetch_outputs(sub.external_prompt_id)
    assert len(outputs) == 1
    assert outputs[0].data[:4] == b"\x89PNG"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_outputs_empty_after_cancel() -> None:
    fake = FakeComfyUI()
    sub = await fake.submit(_req())
    await fake.cancel(sub.external_prompt_id)
    outputs = await fake.fetch_outputs(sub.external_prompt_id)
    assert len(outputs) == 0
