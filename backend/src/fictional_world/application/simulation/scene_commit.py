"""Atomic Stage 1 scene persistence and canonical commit integration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4, uuid5

from pydantic import Field

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.simulation.commit import (
    CommitOperationCommand,
    EventCommitService,
)
from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import MemoryKind, SceneStage
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.effects.commands import CreateRecentMemoryEffect, EffectCommand
from fictional_world.domain.events.persistence import OutboxMessageRecord
from fictional_world.domain.scenes.persistence import (
    ActionProposalRecord,
    ActionTargetRecord,
    NarrationRecord,
    ReactionProposalRecord,
    SceneActionRecord,
    SceneParticipantRecord,
    SceneRecord,
    SceneResolutionRecord,
    SceneRunRecord,
    StreamEventRecord,
)
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    ReactionProposal,
    SceneDraft,
    SceneResolution,
)

_SCENE_RUN_NAMESPACE = UUID("25d3136b-4130-530d-a1a4-42df24f29bc6")
_NARRATION_NAMESPACE = UUID("80c0709b-ce4a-54cb-b990-a6c508ce3824")
_STREAM_NAMESPACE = UUID("9681dc74-aa13-5b62-989a-78732d451dd0")


class SceneCommitError(DomainError):
    """Scene inputs or an existing idempotent result are inconsistent."""


class CommitSceneCommand(StrictContract):
    """Complete non-model scene output ready for one short transaction."""

    world_id: UUID
    phase_run_id: UUID
    absolute_phase_index: int = Field(ge=0)
    idempotency_key: str = Field(min_length=1, max_length=100)
    scene: SceneDraft
    proposals: tuple[ActionProposal, ...] = Field(min_length=1)
    reactions: tuple[ReactionProposal, ...] = ()
    resolution: SceneResolution
    expected_versions: dict[str, int] = Field(default_factory=dict)
    observer_ids: tuple[UUID, ...] = Field(min_length=1)
    knowledge_scope_hashes: dict[UUID, str] = Field(default_factory=dict)
    narration_body: str | None = Field(default=None, min_length=1, max_length=8_000)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class SceneCommitResult:
    event_id: UUID
    event_sequence: int
    scene_id: UUID
    resolution_id: UUID
    scene_run_id: UUID
    narration_id: UUID
    stream_event_id: UUID
    already_existed: bool


class SceneCommitService:
    """Persist a resolved scene through the existing canonical commit service.

    The caller owns the active unit of work and commits it only after this method
    succeeds. This service performs no model or remote I/O.
    """

    def __init__(self, event_commit_service: EventCommitService | None = None) -> None:
        self._event_commit_service = event_commit_service or EventCommitService()

    async def commit(
        self,
        uow: UnitOfWork,
        command: CommitSceneCommand,
    ) -> SceneCommitResult:
        """Write scene projections, event/effects, memories, stream, and outbox atomically."""

        self._validate(command)
        event_key = _key(command.idempotency_key, "event")
        existing_event = await uow.events.find_by_idempotency_key(event_key)
        if existing_event is not None:
            return await self._existing_result(uow, command, existing_event.id)

        for proposal in command.proposals:
            await self._ensure_proposal(uow, command, proposal)
        await self._ensure_scene(uow, command)
        for beat_index, reaction in enumerate(command.reactions, start=1):
            await self._ensure_reaction(uow, command, reaction, beat_index=beat_index)

        commit_effects = self._effects_with_memories(command)
        event_result = await self._event_commit_service.commit(
            uow,
            CommitOperationCommand(
                world_id=command.world_id,
                idempotency_key=event_key,
                effects=commit_effects,
                expected_versions=command.expected_versions,
                event_type="SCENE_COMMITTED",
                canonical_summary=command.resolution.canonical_summary,
                structured_facts={
                    "scene_id": str(command.scene.scene_id),
                    "snapshot_id": str(command.scene.snapshot_id),
                    "resolution_level": command.resolution.level.value,
                },
                importance=Decimal(str(max(0.1, command.scene.priority.final_score))),
                visibility_class="observable",
                source_kind="engine",
                absolute_phase_index=command.absolute_phase_index,
                phase_run_id=command.phase_run_id,
                scene_id=command.scene.scene_id,
                initiator_entity_id=command.proposals[0].actor_id,
                location_id=command.scene.location_id,
                observer_ids=command.observer_ids,
                enqueue_outbox=True,
            ),
        )

        resolution_record = await uow.scene_resolutions.insert(
            self._resolution_record(command, event_id=event_result.event_id)
        )
        scene_run = await uow.scene_runs.insert(
            self._scene_run_record(command, event_id=event_result.event_id)
        )
        narration = await uow.narrations.insert(
            self._narration_record(command, event_id=event_result.event_id)
        )
        stream_event = await uow.stream_events.insert(
            self._stream_record(
                command,
                event_id=event_result.event_id,
                sequence=event_result.sequence_number,
                narration_id=narration.id,
            )
        )
        await uow.outbox.insert_many(
            self._projection_outbox(
                command,
                event_id=event_result.event_id,
                narration_id=narration.id,
                stream_event_id=stream_event.id,
            )
        )
        return SceneCommitResult(
            event_id=event_result.event_id,
            event_sequence=event_result.sequence_number,
            scene_id=command.scene.scene_id,
            resolution_id=resolution_record.id,
            scene_run_id=scene_run.id,
            narration_id=narration.id,
            stream_event_id=stream_event.id,
            already_existed=False,
        )

    @staticmethod
    def _validate(command: CommitSceneCommand) -> None:
        scene = command.scene
        if scene.phase_id != command.phase_run_id:
            raise SceneCommitError("scene phase does not match the commit phase")
        if command.resolution.scene_id != scene.scene_id:
            raise SceneCommitError("resolution belongs to a different scene")
        proposal_ids = {proposal.decision_request_id for proposal in command.proposals}
        if proposal_ids != set(scene.action_proposal_ids):
            raise SceneCommitError("scene proposal IDs do not match supplied proposals")
        actor_ids = {proposal.actor_id for proposal in command.proposals}
        if actor_ids != set(scene.participant_ids):
            raise SceneCommitError("scene participant IDs do not match proposal actors")
        if not set(command.observer_ids).issubset(actor_ids):
            raise SceneCommitError("observer IDs must be scene participants")
        if set(command.knowledge_scope_hashes) - actor_ids:
            raise SceneCommitError("knowledge scope hash belongs to a non-participant")
        for reaction in command.reactions:
            if reaction.scene_id != scene.scene_id:
                raise SceneCommitError("reaction belongs to a different scene")
            if reaction.triggering_attempt_id not in proposal_ids:
                raise SceneCommitError("reaction references an attempt outside the scene")
            if reaction.reactor_id not in actor_ids:
                raise SceneCommitError("reaction author is not a scene participant")

    async def _ensure_proposal(
        self,
        uow: UnitOfWork,
        command: CommitSceneCommand,
        proposal: ActionProposal,
    ) -> None:
        key = _key(command.idempotency_key, f"action:{proposal.decision_request_id}")
        existing = await uow.action_proposals.find_by_idempotency_key(key)
        if existing is not None:
            if existing.id != proposal.decision_request_id:
                raise SceneCommitError("action idempotency key resolved to another proposal")
            return
        await uow.action_proposals.insert(
            ActionProposalRecord(
                id=proposal.decision_request_id,
                phase_run_id=command.phase_run_id,
                snapshot_id=command.scene.snapshot_id,
                actor_id=proposal.actor_id,
                action_family=proposal.action_family.value,
                intent=proposal.description,
                utterance=proposal.utterance,
                target_location_id=proposal.target_location_id,
                visibility=proposal.visibility.value,
                estimated_duration_phases=proposal.estimated_duration_phases,
                continuation_activity_id=proposal.continuation_activity_id,
                desired_effects={
                    "resource_intentions": [
                        item.model_dump(mode="json") for item in proposal.resource_intentions
                    ],
                    "desired_outcomes": [
                        item.model_dump(mode="json") for item in proposal.desired_outcomes
                    ],
                },
                fallback_action=proposal.fallback.model_dump(mode="json"),
                validation_status="valid",
                idempotency_key=key,
                targets=tuple(
                    ActionTargetRecord(
                        action_proposal_id=proposal.decision_request_id,
                        target_entity_id=target_id,
                        target_role="direct",
                        ordinal=ordinal,
                    )
                    for ordinal, target_id in enumerate(proposal.target_entity_ids)
                ),
            )
        )

    async def _ensure_scene(self, uow: UnitOfWork, command: CommitSceneCommand) -> None:
        scene = command.scene
        key = _key(command.idempotency_key, "scene")
        existing = await uow.scenes.find_by_idempotency_key(key)
        if existing is not None:
            if existing.id != scene.scene_id or existing.snapshot_id != scene.snapshot_id:
                raise SceneCommitError("scene idempotency key resolved to different inputs")
            return
        await uow.scenes.insert(
            SceneRecord(
                id=scene.scene_id,
                phase_run_id=command.phase_run_id,
                snapshot_id=scene.snapshot_id,
                location_id=scene.location_id,
                scene_type=_scene_type(command.proposals),
                state=SceneStage.COMPLETE.value,
                priority_score=Decimal(str(scene.priority.final_score)),
                priority_breakdown=scene.priority.model_dump(mode="json"),
                beat_budget=scene.beat_budget,
                high_impact=scene.high_impact,
                mutable_aggregate_ids=scene.participant_ids,
                idempotency_key=key,
                started_at=command.occurred_at,
                completed_at=command.occurred_at,
                actions=tuple(
                    SceneActionRecord(
                        scene_id=scene.scene_id,
                        proposal_id=proposal_id,
                        role="initiator" if ordinal == 0 else "co_intent",
                        ordinal=ordinal,
                    )
                    for ordinal, proposal_id in enumerate(scene.action_proposal_ids)
                ),
                participants=tuple(
                    SceneParticipantRecord(
                        scene_id=scene.scene_id,
                        entity_id=participant_id,
                        participant_role="actor",
                        reaction_eligible=True,
                        knowledge_scope_hash=command.knowledge_scope_hashes.get(participant_id),
                    )
                    for participant_id in scene.participant_ids
                ),
            )
        )

    async def _ensure_reaction(
        self,
        uow: UnitOfWork,
        command: CommitSceneCommand,
        reaction: ReactionProposal,
        *,
        beat_index: int,
    ) -> None:
        key = _key(command.idempotency_key, f"reaction:{reaction.reaction_request_id}")
        existing = await uow.reactions.find_by_idempotency_key(key)
        if existing is not None:
            if existing.id != reaction.reaction_request_id:
                raise SceneCommitError("reaction idempotency key resolved to another reaction")
            return
        await uow.reactions.insert(
            ReactionProposalRecord(
                id=reaction.reaction_request_id,
                scene_id=command.scene.scene_id,
                phase_run_id=command.phase_run_id,
                snapshot_id=command.scene.snapshot_id,
                triggering_attempt_id=reaction.triggering_attempt_id,
                reactor_id=reaction.reactor_id,
                beat_index=beat_index,
                action_family=reaction.action_family.value,
                description=reaction.description,
                utterance=reaction.utterance,
                target_entity_ids=reaction.target_entity_ids,
                resource_intentions={
                    "items": [item.model_dump(mode="json") for item in reaction.resource_intentions]
                },
                desired_outcomes={
                    "items": [item.model_dump(mode="json") for item in reaction.desired_outcomes]
                },
                validation_status="valid",
                source_kind="model",
                idempotency_key=key,
            )
        )

    @staticmethod
    def _effects_with_memories(command: CommitSceneCommand) -> tuple[EffectCommand, ...]:
        effects: list[EffectCommand] = list(command.resolution.effects)
        owners_with_memory = {
            effect.owner_character_id
            for effect in effects
            if isinstance(effect, CreateRecentMemoryEffect)
        }
        for observer_id in command.observer_ids:
            if observer_id in owners_with_memory:
                continue
            effects.append(
                CreateRecentMemoryEffect(
                    effect_key=f"scene-memory-{observer_id.hex}",
                    source_attempt_ids=command.resolution.accepted_attempt_ids,
                    justification="Materialize a recent episodic memory from a perceived scene.",
                    owner_character_id=observer_id,
                    memory_kind=MemoryKind.EPISODIC,
                    text=command.resolution.canonical_summary,
                    salience=max(0.1, command.scene.priority.final_score),
                    confidence=command.resolution.confidence,
                )
            )
        return tuple(effects)

    @staticmethod
    def _resolution_record(
        command: CommitSceneCommand,
        *,
        event_id: UUID,
    ) -> SceneResolutionRecord:
        resolution = command.resolution
        return SceneResolutionRecord(
            id=resolution.resolution_request_id,
            scene_id=command.scene.scene_id,
            resolution_level=resolution.level.value,
            accepted_attempt_ids=resolution.accepted_attempt_ids,
            rejected_assumptions={"items": list(resolution.rejected_assumptions)},
            proposed_effects={
                "effects": [effect.model_dump(mode="json") for effect in resolution.effects]
            },
            observation_seeds={"observer_ids": [str(value) for value in command.observer_ids]},
            narration_constraints=resolution.narration_constraints.model_dump(mode="json"),
            visual_significance=Decimal(str(resolution.visual_significance)),
            confidence=Decimal(str(resolution.confidence)),
            expected_aggregate_versions=dict(command.expected_versions),
            validation_status="committed",
            commit_event_id=event_id,
            canonical_summary=resolution.canonical_summary,
            idempotency_key=_key(command.idempotency_key, "resolution"),
        )

    @staticmethod
    def _scene_run_record(
        command: CommitSceneCommand,
        *,
        event_id: UUID,
    ) -> SceneRunRecord:
        scene = command.scene
        return SceneRunRecord(
            id=uuid5(_SCENE_RUN_NAMESPACE, str(scene.scene_id)),
            scene_id=scene.scene_id,
            phase_run_id=command.phase_run_id,
            status="completed",
            stage=SceneStage.COMPLETE.value,
            beat_count=len(command.reactions),
            beat_budget=scene.beat_budget,
            high_impact=scene.high_impact,
            resolution_id=command.resolution.resolution_request_id,
            committed_event_id=event_id,
            attempt_count=1,
            idempotency_key=_key(command.idempotency_key, "run"),
            started_at=command.occurred_at,
            completed_at=command.occurred_at,
        )

    @staticmethod
    def _narration_record(
        command: CommitSceneCommand,
        *,
        event_id: UUID,
    ) -> NarrationRecord:
        body = command.narration_body or command.resolution.canonical_summary
        perspective = command.resolution.narration_constraints.perspective
        return NarrationRecord(
            id=uuid5(_NARRATION_NAMESPACE, f"{command.scene.scene_id}:{perspective}"),
            world_id=command.world_id,
            scene_id=command.scene.scene_id,
            world_event_id=event_id,
            perspective=perspective,
            body=body,
            source_kind="deterministic" if command.narration_body is None else "model",
            is_fallback=command.narration_body is None,
            content_hash=hashlib.sha256(body.encode()).hexdigest(),
            idempotency_key=_key(command.idempotency_key, "narration"),
        )

    @staticmethod
    def _stream_record(
        command: CommitSceneCommand,
        *,
        event_id: UUID,
        sequence: int,
        narration_id: UUID,
    ) -> StreamEventRecord:
        return StreamEventRecord(
            id=uuid5(_STREAM_NAMESPACE, str(event_id)),
            world_id=command.world_id,
            sequence=sequence,
            event_type="scene.committed",
            occurred_at=command.occurred_at,
            fictional_time={
                "absolute_phase_index": command.absolute_phase_index,
            },
            payload={
                "scene_id": str(command.scene.scene_id),
                "event_id": str(event_id),
                "narration_id": str(narration_id),
                "summary": command.resolution.canonical_summary,
            },
            phase_run_id=command.phase_run_id,
            scene_id=command.scene.scene_id,
            world_event_id=event_id,
            perspective_scope="world",
            idempotency_key=_key(command.idempotency_key, "stream"),
        )

    @staticmethod
    def _projection_outbox(
        command: CommitSceneCommand,
        *,
        event_id: UUID,
        narration_id: UUID,
        stream_event_id: UUID,
    ) -> tuple[OutboxMessageRecord, ...]:
        return (
            OutboxMessageRecord(
                id=uuid4(),
                world_event_id=event_id,
                message_type="narration.ready",
                payload={
                    "world_id": str(command.world_id),
                    "scene_id": str(command.scene.scene_id),
                    "narration_id": str(narration_id),
                },
                idempotency_key=_key(command.idempotency_key, "outbox:narration"),
                state="pending",
            ),
            OutboxMessageRecord(
                id=uuid4(),
                world_event_id=event_id,
                message_type="stream_event.ready",
                payload={
                    "world_id": str(command.world_id),
                    "stream_event_id": str(stream_event_id),
                },
                idempotency_key=_key(command.idempotency_key, "outbox:stream"),
                state="pending",
            ),
        )

    async def _existing_result(
        self,
        uow: UnitOfWork,
        command: CommitSceneCommand,
        event_id: UUID,
    ) -> SceneCommitResult:
        event = await uow.events.get(event_id)
        resolution = await uow.scene_resolutions.find_by_idempotency_key(
            _key(command.idempotency_key, "resolution")
        )
        scene_run = await uow.scene_runs.find_by_idempotency_key(
            _key(command.idempotency_key, "run")
        )
        narration = await uow.narrations.find_by_idempotency_key(
            _key(command.idempotency_key, "narration")
        )
        stream = await uow.stream_events.find_by_idempotency_key(
            _key(command.idempotency_key, "stream")
        )
        if (
            event is None
            or event.scene_id != command.scene.scene_id
            or resolution is None
            or scene_run is None
            or narration is None
            or stream is None
        ):
            raise SceneCommitError("idempotent scene commit is incomplete or inconsistent")
        return SceneCommitResult(
            event_id=event.id,
            event_sequence=event.sequence_number,
            scene_id=command.scene.scene_id,
            resolution_id=resolution.id,
            scene_run_id=scene_run.id,
            narration_id=narration.id,
            stream_event_id=stream.id,
            already_existed=True,
        )


def _scene_type(proposals: tuple[ActionProposal, ...]) -> str:
    families = {proposal.action_family.value for proposal in proposals}
    if families.intersection({"communicate", "socialize"}):
        return "social"
    if families == {"move"}:
        return "travel"
    if len(proposals) == 1:
        return "solo"
    return "shared"


def _key(base: str, suffix: str) -> str:
    return f"scene:{base}:{suffix}"


__all__ = [
    "CommitSceneCommand",
    "SceneCommitError",
    "SceneCommitResult",
    "SceneCommitService",
]
