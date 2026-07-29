"""WorldOrchestrator protocol and Stage 0 result types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class PauseMode(StrEnum):
    AFTER_SAFE_BOUNDARY = "after_safe_boundary"
    IMMEDIATE = "immediate"


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    world_id: UUID
    active_phase_id: UUID | None
    tasks_created: int
    phase_completed: bool
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PhaseAdvanceResult:
    phase_run_id: UUID
    absolute_phase_index: int
    phase_name: str
    already_completed: bool
    snapshot_id: UUID | None
    event_ids: tuple[UUID, ...]


class WorldOrchestrator(Protocol):
    async def start_world(self, world_id: UUID) -> None: ...

    async def request_phase_advance(self, world_id: UUID) -> PhaseAdvanceResult: ...

    async def pause_world(self, world_id: UUID, mode: PauseMode) -> None: ...

    async def resume_world(self, world_id: UUID) -> PhaseAdvanceResult | None: ...

    async def reconcile(self, world_id: UUID) -> ReconciliationReport: ...
