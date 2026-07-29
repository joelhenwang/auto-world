"""Deterministic Stage 0 phase runner (S0-ORCH-002)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fictional_world.application.orchestration.clock import advance_world_clock
from fictional_world.application.orchestration.protocol import (
    PauseMode,
    PhaseAdvanceResult,
    ReconciliationReport,
)
from fictional_world.application.orchestration.scripted_actions import mira_stage0_effects
from fictional_world.application.orchestration.task_queue import CreateTaskCommand, TaskQueueService
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.simulation.commit import (
    CommitOperationCommand,
    EventCommitService,
    expected_character_state_key,
)
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.phases.records import (
    PhaseRunRecord,
    PhaseSnapshotCharacterRecord,
    PhaseSnapshotRecord,
)
from fictional_world.domain.phases.states import (
    PAUSE_SAFE_STATES,
    TERMINAL_PHASE_STATES,
    PhaseRunState,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.world.records import WorldClockRecord

WORKER_ID = "stage0-phase-runner"


class PhaseRunnerError(DomainError):
    """Raised when phase orchestration cannot proceed."""


def _phase_idempotency_key(world_id: UUID, absolute_phase_index: int) -> str:
    return f"world:{world_id}:phase:{absolute_phase_index}:PHASE_RUN:generation:0"


def _task_key(world_id: UUID, phase_id: UUID, task_type: str) -> str:
    return f"world:{world_id}:phase:{phase_id}:{task_type}:generation:0"


def _event_key(world_id: UUID, phase_id: UUID, kind: str) -> str:
    return f"world:{world_id}:phase:{phase_id}:event:{kind}:generation:0"


def _manifest_hash(manifest: dict[str, Any]) -> str:
    raw = json.dumps(manifest, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class DeterministicPhaseRunner:
    """Postgres-backed Stage 0 WorldOrchestrator adapter."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._tasks = TaskQueueService(uow)
        self._commit = EventCommitService()

    async def start_world(self, world_id: UUID) -> None:
        world = await self._uow.worlds.get(world_id)
        if world is None:
            raise PhaseRunnerError(f"world not found: {world_id}")
        if world.status not in {"active", "paused"}:
            raise PhaseRunnerError(f"world {world.slug} status {world.status} cannot start")

    async def request_phase_advance(
        self,
        world_id: UUID,
        *,
        stop_after_snapshot: bool = False,
    ) -> PhaseAdvanceResult:
        await self.start_world(world_id)
        clock = await self._require_clock(world_id)
        target_clock = await self._resolve_target_clock(world_id, clock)
        return await self._run_phase(
            world_id, target_clock, stop_after_snapshot=stop_after_snapshot
        )

    async def pause_world(self, world_id: UUID, mode: PauseMode) -> None:
        _ = mode
        phase = await self._uow.phases.find_active_for_world(world_id)
        if phase is None:
            return
        state = PhaseRunState(phase.state)
        if state in TERMINAL_PHASE_STATES:
            return
        if state not in PAUSE_SAFE_STATES and state is not PhaseRunState.PAUSED:
            # Soft pause: mark paused; resume continues from durable state.
            pass
        await self._uow.phases.save(
            phase.model_copy(update={"state": PhaseRunState.PAUSED.value}),
            expected_version=phase.version,
        )

    async def resume_world(self, world_id: UUID) -> PhaseAdvanceResult | None:
        phase = await self._uow.phases.find_active_for_world(world_id)
        if phase is None:
            return None
        clock = await self._require_clock(world_id)
        if clock.absolute_phase_index != phase.absolute_phase_index:
            # Align runner to the durable phase index clock when possible.
            pass
        target = clock.model_copy(
            update={
                "absolute_phase_index": phase.absolute_phase_index,
                "phase_name": phase.phase_name,
            }
        )
        if PhaseRunState(phase.state) is PhaseRunState.PAUSED:
            phase = await self._uow.phases.save(
                phase.model_copy(update={"state": PhaseRunState.PENDING.value}),
                expected_version=phase.version,
            )
        return await self._run_phase(world_id, target, existing=phase)

    async def reconcile(self, world_id: UUID) -> ReconciliationReport:
        phase = await self._uow.phases.find_active_for_world(world_id)
        if phase is None:
            return ReconciliationReport(
                world_id=world_id,
                active_phase_id=None,
                tasks_created=0,
                phase_completed=False,
                notes=("no active phase",),
            )
        before = await self._ensure_phase_tasks(world_id, phase)
        result = await self.resume_world(world_id)
        completed = False
        if result is not None:
            latest = await self._uow.phases.get(result.phase_run_id)
            completed = latest is not None and PhaseRunState(latest.state) is PhaseRunState.COMPLETED
        return ReconciliationReport(
            world_id=world_id,
            active_phase_id=phase.id,
            tasks_created=before,
            phase_completed=completed,
            notes=("reconciled active phase",),
        )

    async def _resolve_target_clock(
        self, world_id: UUID, clock: WorldClockRecord
    ) -> WorldClockRecord:
        current = await self._uow.phases.find_by_world_and_index(
            world_id, clock.absolute_phase_index
        )
        if current is None:
            return clock
        if PhaseRunState(current.state) not in TERMINAL_PHASE_STATES:
            return clock.model_copy(
                update={
                    "absolute_phase_index": current.absolute_phase_index,
                    "phase_name": current.phase_name,
                }
            )
        # Current index already completed — advance calendar for the next phase.
        return advance_world_clock(clock)

    async def _run_phase(
        self,
        world_id: UUID,
        target_clock: WorldClockRecord,
        *,
        existing: PhaseRunRecord | None = None,
        stop_after_snapshot: bool = False,
    ) -> PhaseAdvanceResult:
        phase = existing or await self._uow.phases.find_by_world_and_index(
            world_id, target_clock.absolute_phase_index
        )
        if phase is not None and PhaseRunState(phase.state) is PhaseRunState.COMPLETED:
            snapshot = await self._uow.snapshots.get_for_phase(phase.id)
            return PhaseAdvanceResult(
                phase_run_id=phase.id,
                absolute_phase_index=phase.absolute_phase_index,
                phase_name=phase.phase_name,
                already_completed=True,
                snapshot_id=snapshot.id if snapshot else None,
                event_ids=(),
            )

        if phase is None:
            character_ids = await self._uow.characters.list_character_ids_for_world(world_id)
            phase = await self._create_phase(world_id, target_clock, len(character_ids))

        await self._ensure_phase_tasks(world_id, phase)
        event_ids: list[UUID] = []

        phase = await self._set_state(phase, PhaseRunState.ACCEPTING_COMMANDS)
        await self._complete_task(world_id, phase.id, "APPLY_USER_COMMANDS")

        phase = await self._set_state(phase, PhaseRunState.ADVANCING_CLOCK)
        clock = await self._require_clock(world_id)
        if clock.absolute_phase_index != target_clock.absolute_phase_index:
            # Persist target calendar position with the tick event below.
            pass
        await self._complete_task(world_id, phase.id, "ADVANCE_CLOCK")

        phase = await self._set_state(phase, PhaseRunState.APPLYING_WORLD_TICK)
        tick = await self._commit_world_tick(world_id, phase, target_clock)
        event_ids.append(tick)
        await self._persist_clock(target_clock)
        await self._complete_task(world_id, phase.id, "WORLD_TICK")

        phase = await self._set_state(phase, PhaseRunState.DIRECTOR_REVIEW)
        await self._complete_task(world_id, phase.id, "DIRECTOR_REVIEW")

        phase = await self._set_state(phase, PhaseRunState.SNAPSHOT_SEALED)
        snapshot = await self._seal_snapshot(world_id, phase, target_clock)
        await self._complete_task(world_id, phase.id, "BUILD_PHASE_SNAPSHOT")

        if stop_after_snapshot:
            phase = await self._set_state(phase, PhaseRunState.PAUSED)
            return PhaseAdvanceResult(
                phase_run_id=phase.id,
                absolute_phase_index=phase.absolute_phase_index,
                phase_name=phase.phase_name,
                already_completed=False,
                snapshot_id=snapshot.id,
                event_ids=tuple(event_ids),
            )

        # Pause boundary: if marked paused after snapshot, stop here.
        refreshed = await self._uow.phases.get(phase.id)
        if refreshed is not None and PhaseRunState(refreshed.state) is PhaseRunState.PAUSED:
            return PhaseAdvanceResult(
                phase_run_id=phase.id,
                absolute_phase_index=phase.absolute_phase_index,
                phase_name=phase.phase_name,
                already_completed=False,
                snapshot_id=snapshot.id,
                event_ids=tuple(event_ids),
            )

        phase = await self._set_state(phase, PhaseRunState.GENERATING_INTENTS)
        await self._complete_task(world_id, phase.id, "SCRIPTED_CHARACTER_ACTION")

        phase = await self._set_state(phase, PhaseRunState.RESOLVING_SCENES)
        action_event = await self._commit_scripted_actions(world_id, phase, target_clock)
        event_ids.append(action_event)
        await self._complete_task(world_id, phase.id, "RESOLVE_SCENES")
        await self._complete_task(world_id, phase.id, "WRITE_MEMORIES")
        await self._complete_task(world_id, phase.id, "ENQUEUE_IMAGES")

        phase = await self._set_state(phase, PhaseRunState.FINALIZING)
        character_ids = await self._uow.characters.list_character_ids_for_world(world_id)
        now = datetime.now(UTC)
        phase = await self._uow.phases.save(
            phase.model_copy(
                update={
                    "state": PhaseRunState.COMPLETED.value,
                    "completed_character_count": len(character_ids),
                    "expected_scene_count": 1,
                    "completed_scene_count": 1,
                    "completed_at": now,
                }
            ),
            expected_version=phase.version,
        )
        await self._complete_task(world_id, phase.id, "FINALIZE_PHASE")

        return PhaseAdvanceResult(
            phase_run_id=phase.id,
            absolute_phase_index=phase.absolute_phase_index,
            phase_name=phase.phase_name,
            already_completed=False,
            snapshot_id=snapshot.id,
            event_ids=tuple(event_ids),
        )

    async def _create_phase(
        self, world_id: UUID, clock: WorldClockRecord, character_count: int
    ) -> PhaseRunRecord:
        key = _phase_idempotency_key(world_id, clock.absolute_phase_index)
        existing = await self._uow.phases.find_by_idempotency_key(key)
        if existing is not None:
            return existing
        now = datetime.now(UTC)
        return await self._uow.phases.insert(
            PhaseRunRecord(
                id=uuid4(),
                world_id=world_id,
                absolute_phase_index=clock.absolute_phase_index,
                phase_name=clock.phase_name,
                resolution_mode="detailed",
                state=PhaseRunState.PENDING.value,
                expected_character_count=character_count,
                completed_character_count=0,
                expected_scene_count=1,
                completed_scene_count=0,
                idempotency_key=key,
                started_at=now,
                version=0,
            )
        )

    async def _ensure_phase_tasks(self, world_id: UUID, phase: PhaseRunRecord) -> int:
        created = 0
        task_types = (
            "APPLY_USER_COMMANDS",
            "ADVANCE_CLOCK",
            "WORLD_TICK",
            "DIRECTOR_REVIEW",
            "BUILD_PHASE_SNAPSHOT",
            "SCRIPTED_CHARACTER_ACTION",
            "RESOLVE_SCENES",
            "WRITE_MEMORIES",
            "ENQUEUE_IMAGES",
            "FINALIZE_PHASE",
        )
        previous: UUID | None = None
        for task_type in task_types:
            result = await self._tasks.create(
                CreateTaskCommand(
                    task_type=task_type,
                    idempotency_key=_task_key(world_id, phase.id, task_type),
                    payload={
                        "world_id": str(world_id),
                        "phase_run_id": str(phase.id),
                    },
                    world_id=world_id,
                    phase_run_id=phase.id,
                    priority=10,
                    depends_on=(previous,) if previous is not None else (),
                )
            )
            if not result.already_existed:
                created += 1
            previous = result.task.id
        return created

    async def _complete_task(self, world_id: UUID, phase_id: UUID, task_type: str) -> None:
        key = _task_key(world_id, phase_id, task_type)
        task = await self._uow.tasks.find_by_idempotency_key(key)
        if task is None:
            return
        from fictional_world.domain.common.enums import TaskState

        if task.state is TaskState.SUCCEEDED:
            return
        now = datetime.now(UTC)
        if task.lease_owner == WORKER_ID and task.state in {
            TaskState.CLAIMED,
            TaskState.RUNNING,
        }:
            await self._tasks.complete(task.id, worker_id=WORKER_ID, now=now)
            return
        claimed = await self._tasks.claim(worker_id=WORKER_ID, now=now, limit=20)
        owned = next((row for row in claimed if row.id == task.id), None)
        if owned is not None:
            await self._tasks.complete(owned.id, worker_id=WORKER_ID, now=now)
            return
        current = await self._uow.tasks.get(task.id)
        if current is None or current.state is TaskState.SUCCEEDED:
            return
        if current.lease_owner == WORKER_ID:
            await self._tasks.complete(task.id, worker_id=WORKER_ID, now=now)
            return
        raise PhaseRunnerError(
            f"unable to complete task {task_type} for phase {phase_id} "
            f"(state={current.state.value})"
        )

    async def _commit_world_tick(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        clock: WorldClockRecord,
    ) -> UUID:
        result = await self._commit.commit(
            self._uow,
            CommitOperationCommand(
                world_id=world_id,
                idempotency_key=_event_key(world_id, phase.id, "WORLD_TICK"),
                event_type="WORLD_TICK",
                canonical_summary=(
                    f"World tick for {clock.phase_name} "
                    f"(absolute_phase_index={clock.absolute_phase_index})"
                ),
                structured_facts={
                    "phase_name": clock.phase_name,
                    "absolute_phase_index": clock.absolute_phase_index,
                    "absolute_day_index": clock.absolute_day_index,
                },
                absolute_phase_index=clock.absolute_phase_index,
                phase_run_id=phase.id,
                source_kind="engine",
                importance=Decimal("0.3"),
                effects=(),
                expected_versions={},
                enqueue_outbox=True,
            ),
        )
        return result.event_id

    async def _commit_scripted_actions(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        clock: WorldClockRecord,
    ) -> UUID:
        mira_id = seed_uuid("character/mira-talren")
        inn_id = seed_uuid("location/veycross/cinder-lantern-inn")
        state = await self._uow.characters.get_state(mira_id)
        if state is None:
            # World without Mira — no-op success for generic worlds.
            result = await self._commit.commit(
                self._uow,
                CommitOperationCommand(
                    world_id=world_id,
                    idempotency_key=_event_key(world_id, phase.id, "SCRIPTED_ACTIONS"),
                    event_type="SCRIPTED_ACTIONS",
                    canonical_summary="No scripted focus characters for this world.",
                    absolute_phase_index=clock.absolute_phase_index,
                    phase_run_id=phase.id,
                    effects=(),
                    expected_versions={},
                    enqueue_outbox=False,
                ),
            )
            return result.event_id

        effects = mira_stage0_effects(mira_id=mira_id, inn_id=inn_id)
        result = await self._commit.commit(
            self._uow,
            CommitOperationCommand(
                world_id=world_id,
                idempotency_key=_event_key(world_id, phase.id, "SCRIPTED_ACTIONS"),
                event_type="SCRIPTED_ACTIONS",
                canonical_summary="Mira waits, observes the inn, and rests.",
                structured_facts={
                    "character_key": "character/mira-talren",
                    "script": "wait,observe,rest,memory",
                },
                absolute_phase_index=clock.absolute_phase_index,
                phase_run_id=phase.id,
                initiator_entity_id=mira_id,
                location_id=state.location_id,
                observer_ids=(mira_id,),
                effects=effects,
                expected_versions={expected_character_state_key(mira_id): state.version},
                enqueue_outbox=True,
            ),
        )
        return result.event_id

    async def _seal_snapshot(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        clock: WorldClockRecord,
    ) -> PhaseSnapshotRecord:
        existing = await self._uow.snapshots.get_for_phase(phase.id)
        if existing is not None:
            return existing
        world = await self._uow.worlds.get(world_id)
        if world is None:
            raise PhaseRunnerError(f"world not found: {world_id}")
        character_ids = await self._uow.characters.list_character_ids_for_world(world_id)
        characters: list[PhaseSnapshotCharacterRecord] = []
        character_manifest: list[dict[str, Any]] = []
        snapshot_id = uuid4()
        for character_id in character_ids:
            state = await self._uow.characters.get_state(character_id)
            if state is None:
                continue
            context_hash = hashlib.sha256(
                f"{character_id}:{state.version}:{state.current_card_version_id}".encode()
            ).hexdigest()
            characters.append(
                PhaseSnapshotCharacterRecord(
                    snapshot_id=snapshot_id,
                    character_id=character_id,
                    character_state_version=state.version,
                    card_version_id=state.current_card_version_id,
                    location_id=state.location_id,
                    active_activity_id=state.active_activity_id,
                    context_source_hash=context_hash,
                    eligibility_status="eligible",
                    eligibility_reason="scripted_deterministic",
                )
            )
            character_manifest.append(
                {
                    "character_id": str(character_id),
                    "state_version": state.version,
                    "card_version_id": str(state.current_card_version_id),
                    "location_id": str(state.location_id) if state.location_id else None,
                }
            )
        manifest = {
            "world_id": str(world_id),
            "phase_run_id": str(phase.id),
            "absolute_phase_index": phase.absolute_phase_index,
            "phase_name": phase.phase_name,
            "source_event_sequence": world.current_event_sequence,
            "world_clock_version": clock.version,
            "characters": character_manifest,
        }
        now = datetime.now(UTC)
        return await self._uow.snapshots.insert(
            PhaseSnapshotRecord(
                id=snapshot_id,
                phase_run_id=phase.id,
                world_id=world_id,
                source_event_sequence=world.current_event_sequence,
                world_clock_version=clock.version,
                state_manifest=manifest,
                state_hash=_manifest_hash(manifest),
                sealed_at=now,
                characters=tuple(characters),
            )
        )

    async def _persist_clock(self, clock: WorldClockRecord) -> WorldClockRecord:
        current = await self._require_clock(clock.world_id)
        if (
            current.absolute_phase_index == clock.absolute_phase_index
            and current.phase_name == clock.phase_name
        ):
            return current
        updated = clock.model_copy(update={"version": current.version})
        return await self._uow.worlds.upsert_clock(
            updated, expected_version=current.version
        )

    async def _set_state(
        self, phase: PhaseRunRecord, state: PhaseRunState
    ) -> PhaseRunRecord:
        if PhaseRunState(phase.state) is state:
            return phase
        return await self._uow.phases.save(
            phase.model_copy(update={"state": state.value}),
            expected_version=phase.version,
        )

    async def _require_clock(self, world_id: UUID) -> WorldClockRecord:
        clock = await self._uow.worlds.get_clock(world_id)
        if clock is None:
            raise PhaseRunnerError(f"world clock missing for {world_id}")
        return clock
