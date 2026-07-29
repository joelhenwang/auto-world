"""Stage 1 runtime, perspective-safe reads, and player-control routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status

from fictional_world.application.context.types import STAGE1_ACTION_FAMILIES
from fictional_world.application.orchestration.protocol import PauseMode, PhaseAdvanceResult
from fictional_world.domain.scenes.persistence import (
    PlayerControlSessionRecord,
    SceneRecord,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.tasks.user_command import UserCommandRecord
from fictional_world.interfaces.http.dependencies import SettingsDep, UowDep
from fictional_world.interfaces.http.dto import (
    AcquirePlayerControlRequest,
    AdvancePhaseResponse,
    CharacterSummaryRead,
    PauseWorldRequest,
    PlayerActionRequest,
    PlayerActionResponse,
    PlayerControlRead,
    ReleasePlayerControlRequest,
    RuntimeCommandResponse,
    SceneSummaryRead,
    StreamEventRead,
)
from fictional_world.interfaces.http.errors import conflict, not_found
from fictional_world.interfaces.http.runtime import phase_runner_for_world

router = APIRouter(prefix="/api/v1/worlds", tags=["stage1"])

_CHARACTER_NAMES = {
    seed_uuid("character/mira-talren"): "Mira Talren",
    seed_uuid("character/dain-arcen"): "Dain Arcen",
}


async def _require_world(world_id: UUID, uow: UowDep) -> None:
    if await uow.worlds.get(world_id) is None:
        raise not_found("world", world_id)


async def _runner(uow: UowDep, settings: SettingsDep, world_id: UUID):
    return await phase_runner_for_world(uow, settings, world_id)


def _advance_response(result: PhaseAdvanceResult) -> AdvancePhaseResponse:
    return AdvancePhaseResponse(
        phase_run_id=result.phase_run_id,
        absolute_phase_index=result.absolute_phase_index,
        phase_name=result.phase_name,
        already_completed=result.already_completed,
        snapshot_id=result.snapshot_id,
        event_ids=list(result.event_ids),
    )


def _player_control_read(session: PlayerControlSessionRecord) -> PlayerControlRead:
    return PlayerControlRead.model_validate(session, from_attributes=True)


@router.post("/{world_id}/advance", response_model=AdvancePhaseResponse)
async def advance_stage1_world(
    world_id: UUID,
    uow: UowDep,
    settings: SettingsDep,
) -> AdvancePhaseResponse:
    await _require_world(world_id, uow)
    result = await _runner(uow, settings, world_id).request_phase_advance(world_id)
    await uow.commit()
    return _advance_response(result)


@router.post("/{world_id}/pause", response_model=RuntimeCommandResponse)
async def pause_stage1_world(
    world_id: UUID,
    request: PauseWorldRequest,
    uow: UowDep,
    settings: SettingsDep,
) -> RuntimeCommandResponse:
    await _require_world(world_id, uow)
    await _runner(uow, settings, world_id).pause_world(world_id, PauseMode(request.mode))
    await uow.commit()
    return RuntimeCommandResponse(world_id=world_id, status="paused")


@router.post("/{world_id}/resume", response_model=RuntimeCommandResponse)
async def resume_stage1_world(
    world_id: UUID,
    uow: UowDep,
    settings: SettingsDep,
) -> RuntimeCommandResponse:
    await _require_world(world_id, uow)
    result = await _runner(uow, settings, world_id).resume_world(world_id)
    await uow.commit()
    return RuntimeCommandResponse(
        world_id=world_id,
        status="idle" if result is None else "advanced",
        phase=None if result is None else _advance_response(result),
    )


@router.get("/{world_id}/timeline", response_model=list[StreamEventRead])
async def timeline(
    world_id: UUID,
    uow: UowDep,
    *,
    after_sequence: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    observer_id: UUID | None = None,
) -> list[StreamEventRead]:
    await _require_world(world_id, uow)
    if observer_id is not None:
        character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
        if observer_id not in character_ids:
            raise not_found("observer", observer_id)
    events = await uow.stream_events.list_after(
        world_id,
        after_sequence=after_sequence,
        limit=limit,
    )
    allowed_scopes = {"world"}
    if observer_id is not None:
        allowed_scopes.add(f"character:{observer_id}")
    return [
        StreamEventRead.model_validate(event, from_attributes=True)
        for event in events
        if event.perspective_scope in allowed_scopes
    ]


@router.get("/{world_id}/scenes", response_model=list[SceneSummaryRead])
async def scenes(
    world_id: UUID,
    phase_run_id: UUID,
    uow: UowDep,
) -> list[SceneSummaryRead]:
    await _require_world(world_id, uow)
    phase = await uow.phases.get(phase_run_id)
    if phase is None or phase.world_id != world_id:
        raise not_found("phase_run", phase_run_id)
    records = await uow.scenes.list_for_phase(phase_run_id)
    return [await _scene_read(uow, record) for record in records]


async def _scene_read(uow: UowDep, scene: SceneRecord) -> SceneSummaryRead:
    resolution = await uow.scene_resolutions.get_for_scene(scene.id)
    narrations = await uow.narrations.list_for_scene(scene.id)
    return SceneSummaryRead(
        id=scene.id,
        phase_run_id=scene.phase_run_id,
        snapshot_id=scene.snapshot_id,
        location_id=scene.location_id,
        scene_type=scene.scene_type,
        state=scene.state,
        priority_score=scene.priority_score,
        beat_budget=scene.beat_budget,
        participant_ids=[participant.entity_id for participant in scene.participants],
        resolution_level=None if resolution is None else resolution.resolution_level,
        canonical_summary=None if resolution is None else resolution.canonical_summary,
        narration=None if not narrations else narrations[0].body,
    )


@router.get("/{world_id}/characters", response_model=list[CharacterSummaryRead])
async def characters(world_id: UUID, uow: UowDep) -> list[CharacterSummaryRead]:
    await _require_world(world_id, uow)
    character_ids = await uow.characters.list_character_ids_for_world(world_id)
    summaries: list[CharacterSummaryRead] = []
    for character_id in character_ids:
        state = await uow.characters.get_state(character_id)
        if state is None:
            continue
        card = await uow.characters.get_card(state.current_card_version_id)
        raw_name = None if card is None else card.identity.get("canonical_name")
        name = (
            str(raw_name)
            if raw_name is not None
            else _CHARACTER_NAMES.get(character_id, f"Character {character_id}")
        )
        summaries.append(
            CharacterSummaryRead(
                id=character_id,
                name=name,
                location_id=state.location_id,
                life_status=state.life_status,
                stamina=state.stamina,
                energy=state.energy,
                pain=state.pain,
                stress=state.stress,
                active_activity_id=state.active_activity_id,
                state_version=state.version,
            )
        )
    return summaries


@router.post(
    "/{world_id}/characters/{character_id}/player/acquire",
    response_model=PlayerControlRead,
)
async def acquire_player_control(
    world_id: UUID,
    character_id: UUID,
    request: AcquirePlayerControlRequest,
    uow: UowDep,
) -> PlayerControlRead:
    await _require_character(world_id, character_id, uow)
    by_key = await uow.player_controls.find_by_idempotency_key(request.idempotency_key)
    if by_key is not None:
        if (
            by_key.world_id != world_id
            or by_key.character_id != character_id
            or by_key.controller_id != request.controller_id
        ):
            raise conflict("player-control idempotency key belongs to another request")
        return _player_control_read(by_key)
    active = await uow.player_controls.find_active_for_character(character_id)
    if active is not None:
        if active.controller_id == request.controller_id:
            return _player_control_read(active)
        raise conflict("character is already controlled by another controller")
    now = datetime.now(UTC)
    inserted = await uow.player_controls.insert(
        PlayerControlSessionRecord(
            id=uuid4(),
            world_id=world_id,
            character_id=character_id,
            controller_id=request.controller_id,
            status="active",
            acquired_at=now,
            idempotency_key=request.idempotency_key,
        )
    )
    await uow.commit()
    return _player_control_read(inserted)


@router.post(
    "/{world_id}/characters/{character_id}/player/release",
    response_model=PlayerControlRead,
)
async def release_player_control(
    world_id: UUID,
    character_id: UUID,
    request: ReleasePlayerControlRequest,
    uow: UowDep,
) -> PlayerControlRead:
    await _require_character(world_id, character_id, uow)
    session = await uow.player_controls.get(request.session_id)
    if session is None:
        raise not_found("player_control_session", request.session_id)
    if (
        session.world_id != world_id
        or session.character_id != character_id
        or session.controller_id != request.controller_id
    ):
        raise conflict("player-control session ownership mismatch")
    if session.status == "released":
        return _player_control_read(session)
    if session.status not in {"active", "waiting_input"}:
        raise conflict(f"player-control session cannot be released from {session.status}")
    saved = await uow.player_controls.save(
        session.model_copy(
            update={
                "status": "released",
                "waiting_input": False,
                "released_at": datetime.now(UTC),
            }
        ),
        expected_version=session.version,
    )
    await uow.commit()
    return _player_control_read(saved)


@router.post(
    "/{world_id}/characters/{character_id}/player/action",
    response_model=PlayerActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_player_action(
    world_id: UUID,
    character_id: UUID,
    request: PlayerActionRequest,
    uow: UowDep,
) -> PlayerActionResponse:
    await _require_character(world_id, character_id, uow)
    session = await uow.player_controls.get(request.session_id)
    if (
        session is None
        or session.world_id != world_id
        or session.character_id != character_id
        or session.controller_id != request.controller_id
        or session.status not in {"active", "waiting_input"}
    ):
        raise conflict("active player-control session required")
    if request.action_family not in STAGE1_ACTION_FAMILIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="action family is outside Stage 1",
        )
    character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
    if not set(request.target_entity_ids).issubset(character_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="action references an unknown target entity",
        )
    if (
        request.target_location_id is not None
        and await uow.characters.get_location(request.target_location_id) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="action references an unknown target location",
        )
    existing = await uow.user_commands.find_by_idempotency_key(request.idempotency_key)
    if existing is not None:
        if existing.world_id != world_id or existing.target_entity_id != character_id:
            raise conflict("player-action idempotency key belongs to another request")
        return PlayerActionResponse(
            command_id=existing.id,
            status=existing.status,
            already_existed=True,
        )
    inserted = await uow.user_commands.insert(
        UserCommandRecord(
            id=uuid4(),
            world_id=world_id,
            actor_role="player",
            command_type="character_action_attempt",
            payload={
                "session_id": str(session.id),
                "controller_id": request.controller_id,
                "action_family": request.action_family,
                "description": request.description,
                "utterance": request.utterance,
                "target_entity_ids": [str(value) for value in request.target_entity_ids],
                "target_location_id": (
                    None if request.target_location_id is None else str(request.target_location_id)
                ),
            },
            target_entity_id=character_id,
            requested_phase_boundary="accept_commands",
            idempotency_key=request.idempotency_key,
            permission_decision="allowed",
            status="pending",
            decided_at=datetime.now(UTC),
        )
    )
    await uow.commit()
    return PlayerActionResponse(
        command_id=inserted.id,
        status=inserted.status,
        already_existed=False,
    )


async def _require_character(world_id: UUID, character_id: UUID, uow: UowDep) -> None:
    character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
    if character_id not in character_ids:
        raise not_found("character", character_id)


__all__ = ["router"]
