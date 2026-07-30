"""Stage 3 additive queries and thirty-day orchestration commands."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from fictional_world.application.orchestration.protocol import DayAdvanceResult
from fictional_world.application.orchestration.stage3_ops import (
    MonthFinalizeResult,
    ThirtyDayRunResult,
)
from fictional_world.interfaces.http.dependencies import SettingsDep, UowDep
from fictional_world.interfaces.http.dto import (
    ArcRead,
    DayAdvanceResponse,
    ExportListRead,
    FactionRead,
    LongTermMemoryRead,
    MonthFinalizeSummaryRead,
    MonthRunRead,
    PhaseAdvanceSummaryRead,
    RunThirtyDaysResponse,
)
from fictional_world.interfaces.http.errors import not_found
from fictional_world.interfaces.http.runtime import phase_runner_for_world

router = APIRouter(prefix="/api/v1/worlds", tags=["stage3"])


async def _require_world(world_id: UUID, uow: UowDep) -> None:
    if await uow.worlds.get(world_id) is None:
        raise not_found("world", world_id)


async def _require_character(world_id: UUID, character_id: UUID, uow: UowDep) -> None:
    character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
    if character_id not in character_ids:
        raise not_found("character", character_id)


def _day_advance_response(result: DayAdvanceResult) -> DayAdvanceResponse:
    return DayAdvanceResponse(
        world_id=result.world_id,
        day_index=result.day_index,
        day_run_id=result.day_run_id,
        recovery_snapshot_id=result.recovery_snapshot_id,
        already_finalized=result.already_finalized,
        hard_audit_violations=result.hard_audit_violations,
        phase_results=[
            PhaseAdvanceSummaryRead(
                phase_run_id=phase.phase_run_id,
                absolute_phase_index=phase.absolute_phase_index,
                phase_name=phase.phase_name,
                already_completed=phase.already_completed,
            )
            for phase in result.phase_results
        ],
    )


def _month_finalize_summary(result: MonthFinalizeResult) -> MonthFinalizeSummaryRead:
    return MonthFinalizeSummaryRead(
        month_index=result.month_index,
        month_run_id=result.month_run_id,
        already_finalized=result.already_finalized,
        chapter_count=len(result.chapter_ids),
        reflection_count=len(result.reflection_ids),
    )


def _thirty_day_response(result: ThirtyDayRunResult) -> RunThirtyDaysResponse:
    return RunThirtyDaysResponse(
        world_id=result.world_id,
        days_completed=len(result.day_results),
        day_results=[_day_advance_response(day) for day in result.day_results],
        month=(
            None if result.month_result is None else _month_finalize_summary(result.month_result)
        ),
    )


@router.get("/{world_id}/month-runs", response_model=list[MonthRunRead])
async def list_month_runs(world_id: UUID, uow: UowDep) -> list[MonthRunRead]:
    await _require_world(world_id, uow)
    runs = await uow.month_runs.list_for_world(world_id)
    return [
        MonthRunRead(
            id=run.id,
            world_id=run.world_id,
            month_index=run.month_index,
            status=run.status,
            start_day_index=run.start_day_index,
            end_day_index=run.end_day_index,
            metrics=dict(run.metrics),
            completed_at=run.completed_at,
        )
        for run in runs
    ]


@router.get(
    "/{world_id}/characters/{character_id}/memories",
    response_model=list[LongTermMemoryRead],
)
async def list_character_memories(
    world_id: UUID,
    character_id: UUID,
    uow: UowDep,
) -> list[LongTermMemoryRead]:
    """Perspective-safe: only returns long-term memories owned by ``character_id``."""

    await _require_character(world_id, character_id, uow)
    memories = await uow.long_term_memories.list_for_owner(world_id, character_id)
    return [
        LongTermMemoryRead(
            id=memory.id,
            world_id=memory.world_id,
            owner_character_id=memory.owner_character_id,
            memory_type=memory.memory_type,
            content=memory.content,
            salience=memory.salience,
            confidence=memory.confidence,
            emotional_weight=memory.emotional_weight,
            visibility=memory.visibility,
            occurred_phase_index=memory.occurred_phase_index,
            created_phase_index=memory.created_phase_index,
            status=memory.status,
            decay_score=memory.decay_score,
        )
        for memory in memories
        if memory.owner_character_id == character_id and memory.world_id == world_id
    ]


@router.get("/{world_id}/arcs", response_model=list[ArcRead])
async def list_arcs(world_id: UUID, uow: UowDep) -> list[ArcRead]:
    await _require_world(world_id, uow)
    arcs = await uow.arcs.list_for_world(world_id)
    return [
        ArcRead(
            id=arc.id,
            world_id=arc.world_id,
            arc_key=arc.arc_key,
            title=arc.title,
            arc_scope=arc.arc_scope,
            status=arc.status,
            premise=arc.premise,
            objective=arc.objective,
            progress=arc.progress,
            participant_entity_ids=list(arc.participant_entity_ids),
            dominant_genres=list(arc.dominant_genres),
            version=arc.version,
        )
        for arc in arcs
    ]


@router.get("/{world_id}/factions", response_model=list[FactionRead])
async def list_factions(world_id: UUID, uow: UowDep) -> list[FactionRead]:
    await _require_world(world_id, uow)
    factions = await uow.factions.list_for_world(world_id)
    return [
        FactionRead(
            id=faction.id,
            world_id=faction.world_id,
            faction_key=faction.faction_key,
            name=faction.name,
            faction_type=faction.faction_type,
            status=faction.status,
            territory_location_ids=list(faction.territory_location_ids),
            plot_armour_bias=faction.plot_armour_bias,
            version=faction.version,
        )
        for faction in factions
    ]


@router.get("/{world_id}/exports", response_model=ExportListRead)
async def list_exports(world_id: UUID, uow: UowDep) -> ExportListRead:
    await _require_world(world_id, uow)
    return ExportListRead(items=[])


@router.post(
    "/{world_id}/commands/run-thirty-days",
    response_model=RunThirtyDaysResponse,
)
async def run_thirty_days(
    world_id: UUID,
    uow: UowDep,
    settings: SettingsDep,
) -> RunThirtyDaysResponse:
    await _require_world(world_id, uow)
    runner = await phase_runner_for_world(uow, settings, world_id, force_stage2=True)
    try:
        result = await runner.run_thirty_days(world_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    await uow.commit()
    return _thirty_day_response(result)


__all__ = ["router"]
