"""Stage 2 additive queries and day-orchestration commands."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, HTTPException, Query, status

from fictional_world.application.orchestration.protocol import DayAdvanceResult
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.tasks.user_command import UserCommandRecord
from fictional_world.interfaces.http.dependencies import SettingsDep, UowDep
from fictional_world.interfaces.http.dto import (
    BeliefRead,
    CharacterDetailRead,
    CharacterDiaryBundleRead,
    CommitmentRead,
    DayAdvanceResponse,
    DayProgressRead,
    DayRunRead,
    DiaryEntryRead,
    DirectorHookRead,
    DirectorHooksMetricsRead,
    GoalRead,
    LocationMapRead,
    MapStateRead,
    NarrativeMetricRead,
    NpcDetailRead,
    NpcLifecycleRead,
    NpcSummaryRead,
    PhaseAdvanceSummaryRead,
    PlanRead,
    ProposeDirectorEventRequest,
    ProposeDirectorEventResponse,
    RelationshipEdgeRead,
    RouteMapRead,
    RunUntilDayRequest,
    RunUntilDayResponse,
    SummaryRead,
    TaskFailureRead,
    TravelProgressSummaryRead,
)
from fictional_world.interfaces.http.errors import conflict, forbidden, not_found
from fictional_world.interfaces.http.runtime import phase_runner_for_world

router = APIRouter(prefix="/api/v1/worlds", tags=["stage2"])

_CHARACTER_NAMES = {
    seed_uuid("character/mira-talren"): "Mira Talren",
    seed_uuid("character/dain-arcen"): "Dain Arcen",
    seed_uuid("character/iri-voss"): "Iri Voss",
    seed_uuid("character/torren-kest"): "Torren Kest",
}

ObserverMode = Literal["player", "watcher", "director"]


async def _require_world(world_id: UUID, uow: UowDep) -> None:
    if await uow.worlds.get(world_id) is None:
        raise not_found("world", world_id)


async def _require_character(world_id: UUID, character_id: UUID, uow: UowDep) -> None:
    character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
    if character_id not in character_ids:
        raise not_found("character", character_id)


def _resolve_mode(
    *,
    mode: str | None,
    x_observer_mode: str | None,
) -> ObserverMode:
    raw = (mode or x_observer_mode or "player").strip().casefold()
    if raw not in {"player", "watcher", "director"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="mode must be player, watcher, or director",
        )
    return raw  # type: ignore[return-value]


def _require_privileged(mode: ObserverMode) -> None:
    if mode == "player":
        raise forbidden("director/watcher mode required")


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


async def _character_name(uow: UowDep, character_id: UUID) -> str:
    state = await uow.characters.get_state(character_id)
    if state is not None:
        card = await uow.characters.get_card(state.current_card_version_id)
        raw_name = None if card is None else card.identity.get("canonical_name")
        if raw_name is not None:
            return str(raw_name)
    entity = await uow.characters.get_entity(character_id)
    if entity is not None:
        return entity.canonical_name
    return _CHARACTER_NAMES.get(character_id, f"Character {character_id}")


@router.get("/{world_id}/day-progress", response_model=DayProgressRead)
async def day_progress(world_id: UUID, uow: UowDep) -> DayProgressRead:
    await _require_world(world_id, uow)
    clock = await uow.worlds.get_clock(world_id)
    if clock is None:
        raise not_found("world_clock", world_id)
    day_runs = await uow.day_runs.list_for_world(world_id)
    current = next(
        (run for run in day_runs if run.day_index == clock.absolute_day_index),
        None,
    )
    completed = sum(1 for run in day_runs if run.status == "completed")
    return DayProgressRead(
        world_id=world_id,
        day_index=clock.absolute_day_index,
        phase_name=clock.phase_name,
        phase_ordinal=clock.phase_ordinal,
        absolute_phase_index=clock.absolute_phase_index,
        resolution_mode=clock.resolution_mode,
        clock_version=clock.version,
        day_run=(
            None
            if current is None
            else DayRunRead(
                id=current.id,
                world_id=current.world_id,
                day_index=current.day_index,
                status=current.status,
                recovery_snapshot_id=current.recovery_snapshot_id,
                version=current.version,
            )
        ),
        completed_day_count=completed,
    )


@router.get("/{world_id}/map", response_model=MapStateRead)
async def map_state(world_id: UUID, uow: UowDep) -> MapStateRead:
    await _require_world(world_id, uow)
    locations = await uow.characters.list_locations_for_world(world_id)
    location_reads: list[LocationMapRead] = []
    for location in locations:
        entity = await uow.characters.get_entity(location.entity_id)
        location_reads.append(
            LocationMapRead(
                id=location.entity_id,
                name="" if entity is None else entity.canonical_name,
                location_type=location.location_type,
                region_code=location.region_code,
                parent_location_id=location.parent_location_id,
                coordinate_x=location.coordinate_x,
                coordinate_y=location.coordinate_y,
                environment_tags=list(location.environment_tags),
            )
        )
    routes = await uow.routes.list_for_world(world_id)
    route_reads = [
        RouteMapRead(
            id=route.id,
            origin_location_id=route.origin_location_id,
            destination_location_id=route.destination_location_id,
            is_bidirectional=route.is_bidirectional,
            distance_units=route.distance_units,
            base_duration_phases=route.base_duration_phases,
            status=route.status,
            danger_level=route.danger_level,
        )
        for route in routes
    ]
    travel: list[TravelProgressSummaryRead] = []
    for character_id in await uow.characters.list_character_ids_for_world(world_id):
        activities = await uow.activities.list_for_owner(character_id, world_id=world_id)
        for activity in activities:
            if activity.activity_type != "travel":
                continue
            if activity.status not in {"active", "paused", "in_progress"}:
                continue
            travel.append(
                TravelProgressSummaryRead(
                    activity_id=activity.id,
                    owner_entity_id=activity.owner_entity_id,
                    route_id=activity.route_id,
                    origin_location_id=activity.origin_location_id,
                    destination_location_id=activity.destination_location_id,
                    status=activity.status,
                    progress=activity.progress,
                    started_phase_index=activity.started_phase_index,
                    expected_end_phase_index=activity.expected_end_phase_index,
                )
            )
    return MapStateRead(locations=location_reads, routes=route_reads, travel_progress=travel)


@router.get(
    "/{world_id}/characters/{character_id}",
    response_model=CharacterDetailRead,
)
async def character_detail(
    world_id: UUID,
    character_id: UUID,
    uow: UowDep,
) -> CharacterDetailRead:
    await _require_character(world_id, character_id, uow)
    state = await uow.characters.get_state(character_id)
    if state is None:
        raise not_found("character_state", character_id)
    character = await uow.characters.get_character(character_id)
    goals = await uow.goals.list_for_owner(character_id, world_id=world_id)
    plans: list[PlanRead] = []
    for goal in goals:
        for plan in await uow.plans.list_for_goal(goal.id):
            plans.append(
                PlanRead(
                    id=plan.id,
                    goal_id=plan.goal_id,
                    title=plan.title,
                    status=plan.status,
                    is_primary=plan.is_primary,
                    commitment_level=plan.commitment_level,
                    revision_number=plan.revision_number,
                )
            )
    commitments = await uow.commitments.list_for_debtor(character_id, world_id=world_id)
    return CharacterDetailRead(
        id=character_id,
        name=await _character_name(uow, character_id),
        character_kind=None if character is None else character.character_kind,
        location_id=state.location_id,
        life_status=state.life_status,
        stamina=state.stamina,
        energy=state.energy,
        pain=state.pain,
        stress=state.stress,
        active_activity_id=state.active_activity_id,
        state_version=state.version,
        goals=[
            GoalRead(
                id=goal.id,
                description=goal.description,
                category=goal.category,
                priority=goal.priority,
                status=goal.status,
                horizon=goal.horizon,
                allows_alternative_plans=goal.allows_alternative_plans,
            )
            for goal in goals
        ],
        plans=plans,
        commitments=[
            CommitmentRead(
                id=item.id,
                debtor_character_id=item.debtor_character_id,
                beneficiary_character_id=item.beneficiary_character_id,
                description=item.description,
                status=item.status,
            )
            for item in commitments
        ],
    )


@router.get(
    "/{world_id}/characters/{character_id}/beliefs",
    response_model=list[BeliefRead],
)
async def character_beliefs(
    world_id: UUID,
    character_id: UUID,
    uow: UowDep,
) -> list[BeliefRead]:
    """Perspective-safe: only returns beliefs owned by ``character_id``."""

    await _require_character(world_id, character_id, uow)
    beliefs = await uow.beliefs.list_for_character(character_id, world_id=world_id)
    return [
        BeliefRead(
            id=belief.id,
            character_id=belief.character_id,
            proposition_key=belief.proposition_key,
            belief_text=belief.belief_text,
            confidence=belief.confidence,
            status=belief.status,
            evidence_summary=dict(belief.evidence_summary),
            version=belief.version,
        )
        for belief in beliefs
        if belief.character_id == character_id and belief.world_id == world_id
    ]


@router.get(
    "/{world_id}/characters/{character_id}/relationships",
    response_model=list[RelationshipEdgeRead],
)
async def character_relationships(
    world_id: UUID,
    character_id: UUID,
    uow: UowDep,
) -> list[RelationshipEdgeRead]:
    await _require_character(world_id, character_id, uow)
    edges = await uow.relationship_edges.list_for_source(character_id, world_id=world_id)
    return [
        RelationshipEdgeRead(
            source_character_id=edge.source_character_id,
            target_character_id=edge.target_character_id,
            familiarity=edge.familiarity,
            trust=edge.trust,
            affection=edge.affection,
            attraction=edge.attraction,
            respect=edge.respect,
            fear=edge.fear,
            resentment=edge.resentment,
            dependency=edge.dependency,
            loyalty=edge.loyalty,
            perceived_reciprocity=edge.perceived_reciprocity,
            last_meaningful_interaction_phase=edge.last_meaningful_interaction_phase,
            version=edge.version,
        )
        for edge in edges
    ]


@router.get("/{world_id}/npcs", response_model=list[NpcSummaryRead])
async def list_npcs(world_id: UUID, uow: UowDep) -> list[NpcSummaryRead]:
    await _require_world(world_id, uow)
    items = await uow.npcs.list_for_world(world_id)
    return [
        NpcSummaryRead(
            character_id=profile.character_id,
            display_name=profile.display_name,
            role_tags=list(profile.role_tags),
            lifecycle=(
                None
                if lifecycle is None
                else NpcLifecycleRead(
                    character_id=lifecycle.character_id,
                    lifecycle_status=lifecycle.lifecycle_status,
                    activated_phase_index=lifecycle.activated_phase_index,
                    archive_phase_index=lifecycle.archive_phase_index,
                    ttl_until_phase=lifecycle.ttl_until_phase,
                    relevance_score=lifecycle.relevance_score,
                    archive_summary=lifecycle.archive_summary,
                    last_scene_phase_index=lifecycle.last_scene_phase_index,
                    version=lifecycle.version,
                )
            ),
        )
        for profile, lifecycle in items
    ]


@router.get("/{world_id}/npcs/{character_id}", response_model=NpcDetailRead)
async def npc_detail(
    world_id: UUID,
    character_id: UUID,
    uow: UowDep,
) -> NpcDetailRead:
    await _require_world(world_id, uow)
    profile = await uow.npcs.get_profile(character_id)
    if profile is None or profile.world_id != world_id:
        raise not_found("npc", character_id)
    lifecycle = await uow.npcs.get_lifecycle(character_id)
    return NpcDetailRead(
        character_id=profile.character_id,
        display_name=profile.display_name,
        role_tags=list(profile.role_tags),
        compact_card=dict(profile.compact_card),
        source_hook_id=profile.source_hook_id,
        similarity_fingerprint=profile.similarity_fingerprint,
        lifecycle=(
            None
            if lifecycle is None
            else NpcLifecycleRead(
                character_id=lifecycle.character_id,
                lifecycle_status=lifecycle.lifecycle_status,
                activated_phase_index=lifecycle.activated_phase_index,
                archive_phase_index=lifecycle.archive_phase_index,
                ttl_until_phase=lifecycle.ttl_until_phase,
                relevance_score=lifecycle.relevance_score,
                archive_summary=lifecycle.archive_summary,
                last_scene_phase_index=lifecycle.last_scene_phase_index,
                version=lifecycle.version,
            )
        ),
    )


@router.get(
    "/{world_id}/characters/{character_id}/diaries",
    response_model=CharacterDiaryBundleRead,
)
async def character_diaries(
    world_id: UUID,
    character_id: UUID,
    uow: UowDep,
) -> CharacterDiaryBundleRead:
    await _require_character(world_id, character_id, uow)
    diaries = await uow.diary_entries.list_for_owner(character_id, world_id=world_id)
    summaries = await uow.summaries.list_for_owner(character_id, world_id=world_id)
    return CharacterDiaryBundleRead(
        character_id=character_id,
        diaries=[
            DiaryEntryRead(
                id=entry.id,
                owner_character_id=entry.owner_character_id,
                day_index=entry.day_index,
                content=entry.content,
                summary_id=entry.summary_id,
                version=entry.version,
            )
            for entry in diaries
        ],
        summaries=[
            SummaryRead(
                id=summary.id,
                owner_character_id=summary.owner_character_id,
                summary_type=summary.summary_type,
                start_phase_index=summary.start_phase_index,
                end_phase_index=summary.end_phase_index,
                content=summary.content,
                perspective=summary.perspective,
                version_number=summary.version_number,
            )
            for summary in summaries
        ],
    )


@router.get("/{world_id}/director", response_model=DirectorHooksMetricsRead)
async def director_hooks_metrics(
    world_id: UUID,
    uow: UowDep,
    *,
    mode: str | None = Query(default=None),
    x_observer_mode: str | None = Header(default=None, alias="X-Observer-Mode"),
) -> DirectorHooksMetricsRead:
    await _require_world(world_id, uow)
    observer_mode = _resolve_mode(mode=mode, x_observer_mode=x_observer_mode)
    _require_privileged(observer_mode)
    hooks = await uow.hooks.list_for_world(world_id)
    metrics = await uow.narrative_metrics.list_for_world(world_id, limit=100)
    return DirectorHooksMetricsRead(
        hooks=[
            DirectorHookRead(
                id=hook.id,
                hook_key=hook.hook_key,
                title=hook.title,
                status=hook.status,
                premise=hook.premise,
                disclosure_state=hook.disclosure_state,
                cooldown_until_phase=hook.cooldown_until_phase,
                involved_entity_ids=list(hook.involved_entity_ids),
                version=hook.version,
            )
            for hook in hooks
        ],
        metrics=[
            NarrativeMetricRead(
                id=metric.id,
                metric_key=metric.metric_key,
                metric_value=metric.metric_value,
                window_start_phase=metric.window_start_phase,
                window_end_phase=metric.window_end_phase,
                payload=dict(metric.payload),
            )
            for metric in metrics
        ],
    )


@router.get("/{world_id}/tasks/failures", response_model=list[TaskFailureRead])
async def task_failures(
    world_id: UUID,
    uow: UowDep,
    *,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[TaskFailureRead]:
    await _require_world(world_id, uow)
    tasks = await uow.tasks.list_failures_for_world(world_id, limit=limit)
    return [
        TaskFailureRead(
            id=task.id,
            task_type=task.task_type,
            state=str(task.state),
            attempt_count=task.attempt_count,
            error_code=task.error_code,
            error_detail=None if task.error_detail is None else dict(task.error_detail),
            phase_run_id=task.phase_run_id,
            created_at=task.created_at,
            completed_at=task.completed_at,
        )
        for task in tasks
    ]


@router.post("/{world_id}/run-day", response_model=DayAdvanceResponse)
async def run_day(
    world_id: UUID,
    uow: UowDep,
    settings: SettingsDep,
) -> DayAdvanceResponse:
    await _require_world(world_id, uow)
    runner = await phase_runner_for_world(uow, settings, world_id, force_stage2=True)
    try:
        result = await runner.run_day(world_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    await uow.commit()
    return _day_advance_response(result)


@router.post("/{world_id}/run-until-day", response_model=RunUntilDayResponse)
async def run_until_day(
    world_id: UUID,
    request: RunUntilDayRequest,
    uow: UowDep,
    settings: SettingsDep,
) -> RunUntilDayResponse:
    await _require_world(world_id, uow)
    runner = await phase_runner_for_world(uow, settings, world_id, force_stage2=True)
    days: list[DayAdvanceResponse] = []
    try:
        for _ in range(request.target_day_index + 8):
            day_runs = await uow.day_runs.list_for_world(world_id)
            if any(
                run.day_index >= request.target_day_index and run.status == "completed"
                for run in day_runs
            ):
                break
            result = await runner.run_day(world_id)
            days.append(_day_advance_response(result))
            if result.day_index >= request.target_day_index:
                break
        else:
            raise conflict("run-until-day exceeded safety bound")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    await uow.commit()
    return RunUntilDayResponse(
        world_id=world_id,
        target_day_index=request.target_day_index,
        days=days,
    )


@router.post(
    "/{world_id}/director/propose-event",
    response_model=ProposeDirectorEventResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def propose_director_event(
    world_id: UUID,
    request: ProposeDirectorEventRequest,
    uow: UowDep,
    *,
    mode: str | None = Query(default=None),
    x_observer_mode: str | None = Header(default=None, alias="X-Observer-Mode"),
) -> ProposeDirectorEventResponse:
    await _require_world(world_id, uow)
    observer_mode = _resolve_mode(mode=mode, x_observer_mode=x_observer_mode)
    if observer_mode != "director":
        raise forbidden("director mode required")
    existing = await uow.user_commands.find_by_idempotency_key(request.idempotency_key)
    if existing is not None:
        if existing.world_id != world_id or existing.command_type != "director_event_proposal":
            raise conflict("director-proposal idempotency key belongs to another request")
        return ProposeDirectorEventResponse(
            command_id=existing.id,
            status=existing.status,
            already_existed=True,
        )
    inserted = await uow.user_commands.insert(
        UserCommandRecord(
            id=uuid4(),
            world_id=world_id,
            actor_role="director",
            command_type="director_event_proposal",
            payload={
                "proposal_kind": request.proposal_kind,
                "summary": request.summary,
                "public_payload": request.public_payload,
            },
            requested_phase_boundary="accept_commands",
            idempotency_key=request.idempotency_key,
            permission_decision="allowed",
            status="pending",
            decided_at=datetime.now(UTC),
        )
    )
    await uow.commit()
    return ProposeDirectorEventResponse(
        command_id=inserted.id,
        status=inserted.status,
        already_existed=False,
    )


__all__ = ["router"]
