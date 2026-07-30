"""Stage 3 thirty-day workflow ops mixed into DeterministicPhaseRunner."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from uuid import UUID, uuid4

from fictional_world.application.memory.monthly_reflection import (
    apply_forgetting_weights,
    build_monthly_chapter,
    build_reflection_run,
)
from fictional_world.application.orchestration.protocol import DayAdvanceResult
from fictional_world.application.orchestration.stage2_ops import STAGE2_CHARACTER_IDS
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.stage3.persistence import (
    MemoryPersistenceRecord,
    MonthRunPersistenceRecord,
)
from fictional_world.domain.time.calendar import PHASE_ORDER

_PHASES_PER_DAY = len(PHASE_ORDER)
DAYS_PER_MONTH = 30


@dataclass(frozen=True, slots=True)
class MonthFinalizeResult:
    world_id: UUID
    month_index: int
    month_run_id: UUID | None
    already_finalized: bool
    chapter_ids: tuple[UUID, ...]
    reflection_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class ThirtyDayRunResult:
    world_id: UUID
    day_results: tuple[DayAdvanceResult, ...]
    month_result: MonthFinalizeResult | None


def month_run_idempotency_key(world_id: UUID, month_index: int) -> str:
    return f"month-run:{world_id}:{month_index}"


def month_phase_bounds(month_index: int) -> tuple[int, int]:
    """Inclusive absolute phase range for a 30-day month (1-indexed month)."""

    start_day = (month_index - 1) * DAYS_PER_MONTH
    end_day = start_day + DAYS_PER_MONTH - 1
    start_phase = start_day * _PHASES_PER_DAY
    end_phase = (end_day + 1) * _PHASES_PER_DAY - 1
    return start_phase, end_phase


class Stage3PhaseOps:
    """Mixin: thirty-day + monthly barrier.

    Attribute stubs declared for basedpyright; concrete values live on
    ``DeterministicPhaseRunner`` / ``Stage2PhaseOps``.
    """

    _uow: UnitOfWork
    _stage2: bool

    def _stage2_error(self, message: str) -> DomainError:
        raise NotImplementedError

    async def run_day(self, world_id: UUID) -> DayAdvanceResult:
        raise NotImplementedError

    async def finalize_month(
        self,
        world_id: UUID,
        *,
        month_index: int = 1,
    ) -> MonthFinalizeResult:
        """Idempotent monthly barrier: month_run + chapters + reflections."""

        key = month_run_idempotency_key(world_id, month_index)
        existing = await self._uow.month_runs.get_by_world_month(world_id, month_index)
        if existing is not None and existing.status == "completed":
            return MonthFinalizeResult(
                world_id=world_id,
                month_index=month_index,
                month_run_id=existing.id,
                already_finalized=True,
                chapter_ids=(),
                reflection_ids=(),
            )

        start_phase, end_phase = month_phase_bounds(month_index)
        start_day = (month_index - 1) * DAYS_PER_MONTH
        end_day = start_day + DAYS_PER_MONTH - 1

        chapter_ids: list[UUID] = []
        reflection_ids: list[UUID] = []
        for character_id in STAGE2_CHARACTER_IDS:
            recent = await self._uow.recent_memories.list_for_owner(
                character_id,
                world_id=world_id,
                limit=5_000,
            )
            long_term: list[MemoryPersistenceRecord] = []
            for item in recent:
                if not (start_phase <= item.created_phase_index <= end_phase):
                    continue
                if item.world_id != world_id:
                    continue
                record = MemoryPersistenceRecord(
                    id=item.id,
                    world_id=item.world_id,
                    owner_character_id=item.owner_character_id,
                    memory_type=item.memory_type,
                    content=item.content,
                    salience=item.salience,
                    confidence=item.confidence,
                    emotional_weight=item.emotional_weight,
                    visibility=item.visibility,
                    occurred_phase_index=item.occurred_phase_index,
                    created_phase_index=item.created_phase_index,
                    last_recalled_phase_index=item.last_recalled_phase_index,
                    recall_count=item.recall_count,
                    decay_score=item.decay_score,
                    status=item.status,
                    content_hash=item.content_hash,
                    summary_version=item.summary_version,
                    source_event_id=item.source_event_id,
                )
                existing_mem = await self._uow.long_term_memories.get(record.id)
                if existing_mem is None:
                    with contextlib.suppress(Exception):
                        await self._uow.long_term_memories.insert(record)
                long_term.append(record)

            chapter = build_monthly_chapter(
                long_term,
                world_id=world_id,
                owner_character_id=character_id,
                month_index=month_index,
                start_phase_index=start_phase,
                end_phase_index=end_phase,
            )
            chapter_ids.append(chapter.id)
            reflection = build_reflection_run(
                world_id=world_id,
                owner_character_id=character_id,
                month_index=month_index,
                chapter=chapter,
                proposals=(),
                available_memory_ids={m.id for m in long_term},
            )
            reflection_ids.append(reflection.id)
            _ = apply_forgetting_weights(long_term)

        month_run = MonthRunPersistenceRecord(
            id=uuid4() if existing is None else existing.id,
            world_id=world_id,
            month_index=month_index,
            status="completed",
            start_day_index=start_day,
            end_day_index=end_day,
            idempotency_key=key,
            metrics={
                "chapter_ids": [str(x) for x in chapter_ids],
                "reflection_ids": [str(x) for x in reflection_ids],
                "start_phase_index": start_phase,
                "end_phase_index": end_phase,
            },
        )
        if existing is None:
            saved = await self._uow.month_runs.insert(month_run)
        else:
            saved = month_run
        return MonthFinalizeResult(
            world_id=world_id,
            month_index=month_index,
            month_run_id=saved.id,
            already_finalized=False,
            chapter_ids=tuple(chapter_ids),
            reflection_ids=tuple(reflection_ids),
        )

    async def run_thirty_days(self, world_id: UUID) -> ThirtyDayRunResult:
        """Run thirty Stage 2 profile days then the monthly barrier."""

        if not self._stage2:
            raise self._stage2_error("run_thirty_days requires stage2=True")
        days: list[DayAdvanceResult] = []
        for _ in range(DAYS_PER_MONTH):
            days.append(await self.run_day(world_id))
        month = await self.finalize_month(world_id, month_index=1)
        return ThirtyDayRunResult(
            world_id=world_id,
            day_results=tuple(days),
            month_result=month,
        )
