"""Replayable Stage 1/2 world stream WebSocket."""

from __future__ import annotations

from typing import cast
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fictional_world.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from fictional_world.interfaces.http.dto import StreamEventRead

router = APIRouter(tags=["websocket"])

# Additive Stage 2 envelope types retained for OpenAPI/clients; replay still uses
# stream_event + replay_complete + pong + error. Future day/director projections
# may emit day.finalized / director.metric / day.progress without breaking clients.
_STAGE2_ENVELOPE_TYPES = frozenset({"day.finalized", "director.metric", "day.progress"})
_ = _STAGE2_ENVELOPE_TYPES


@router.websocket("/ws/v1/worlds/{world_id}")
async def world_stream(websocket: WebSocket, world_id: UUID) -> None:
    """Replay durable stream events and support explicit client polling."""

    await websocket.accept()
    try:
        cursor = max(0, int(websocket.query_params.get("after_sequence", "0")))
    except ValueError:
        await websocket.send_json({"type": "error", "detail": "after_sequence must be an integer"})
        await websocket.close(code=4400)
        return
    observer_raw = websocket.query_params.get("observer_id")
    try:
        observer_id = None if observer_raw is None else UUID(observer_raw)
    except ValueError:
        await websocket.send_json({"type": "error", "detail": "observer_id must be a UUID"})
        await websocket.close(code=4400)
        return

    factory = cast(
        async_sessionmaker[AsyncSession],
        websocket.app.state.session_factory,
    )
    validation_error = await _validate_scope(factory, world_id, observer_id)
    if validation_error is not None:
        await websocket.send_json({"type": "error", "detail": validation_error})
        await websocket.close(code=4404)
        return

    try:
        cursor = await _send_replay(
            websocket,
            factory,
            world_id=world_id,
            observer_id=observer_id,
            after_sequence=cursor,
        )
        while True:
            raw_message: object = await websocket.receive_json()
            message = (
                cast(dict[object, object], raw_message) if isinstance(raw_message, dict) else {}
            )
            raw_type = message.get("type")
            message_type = raw_type if isinstance(raw_type, str) else None
            if message_type == "poll":
                cursor = await _send_replay(
                    websocket,
                    factory,
                    world_id=world_id,
                    observer_id=observer_id,
                    after_sequence=cursor,
                )
            elif message_type == "ping":
                await websocket.send_json({"type": "pong", "last_sequence": cursor})
            else:
                await websocket.send_json({"type": "error", "detail": "expected poll or ping"})
    except WebSocketDisconnect:
        return


async def _validate_scope(
    factory: async_sessionmaker[AsyncSession],
    world_id: UUID,
    observer_id: UUID | None,
) -> str | None:
    async with SqlAlchemyUnitOfWork(factory) as uow:
        if await uow.worlds.get(world_id) is None:
            return f"world not found: {world_id}"
        if observer_id is not None:
            character_ids = set(await uow.characters.list_character_ids_for_world(world_id))
            if observer_id not in character_ids:
                return f"observer not found: {observer_id}"
    return None


async def _send_replay(
    websocket: WebSocket,
    factory: async_sessionmaker[AsyncSession],
    *,
    world_id: UUID,
    observer_id: UUID | None,
    after_sequence: int,
) -> int:
    async with SqlAlchemyUnitOfWork(factory) as uow:
        events = await uow.stream_events.list_after(
            world_id,
            after_sequence=after_sequence,
            limit=500,
        )
    allowed_scopes = {"world"}
    if observer_id is not None:
        allowed_scopes.add(f"character:{observer_id}")
    cursor = after_sequence
    for event in events:
        if event.perspective_scope not in allowed_scopes:
            continue
        cursor = max(cursor, event.sequence)
        payload = StreamEventRead.model_validate(event, from_attributes=True)
        await websocket.send_json(
            {
                "type": "stream_event",
                "sequence": event.sequence,
                "event": payload.model_dump(mode="json"),
            }
        )
    await websocket.send_json({"type": "replay_complete", "last_sequence": cursor})
    return cursor


__all__ = ["router"]
