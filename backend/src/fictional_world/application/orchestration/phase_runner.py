"""Deterministic Stage 0 phase runner (S0-ORCH-002)."""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4, uuid5

from fictional_world.agents.character_decision import DecisionGraphInput, run_decision_graph
from fictional_world.agents.character_reaction import ReactionGraphInput, run_reaction_graph
from fictional_world.agents.resolver import ResolutionGraphInput, run_resolution_graph
from fictional_world.application.context import (
    ContextTaskType,
    SealedContextPackage,
    assemble_character_context,
)
from fictional_world.application.models.protocols import TextModelGateway
from fictional_world.application.orchestration.budget import BudgetService
from fictional_world.application.orchestration.clock import advance_world_clock
from fictional_world.application.orchestration.protocol import (
    PauseMode,
    PhaseAdvanceResult,
    ReconciliationReport,
)
from fictional_world.application.orchestration.scripted_actions import mira_stage0_effects
from fictional_world.application.orchestration.task_queue import CreateTaskCommand, TaskQueueService
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.simulation.activation import ActivationResult
from fictional_world.application.simulation.commit import (
    CommitOperationCommand,
    EventCommitService,
    expected_character_state_key,
)
from fictional_world.application.simulation.request_estimate import (
    PhaseRequestEstimate,
    estimate_phase_model_requests,
)
from fictional_world.application.simulation.scene_assembly import assemble_scenes
from fictional_world.application.simulation.scene_commit import (
    CommitSceneCommand,
    SceneCommitService,
)
from fictional_world.application.simulation.time import (
    STAGE1_ENABLED_PHASE_NAMES,
    STAGE2_ENABLED_PHASE_NAMES,
)
from fictional_world.domain.common.enums import BudgetStatus
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
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    ReactionProposal,
    SceneDraft,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.world.records import WorldClockRecord

