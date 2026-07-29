"""MemoryConsolidationGraph — thin async wrapper around daily consolidation.

Returns derived summary/diary/day-run records only. Persistence is the caller's
responsibility; this graph never opens a UoW or commits domain state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from fictional_world.application.memory import (
    ConsolidatorCallable,
    DailyConsolidationResult,
    consolidate_day,
)
from fictional_world.domain.knowledge.persistence import (
    ObservationPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.memory.persistence import RecentMemoryRecord


@dataclass(frozen=True, slots=True)
class MemoryConsolidationGraphInput:
    """End-of-day consolidation authority for one world day."""

    world_id: UUID
    day_index: int
    character_ids: tuple[UUID, ...]
    observations: tuple[ObservationPersistenceRecord, ...] = ()
    recent_memories: tuple[RecentMemoryRecord, ...] = ()
    secret_access: tuple[SecretAccessPersistenceRecord, ...] = ()
    secret_catalog: Mapping[str, str] | None = None
    consolidator: ConsolidatorCallable | None = None
    prior: DailyConsolidationResult | None = None
    version_number: int = 1
    now: datetime | None = None


async def run_memory_consolidation_graph(
    graph_input: MemoryConsolidationGraphInput,
) -> DailyConsolidationResult:
    """Call ``consolidate_day`` without persisting. Async for orchestration symmetry."""

    return consolidate_day(
        world_id=graph_input.world_id,
        day_index=graph_input.day_index,
        character_ids=graph_input.character_ids,
        observations=graph_input.observations,
        recent_memories=graph_input.recent_memories,
        secret_access=graph_input.secret_access,
        secret_catalog=graph_input.secret_catalog,
        consolidator=graph_input.consolidator,
        prior=graph_input.prior,
        version_number=graph_input.version_number,
        now=graph_input.now,
    )


__all__ = [
    "MemoryConsolidationGraphInput",
    "run_memory_consolidation_graph",
]
