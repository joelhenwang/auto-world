"""Stage 2 phase + day workflow ops mixed into DeterministicPhaseRunner."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import UUID, uuid5

from fictional_world.agents.character_decision import DecisionGraphInput, run_decision_graph
from fictional_world.agents.character_reaction import ReactionGraphInput, run_reaction_graph
from fictional_world.agents.director_proposal import (
    DirectorProposalGraphInput,
    run_director_proposal_graph,
)
from fictional_world.agents.memory_consolidation import (
    MemoryConsolidationGraphInput,
    run_memory_consolidation_graph,
)
from fictional_world.agents.resolver import ResolutionGraphInput, run_resolution_graph
from fictional_world.application.context import (
    ContextTaskType,
    SealedContextPackage,
    assemble_character_context,
)
from fictional_world.application.director.persistence import (
    DirectorPersistencePorts,
    record_narrative_metric,
)
from fictional_world.application.director.types import DirectorWorldSnapshot
from fictional_world.application.memory.daily_consolidation import (
    DAY_RUN_STATUS_COMPLETED,
    day_consolidation_idempotency_key,
    day_phase_bounds,
)
from fictional_world.application.models.protocols import TextModelGateway
from fictional_world.application.orchestration.budget import BudgetService
from fictional_world.application.orchestration.protocol import (
    DayAdvanceResult,
    PhaseAdvanceResult,
    SevenDayRunResult,
)
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.simulation.activation import (
    ActivationDecision,
    ActivationResult,
    evaluate_activation_decision,
)
from fictional_world.application.simulation.commit import expected_character_state_key
from fictional_world.application.simulation.request_estimate import PhaseRequestEstimate
from fictional_world.application.simulation.scene_assembly import (
    assemble_multiparty_scenes,
    assemble_scenes,
)
from fictional_world.application.simulation.scene_commit import (
    CommitSceneCommand,
    SceneCommitService,
)
from fictional_world.application.simulation.time import STAGE2_PHASE_PROFILE
from fictional_world.domain.common.enums import ActionFamily, BudgetStatus, Visibility
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.continuity.persistence import DayRunPersistenceRecord
from fictional_world.domain.knowledge.persistence import (
    ObservationPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.phases.records import (
    PhaseRunRecord,
    PhaseSnapshotCharacterRecord,
    PhaseSnapshotRecord,
)
from fictional_world.domain.phases.states import PhaseRunState
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    FallbackAction,
    ReactionProposal,
    SceneDraft,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.world.records import WorldClockRecord

STAGE2_CHARACTER_IDS = (
    seed_uuid("character/mira-talren"),
    seed_uuid("character/dain-arcen"),
    seed_uuid("character/iri-voss"),
    seed_uuid("character/torren-kest"),
)
STAGE2_CHARACTER_NAMES: dict[UUID, str] = {
    seed_uuid("character/mira-talren"): "Mira",
    seed_uuid("character/dain-arcen"): "Dain",
    seed_uuid("character/iri-voss"): "Iri",
    seed_uuid("character/torren-kest"): "Torren",
}
STAGE2_LOCATION_IDS = frozenset(
    {
        seed_uuid("location/veycross/cinder-lantern-inn"),
        seed_uuid("location/veycross/market-square"),
        seed_uuid("location/veycross/east-bridge"),
        seed_uuid("location/veycross/lantern-annex"),
        seed_uuid("location/veycross/river-forge"),
        seed_uuid("location/veycross/wardens-yard"),
        seed_uuid("location/veycross/lantern-ward"),
        seed_uuid("location/north-road/corridor"),
        seed_uuid("location/north-road/old-beacon"),
        seed_uuid("location/west-road/ash-orchard"),
    }
)


class Stage2PhaseOps:
    """Mixin: Stage 2 ten-phase runner + day / seven-day workflow.

    Attribute and helper stubs are declared for basedpyright; concrete
    implementations live on ``DeterministicPhaseRunner``.
    """

    _uow: UnitOfWork
    _model_gateway: TextModelGateway | None
    _budget: BudgetService
    _scene_commit: SceneCommitService
    _stage2: bool

    async def start_world(self, world_id: UUID) -> None:
        raise NotImplementedError

    async def request_phase_advance(
        self,
        world_id: UUID,
        *,
        stop_after_snapshot: bool = False,
    ) -> PhaseAdvanceResult:
        raise NotImplementedError

    def estimate_phase_requests(
        self,
        activations: tuple[ActivationResult, ...] | list[ActivationResult],
        *,
        director_call_planned: bool = False,
        ambiguous_scene_count: int = 0,
    ) -> PhaseRequestEstimate:
        raise NotImplementedError

    async def _create_phase(
        self, world_id: UUID, clock: WorldClockRecord, character_count: int
    ) -> PhaseRunRecord:
        raise NotImplementedError

    async def _ensure_phase_tasks(self, world_id: UUID, phase: PhaseRunRecord) -> int:
        raise NotImplementedError

    async def _set_state(self, phase: PhaseRunRecord, state: PhaseRunState) -> PhaseRunRecord:
        raise NotImplementedError

    async def _complete_task(self, world_id: UUID, phase_id: UUID, task_type: str) -> None:
        raise NotImplementedError

    async def _commit_world_tick(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        clock: WorldClockRecord,
    ) -> UUID:
        raise NotImplementedError

    async def _persist_clock(self, clock: WorldClockRecord) -> WorldClockRecord:
        raise NotImplementedError

    async def _seal_snapshot(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        clock: WorldClockRecord,
    ) -> PhaseSnapshotRecord:
        raise NotImplementedError

    async def _require_phase(self, phase_id: UUID) -> PhaseRunRecord:
        raise NotImplementedError

    async def _require_clock(self, world_id: UUID) -> WorldClockRecord:
        raise NotImplementedError

    async def _resolve_target_clock(
        self, world_id: UUID, clock: WorldClockRecord
    ) -> WorldClockRecord:
        raise NotImplementedError

    async def _run_stage2_phase(
        self,
        world_id: UUID,
        target_clock: WorldClockRecord,
        *,
        existing: PhaseRunRecord | None,
        stop_after_snapshot: bool,
    ) -> PhaseAdvanceResult:
        if self._model_gateway is None:
            raise self._stage2_error("Stage 2 profile requires a text model gateway")
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

        active_character_ids = await self._stage2_active_character_ids(world_id)
        if len(active_character_ids) != len(STAGE2_CHARACTER_IDS):
            raise self._stage2_error("Stage 2 requires four seeded focus characters")
        if phase is None:
            phase = await self._create_phase(
                world_id,
                target_clock,
                len(active_character_ids),
            )
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
        await self._stage2_director_review(world_id, phase, target_clock)
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

        activations = await self._stage2_activations(world_id, phase, snapshot)
        phase = await self._reserve_stage2_budget(world_id, phase, activations)

        phase = await self._set_state(phase, PhaseRunState.GENERATING_INTENTS)
        proposals, decision_contexts, actor_locations = await self._stage2_decisions(
            world_id,
            phase,
            snapshot,
            activations,
        )
        scenes = self._stage2_assemble_scenes(
            phase.id,
            snapshot.id,
            proposals,
            actor_locations,
            decision_contexts,
        )
        reactions = await self._stage2_reactions(
            world_id,
            snapshot,
            scenes,
            proposals,
        )
        if scenes:
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
                            allowed_location_ids=STAGE2_LOCATION_IDS,
                        ),
                        self._model_gateway,
                    )
                    for scene in scenes
                )
            )
        else:
            resolutions = ()
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
            resolution = resolution_by_scene[scene.scene_id]
            # Disambiguate routine memory content across phases (unique content_hash).
            resolution = resolution.model_copy(
                update={
                    "canonical_summary": (
                        f"{resolution.canonical_summary} "
                        f"[phase={phase.absolute_phase_index} scene={scene.scene_id}]"
                    )
                }
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
                    resolution=resolution,
                    expected_versions={
                        expected_character_state_key(character_id): snapshot_versions[character_id]
                        for character_id in scene.participant_ids
                        if character_id in snapshot_versions
                    },
                    observer_ids=scene.participant_ids,
                    knowledge_scope_hashes={
                        character_id: decision_contexts[character_id].package_hash
                        for character_id in scene.participant_ids
                        if character_id in decision_contexts
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
                    "expected_scene_count": max(1, len(scenes)),
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

    async def run_day(
        self,
        world_id: UUID,
    ) -> DayAdvanceResult:
        """Advance ten Stage 2 phases then finalize the calendar day."""

        if not self._stage2:
            raise self._stage2_error("run_day requires stage2=True")
        await self.start_world(world_id)
        clock = await self._require_clock(world_id)
        # Resolve the next runnable phase first so day_index reflects midnight→dawn rollover.
        target = await self._resolve_target_clock(world_id, clock)
        day_index = target.absolute_day_index
        phase_results: list[PhaseAdvanceResult] = []
        for _ in STAGE2_PHASE_PROFILE:
            advance = await self.request_phase_advance(world_id)
            phase_results.append(advance)

        recovery_snapshot_id = phase_results[-1].snapshot_id if phase_results else None
        day_run, already, hard_violations = await self.finalize_day(
            world_id,
            day_index=day_index,
            recovery_snapshot_id=recovery_snapshot_id,
        )
        return DayAdvanceResult(
            world_id=world_id,
            day_index=day_index,
            phase_results=tuple(phase_results),
            day_run_id=None if day_run is None else day_run.id,
            recovery_snapshot_id=(None if day_run is None else day_run.recovery_snapshot_id),
            already_finalized=already,
            hard_audit_violations=hard_violations,
        )

    async def run_seven_days(
        self,
        world_id: UUID,
    ) -> SevenDayRunResult:
        """Run seven consecutive Stage 2 days."""

        if not self._stage2:
            raise self._stage2_error("run_seven_days requires stage2=True")
        days: list[DayAdvanceResult] = []
        for _ in range(7):
            days.append(await self.run_day(world_id))
        return SevenDayRunResult(world_id=world_id, day_results=tuple(days))

    async def finalize_day(
        self,
        world_id: UUID,
        *,
        day_index: int,
        recovery_snapshot_id: UUID | None,
    ) -> tuple[DayRunPersistenceRecord | None, bool, int]:
        """Idempotent day-finalization barrier (consolidation + audit + recovery)."""

        key = day_consolidation_idempotency_key(world_id, day_index)
        existing = await self._uow.day_runs.find_by_idempotency_key(key)
        if existing is not None and existing.status == DAY_RUN_STATUS_COMPLETED:
            audit = await self._uow.daily_audits.get_by_day_run(existing.id)
            hard = 0 if audit is None else audit.hard_violation_count
            if recovery_snapshot_id is not None and existing.recovery_snapshot_id is None:
                existing = await self._uow.day_runs.save(
                    existing.model_copy(update={"recovery_snapshot_id": recovery_snapshot_id}),
                    expected_version=existing.version,
                )
            return existing, True, hard

        character_ids = await self._stage2_active_character_ids(world_id)
        start_phase, end_phase = day_phase_bounds(day_index)
        events = await self._uow.events.list_for_world(world_id, limit=2_000)
        day_event_ids = {
            event.id for event in events if start_phase <= event.absolute_phase_index <= end_phase
        }
        observations: list[ObservationPersistenceRecord] = []
        memories: list[RecentMemoryRecord] = []
        for character_id in character_ids:
            owned_obs = await self._uow.observations.list_for_observer(
                character_id,
                limit=500,
            )
            observations.extend(obs for obs in owned_obs if obs.world_event_id in day_event_ids)
            memories.extend(
                await self._uow.recent_memories.list_for_owner(
                    character_id,
                    world_id=world_id,
                    limit=200,
                )
            )
        secret_access: list[SecretAccessPersistenceRecord] = []
        for character_id in character_ids:
            secret_access.extend(
                await self._uow.secret_access.list_for_holder(
                    character_id,
                    world_id=world_id,
                )
            )

        result = await run_memory_consolidation_graph(
            MemoryConsolidationGraphInput(
                world_id=world_id,
                day_index=day_index,
                character_ids=character_ids,
                observations=tuple(observations),
                recent_memories=tuple(memories),
                secret_access=tuple(secret_access),
            )
        )
        day_run = result.day_run.model_copy(update={"recovery_snapshot_id": recovery_snapshot_id})
        # Re-check after model/CPU work for concurrent duplicate delivery.
        raced = await self._uow.day_runs.find_by_idempotency_key(key)
        if raced is not None and raced.status == DAY_RUN_STATUS_COMPLETED:
            audit = await self._uow.daily_audits.get_by_day_run(raced.id)
            return raced, True, 0 if audit is None else audit.hard_violation_count

        await self._uow.day_runs.insert(day_run)
        await self._uow.daily_audits.insert(
            result.daily_audit.model_copy(update={"day_run_id": day_run.id})
        )
        for character in result.characters:
            await self._uow.summaries.insert(character.summary)
            if character.sources:
                await self._uow.summaries.insert_sources(character.sources)
            await self._uow.diary_entries.insert(character.diary)
        return day_run, False, result.daily_audit.hard_violation_count

    def _stage2_error(self, message: str) -> DomainError:
        return DomainError(message)

    async def _stage2_active_character_ids(
        self,
        world_id: UUID,
    ) -> tuple[UUID, ...]:
        world_character_ids = set(await self._uow.characters.list_character_ids_for_world(world_id))
        return tuple(
            character_id
            for character_id in STAGE2_CHARACTER_IDS
            if character_id in world_character_ids
        )

    async def _stage2_director_review(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        clock: WorldClockRecord,
    ) -> None:
        """Evaluate Director trigger; quiet path records metrics without inventing canon."""

        snapshot = DirectorWorldSnapshot(
            world_id=world_id,
            current_phase_index=clock.absolute_phase_index,
            phases_since_meaningful_choice=0,
            recent_location_keys=(),
            recent_participant_keys=(),
            recent_action_families=(),
            goal_progress_delta=0.2,
            unresolved_hook_count=0,
            emotional_intensity_history=(0.4, 0.45, 0.5),
            last_disruptive_event_phase=None,
            protected_secret_keys=(),
            recent_trope_tags=(),
            trope_cooldown_remaining=0,
        )
        # Close DB work before any potential model path (graph is local/no-model here).
        await self._uow.commit()
        graph_result = await run_director_proposal_graph(
            DirectorProposalGraphInput(world_snapshot=snapshot, proposal=None)
        )
        await record_narrative_metric(
            cast(DirectorPersistencePorts, self._uow),
            world_id=world_id,
            metric_key="director.trigger",
            metric_value=graph_result.trigger.metrics.stagnation_score,
            window_start_phase=phase.absolute_phase_index,
            window_end_phase=phase.absolute_phase_index,
            payload={
                "should_call": graph_result.trigger.should_call,
                "reasons": list(graph_result.trigger.reasons),
                "accepted": graph_result.accepted_proposal is not None,
                "fallback": (
                    None if graph_result.fallback is None else graph_result.fallback.reason
                ),
            },
        )
        # Validated effects would commit via EventCommitService — quiet path skips.

    async def _stage2_activations(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        snapshot: PhaseSnapshotRecord,
    ) -> dict[UUID, ActivationResult]:
        activations: dict[UUID, ActivationResult] = {}
        payload: list[dict[str, str]] = []
        for character in snapshot.characters:
            if character.character_id not in STAGE2_CHARACTER_IDS:
                continue
            state = await self._uow.characters.get_state(character.character_id)
            if state is None:
                continue
            activity = None
            if state.active_activity_id is not None:
                activity = await self._uow.activities.get(state.active_activity_id)
            result = evaluate_activation_decision(
                state,
                phase=phase.phase_name,
                active_activity=activity,
            )
            activations[character.character_id] = result
            payload.append(
                {
                    "character_id": str(character.character_id),
                    "decision": result.decision.value,
                    "reason": result.reason,
                }
            )
        await record_narrative_metric(
            cast(DirectorPersistencePorts, self._uow),
            world_id=world_id,
            metric_key="activation.phase",
            metric_value=sum(1 for item in activations.values() if item.requires_model),
            window_start_phase=phase.absolute_phase_index,
            window_end_phase=phase.absolute_phase_index,
            payload={"activations": payload},
        )
        return activations

    async def _reserve_stage2_budget(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        activations: dict[UUID, ActivationResult],
    ) -> PhaseRunRecord:
        estimate = self.estimate_phase_requests(
            tuple(activations.values()),
            director_call_planned=False,
            ambiguous_scene_count=len(activations),
        )
        required = max(1, estimate.total_mandatory)
        reservation = await self._budget.reserve_for_duration(
            reservation_key=f"stage2:phase:{phase.id}:model-requests",
            required_request_count=required,
            provider_kind="fake",
            model_slug="fake/stage2",
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

    async def _stage2_decisions(
        self,
        world_id: UUID,
        phase: PhaseRunRecord,
        snapshot: PhaseSnapshotRecord,
        activations: dict[UUID, ActivationResult],
    ) -> tuple[
        tuple[ActionProposal, ...],
        dict[UUID, SealedContextPackage],
        dict[UUID, UUID | None],
    ]:
        if self._model_gateway is None:
            raise self._stage2_error("Stage 2 profile requires a text model gateway")
        snapshot_characters = tuple(
            sorted(
                (
                    character
                    for character in snapshot.characters
                    if character.character_id in STAGE2_CHARACTER_IDS
                ),
                key=lambda character: character.character_id.int,
            )
        )
        actor_locations = {
            character.character_id: character.location_id for character in snapshot_characters
        }
        contexts: dict[UUID, SealedContextPackage] = {}
        continue_proposals: list[ActionProposal] = []
        decision_characters: list[PhaseSnapshotCharacterRecord] = []
        for character in snapshot_characters:
            activation = activations.get(character.character_id)
            if activation is None:
                continue
            if activation.decision in {
                ActivationDecision.SLEEP,
                ActivationDecision.SKIP,
            }:
                continue
            state = await self._uow.characters.get_state(character.character_id)
            card = await self._uow.characters.get_card(character.card_version_id)
            if state is None or card is None:
                raise self._stage2_error(
                    f"snapshot character data missing: {character.character_id}"
                )
            if activation.decision is ActivationDecision.CONTINUE_ACTIVITY:
                continue_proposals.append(
                    ActionProposal(
                        decision_request_id=uuid5(phase.id, f"continue:{character.character_id}"),
                        actor_id=character.character_id,
                        action_family=ActionFamily.CONTINUE_ACTIVITY,
                        description=(
                            f"Continue activity without a model call ({activation.reason})."
                        ),
                        visibility=Visibility.OBSERVABLE,
                        fallback=FallbackAction(
                            action_family=ActionFamily.WAIT,
                            description="Wait if continuation cannot proceed.",
                        ),
                        continuation_activity_id=state.active_activity_id,
                    )
                )
                # Still assemble a sealed context hash for scene commit knowledge scopes.
                contexts[character.character_id] = assemble_character_context(
                    observer_id=character.character_id,
                    phase_snapshot_id=snapshot.id,
                    task_type=ContextTaskType.CHARACTER_DECISION,
                    card=card,
                    state=state,
                    recent_memories=(),
                    package_id=uuid5(snapshot.id, f"continue-context:{character.character_id}"),
                    now=snapshot.sealed_at,
                )
                continue

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
            decision_characters.append(character)

        await self._uow.commit()
        model_proposals: list[ActionProposal] = []
        if decision_characters:
            model_proposals = list(
                await asyncio.gather(
                    *(
                        run_decision_graph(
                            DecisionGraphInput(
                                context=contexts[character.character_id],
                                phase_label=phase.phase_name,
                                decision_request_id=uuid5(
                                    phase.id, f"decision:{character.character_id}"
                                ),
                                allowed_entity_ids=frozenset(STAGE2_CHARACTER_IDS),
                                allowed_location_ids=STAGE2_LOCATION_IDS,
                                other_character_names=tuple(
                                    STAGE2_CHARACTER_NAMES[peer_id]
                                    for peer_id in STAGE2_CHARACTER_IDS
                                    if peer_id != character.character_id
                                ),
                            ),
                            self._model_gateway,
                        )
                        for character in decision_characters
                    )
                )
            )
        return (
            (*continue_proposals, *model_proposals),
            contexts,
            actor_locations,
        )

    def _stage2_assemble_scenes(
        self,
        phase_id: UUID,
        snapshot_id: UUID,
        proposals: tuple[ActionProposal, ...],
        actor_locations: dict[UUID, UUID | None],
        decision_contexts: dict[UUID, SealedContextPackage],
    ) -> tuple[SceneDraft, ...]:
        if not proposals:
            return ()
        try:
            assembled = assemble_multiparty_scenes(
                phase_id,
                snapshot_id,
                proposals,
                actor_locations,
                focus_character_ids=STAGE2_CHARACTER_IDS,
                knowledge_scope_hashes={
                    character_id: context.package_hash
                    for character_id, context in decision_contexts.items()
                },
            )
            return tuple(item.draft for item in assembled)
        except ValueError:
            return assemble_scenes(phase_id, snapshot_id, proposals, actor_locations)

    async def _stage2_reactions(
        self,
        world_id: UUID,
        snapshot: PhaseSnapshotRecord,
        scenes: tuple[SceneDraft, ...],
        proposals: tuple[ActionProposal, ...],
    ) -> tuple[ReactionProposal, ...]:
        if self._model_gateway is None:
            raise self._stage2_error("Stage 2 profile requires a text model gateway")
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
                        raise self._stage2_error(f"reaction character data missing: {reactor_id}")
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
                        package_id=uuid5(snapshot.id, f"reaction-context:{request_id}"),
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
                            participant_ids=frozenset(scene.participant_ids),
                        )
                    )
        if not jobs:
            return ()
        await self._uow.commit()
        reactions = await asyncio.gather(
            *(run_reaction_graph(graph_input, self._model_gateway) for graph_input in jobs)
        )
        return tuple(reactions)


__all__ = [
    "STAGE2_CHARACTER_IDS",
    "STAGE2_CHARACTER_NAMES",
    "STAGE2_LOCATION_IDS",
    "Stage2PhaseOps",
]
