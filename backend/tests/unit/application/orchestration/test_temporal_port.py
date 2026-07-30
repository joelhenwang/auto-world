"""S4-ORCH-002: Temporal port exists and documents Stage 4 deferral."""

from __future__ import annotations

from uuid import uuid4

import pytest

from fictional_world.application.orchestration.protocol import PauseMode
from fictional_world.application.orchestration.temporal_port import (
    TEMPORAL_ADOPTION_STATUS,
    TEMPORAL_DEFER_REASON,
    NoopTemporalOrchestrator,
    TemporalDeferredError,
    TemporalOrchestratorPort,
)


@pytest.mark.unit
def test_noop_temporal_port_documents_deferral() -> None:
    """Noop adapter exists, reports deferred adoption, and cites ADR-0003."""

    port: TemporalOrchestratorPort = NoopTemporalOrchestrator()

    assert TEMPORAL_ADOPTION_STATUS == "deferred"
    assert port.adoption_status == "deferred"
    assert port.defer_reason is not None
    assert "ADR-0003" in port.defer_reason
    assert "PostgreSQL" in port.defer_reason
    assert "deferred" in TEMPORAL_DEFER_REASON.lower()
    assert "Temporal" in TEMPORAL_DEFER_REASON


@pytest.mark.unit
@pytest.mark.asyncio
async def test_noop_temporal_port_rejects_live_orchestration() -> None:
    """Deferred noop must not silently act as a live Temporal orchestrator."""

    port = NoopTemporalOrchestrator()
    world_id = uuid4()

    with pytest.raises(TemporalDeferredError, match="ADR-0003"):
        await port.start_world(world_id)

    with pytest.raises(TemporalDeferredError, match="ADR-0003"):
        await port.request_phase_advance(world_id)

    with pytest.raises(TemporalDeferredError, match="ADR-0003"):
        await port.pause_world(world_id, PauseMode.AFTER_SAFE_BOUNDARY)

    with pytest.raises(TemporalDeferredError, match="ADR-0003"):
        await port.resume_world(world_id)

    with pytest.raises(TemporalDeferredError, match="ADR-0003"):
        await port.reconcile(world_id)
