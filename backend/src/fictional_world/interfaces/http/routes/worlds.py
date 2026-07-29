"""World / clock / phase / event read + advance routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.interfaces.http.dependencies import UowDep
from fictional_world.interfaces.http.dto import (
    AdvancePhaseResponse,
    ClockRead,
    EventRead,
    PhaseRead,
    ReconcileResponse,
    WorldRead,
)
from fictional_world.interfaces.http.errors import not_found
from fictional_world.observability.audit import AuditEvent, emit_audit

router = APIRouter(prefix="/worlds", tags=["worlds"])


def _world_read(world: object) -> WorldRead:
    return WorldRead.model_validate(world, from_attributes=True)


def _clock_read(clock: object) -> ClockRead:
    return ClockRead.model_validate(clock, from_attributes=True)


def _phase_read(phase: object) -> PhaseRead:
    return PhaseRead.model_validate(phase, from_attributes=True)


def _event_read(event: object) -> EventRead:
    return EventRead.model_validate(event, from_attributes=True)


@router.get("/by-slug/{slug}", response_model=WorldRead)
async def get_world_by_slug(slug: str, uow: UowDep) -> WorldRead:
    world = await uow.worlds.get_by_slug(slug)
    if world is None:
        raise not_found("world", slug)
    return _world_read(world)


@router.get("/{world_id}", response_model=WorldRead)
async def get_world(world_id: UUID, uow: UowDep) -> WorldRead:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    return _world_read(world)


@router.get("/{world_id}/clock", response_model=ClockRead)
async def get_clock(world_id: UUID, uow: UowDep) -> ClockRead:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    clock = await uow.worlds.get_clock(world_id)
    if clock is None:
        raise not_found("world_clock", world_id)
    return _clock_read(clock)


@router.get("/{world_id}/phases/active", response_model=PhaseRead | None)
async def get_active_phase(world_id: UUID, uow: UowDep) -> PhaseRead | None:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    phase = await uow.phases.find_active_for_world(world_id)
    if phase is None:
        return None
    return _phase_read(phase)


@router.get("/{world_id}/phases/{absolute_phase_index}", response_model=PhaseRead)
async def get_phase_by_index(world_id: UUID, absolute_phase_index: int, uow: UowDep) -> PhaseRead:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    phase = await uow.phases.find_by_world_and_index(world_id, absolute_phase_index)
    if phase is None:
        raise not_found("phase_run", f"{world_id}:{absolute_phase_index}")
    return _phase_read(phase)


@router.get("/{world_id}/events", response_model=list[EventRead])
async def list_events(
    world_id: UUID,
    uow: UowDep,
    *,
    after_sequence: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[EventRead]:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    events = await uow.events.list_for_world(world_id, after_sequence=after_sequence, limit=limit)
    return [_event_read(event) for event in events]


@router.post(
    "/{world_id}/commands/advance-phase",
    response_model=AdvancePhaseResponse,
    status_code=status.HTTP_200_OK,
)
async def advance_phase(world_id: UUID, uow: UowDep) -> AdvancePhaseResponse:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    runner = DeterministicPhaseRunner(uow)
    result = await runner.request_phase_advance(world_id)
    await uow.commit()
    emit_audit(
        AuditEvent(
            action="advance_phase",
            world_id=world_id,
            resource_type="phase_run",
            resource_id=str(result.phase_run_id),
            detail={
                "absolute_phase_index": result.absolute_phase_index,
                "phase_name": result.phase_name,
                "already_completed": result.already_completed,
            },
        )
    )
    return AdvancePhaseResponse(
        phase_run_id=result.phase_run_id,
        absolute_phase_index=result.absolute_phase_index,
        phase_name=result.phase_name,
        already_completed=result.already_completed,
        snapshot_id=result.snapshot_id,
        event_ids=list(result.event_ids),
    )


@router.post(
    "/{world_id}/commands/reconcile",
    response_model=ReconcileResponse,
    status_code=status.HTTP_200_OK,
)
async def reconcile_world(world_id: UUID, uow: UowDep) -> ReconcileResponse:
    world = await uow.worlds.get(world_id)
    if world is None:
        raise not_found("world", world_id)
    runner = DeterministicPhaseRunner(uow)
    report = await runner.reconcile(world_id)
    await uow.commit()
    emit_audit(
        AuditEvent(
            action="reconcile",
            world_id=world_id,
            resource_type="world",
            resource_id=str(world_id),
            detail={"phase_completed": report.phase_completed},
        )
    )
    return ReconcileResponse(
        world_id=report.world_id,
        active_phase_id=report.active_phase_id,
        tasks_created=report.tasks_created,
        phase_completed=report.phase_completed,
        notes=list(report.notes),
    )
