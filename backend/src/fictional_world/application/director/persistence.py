"""Director bookkeeping persistence via UnitOfWork repositories.

These helpers upsert ``hook`` and append ``narrative_metric`` rows only.
They do **not** commit ``world_event`` rows or apply effect commands — that
remains the resolver / EventCommitService boundary (see package docstring).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from fictional_world.domain.continuity.persistence import (
    HookPersistenceRecord,
    NarrativeMetricPersistenceRecord,
)


class HookUpsertPorts(Protocol):
    async def get_by_key(self, world_id: UUID, hook_key: str) -> HookPersistenceRecord | None: ...

    async def insert(self, hook: HookPersistenceRecord) -> HookPersistenceRecord: ...

    async def update(self, hook: HookPersistenceRecord) -> HookPersistenceRecord: ...


class NarrativeMetricInsertPorts(Protocol):
    async def insert(
        self, metric: NarrativeMetricPersistenceRecord
    ) -> NarrativeMetricPersistenceRecord: ...


class DirectorPersistencePorts(Protocol):
    """Minimal UoW surface used by Director bookkeeping helpers."""

    hooks: HookUpsertPorts
    narrative_metrics: NarrativeMetricInsertPorts


async def upsert_hook(
    uow: DirectorPersistencePorts, hook: HookPersistenceRecord
) -> HookPersistenceRecord:
    """Insert or update a hook by ``(world_id, hook_key)``.

    Increments ``version`` on update. Does not create world events.
    """
    existing = await uow.hooks.get_by_key(hook.world_id, hook.hook_key)
    if existing is None:
        return await uow.hooks.insert(hook)
    updated = hook.model_copy(
        update={
            "id": existing.id,
            "version": existing.version + 1,
            "created_at": existing.created_at,
        }
    )
    return await uow.hooks.update(updated)


async def record_narrative_metric(
    uow: DirectorPersistencePorts,
    *,
    world_id: UUID,
    metric_key: str,
    metric_value: Decimal | float | int,
    window_start_phase: int,
    window_end_phase: int,
    payload: dict[str, object] | None = None,
    metric_id: UUID | None = None,
) -> NarrativeMetricPersistenceRecord:
    """Append a narrative metric sample (Director trigger / pacing telemetry)."""
    record = NarrativeMetricPersistenceRecord(
        id=metric_id or uuid4(),
        world_id=world_id,
        metric_key=metric_key,
        metric_value=Decimal(str(metric_value)),
        window_start_phase=window_start_phase,
        window_end_phase=window_end_phase,
        payload=dict(payload or {}),
    )
    return await uow.narrative_metrics.insert(record)