WORKER_ID = "stage0-phase-runner"
STAGE1_WORKER_ID = "stage1-phase-runner"
STAGE2_WORKER_ID = "stage2-phase-runner"
STAGE1_ENABLED_PHASES = STAGE1_ENABLED_PHASE_NAMES
STAGE2_ENABLED_PHASES = STAGE2_ENABLED_PHASE_NAMES
STAGE1_CHARACTER_IDS = (
    seed_uuid("character/mira-talren"),
    seed_uuid("character/dain-arcen"),
)
STAGE1_LOCATION_IDS = frozenset(
    {
        seed_uuid("location/veycross/cinder-lantern-inn"),
        seed_uuid("location/veycross/market-square"),
        seed_uuid("location/veycross/east-bridge"),
    }
)


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
    """Postgres-backed Stage 0 runner with additive Stage 1 / Stage 2 profiles."""

    def __init__(
        self,
        uow: UnitOfWork,
        *,
        model_gateway: TextModelGateway | None = None,
        stage1: bool = False,
        stage2: bool = False,
    ) -> None:
        if stage1 and stage2:
            raise PhaseRunnerError("stage1 and stage2 profiles are mutually exclusive")
        self._uow = uow
        self._tasks = TaskQueueService(uow)
        self._commit = EventCommitService()
        self._scene_commit = SceneCommitService(self._commit)
        self._budget = BudgetService(uow)
        self._model_gateway = model_gateway
        self._stage1 = stage1
        self._stage2 = stage2

    def estimate_phase_requests(
        self,
        activations: tuple[ActivationResult, ...] | list[ActivationResult],
        *,
        director_call_planned: bool = False,
        ambiguous_scene_count: int = 0,
    ) -> PhaseRequestEstimate:
        """Estimate mandatory model requests before starting a phase (Stage 2)."""

        return estimate_phase_model_requests(
            activations,
            director_call_planned=director_call_planned,
            ambiguous_scene_count=ambiguous_scene_count,
        )

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
            completed = (
                latest is not None and PhaseRunState(latest.state) is PhaseRunState.COMPLETED
            )
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
            target = clock
        elif PhaseRunState(current.state) not in TERMINAL_PHASE_STATES:
            target = clock.model_copy(
                update={
                    "absolute_phase_index": current.absolute_phase_index,
                    "phase_name": current.phase_name,
                }
            )
        else:
            # Current index already completed — advance calendar for the next phase.
            target = advance_world_clock(clock)
        if self._stage1:
            while target.phase_name not in STAGE1_ENABLED_PHASES:
                target = advance_world_clock(target)
        elif self._stage2 and target.phase_name not in STAGE2_ENABLED_PHASES:
            # Stage 2 uses the full ten-phase calendar; no skipping.
            raise PhaseRunnerError(
                f"Stage 2 profile does not recognize phase {target.phase_name!r}"
            )
        return target

    async def _run_phase(
        self,
        world_id: UUID,
        target_clock: WorldClockRecord,
        *,
        existing: PhaseRunRecord | None = None,
        stop_after_snapshot: bool = False,
    ) -> PhaseAdvanceResult:
        if self._stage1:
            return await self._run_stage1_phase(
                world_id,
                target_clock,
                existing=existing,
                stop_after_snapshot=stop_after_snapshot,
            )
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

    async def _run_stage1_phase(
        self,
        world_id: UUID,
        target_clock: WorldClockRecord,
        *,
        existing: PhaseRunRecord | None,
        stop_after_snapshot: bool,
    ) -> PhaseAdvanceResult:
        if self._model_gateway is None:
            raise PhaseRunnerError("Stage 1 profile requires a text model gateway")
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
                snapshot_id=None if snapshot is None else snapshot.id,
                event_ids=(),
            )

        active_character_ids = await self._stage1_active_character_ids(world_id)
        if len(active_character_ids) != len(STAGE1_CHARACTER_IDS):
            raise PhaseRunnerError("Stage 1 requires seeded Mira and Dain")
        if phase is None:
            phase = await self._create_phase(
                world_id,
                target_clock,
                len(active_character_ids),
            )
        phase = await self._reserve_stage1_budget(world_id, phase)
        await self._ensure_phase_tasks(world_id, phase)
        event_ids: list[UUID] = []

        phase = await self._set_state(phase, PhaseRunState.ACCEPTING_COMMANDS)
        await self._complete_task(world_id, phase.id, "APPLY_USER_COMMANDS")
        phase = await self._set_state(phase, PhaseRunState.ADVANCING_CLOCK)
        await self._complete_task(world_id, phase.id, "ADVANCE_CLOCK")
        phase = await self._set_state(phase, PhaseRunState.APPLYING_WORLD_TICK)
        event_ids.append(await self._commit_world_tick(world_id, phase, target_clock))
        await self._persist_clock(target_clock)
        await self._complete_task(world_id, phase.id, "WORLD_TICK")
        phase = await self._set_state(phase, PhaseRunState.DIRECTOR_REVIEW)
        await self._complete_task(world_id, phase.id, "DIRECTOR_REVIEW")
        phase = await self._set_state(phase, PhaseRunState.SNAPSHOT_SEALED)
        snapshot = await self._seal_snapshot(world_id, phase, target_clock)
        await self._complete_task(world_id, phase.id, "BUILD_PHASE_SNAPSHOT")

        if stop_after_snapshot:
            phase = await self._set_state(phase, PhaseRunState.PAUSED)
            await self._uow.commit()
            return PhaseAdvanceResult(
                phase_run_id=phase.id,
                absolute_phase_index=phase.absolute_phase_index,
                phase_name=phase.phase_name,
                already_completed=False,
                snapshot_id=snapshot.id,
                event_ids=tuple(event_ids),
            )

        refreshed = await self._uow.phases.get(phase.id)
        if refreshed is not None and PhaseRunState(refreshed.state) is PhaseRunState.PAUSED:
            await self._uow.commit()
            return PhaseAdvanceResult(
                phase_run_id=phase.id,
                absolute_phase_index=phase.absolute_phase_index,
                phase_name=phase.phase_name,
                already_completed=False,
                snapshot_id=snapshot.id,
                event_ids=tuple(event_ids),
            )

        phase = await self._set_state(phase, PhaseRunState.GENERATING_INTENTS)
        proposals, decision_contexts, actor_locations = await self._stage1_decisions(
            world_id,
            phase,
            snapshot,
        )
        scenes = assemble_scenes(phase.id, snapshot.id, proposals, actor_locations)
        reactions = await self._stage1_reactions(
            world_id,
            snapshot,
            scenes,
            proposals,
        )
        resolutions = await asyncio.gather(
            *(
                run_resolution_graph(
                    ResolutionGraphInput(
                        scene=scene,
                        proposals=tuple(
                            proposal
                            for proposal in proposals
                            if proposal.decision_request_id in scene.action_proposal_ids
                        ),
                        reactions=tuple(
                            reaction
                            for reaction in reactions
                            if reaction.scene_id == scene.scene_id
                        ),
                        resolution_request_id=uuid5(scene.scene_id, "resolution"),
                        actor_locations=actor_locations,
                        allowed_entity_ids=frozenset(active_character_ids),
                        allowed_location_ids=STAGE1_LOCATION_IDS,
                    ),
                    self._model_gateway,
                )
                for scene in scenes
            )
        )
        await self._complete_task(world_id, phase.id, "GENERATE_CHARACTER_INTENTS")
        await self._uow.commit()

        phase = await self._require_phase(phase.id)
        phase = await self._set_state(phase, PhaseRunState.RESOLVING_SCENES)
        resolution_by_scene = {item.scene_id: item for item in resolutions}
        snapshot_versions = {
            character.character_id: character.character_state_version
            for character in snapshot.characters
        }
        for scene in scenes:
            scene_proposals = tuple(
                proposal
                for proposal in proposals
                if proposal.decision_request_id in scene.action_proposal_ids
            )
            scene_reactions = tuple(
                reaction for reaction in reactions if reaction.scene_id == scene.scene_id
            )
            result = await self._scene_commit.commit(
                self._uow,
                CommitSceneCommand(
                    world_id=world_id,
                    phase_run_id=phase.id,
                    absolute_phase_index=phase.absolute_phase_index,
                    idempotency_key=f"phase-{phase.id}-scene-{scene.scene_id}",
                    scene=scene,
                    proposals=scene_proposals,
                    reactions=scene_reactions,
                    resolution=resolution_by_scene[scene.scene_id],
                    expected_versions={
                        expected_character_state_key(character_id): snapshot_versions[character_id]
                        for character_id in scene.participant_ids
                    },
                    observer_ids=scene.participant_ids,
                    knowledge_scope_hashes={
                        character_id: decision_contexts[character_id].package_hash
                        for character_id in scene.participant_ids
                    },
                ),
            )
            event_ids.append(result.event_id)
            await self._uow.commit()

        await self._complete_task(world_id, phase.id, "RESOLVE_SCENES")
        await self._complete_task(world_id, phase.id, "WRITE_MEMORIES")
        await self._complete_task(world_id, phase.id, "ENQUEUE_IMAGES")
        phase = await self._require_phase(phase.id)
        phase = await self._set_state(phase, PhaseRunState.FINALIZING)
        now = datetime.now(UTC)
        phase = await self._uow.phases.save(
            phase.model_copy(
                update={
                    "state": PhaseRunState.COMPLETED.value,
                    "completed_character_count": len(active_character_ids),
                    "expected_scene_count": len(scenes),
                    "completed_scene_count": len(scenes),
                    "completed_at": now,
                }
            ),
            expected_version=phase.version,
        )
        await self._complete_task(world_id, phase.id, "FINALIZE_PHASE")
        if phase.request_reservation_id is not None:
            reservation = await self._uow.budgets.get(phase.request_reservation_id)
            if reservation is not None and reservation.status is BudgetStatus.RESERVED:
                await self._budget.consume(reservation.id, now=now)
        return PhaseAdvanceResult(
            phase_run_id=phase.id,
            absolute_phase_index=phase.absolute_phase_index,
            phase_name=phase.phase_name,
            already_completed=False,
            snapshot_id=snapshot.id,
            event_ids=tuple(event_ids),
        )

    async def _stage1_active_character_ids(self, world_id: UUID) -> tuple[UUID, ...]:
        world_character_ids = set(await self._uow.characters.list_character_ids_for_world(world_id))
        return tuple(
            character_id
            for character_id in STAGE1_CHARACTER_IDS
            if character_id in world_character_ids
        )

    async def _reserve_stage1_budget(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
    ) -> PhaseRunRecord:
        reservation = await self._budget.reserve_for_duration(
            reservation_key=f"stage1:phase:{phase.id}:model-requests",
            required_request_count=8,
            provider_kind="fake",
            model_slug="fake/stage1",
            ttl=timedelta(minutes=30),
            world_id=world_id,
            phase_run_id=phase.id,
        )
        if phase.request_reservation_id == reservation.reservation.id:
            return phase
        return await self._uow.phases.save(
            phase.model_copy(update={"request_reservation_id": reservation.reservation.id}),
            expected_version=phase.version,
        )

    async def _stage1_decisions(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        snapshot: PhaseSnapshotRecord,
    ) -> tuple[
        tuple[ActionProposal, ...],
        dict[UUID, SealedContextPackage],
        dict[UUID, UUID | None],
    ]:
        if self._model_gateway is None:
            raise PhaseRunnerError("Stage 1 profile requires a text model gateway")
        snapshot_characters = tuple(
            sorted(
                (
                    character
                    for character in snapshot.characters
                    if character.character_id in STAGE1_CHARACTER_IDS
                ),
                key=lambda character: character.character_id.int,
            )
        )
        actor_locations = {
            character.character_id: character.location_id for character in snapshot_characters
        }
        contexts: dict[UUID, SealedContextPackage] = {}
        for character in snapshot_characters:
            state = await self._uow.characters.get_state(character.character_id)
            card = await self._uow.characters.get_card(character.card_version_id)
            if state is None or card is None:
                raise PhaseRunnerError(f"snapshot character data missing: {character.character_id}")
            memories = await self._uow.recent_memories.list_for_owner(
                character.character_id,
                world_id=world_id,
                limit=12,
            )
            peers = tuple(
                peer.character_id
                for peer in snapshot_characters
                if peer.character_id != character.character_id
                and peer.location_id == character.location_id
            )
            contexts[character.character_id] = assemble_character_context(
                observer_id=character.character_id,
                phase_snapshot_id=snapshot.id,
                task_type=ContextTaskType.CHARACTER_DECISION,
                card=card,
                state=state,
                recent_memories=tuple(memory.content for memory in memories),
                perception_facts=(
                    {
                        "source_id": f"snapshot:{snapshot.id}:{character.character_id}",
                        "location_id": (
                            None if character.location_id is None else str(character.location_id)
                        ),
                        "co_located_character_ids": [str(peer) for peer in peers],
                    },
                ),
                co_located_character_ids=peers,
                package_id=uuid5(snapshot.id, f"decision-context:{character.character_id}"),
                now=snapshot.sealed_at,
            )

        # Explicitly close the read transaction before concurrent model inference.
        await self._uow.commit()
        proposals = await asyncio.gather(
            *(
                run_decision_graph(
                    DecisionGraphInput(
                        context=contexts[character.character_id],
                        phase_label=phase.phase_name,
                        decision_request_id=uuid5(phase.id, f"decision:{character.character_id}"),
                        allowed_entity_ids=frozenset(STAGE1_CHARACTER_IDS),
                        allowed_location_ids=STAGE1_LOCATION_IDS,
                        other_character_names=(
                            "Dain" if character.character_id == STAGE1_CHARACTER_IDS[0] else "Mira",
                        ),
                    ),
                    self._model_gateway,
                )
                for character in snapshot_characters
            )
        )
        return tuple(proposals), contexts, actor_locations

    async def _stage1_reactions(
        self,
        world_id: UUID,
        snapshot: PhaseSnapshotRecord,
        scenes: tuple[SceneDraft, ...],
        proposals: tuple[ActionProposal, ...],
    ) -> tuple[ReactionProposal, ...]:
        if self._model_gateway is None:
            raise PhaseRunnerError("Stage 1 profile requires a text model gateway")
        proposal_by_id = {proposal.decision_request_id: proposal for proposal in proposals}
        snapshot_by_character = {
            character.character_id: character for character in snapshot.characters
        }
        jobs: list[ReactionGraphInput] = []
        for scene in scenes:
            for proposal_id in scene.action_proposal_ids:
                proposal = proposal_by_id[proposal_id]
                reactor_ids = tuple(
                    target_id
                    for target_id in proposal.target_entity_ids
                    if target_id in scene.participant_ids and target_id != proposal.actor_id
                )
                for reactor_id in reactor_ids:
                    character = snapshot_by_character[reactor_id]
                    state = await self._uow.characters.get_state(reactor_id)
                    card = await self._uow.characters.get_card(character.card_version_id)
                    if state is None or card is None:
                        raise PhaseRunnerError(f"reaction character data missing: {reactor_id}")
                    memories = await self._uow.recent_memories.list_for_owner(
                        reactor_id,
                        world_id=world_id,
                        limit=12,
                    )
                    request_id = uuid5(
                        scene.scene_id,
                        f"reaction:{reactor_id}:{proposal.decision_request_id}",
                    )
                    context = assemble_character_context(
                        observer_id=reactor_id,
                        phase_snapshot_id=snapshot.id,
                        task_type=ContextTaskType.CHARACTER_REACTION,
                        card=card,
                        state=state,
                        recent_memories=tuple(memory.content for memory in memories),
                        co_located_character_ids=tuple(
                            value for value in scene.participant_ids if value != reactor_id
                        ),
                        scene_working={
                            "scene_id": str(scene.scene_id),
                            "participant_ids": [str(value) for value in scene.participant_ids],
                            "snapshot_id": str(snapshot.id),
                        },
                        package_id=uuid5(
                            snapshot.id,
                            f"reaction-context:{request_id}",
                        ),
                        now=snapshot.sealed_at,
                    )
                    jobs.append(
                        ReactionGraphInput(
                            context=context,
                            scene_id=scene.scene_id,
                            reaction_request_id=request_id,
                            perceived_attempt=proposal,
                            remaining_beat_budget=max(1, scene.beat_budget - 1),
                            allowed_entity_ids=frozenset(scene.participant_ids),
                        )
                    )
        if not jobs:
            return ()
        # Explicitly close reaction-context reads before model inference.
        await self._uow.commit()
        reactions = await asyncio.gather(
            *(run_reaction_graph(graph_input, self._model_gateway) for graph_input in jobs)
        )
        return tuple(reactions)

    async def _require_phase(self, phase_id: UUID) -> PhaseRunRecord:
        phase = await self._uow.phases.get(phase_id)
        if phase is None:
            raise PhaseRunnerError(f"phase not found: {phase_id}")
        return phase

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
        character_task = (
            "GENERATE_CHARACTER_INTENTS" if self._stage1 else "SCRIPTED_CHARACTER_ACTION"
        )
        task_types = (
            "APPLY_USER_COMMANDS",
            "ADVANCE_CLOCK",
            "WORLD_TICK",
            "DIRECTOR_REVIEW",
            "BUILD_PHASE_SNAPSHOT",
            character_task,
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
        if self._stage2:
            worker_id = STAGE2_WORKER_ID
        elif self._stage1:
            worker_id = STAGE1_WORKER_ID
        else:
            worker_id = WORKER_ID
        if task.lease_owner == worker_id and task.state in {
            TaskState.CLAIMED,
            TaskState.RUNNING,
        }:
            await self._tasks.complete(task.id, worker_id=worker_id, now=now)
            return
        claimed = await self._tasks.claim(worker_id=worker_id, now=now, limit=20)
        owned = next((row for row in claimed if row.id == task.id), None)
        if owned is not None:
            await self._tasks.complete(owned.id, worker_id=worker_id, now=now)
            return
        current = await self._uow.tasks.get(task.id)
        if current is None or current.state is TaskState.SUCCEEDED:
            return
        if current.lease_owner == worker_id:
            await self._tasks.complete(task.id, worker_id=worker_id, now=now)
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

        effects = mira_stage0_effects(
            mira_id=mira_id,
            inn_id=inn_id,
            absolute_phase_index=clock.absolute_phase_index,
        )
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
        return await self._uow.worlds.upsert_clock(updated, expected_version=current.version)

    async def _set_state(self, phase: PhaseRunRecord, state: PhaseRunState) -> PhaseRunRecord:
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
