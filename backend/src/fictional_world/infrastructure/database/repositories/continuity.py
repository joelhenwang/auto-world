"""SQLAlchemy repositories for Stage 2 continuity / knowledge tables."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.continuity.persistence import (
    ActivityPersistenceRecord,
    CommitmentPersistenceRecord,
    DayRunPersistenceRecord,
    DiaryEntryPersistenceRecord,
    GoalPersistenceRecord,
    HookPersistenceRecord,
    NpcLifecyclePersistenceRecord,
    NpcProfilePersistenceRecord,
    PlanPersistenceRecord,
    PlanStepPersistenceRecord,
    RelationshipEdgePersistenceRecord,
    RoutePersistenceRecord,
    SummaryPersistenceRecord,
)
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    ClaimPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.infrastructure.database.mappings.continuity_records import (
    activity_to_record,
    belief_to_record,
    claim_to_record,
    commitment_to_record,
    day_run_to_record,
    diary_entry_to_record,
    goal_to_record,
    hook_to_record,
    npc_lifecycle_to_record,
    npc_profile_to_record,
    plan_step_to_record,
    plan_to_record,
    relationship_edge_to_record,
    route_to_record,
    secret_access_to_record,
    summary_to_record,
)
from fictional_world.infrastructure.database.models.continuity import (
    ActivityRow,
    CommitmentRow,
    DayRunRow,
    DiaryEntryRow,
    GoalRow,
    HookRow,
    NpcLifecycleRow,
    NpcProfileRow,
    PlanRow,
    PlanStepRow,
    RelationshipEdgeRow,
    RouteRow,
    SummaryRow,
)
from fictional_world.infrastructure.database.models.knowledge import (
    BeliefRow,
    ClaimListenerRow,
    ClaimRow,
    SecretAccessRow,
)


class SqlAlchemyGoalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, goal_id: UUID) -> GoalPersistenceRecord | None:
        row = await self._session.get(GoalRow, goal_id)
        return goal_to_record(row) if row is not None else None

    async def insert(self, goal: GoalPersistenceRecord) -> GoalPersistenceRecord:
        row = GoalRow(
            id=goal.id,
            world_id=goal.world_id,
            owner_character_id=goal.owner_character_id,
            description=goal.description,
            category=goal.category,
            priority=goal.priority,
            status=goal.status,
            horizon=goal.horizon,
            success_conditions=dict(goal.success_conditions),
            failure_conditions=dict(goal.failure_conditions),
            allows_alternative_plans=goal.allows_alternative_plans,
            source_event_id=goal.source_event_id,
            version=goal.version,
        )
        self._session.add(row)
        await self._session.flush()
        return goal_to_record(row)

    async def list_for_owner(
        self, owner_character_id: UUID, *, world_id: UUID
    ) -> Sequence[GoalPersistenceRecord]:
        result = await self._session.execute(
            select(GoalRow)
            .where(
                GoalRow.owner_character_id == owner_character_id,
                GoalRow.world_id == world_id,
            )
            .order_by(GoalRow.created_at.asc())
        )
        return [goal_to_record(row) for row in result.scalars().all()]


class SqlAlchemyPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, plan_id: UUID) -> PlanPersistenceRecord | None:
        row = await self._session.get(PlanRow, plan_id)
        return plan_to_record(row) if row is not None else None

    async def insert(self, plan: PlanPersistenceRecord) -> PlanPersistenceRecord:
        row = PlanRow(
            id=plan.id,
            goal_id=plan.goal_id,
            world_id=plan.world_id,
            owner_character_id=plan.owner_character_id,
            title=plan.title,
            status=plan.status,
            is_primary=plan.is_primary,
            expected_horizon=plan.expected_horizon,
            commitment_level=plan.commitment_level,
            revision_number=plan.revision_number,
            source_event_id=plan.source_event_id,
            version=plan.version,
        )
        self._session.add(row)
        await self._session.flush()
        return plan_to_record(row)

    async def list_for_goal(self, goal_id: UUID) -> Sequence[PlanPersistenceRecord]:
        result = await self._session.execute(
            select(PlanRow).where(PlanRow.goal_id == goal_id).order_by(PlanRow.created_at.asc())
        )
        return [plan_to_record(row) for row in result.scalars().all()]

    async def insert_step(self, step: PlanStepPersistenceRecord) -> PlanStepPersistenceRecord:
        row = PlanStepRow(
            id=step.id,
            plan_id=step.plan_id,
            step_index=step.step_index,
            description=step.description,
            status=step.status,
            target_entity_id=step.target_entity_id,
            target_location_id=step.target_location_id,
            activity_id=step.activity_id,
            prerequisites=dict(step.prerequisites),
            expected_duration_phases=step.expected_duration_phases,
            version=step.version,
        )
        self._session.add(row)
        await self._session.flush()
        return plan_step_to_record(row)


class SqlAlchemyCommitmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, commitment_id: UUID) -> CommitmentPersistenceRecord | None:
        row = await self._session.get(CommitmentRow, commitment_id)
        return commitment_to_record(row) if row is not None else None

    async def insert(self, commitment: CommitmentPersistenceRecord) -> CommitmentPersistenceRecord:
        row = CommitmentRow(
            id=commitment.id,
            world_id=commitment.world_id,
            debtor_character_id=commitment.debtor_character_id,
            beneficiary_character_id=commitment.beneficiary_character_id,
            description=commitment.description,
            due_condition=dict(commitment.due_condition),
            status=commitment.status,
            created_event_id=commitment.created_event_id,
            fulfilled_event_id=commitment.fulfilled_event_id,
            version=commitment.version,
        )
        self._session.add(row)
        await self._session.flush()
        return commitment_to_record(row)

    async def list_for_debtor(
        self, debtor_character_id: UUID, *, world_id: UUID
    ) -> Sequence[CommitmentPersistenceRecord]:
        result = await self._session.execute(
            select(CommitmentRow)
            .where(
                CommitmentRow.debtor_character_id == debtor_character_id,
                CommitmentRow.world_id == world_id,
            )
            .order_by(CommitmentRow.created_at.asc())
        )
        return [commitment_to_record(row) for row in result.scalars().all()]


class SqlAlchemyRelationshipEdgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, source_character_id: UUID, target_character_id: UUID
    ) -> RelationshipEdgePersistenceRecord | None:
        row = await self._session.get(
            RelationshipEdgeRow, (source_character_id, target_character_id)
        )
        return relationship_edge_to_record(row) if row is not None else None

    async def insert(
        self, edge: RelationshipEdgePersistenceRecord
    ) -> RelationshipEdgePersistenceRecord:
        row = RelationshipEdgeRow(
            source_character_id=edge.source_character_id,
            target_character_id=edge.target_character_id,
            world_id=edge.world_id,
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
            last_source_event_id=edge.last_source_event_id,
            version=edge.version,
        )
        self._session.add(row)
        await self._session.flush()
        return relationship_edge_to_record(row)

    async def list_for_source(
        self, source_character_id: UUID, *, world_id: UUID
    ) -> Sequence[RelationshipEdgePersistenceRecord]:
        result = await self._session.execute(
            select(RelationshipEdgeRow).where(
                RelationshipEdgeRow.source_character_id == source_character_id,
                RelationshipEdgeRow.world_id == world_id,
            )
        )
        return [relationship_edge_to_record(row) for row in result.scalars().all()]


class SqlAlchemyClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, claim_id: UUID) -> ClaimPersistenceRecord | None:
        row = await self._session.get(ClaimRow, claim_id)
        if row is None:
            return None
        listeners = await self._listeners(claim_id)
        return claim_to_record(row, listeners)

    async def insert(self, claim: ClaimPersistenceRecord) -> ClaimPersistenceRecord:
        row = ClaimRow(
            id=claim.id,
            world_id=claim.world_id,
            source_event_id=claim.source_event_id,
            speaker_id=claim.speaker_id,
            proposition_key=claim.proposition_key,
            proposition_text=claim.proposition_text,
            truth_status=claim.truth_status,
            intent_class=claim.intent_class,
            confidence_expressed=claim.confidence_expressed,
        )
        self._session.add(row)
        await self._session.flush()
        for listener_id in claim.listener_ids:
            self._session.add(ClaimListenerRow(claim_id=claim.id, listener_id=listener_id))
        if claim.listener_ids:
            await self._session.flush()
        return claim_to_record(row, list(claim.listener_ids))

    async def list_for_speaker(
        self, speaker_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[ClaimPersistenceRecord]:
        result = await self._session.execute(
            select(ClaimRow)
            .where(ClaimRow.speaker_id == speaker_id, ClaimRow.world_id == world_id)
            .order_by(ClaimRow.created_at.desc())
            .limit(limit)
        )
        out: list[ClaimPersistenceRecord] = []
        for row in result.scalars().all():
            listeners = await self._listeners(row.id)
            out.append(claim_to_record(row, listeners))
        return out

    async def _listeners(self, claim_id: UUID) -> list[UUID]:
        result = await self._session.execute(
            select(ClaimListenerRow.listener_id).where(ClaimListenerRow.claim_id == claim_id)
        )
        return list(result.scalars().all())


class SqlAlchemyBeliefRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, belief_id: UUID) -> BeliefPersistenceRecord | None:
        row = await self._session.get(BeliefRow, belief_id)
        return belief_to_record(row) if row is not None else None

    async def insert(self, belief: BeliefPersistenceRecord) -> BeliefPersistenceRecord:
        row = BeliefRow(
            id=belief.id,
            world_id=belief.world_id,
            character_id=belief.character_id,
            proposition_key=belief.proposition_key,
            belief_text=belief.belief_text,
            confidence=belief.confidence,
            status=belief.status,
            first_source_observation_id=belief.first_source_observation_id,
            last_source_event_id=belief.last_source_event_id,
            evidence_summary=dict(belief.evidence_summary),
            version=belief.version,
        )
        self._session.add(row)
        await self._session.flush()
        return belief_to_record(row)

    async def list_for_character(
        self, character_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[BeliefPersistenceRecord]:
        result = await self._session.execute(
            select(BeliefRow)
            .where(BeliefRow.character_id == character_id, BeliefRow.world_id == world_id)
            .order_by(BeliefRow.updated_at.desc())
            .limit(limit)
        )
        return [belief_to_record(row) for row in result.scalars().all()]


class SqlAlchemySecretAccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, secret_access_id: UUID) -> SecretAccessPersistenceRecord | None:
        row = await self._session.get(SecretAccessRow, secret_access_id)
        return secret_access_to_record(row) if row is not None else None

    async def insert(self, access: SecretAccessPersistenceRecord) -> SecretAccessPersistenceRecord:
        row = SecretAccessRow(
            id=access.id,
            world_id=access.world_id,
            secret_key=access.secret_key,
            owner_character_id=access.owner_character_id,
            holder_character_id=access.holder_character_id,
            access_level=access.access_level,
            granted_event_id=access.granted_event_id,
            revoked_event_id=access.revoked_event_id,
        )
        self._session.add(row)
        await self._session.flush()
        return secret_access_to_record(row)

    async def list_for_holder(
        self, holder_character_id: UUID, *, world_id: UUID
    ) -> Sequence[SecretAccessPersistenceRecord]:
        result = await self._session.execute(
            select(SecretAccessRow).where(
                SecretAccessRow.holder_character_id == holder_character_id,
                SecretAccessRow.world_id == world_id,
            )
        )
        return [secret_access_to_record(row) for row in result.scalars().all()]


class SqlAlchemyActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, activity_id: UUID) -> ActivityPersistenceRecord | None:
        row = await self._session.get(ActivityRow, activity_id)
        return activity_to_record(row) if row is not None else None

    async def insert(self, activity: ActivityPersistenceRecord) -> ActivityPersistenceRecord:
        row = ActivityRow(
            id=activity.id,
            world_id=activity.world_id,
            owner_entity_id=activity.owner_entity_id,
            activity_type=activity.activity_type,
            status=activity.status,
            origin_location_id=activity.origin_location_id,
            destination_location_id=activity.destination_location_id,
            route_id=activity.route_id,
            started_phase_index=activity.started_phase_index,
            expected_end_phase_index=activity.expected_end_phase_index,
            progress=activity.progress,
            interruption_conditions=dict(activity.interruption_conditions),
            activity_payload=dict(activity.activity_payload),
            last_source_event_id=activity.last_source_event_id,
            version=activity.version,
        )
        self._session.add(row)
        await self._session.flush()
        return activity_to_record(row)

    async def list_for_owner(
        self, owner_entity_id: UUID, *, world_id: UUID
    ) -> Sequence[ActivityPersistenceRecord]:
        result = await self._session.execute(
            select(ActivityRow).where(
                ActivityRow.owner_entity_id == owner_entity_id,
                ActivityRow.world_id == world_id,
            )
        )
        return [activity_to_record(row) for row in result.scalars().all()]


class SqlAlchemyRouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, route_id: UUID) -> RoutePersistenceRecord | None:
        row = await self._session.get(RouteRow, route_id)
        return route_to_record(row) if row is not None else None

    async def insert(self, route: RoutePersistenceRecord) -> RoutePersistenceRecord:
        row = RouteRow(
            id=route.id,
            world_id=route.world_id,
            origin_location_id=route.origin_location_id,
            destination_location_id=route.destination_location_id,
            is_bidirectional=route.is_bidirectional,
            distance_units=route.distance_units,
            base_duration_phases=route.base_duration_phases,
            allowed_travel_modes=list(route.allowed_travel_modes),
            terrain_tags=list(route.terrain_tags),
            danger_level=route.danger_level,
            seasonal_modifiers=dict(route.seasonal_modifiers),
            status=route.status,
            created_event_id=route.created_event_id,
            version=route.version,
        )
        self._session.add(row)
        await self._session.flush()
        return route_to_record(row)

    async def list_for_world(self, world_id: UUID) -> Sequence[RoutePersistenceRecord]:
        result = await self._session.execute(select(RouteRow).where(RouteRow.world_id == world_id))
        return [route_to_record(row) for row in result.scalars().all()]


class SqlAlchemyHookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, hook_id: UUID) -> HookPersistenceRecord | None:
        row = await self._session.get(HookRow, hook_id)
        return hook_to_record(row) if row is not None else None

    async def insert(self, hook: HookPersistenceRecord) -> HookPersistenceRecord:
        row = HookRow(
            id=hook.id,
            world_id=hook.world_id,
            hook_key=hook.hook_key,
            title=hook.title,
            status=hook.status,
            premise=hook.premise,
            prerequisites=dict(hook.prerequisites),
            scheduled_window=hook.scheduled_window,
            involved_entity_ids=list(hook.involved_entity_ids),
            disclosure_state=hook.disclosure_state,
            cooldown_until_phase=hook.cooldown_until_phase,
            director_profile_key=hook.director_profile_key,
            source_event_id=hook.source_event_id,
            version=hook.version,
        )
        self._session.add(row)
        await self._session.flush()
        return hook_to_record(row)

    async def list_for_world(
        self, world_id: UUID, *, status: str | None = None
    ) -> Sequence[HookPersistenceRecord]:
        stmt = select(HookRow).where(HookRow.world_id == world_id)
        if status is not None:
            stmt = stmt.where(HookRow.status == status)
        result = await self._session.execute(stmt.order_by(HookRow.created_at.asc()))
        return [hook_to_record(row) for row in result.scalars().all()]


class SqlAlchemyNpcRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_profile(self, character_id: UUID) -> NpcProfilePersistenceRecord | None:
        row = await self._session.get(NpcProfileRow, character_id)
        return npc_profile_to_record(row) if row is not None else None

    async def insert_profile(
        self, profile: NpcProfilePersistenceRecord
    ) -> NpcProfilePersistenceRecord:
        row = NpcProfileRow(
            character_id=profile.character_id,
            world_id=profile.world_id,
            display_name=profile.display_name,
            role_tags=list(profile.role_tags),
            compact_card=dict(profile.compact_card),
            source_hook_id=profile.source_hook_id,
            similarity_fingerprint=profile.similarity_fingerprint,
            version=profile.version,
        )
        self._session.add(row)
        await self._session.flush()
        return npc_profile_to_record(row)

    async def get_lifecycle(self, character_id: UUID) -> NpcLifecyclePersistenceRecord | None:
        row = await self._session.get(NpcLifecycleRow, character_id)
        return npc_lifecycle_to_record(row) if row is not None else None

    async def insert_lifecycle(
        self, lifecycle: NpcLifecyclePersistenceRecord
    ) -> NpcLifecyclePersistenceRecord:
        row = NpcLifecycleRow(
            character_id=lifecycle.character_id,
            world_id=lifecycle.world_id,
            lifecycle_status=lifecycle.lifecycle_status,
            activated_phase_index=lifecycle.activated_phase_index,
            archive_phase_index=lifecycle.archive_phase_index,
            ttl_until_phase=lifecycle.ttl_until_phase,
            relevance_score=lifecycle.relevance_score,
            archive_summary=lifecycle.archive_summary,
            last_scene_phase_index=lifecycle.last_scene_phase_index,
            version=lifecycle.version,
        )
        self._session.add(row)
        await self._session.flush()
        return npc_lifecycle_to_record(row)


class SqlAlchemySummaryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, summary_id: UUID) -> SummaryPersistenceRecord | None:
        row = await self._session.get(SummaryRow, summary_id)
        return summary_to_record(row) if row is not None else None

    async def insert(self, summary: SummaryPersistenceRecord) -> SummaryPersistenceRecord:
        row = SummaryRow(
            id=summary.id,
            world_id=summary.world_id,
            owner_character_id=summary.owner_character_id,
            summary_type=summary.summary_type,
            start_phase_index=summary.start_phase_index,
            end_phase_index=summary.end_phase_index,
            content=summary.content,
            structured_extract=dict(summary.structured_extract),
            perspective=summary.perspective,
            version_number=summary.version_number,
            content_hash=summary.content_hash,
            model_call_id=summary.model_call_id,
        )
        self._session.add(row)
        await self._session.flush()
        return summary_to_record(row)

    async def list_for_owner(
        self, owner_character_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[SummaryPersistenceRecord]:
        result = await self._session.execute(
            select(SummaryRow)
            .where(
                SummaryRow.owner_character_id == owner_character_id,
                SummaryRow.world_id == world_id,
            )
            .order_by(SummaryRow.created_at.desc())
            .limit(limit)
        )
        return [summary_to_record(row) for row in result.scalars().all()]


class SqlAlchemyDiaryEntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entry_id: UUID) -> DiaryEntryPersistenceRecord | None:
        row = await self._session.get(DiaryEntryRow, entry_id)
        return diary_entry_to_record(row) if row is not None else None

    async def insert(self, entry: DiaryEntryPersistenceRecord) -> DiaryEntryPersistenceRecord:
        row = DiaryEntryRow(
            id=entry.id,
            world_id=entry.world_id,
            owner_character_id=entry.owner_character_id,
            day_index=entry.day_index,
            content=entry.content,
            summary_id=entry.summary_id,
            content_hash=entry.content_hash,
            version=entry.version,
        )
        self._session.add(row)
        await self._session.flush()
        return diary_entry_to_record(row)

    async def list_for_owner(
        self, owner_character_id: UUID, *, world_id: UUID, limit: int = 50
    ) -> Sequence[DiaryEntryPersistenceRecord]:
        result = await self._session.execute(
            select(DiaryEntryRow)
            .where(
                DiaryEntryRow.owner_character_id == owner_character_id,
                DiaryEntryRow.world_id == world_id,
            )
            .order_by(DiaryEntryRow.day_index.asc())
            .limit(limit)
        )
        return [diary_entry_to_record(row) for row in result.scalars().all()]


class SqlAlchemyDayRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, day_run_id: UUID) -> DayRunPersistenceRecord | None:
        row = await self._session.get(DayRunRow, day_run_id)
        return day_run_to_record(row) if row is not None else None

    async def find_by_idempotency_key(self, key: str) -> DayRunPersistenceRecord | None:
        result = await self._session.execute(
            select(DayRunRow).where(DayRunRow.idempotency_key == key)
        )
        row = result.scalar_one_or_none()
        return day_run_to_record(row) if row is not None else None

    async def insert(self, day_run: DayRunPersistenceRecord) -> DayRunPersistenceRecord:
        row = DayRunRow(
            id=day_run.id,
            world_id=day_run.world_id,
            day_index=day_run.day_index,
            status=day_run.status,
            started_at=day_run.started_at,
            completed_at=day_run.completed_at,
            recovery_snapshot_id=day_run.recovery_snapshot_id,
            idempotency_key=day_run.idempotency_key,
            version=day_run.version,
        )
        self._session.add(row)
        await self._session.flush()
        return day_run_to_record(row)

    async def list_for_world(self, world_id: UUID) -> Sequence[DayRunPersistenceRecord]:
        result = await self._session.execute(
            select(DayRunRow)
            .where(DayRunRow.world_id == world_id)
            .order_by(DayRunRow.day_index.asc())
        )
        return [day_run_to_record(row) for row in result.scalars().all()]
