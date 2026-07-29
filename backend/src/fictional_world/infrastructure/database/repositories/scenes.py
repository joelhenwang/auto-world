"""SQLAlchemy repositories for Stage 1 action/scene/stream tables."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.scenes.persistence import (
    ActionProposalRecord,
    NarrationRecord,
    PlayerControlSessionRecord,
    ReactionProposalRecord,
    SceneRecord,
    SceneResolutionRecord,
    SceneRunRecord,
    StreamEventRecord,
)
from fictional_world.infrastructure.database.mappings.scene_records import (
    action_proposal_to_record,
    narration_to_record,
    player_control_to_record,
    reaction_to_record,
    scene_resolution_to_record,
    scene_run_to_record,
    scene_to_record,
    stream_event_to_record,
)
from fictional_world.infrastructure.database.models.scene import (
    ActionProposalRow,
    ActionTargetRow,
    NarrationRow,
    PlayerControlSessionRow,
    ReactionProposalRow,
    SceneActionRow,
    SceneParticipantRow,
    SceneResolutionRow,
    SceneRow,
    SceneRunRow,
    StreamEventRow,
)


class SqlAlchemyActionProposalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, proposal_id: UUID) -> ActionProposalRecord | None:
        row = await self._session.get(ActionProposalRow, proposal_id)
        if row is None:
            return None
        targets = await self._targets_for(proposal_id)
        return action_proposal_to_record(row, targets)

    async def find_by_idempotency_key(self, key: str) -> ActionProposalRecord | None:
        result = await self._session.execute(
            select(ActionProposalRow).where(ActionProposalRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        targets = await self._targets_for(row.id)
        return action_proposal_to_record(row, targets)

    async def list_for_phase(self, phase_run_id: UUID) -> Sequence[ActionProposalRecord]:
        result = await self._session.execute(
            select(ActionProposalRow)
            .where(ActionProposalRow.phase_run_id == phase_run_id)
            .order_by(ActionProposalRow.created_at.asc())
        )
        rows = list(result.scalars().all())
        out: list[ActionProposalRecord] = []
        for row in rows:
            targets = await self._targets_for(row.id)
            out.append(action_proposal_to_record(row, targets))
        return out

    async def insert(self, proposal: ActionProposalRecord) -> ActionProposalRecord:
        row = ActionProposalRow(
            id=proposal.id,
            phase_run_id=proposal.phase_run_id,
            snapshot_id=proposal.snapshot_id,
            actor_id=proposal.actor_id,
            proposal_kind=proposal.proposal_kind,
            action_family=proposal.action_family,
            intent=proposal.intent,
            utterance=proposal.utterance,
            target_location_id=proposal.target_location_id,
            visibility=proposal.visibility,
            risk_tolerance=proposal.risk_tolerance,
            estimated_duration_phases=proposal.estimated_duration_phases,
            continuation_activity_id=proposal.continuation_activity_id,
            desired_effects=dict(proposal.desired_effects),
            fallback_action=dict(proposal.fallback_action),
            validation_status=proposal.validation_status,
            validation_errors=proposal.validation_errors,
            model_call_id=proposal.model_call_id,
            generation=proposal.generation,
            idempotency_key=proposal.idempotency_key,
        )
        self._session.add(row)
        await self._session.flush()
        target_rows: list[ActionTargetRow] = []
        for target in proposal.targets:
            trow = ActionTargetRow(
                action_proposal_id=proposal.id,
                target_entity_id=target.target_entity_id,
                target_role=target.target_role,
                ordinal=target.ordinal,
            )
            self._session.add(trow)
            target_rows.append(trow)
        if target_rows:
            await self._session.flush()
        return action_proposal_to_record(row, target_rows)

    async def _targets_for(self, proposal_id: UUID) -> list[ActionTargetRow]:
        result = await self._session.execute(
            select(ActionTargetRow)
            .where(ActionTargetRow.action_proposal_id == proposal_id)
            .order_by(ActionTargetRow.ordinal.asc())
        )
        return list(result.scalars().all())


class SqlAlchemySceneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, scene_id: UUID) -> SceneRecord | None:
        row = await self._session.get(SceneRow, scene_id)
        if row is None:
            return None
        actions, participants = await self._children(scene_id)
        return scene_to_record(row, actions, participants)

    async def find_by_idempotency_key(self, key: str) -> SceneRecord | None:
        result = await self._session.execute(
            select(SceneRow).where(SceneRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        actions, participants = await self._children(row.id)
        return scene_to_record(row, actions, participants)

    async def list_for_phase(self, phase_run_id: UUID) -> Sequence[SceneRecord]:
        result = await self._session.execute(
            select(SceneRow)
            .where(SceneRow.phase_run_id == phase_run_id)
            .order_by(SceneRow.priority_score.desc())
        )
        rows = list(result.scalars().all())
        out: list[SceneRecord] = []
        for row in rows:
            actions, participants = await self._children(row.id)
            out.append(scene_to_record(row, actions, participants))
        return out

    async def insert(self, scene: SceneRecord) -> SceneRecord:
        row = SceneRow(
            id=scene.id,
            phase_run_id=scene.phase_run_id,
            snapshot_id=scene.snapshot_id,
            location_id=scene.location_id,
            scene_type=scene.scene_type,
            state=scene.state,
            priority_score=scene.priority_score,
            priority_breakdown=dict(scene.priority_breakdown),
            beat_budget=scene.beat_budget,
            high_impact=scene.high_impact,
            mutable_aggregate_ids=list(scene.mutable_aggregate_ids) or None,
            idempotency_key=scene.idempotency_key,
            started_at=scene.started_at,
            completed_at=scene.completed_at,
            version=scene.version,
            continuation_id=scene.continuation_id,
            director_hook_id=scene.director_hook_id,
            observer_eligibility=dict(scene.observer_eligibility),
        )
        self._session.add(row)
        await self._session.flush()
        action_rows: list[SceneActionRow] = []
        for action in scene.actions:
            arow = SceneActionRow(
                scene_id=scene.id,
                proposal_id=action.proposal_id,
                role=action.role,
                ordinal=action.ordinal,
            )
            self._session.add(arow)
            action_rows.append(arow)
        participant_rows: list[SceneParticipantRow] = []
        for participant in scene.participants:
            prow = SceneParticipantRow(
                scene_id=scene.id,
                entity_id=participant.entity_id,
                participant_role=participant.participant_role,
                reaction_eligible=participant.reaction_eligible,
                knowledge_scope_hash=participant.knowledge_scope_hash,
                joined_at_beat=participant.joined_at_beat,
                left_at_beat=participant.left_at_beat,
            )
            self._session.add(prow)
            participant_rows.append(prow)
        if action_rows or participant_rows:
            await self._session.flush()
        return scene_to_record(row, action_rows, participant_rows)

    async def save(self, scene: SceneRecord, *, expected_version: int) -> SceneRecord:
        row = await self._session.get(SceneRow, scene.id)
        if row is None:
            msg = f"scene {scene.id} not found"
            raise LookupError(msg)
        if int(row.version) != expected_version:
            from fictional_world.infrastructure.database.errors import OptimisticConcurrencyError

            raise OptimisticConcurrencyError(
                entity="scene",
                entity_id=str(scene.id),
                expected_version=expected_version,
            )
        row.state = scene.state
        row.priority_score = scene.priority_score
        row.priority_breakdown = dict(scene.priority_breakdown)
        row.beat_budget = scene.beat_budget
        row.high_impact = scene.high_impact
        row.mutable_aggregate_ids = list(scene.mutable_aggregate_ids) or None
        row.started_at = scene.started_at
        row.completed_at = scene.completed_at
        row.continuation_id = scene.continuation_id
        row.director_hook_id = scene.director_hook_id
        row.observer_eligibility = dict(scene.observer_eligibility)
        row.version = expected_version + 1
        await self._session.flush()
        actions, participants = await self._children(scene.id)
        return scene_to_record(row, actions, participants)

    async def _children(
        self, scene_id: UUID
    ) -> tuple[list[SceneActionRow], list[SceneParticipantRow]]:
        actions = list(
            (
                await self._session.execute(
                    select(SceneActionRow)
                    .where(SceneActionRow.scene_id == scene_id)
                    .order_by(SceneActionRow.ordinal.asc())
                )
            )
            .scalars()
            .all()
        )
        participants = list(
            (
                await self._session.execute(
                    select(SceneParticipantRow).where(SceneParticipantRow.scene_id == scene_id)
                )
            )
            .scalars()
            .all()
        )
        return actions, participants


class SqlAlchemyReactionProposalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, reaction_id: UUID) -> ReactionProposalRecord | None:
        row = await self._session.get(ReactionProposalRow, reaction_id)
        return None if row is None else reaction_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> ReactionProposalRecord | None:
        result = await self._session.execute(
            select(ReactionProposalRow).where(ReactionProposalRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else reaction_to_record(row)

    async def list_for_scene(self, scene_id: UUID) -> Sequence[ReactionProposalRecord]:
        result = await self._session.execute(
            select(ReactionProposalRow)
            .where(ReactionProposalRow.scene_id == scene_id)
            .order_by(ReactionProposalRow.beat_index.asc())
        )
        return [reaction_to_record(row) for row in result.scalars().all()]

    async def insert(self, reaction: ReactionProposalRecord) -> ReactionProposalRecord:
        row = ReactionProposalRow(
            id=reaction.id,
            scene_id=reaction.scene_id,
            phase_run_id=reaction.phase_run_id,
            snapshot_id=reaction.snapshot_id,
            triggering_attempt_id=reaction.triggering_attempt_id,
            reactor_id=reaction.reactor_id,
            beat_index=reaction.beat_index,
            action_family=reaction.action_family,
            description=reaction.description,
            utterance=reaction.utterance,
            target_entity_ids=list(reaction.target_entity_ids) or None,
            resource_intentions=dict(reaction.resource_intentions),
            desired_outcomes=dict(reaction.desired_outcomes),
            validation_status=reaction.validation_status,
            validation_errors=reaction.validation_errors,
            model_call_id=reaction.model_call_id,
            source_kind=reaction.source_kind,
            idempotency_key=reaction.idempotency_key,
        )
        self._session.add(row)
        await self._session.flush()
        return reaction_to_record(row)


class SqlAlchemySceneResolutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, resolution_id: UUID) -> SceneResolutionRecord | None:
        row = await self._session.get(SceneResolutionRow, resolution_id)
        return None if row is None else scene_resolution_to_record(row)

    async def get_for_scene(self, scene_id: UUID) -> SceneResolutionRecord | None:
        result = await self._session.execute(
            select(SceneResolutionRow).where(SceneResolutionRow.scene_id == scene_id)
        )
        row = result.scalar_one_or_none()
        return None if row is None else scene_resolution_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> SceneResolutionRecord | None:
        result = await self._session.execute(
            select(SceneResolutionRow).where(SceneResolutionRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else scene_resolution_to_record(row)

    async def insert(self, resolution: SceneResolutionRecord) -> SceneResolutionRecord:
        row = SceneResolutionRow(
            id=resolution.id,
            scene_id=resolution.scene_id,
            resolution_level=resolution.resolution_level,
            accepted_attempt_ids=list(resolution.accepted_attempt_ids) or None,
            rejected_assumptions=dict(resolution.rejected_assumptions),
            proposed_effects=dict(resolution.proposed_effects),
            delayed_effects=dict(resolution.delayed_effects),
            observation_seeds=dict(resolution.observation_seeds),
            narration_constraints=dict(resolution.narration_constraints),
            visual_significance=resolution.visual_significance,
            confidence=resolution.confidence,
            resolver_profile_id=resolution.resolver_profile_id,
            model_call_id=resolution.model_call_id,
            expected_aggregate_versions=dict(resolution.expected_aggregate_versions),
            validation_status=resolution.validation_status,
            commit_event_id=resolution.commit_event_id,
            canonical_summary=resolution.canonical_summary,
            idempotency_key=resolution.idempotency_key,
        )
        self._session.add(row)
        await self._session.flush()
        return scene_resolution_to_record(row)


class SqlAlchemySceneRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, run_id: UUID) -> SceneRunRecord | None:
        row = await self._session.get(SceneRunRow, run_id)
        return None if row is None else scene_run_to_record(row)

    async def get_for_scene(self, scene_id: UUID) -> SceneRunRecord | None:
        result = await self._session.execute(
            select(SceneRunRow).where(SceneRunRow.scene_id == scene_id)
        )
        row = result.scalar_one_or_none()
        return None if row is None else scene_run_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> SceneRunRecord | None:
        result = await self._session.execute(
            select(SceneRunRow).where(SceneRunRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else scene_run_to_record(row)

    async def insert(self, run: SceneRunRecord) -> SceneRunRecord:
        row = SceneRunRow(
            id=run.id,
            scene_id=run.scene_id,
            phase_run_id=run.phase_run_id,
            status=run.status,
            stage=run.stage,
            beat_count=run.beat_count,
            beat_budget=run.beat_budget,
            high_impact=run.high_impact,
            resolution_id=run.resolution_id,
            committed_event_id=run.committed_event_id,
            attempt_count=run.attempt_count,
            error_code=run.error_code,
            error_detail=run.error_detail,
            idempotency_key=run.idempotency_key,
            started_at=run.started_at,
            completed_at=run.completed_at,
            version=run.version,
        )
        self._session.add(row)
        await self._session.flush()
        return scene_run_to_record(row)


class SqlAlchemyNarrationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, narration_id: UUID) -> NarrationRecord | None:
        row = await self._session.get(NarrationRow, narration_id)
        return None if row is None else narration_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> NarrationRecord | None:
        result = await self._session.execute(
            select(NarrationRow).where(NarrationRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else narration_to_record(row)

    async def list_for_scene(self, scene_id: UUID) -> Sequence[NarrationRecord]:
        result = await self._session.execute(
            select(NarrationRow).where(NarrationRow.scene_id == scene_id)
        )
        return [narration_to_record(row) for row in result.scalars().all()]

    async def insert(self, narration: NarrationRecord) -> NarrationRecord:
        row = NarrationRow(
            id=narration.id,
            world_id=narration.world_id,
            scene_id=narration.scene_id,
            world_event_id=narration.world_event_id,
            perspective=narration.perspective,
            body=narration.body,
            source_kind=narration.source_kind,
            model_call_id=narration.model_call_id,
            is_fallback=narration.is_fallback,
            content_hash=narration.content_hash,
            idempotency_key=narration.idempotency_key,
        )
        self._session.add(row)
        await self._session.flush()
        return narration_to_record(row)


class SqlAlchemyStreamEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: UUID) -> StreamEventRecord | None:
        row = await self._session.get(StreamEventRow, event_id)
        return None if row is None else stream_event_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> StreamEventRecord | None:
        result = await self._session.execute(
            select(StreamEventRow).where(StreamEventRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else stream_event_to_record(row)

    async def list_after(
        self,
        world_id: UUID,
        *,
        after_sequence: int | None = None,
        limit: int = 100,
    ) -> Sequence[StreamEventRecord]:
        stmt = select(StreamEventRow).where(StreamEventRow.world_id == world_id)
        if after_sequence is not None:
            stmt = stmt.where(StreamEventRow.sequence > after_sequence)
        stmt = stmt.order_by(StreamEventRow.sequence.asc()).limit(limit)
        result = await self._session.execute(stmt)
        return [stream_event_to_record(row) for row in result.scalars().all()]

    async def next_sequence(self, world_id: UUID) -> int:
        result = await self._session.execute(
            select(StreamEventRow.sequence)
            .where(StreamEventRow.world_id == world_id)
            .order_by(StreamEventRow.sequence.desc())
            .limit(1)
        )
        current = result.scalar_one_or_none()
        return 1 if current is None else int(current) + 1

    async def insert(self, event: StreamEventRecord) -> StreamEventRecord:
        row = StreamEventRow(
            id=event.id,
            world_id=event.world_id,
            sequence=event.sequence,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            fictional_time=dict(event.fictional_time),
            payload=dict(event.payload),
            schema_version=event.schema_version,
            phase_run_id=event.phase_run_id,
            scene_id=event.scene_id,
            world_event_id=event.world_event_id,
            perspective_scope=event.perspective_scope,
            idempotency_key=event.idempotency_key,
        )
        self._session.add(row)
        await self._session.flush()
        return stream_event_to_record(row)


class SqlAlchemyPlayerControlRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, session_id: UUID) -> PlayerControlSessionRecord | None:
        row = await self._session.get(PlayerControlSessionRow, session_id)
        return None if row is None else player_control_to_record(row)

    async def find_active_for_character(
        self, character_id: UUID
    ) -> PlayerControlSessionRecord | None:
        result = await self._session.execute(
            select(PlayerControlSessionRow).where(
                PlayerControlSessionRow.character_id == character_id,
                PlayerControlSessionRow.status.in_(("active", "waiting_input")),
            )
        )
        row = result.scalar_one_or_none()
        return None if row is None else player_control_to_record(row)

    async def find_by_idempotency_key(self, key: str) -> PlayerControlSessionRecord | None:
        result = await self._session.execute(
            select(PlayerControlSessionRow).where(PlayerControlSessionRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return None if row is None else player_control_to_record(row)

    async def insert(self, session: PlayerControlSessionRecord) -> PlayerControlSessionRecord:
        row = PlayerControlSessionRow(
            id=session.id,
            world_id=session.world_id,
            character_id=session.character_id,
            controller_id=session.controller_id,
            status=session.status,
            acquired_at=session.acquired_at,
            released_at=session.released_at,
            waiting_input=session.waiting_input,
            phase_run_id=session.phase_run_id,
            last_command_id=session.last_command_id,
            idempotency_key=session.idempotency_key,
            version=session.version,
        )
        self._session.add(row)
        await self._session.flush()
        return player_control_to_record(row)

    async def save(
        self, session: PlayerControlSessionRecord, *, expected_version: int
    ) -> PlayerControlSessionRecord:
        row = await self._session.get(PlayerControlSessionRow, session.id)
        if row is None:
            msg = f"player control session {session.id} not found"
            raise LookupError(msg)
        if int(row.version) != expected_version:
            from fictional_world.infrastructure.database.errors import OptimisticConcurrencyError

            raise OptimisticConcurrencyError(
                entity="player_control_session",
                entity_id=str(session.id),
                expected_version=expected_version,
            )
        row.status = session.status
        row.released_at = session.released_at
        row.waiting_input = session.waiting_input
        row.phase_run_id = session.phase_run_id
        row.last_command_id = session.last_command_id
        row.version = expected_version + 1
        await self._session.flush()
        return player_control_to_record(row)
