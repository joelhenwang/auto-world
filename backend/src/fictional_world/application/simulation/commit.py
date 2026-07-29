"""Atomic Stage 0 operation commit (handbook ``06`` §18, task S0-SIM-002)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field
from sqlalchemy.exc import IntegrityError

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import ResourceKind
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.common.result import ValidationResult
from fictional_world.domain.effects.commands import (
    CreateRecentMemoryEffect,
    EffectBase,
    EffectCommand,
    MoveEntityEffect,
    ObserveEffect,
    RestEffect,
    SpendResourceEffect,
    WaitEffect,
)
from fictional_world.domain.events.persistence import (
    EventEffectRecord,
    OutboxMessageRecord,
    WorldEventRecord,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.rules.effects.context import EffectValidationContext, EntitySnapshot
from fictional_world.domain.rules.effects.project import project_effect
from fictional_world.domain.rules.effects.validate import validate_effects
from fictional_world.domain.world.records import AggregateVersionRecord


class EventCommitError(DomainError):
    """Commit rejected before or during the canonical write."""

    def __init__(self, message: str, *, validation: ValidationResult | None = None) -> None:
        self.validation = validation
        super().__init__(message)


class CommitOperationCommand(StrictContract):
    """Stage 0 operation commit input (scene_id optional until scene tables land)."""

    world_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=200)
    effects: tuple[EffectCommand, ...] = ()
    expected_versions: dict[str, int] = Field(default_factory=dict)
    """Keys are ``aggregate_type:uuid`` (e.g. ``character_state:<id>``)."""

    event_type: str = Field(default="OPERATION_COMMITTED", min_length=1, max_length=100)
    canonical_summary: str = Field(min_length=1, max_length=2_000)
    structured_facts: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
    importance: Decimal = Field(default=Decimal("0.5"), ge=0, le=1)
    visibility_class: str = Field(default="public", min_length=1, max_length=50)
    source_kind: str = Field(default="engine", min_length=1, max_length=50)
    absolute_phase_index: int = Field(default=0, ge=0)
    phase_run_id: UUID | None = None
    scene_id: UUID | None = None
    initiator_entity_id: UUID | None = None
    location_id: UUID | None = None
    observer_ids: tuple[UUID, ...] = ()
    """Characters that receive a bounded observation of this commit."""

    enqueue_outbox: bool = True


@dataclass(frozen=True, slots=True)
class CommitResult:
    event_id: UUID
    sequence_number: int
    already_existed: bool
    effect_count: int
    observation_count: int
    memory_count: int


class EventCommitService:
    """Owns the short DB transaction for Stage 0 effect commits. No model I/O."""

    async def commit(self, uow: UnitOfWork, command: CommitOperationCommand) -> CommitResult:
        existing = await uow.events.find_by_idempotency_key(command.idempotency_key)
        if existing is not None:
            return CommitResult(
                event_id=existing.id,
                sequence_number=existing.sequence_number,
                already_existed=True,
                effect_count=len(existing.effects),
                observation_count=0,
                memory_count=0,
            )

        world = await uow.worlds.lock_for_event_sequence(command.world_id)
        await uow.aggregate_versions.verify(command.world_id, command.expected_versions)

        context = await self._load_context(uow, command)
        validation = validate_effects(command.effects, context=context)
        if not validation.ok:
            raise EventCommitError(
                "effect validation failed",
                validation=validation,
            )

        sequence = world.current_event_sequence + 1
        event_id = uuid4()

        effect_rows, final_snapshots, memories = await self._project_and_prepare(
            uow,
            command=command,
            context=context,
            event_id=event_id,
        )

        observations = self._materialize_observations(command, event_id=event_id)
        outbox_messages = (
            self._build_outbox(command, event_id=event_id) if command.enqueue_outbox else ()
        )

        event = WorldEventRecord(
            id=event_id,
            world_id=command.world_id,
            sequence_number=sequence,
            absolute_phase_index=command.absolute_phase_index,
            phase_run_id=command.phase_run_id,
            scene_id=command.scene_id,
            event_type=command.event_type,
            initiator_entity_id=command.initiator_entity_id,
            location_id=command.location_id,
            canonical_summary=command.canonical_summary,
            structured_facts=dict(command.structured_facts),
            importance=command.importance,
            visibility_class=command.visibility_class,
            source_kind=command.source_kind,
            idempotency_key=command.idempotency_key,
            consistency_status="consistent",
            effects=effect_rows,
        )

        try:
            inserted = await uow.events.insert(event)
        except IntegrityError:
            # Concurrent commit won the idempotency race — return durable winner.
            raced = await uow.events.find_by_idempotency_key(command.idempotency_key)
            if raced is not None:
                await uow.rollback()
                return CommitResult(
                    event_id=raced.id,
                    sequence_number=raced.sequence_number,
                    already_existed=True,
                    effect_count=len(raced.effects),
                    observation_count=0,
                    memory_count=0,
                )
            raise

        for character_id, snap in final_snapshots.items():
            current = await uow.characters.get_state_for_update(character_id)
            expected = current.version
            updated = _apply_snapshot_to_state(current, snap)
            saved = await uow.characters.save_state(updated, expected_version=expected)
            await uow.aggregate_versions.upsert(
                AggregateVersionRecord(
                    world_id=command.world_id,
                    aggregate_type="character_state",
                    aggregate_id=character_id,
                    version=saved.version,
                ),
                expected_version=expected,
            )

        if observations:
            await uow.observations.insert_many(observations)
        memory_count = 0
        for memory in memories:
            await uow.recent_memories.insert(memory)
            memory_count += 1
        if outbox_messages:
            await uow.outbox.insert_many(outbox_messages)

        await uow.worlds.advance_event_sequence(
            command.world_id,
            next_sequence=sequence,
            expected_version=world.version,
        )
        return CommitResult(
            event_id=inserted.id,
            sequence_number=inserted.sequence_number,
            already_existed=False,
            effect_count=len(inserted.effects),
            observation_count=len(observations),
            memory_count=memory_count,
        )

    async def _load_context(
        self,
        uow: UnitOfWork,
        command: CommitOperationCommand,
    ) -> EffectValidationContext:
        character_ids: set[UUID] = set(command.observer_ids)
        location_ids: set[UUID] = set()
        for effect in command.effects:
            if isinstance(effect, WaitEffect | RestEffect | SpendResourceEffect | MoveEntityEffect):
                character_ids.add(effect.entity_id)
            if isinstance(effect, ObserveEffect):
                character_ids.add(effect.observer_id)
                # Observe targets may be characters or locations.
                for target_id in effect.target_entity_ids:
                    character_ids.add(target_id)
                    location_ids.add(target_id)
            if isinstance(effect, CreateRecentMemoryEffect):
                character_ids.add(effect.owner_character_id)
            if isinstance(effect, MoveEntityEffect):
                location_ids.add(effect.from_location_id)
                location_ids.add(effect.to_location_id)

        entities: dict[UUID, EntitySnapshot] = {}
        for character_id in character_ids:
            state = await uow.characters.get_state(character_id)
            if state is None:
                continue
            resources = {
                ResourceKind.STAMINA: float(state.stamina),
                ResourceKind.MANA: float(state.mana),
            }
            entities[character_id] = EntitySnapshot(
                entity_id=character_id,
                location_id=state.location_id,
                resources=resources,
                alive=state.life_status == "alive",
            )
            if state.location_id is not None:
                location_ids.add(state.location_id)

        return EffectValidationContext(
            entities=entities,
            known_location_ids=frozenset(location_ids),
            known_character_ids=frozenset(character_ids),
        )

    async def _project_and_prepare(
        self,
        uow: UnitOfWork,
        *,
        command: CommitOperationCommand,
        context: EffectValidationContext,
        event_id: UUID,
    ) -> tuple[
        tuple[EventEffectRecord, ...],
        dict[UUID, EntitySnapshot],
        list[RecentMemoryRecord],
    ]:
        working = EffectValidationContext(
            entities=dict(context.entities),
            known_location_ids=context.known_location_ids,
            known_character_ids=context.known_character_ids,
        )
        effect_rows: list[EventEffectRecord] = []
        mutated_ids: set[UUID] = set()
        memories: list[RecentMemoryRecord] = []
        initial_versions: dict[UUID, int] = {}

        for index, effect in enumerate(command.effects):
            entity_id = _effect_entity_id(effect)
            before_snap = working.entities.get(entity_id) if entity_id is not None else None
            before_payload = _snapshot_payload(before_snap)
            before_version: int | None = None
            if entity_id is not None and _effect_mutates_character(effect):
                if entity_id not in initial_versions:
                    state = await uow.characters.get_state(entity_id)
                    if state is not None:
                        initial_versions[entity_id] = state.version
                before_version = initial_versions.get(entity_id)

            projected = project_effect(effect, context=working)
            working = EffectValidationContext(
                entities=projected.entities,
                known_location_ids=working.known_location_ids,
                known_character_ids=working.known_character_ids,
            )
            after_snap = working.entities.get(entity_id) if entity_id is not None else None
            after_payload = _snapshot_payload(after_snap)

            if entity_id is not None and _effect_mutates_character(effect):
                mutated_ids.add(entity_id)

            for projected_memory in projected.memories:
                memories.append(
                    RecentMemoryRecord(
                        id=uuid4(),
                        world_id=command.world_id,
                        owner_character_id=projected_memory.owner_character_id,
                        memory_type=projected_memory.memory_kind,
                        content=projected_memory.text,
                        salience=Decimal(str(projected_memory.salience)),
                        confidence=Decimal(str(projected_memory.confidence)),
                        emotional_weight=Decimal("0"),
                        visibility="private",
                        occurred_phase_index=command.absolute_phase_index,
                        created_phase_index=command.absolute_phase_index,
                        decay_score=Decimal("1"),
                        status="active",
                        content_hash=_content_hash(projected_memory.text),
                        source_event_id=event_id,
                    )
                )

            effect_rows.append(
                EventEffectRecord(
                    id=uuid4(),
                    world_event_id=event_id,
                    effect_index=index,
                    effect_type=str(getattr(effect, "kind", "unknown")),
                    target_entity_id=entity_id,
                    effect_payload=_effect_payload(effect),
                    previous_state=before_payload,
                    resulting_state=after_payload,
                    target_version_before=before_version,
                    target_version_after=(
                        (before_version + 1) if before_version is not None else None
                    ),
                    source_attempt_ids=effect.source_attempt_ids,
                    validation_manifest={"ok": True},
                )
            )

        final_snapshots = {
            character_id: working.entities[character_id]
            for character_id in mutated_ids
            if character_id in working.entities
        }
        return tuple(effect_rows), final_snapshots, memories

    def _materialize_observations(
        self,
        command: CommitOperationCommand,
        *,
        event_id: UUID,
    ) -> list[ObservationPersistenceRecord]:
        observations: list[ObservationPersistenceRecord] = []
        for observer_id in command.observer_ids:
            summary = command.canonical_summary
            content_hash = _content_hash(f"{event_id}:{observer_id}:{summary}")
            observations.append(
                ObservationPersistenceRecord(
                    id=uuid4(),
                    world_event_id=event_id,
                    observer_id=observer_id,
                    observation_type="operation_commit",
                    perceived_summary=summary,
                    perceived_facts=dict(command.structured_facts),
                    confidence=Decimal("1"),
                    visibility_reason="observer_listed",
                    source_sense_tags=("sight",),
                    content_hash=content_hash,
                )
            )
        for effect in command.effects:
            if isinstance(effect, ObserveEffect):
                content_hash = _content_hash(f"{event_id}:{effect.observer_id}:{effect.effect_key}")
                observations.append(
                    ObservationPersistenceRecord(
                        id=uuid4(),
                        world_event_id=event_id,
                        observer_id=effect.observer_id,
                        observation_type="observe_effect",
                        perceived_summary=effect.justification,
                        perceived_facts={"effect_key": effect.effect_key},
                        confidence=Decimal("0.8"),
                        visibility_reason="observe_effect",
                        source_sense_tags=tuple(c.value for c in effect.channels) or ("sight",),
                        content_hash=content_hash,
                    )
                )
        return observations

    def _build_outbox(
        self,
        command: CommitOperationCommand,
        *,
        event_id: UUID,
    ) -> tuple[OutboxMessageRecord, ...]:
        return (
            OutboxMessageRecord(
                id=uuid4(),
                world_event_id=event_id,
                message_type="event.committed",
                payload={
                    "world_id": str(command.world_id),
                    "event_id": str(event_id),
                    "event_type": command.event_type,
                },
                idempotency_key=f"outbox:{command.idempotency_key}",
                state="pending",
            ),
        )


def _effect_entity_id(effect: EffectBase) -> UUID | None:
    if isinstance(effect, WaitEffect | RestEffect | SpendResourceEffect | MoveEntityEffect):
        return effect.entity_id
    if isinstance(effect, ObserveEffect):
        return effect.observer_id
    if isinstance(effect, CreateRecentMemoryEffect):
        return effect.owner_character_id
    return None


def _effect_mutates_character(effect: EffectBase) -> bool:
    return isinstance(effect, RestEffect | SpendResourceEffect | MoveEntityEffect)


def _snapshot_payload(snap: EntitySnapshot | None) -> dict[str, Any]:
    if snap is None:
        return {}
    return {
        "entity_id": str(snap.entity_id),
        "location_id": str(snap.location_id) if snap.location_id else None,
        "alive": snap.alive,
        "resources": {k.value: v for k, v in snap.resources.items()},
    }


def _effect_payload(effect: EffectBase) -> dict[str, Any]:
    data = effect.model_dump(mode="json")
    return {str(k): v for k, v in data.items()}


def _apply_snapshot_to_state(
    state: CharacterStateRecord,
    snap: EntitySnapshot,
) -> CharacterStateRecord:
    stamina = Decimal(str(snap.resources.get(ResourceKind.STAMINA, float(state.stamina))))
    mana = Decimal(str(snap.resources.get(ResourceKind.MANA, float(state.mana))))
    return state.model_copy(
        update={
            "location_id": snap.location_id,
            "stamina": stamina,
            "mana": mana,
            "life_status": "alive" if snap.alive else state.life_status,
        }
    )


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_character_state_key(character_id: UUID) -> str:
    return f"character_state:{character_id}"


__all__ = [
    "CommitOperationCommand",
    "CommitResult",
    "EventCommitError",
    "EventCommitService",
    "expected_character_state_key",
]
