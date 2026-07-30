"""SQLAlchemy repositories for Stage 3 long-term tables."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from fictional_world.domain.stage3.persistence import (
    ArcPersistenceRecord,
    EmbeddingJobPersistenceRecord,
    EmbeddingModelVersionPersistenceRecord,
    EvaluatorRunPersistenceRecord,
    FactionPersistenceRecord,
    InjuryPersistenceRecord,
    MemoryEmbeddingPersistenceRecord,
    MemoryPersistenceRecord,
    MemorySourcePersistenceRecord,
    MonthRunPersistenceRecord,
    QualityFindingPersistenceRecord,
    StatStatePersistenceRecord,
)
from fictional_world.infrastructure.database.mappings.stage3_records import (
    arc_to_record,
    as_uuid_list,
    embedding_job_to_record,
    embedding_model_version_to_record,
    evaluator_run_to_record,
    faction_to_record,
    format_vector,
    injury_to_record,
    memory_embedding_to_record,
    memory_source_to_record,
    memory_to_record,
    month_run_to_record,
    quality_finding_to_record,
    stat_state_to_record,
)
from fictional_world.infrastructure.database.models.stage3 import (
    ArcRow,
    EmbeddingJobRow,
    EmbeddingModelVersionRow,
    EvaluatorRunRow,
    FactionRow,
    InjuryRow,
    MemoryEmbeddingRow,
    MemoryRow,
    MemorySourceRow,
    MonthRunRow,
    QualityFindingRow,
    StatStateRow,
)


class SqlAlchemyLongTermMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, memory_id: UUID) -> MemoryPersistenceRecord | None:
        row = await self._session.get(MemoryRow, memory_id)
        return memory_to_record(row) if row is not None else None

    async def insert(self, memory: MemoryPersistenceRecord) -> MemoryPersistenceRecord:
        row = MemoryRow(
            id=memory.id,
            world_id=memory.world_id,
            owner_character_id=memory.owner_character_id,
            memory_type=memory.memory_type,
            content=memory.content,
            salience=memory.salience,
            confidence=memory.confidence,
            emotional_weight=memory.emotional_weight,
            visibility=memory.visibility,
            occurred_phase_index=memory.occurred_phase_index,
            created_phase_index=memory.created_phase_index,
            last_recalled_phase_index=memory.last_recalled_phase_index,
            recall_count=memory.recall_count,
            decay_score=memory.decay_score,
            status=memory.status,
            content_hash=memory.content_hash,
            summary_version=memory.summary_version,
            goal_relevance=memory.goal_relevance,
            emotional_resonance=memory.emotional_resonance,
            unresolved_commitment=memory.unresolved_commitment,
            referenced_entity_ids=as_uuid_list(memory.referenced_entity_ids),
            source_event_id=memory.source_event_id,
        )
        self._session.add(row)
        await self._session.flush()
        return memory_to_record(row)

    async def insert_source(
        self, source: MemorySourcePersistenceRecord
    ) -> MemorySourcePersistenceRecord:
        row = MemorySourceRow(
            id=source.id,
            memory_id=source.memory_id,
            source_kind=source.source_kind,
            source_id=source.source_id,
            source_role=source.source_role,
            weight=source.weight,
            ordinal=source.ordinal,
        )
        self._session.add(row)
        await self._session.flush()
        return memory_source_to_record(row)

    async def list_for_owner(
        self,
        world_id: UUID,
        owner_character_id: UUID,
        *,
        visibility: str | None = None,
        status: str = "active",
    ) -> Sequence[MemoryPersistenceRecord]:
        stmt = select(MemoryRow).where(
            MemoryRow.world_id == world_id,
            MemoryRow.owner_character_id == owner_character_id,
            MemoryRow.status == status,
        )
        if visibility is not None:
            stmt = stmt.where(MemoryRow.visibility == visibility)
        stmt = stmt.order_by(MemoryRow.created_phase_index.desc())
        rows = (await self._session.scalars(stmt)).all()
        return [memory_to_record(row) for row in rows]


class SqlAlchemyMemoryEmbeddingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, embedding_id: UUID) -> MemoryEmbeddingPersistenceRecord | None:
        row = await self._session.get(MemoryEmbeddingRow, embedding_id)
        return memory_embedding_to_record(row) if row is not None else None

    async def insert(
        self, embedding: MemoryEmbeddingPersistenceRecord
    ) -> MemoryEmbeddingPersistenceRecord:
        vector_literal = format_vector(embedding.embedding, dimension=embedding.dimension)
        await self._session.execute(
            text(
                """
                INSERT INTO worldsim.memory_embedding (
                    id, memory_id, world_id, owner_character_id,
                    embedding_model_key, embedding_version, dimension, prefix_type,
                    embedded_content_hash, embedding, is_active
                ) VALUES (
                    :id, :memory_id, :world_id, :owner_character_id,
                    :embedding_model_key, :embedding_version, :dimension, :prefix_type,
                    :embedded_content_hash, CAST(:embedding AS vector), :is_active
                )
                """
            ),
            {
                "id": embedding.id,
                "memory_id": embedding.memory_id,
                "world_id": embedding.world_id,
                "owner_character_id": embedding.owner_character_id,
                "embedding_model_key": embedding.embedding_model_key,
                "embedding_version": embedding.embedding_version,
                "dimension": embedding.dimension,
                "prefix_type": embedding.prefix_type,
                "embedded_content_hash": embedding.embedded_content_hash,
                "embedding": vector_literal,
                "is_active": embedding.is_active,
            },
        )
        await self._session.flush()
        loaded = await self.get(embedding.id)
        if loaded is None:
            msg = f"memory_embedding {embedding.id} missing after insert"
            raise RuntimeError(msg)
        return loaded


class SqlAlchemyEmbeddingModelVersionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active(self, model_key: str) -> EmbeddingModelVersionPersistenceRecord | None:
        stmt = select(EmbeddingModelVersionRow).where(
            EmbeddingModelVersionRow.model_key == model_key,
            EmbeddingModelVersionRow.is_active.is_(True),
        )
        row = await self._session.scalar(stmt)
        return embedding_model_version_to_record(row) if row is not None else None

    async def insert(
        self, version: EmbeddingModelVersionPersistenceRecord
    ) -> EmbeddingModelVersionPersistenceRecord:
        row = EmbeddingModelVersionRow(
            id=version.id,
            model_key=version.model_key,
            provider=version.provider,
            model_slug=version.model_slug,
            dimension=version.dimension,
            query_prefix=version.query_prefix,
            passage_prefix=version.passage_prefix,
            truncation_policy=version.truncation_policy,
            embedding_version=version.embedding_version,
            is_active=version.is_active,
            capability_probe=dict(version.capability_probe),
        )
        self._session.add(row)
        await self._session.flush()
        return embedding_model_version_to_record(row)


class SqlAlchemyEmbeddingJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> EmbeddingJobPersistenceRecord | None:
        stmt = select(EmbeddingJobRow).where(EmbeddingJobRow.idempotency_key == idempotency_key)
        row = await self._session.scalar(stmt)
        return embedding_job_to_record(row) if row is not None else None

    async def insert(self, job: EmbeddingJobPersistenceRecord) -> EmbeddingJobPersistenceRecord:
        row = EmbeddingJobRow(
            id=job.id,
            world_id=job.world_id,
            memory_id=job.memory_id,
            embedding_model_key=job.embedding_model_key,
            embedding_version=job.embedding_version,
            status=job.status,
            idempotency_key=job.idempotency_key,
            attempt_count=job.attempt_count,
            last_error=job.last_error,
            completed_at=job.completed_at,
        )
        self._session.add(row)
        await self._session.flush()
        return embedding_job_to_record(row)


class SqlAlchemyStatStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, character_id: UUID, stat_code: str) -> StatStatePersistenceRecord | None:
        row = await self._session.get(StatStateRow, (character_id, stat_code))
        return stat_state_to_record(row) if row is not None else None

    async def upsert(self, state: StatStatePersistenceRecord) -> StatStatePersistenceRecord:
        existing = await self._session.get(StatStateRow, (state.character_id, state.stat_code))
        if existing is None:
            row = StatStateRow(
                character_id=state.character_id,
                world_id=state.world_id,
                stat_code=state.stat_code,
                current_value=state.current_value,
                dynamic_potential_cap=state.dynamic_potential_cap,
                growth_rate=state.growth_rate,
                adaptability=state.adaptability,
                last_source_event_id=state.last_source_event_id,
                version=state.version,
            )
            self._session.add(row)
        else:
            existing.current_value = state.current_value
            existing.dynamic_potential_cap = state.dynamic_potential_cap
            existing.growth_rate = state.growth_rate
            existing.adaptability = state.adaptability
            existing.last_source_event_id = state.last_source_event_id
            existing.version = state.version
            row = existing
        await self._session.flush()
        return stat_state_to_record(row)


class SqlAlchemyInjuryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, injury_id: UUID) -> InjuryPersistenceRecord | None:
        row = await self._session.get(InjuryRow, injury_id)
        return injury_to_record(row) if row is not None else None

    async def insert(self, injury: InjuryPersistenceRecord) -> InjuryPersistenceRecord:
        row = InjuryRow(
            id=injury.id,
            world_id=injury.world_id,
            character_id=injury.character_id,
            body_region=injury.body_region,
            injury_type=injury.injury_type,
            severity=injury.severity,
            bleeding=injury.bleeding,
            pain=injury.pain,
            mobility_penalty=injury.mobility_penalty,
            consciousness_impact=injury.consciousness_impact,
            infection_risk=injury.infection_risk,
            healing_progress=injury.healing_progress,
            treatment=dict(injury.treatment),
            permanent_consequence=injury.permanent_consequence,
            status=injury.status,
            inflicted_event_id=injury.inflicted_event_id,
            healed_event_id=injury.healed_event_id,
            version=injury.version,
        )
        self._session.add(row)
        await self._session.flush()
        return injury_to_record(row)


class SqlAlchemyFactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, faction_id: UUID) -> FactionPersistenceRecord | None:
        row = await self._session.get(FactionRow, faction_id)
        return faction_to_record(row) if row is not None else None

    async def get_by_key(self, world_id: UUID, faction_key: str) -> FactionPersistenceRecord | None:
        stmt = select(FactionRow).where(
            FactionRow.world_id == world_id,
            FactionRow.faction_key == faction_key,
        )
        row = await self._session.scalar(stmt)
        return faction_to_record(row) if row is not None else None

    async def insert(self, faction: FactionPersistenceRecord) -> FactionPersistenceRecord:
        row = FactionRow(
            id=faction.id,
            world_id=faction.world_id,
            faction_key=faction.faction_key,
            name=faction.name,
            faction_type=faction.faction_type,
            status=faction.status,
            leadership=dict(faction.leadership),
            territory_location_ids=as_uuid_list(faction.territory_location_ids),
            goals=dict(faction.goals),
            resources=dict(faction.resources),
            plans=dict(faction.plans),
            plot_armour_bias=faction.plot_armour_bias,
            created_event_id=faction.created_event_id,
            version=faction.version,
        )
        self._session.add(row)
        await self._session.flush()
        return faction_to_record(row)

    async def list_for_world(self, world_id: UUID) -> Sequence[FactionPersistenceRecord]:
        stmt = (
            select(FactionRow)
            .where(FactionRow.world_id == world_id)
            .order_by(FactionRow.faction_key.asc())
        )
        rows = (await self._session.scalars(stmt)).all()
        return [faction_to_record(row) for row in rows]


class SqlAlchemyArcRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, arc_id: UUID) -> ArcPersistenceRecord | None:
        row = await self._session.get(ArcRow, arc_id)
        return arc_to_record(row) if row is not None else None

    async def get_by_key(self, world_id: UUID, arc_key: str) -> ArcPersistenceRecord | None:
        stmt = select(ArcRow).where(ArcRow.world_id == world_id, ArcRow.arc_key == arc_key)
        row = await self._session.scalar(stmt)
        return arc_to_record(row) if row is not None else None

    async def insert(self, arc: ArcPersistenceRecord) -> ArcPersistenceRecord:
        row = ArcRow(
            id=arc.id,
            world_id=arc.world_id,
            arc_key=arc.arc_key,
            title=arc.title,
            arc_scope=arc.arc_scope,
            status=arc.status,
            premise=arc.premise,
            objective=arc.objective,
            milestones=dict(arc.milestones),
            prerequisites=dict(arc.prerequisites),
            closure_conditions=dict(arc.closure_conditions),
            participant_entity_ids=as_uuid_list(arc.participant_entity_ids),
            dominant_genres=list(arc.dominant_genres),
            progress=arc.progress,
            deadline_phase_index=arc.deadline_phase_index,
            start_phase_index=arc.start_phase_index,
            end_phase_index=arc.end_phase_index,
            director_profile_key=arc.director_profile_key,
            source_event_id=arc.source_event_id,
            version=arc.version,
        )
        self._session.add(row)
        await self._session.flush()
        return arc_to_record(row)

    async def list_for_world(self, world_id: UUID) -> Sequence[ArcPersistenceRecord]:
        stmt = select(ArcRow).where(ArcRow.world_id == world_id).order_by(ArcRow.arc_key.asc())
        rows = (await self._session.scalars(stmt)).all()
        return [arc_to_record(row) for row in rows]


class SqlAlchemyEvaluatorRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, run_id: UUID) -> EvaluatorRunPersistenceRecord | None:
        row = await self._session.get(EvaluatorRunRow, run_id)
        return evaluator_run_to_record(row) if row is not None else None

    async def insert(self, run: EvaluatorRunPersistenceRecord) -> EvaluatorRunPersistenceRecord:
        row = EvaluatorRunRow(
            id=run.id,
            world_id=run.world_id,
            scope=run.scope,
            target_ref=run.target_ref,
            status=run.status,
            idempotency_key=run.idempotency_key,
            findings_summary=dict(run.findings_summary),
            requested_narration_regen=run.requested_narration_regen,
            model_call_id=run.model_call_id,
        )
        self._session.add(row)
        await self._session.flush()
        return evaluator_run_to_record(row)

    async def insert_finding(
        self, finding: QualityFindingPersistenceRecord
    ) -> QualityFindingPersistenceRecord:
        row = QualityFindingRow(
            id=finding.id,
            evaluator_run_id=finding.evaluator_run_id,
            world_id=finding.world_id,
            finding_code=finding.finding_code,
            severity=finding.severity,
            message=finding.message,
            evidence_refs=dict(finding.evidence_refs),
            can_mutate_canon=finding.can_mutate_canon,
        )
        self._session.add(row)
        await self._session.flush()
        return quality_finding_to_record(row)


class SqlAlchemyMonthRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, month_run_id: UUID) -> MonthRunPersistenceRecord | None:
        row = await self._session.get(MonthRunRow, month_run_id)
        return month_run_to_record(row) if row is not None else None

    async def get_by_world_month(
        self, world_id: UUID, month_index: int
    ) -> MonthRunPersistenceRecord | None:
        stmt = select(MonthRunRow).where(
            MonthRunRow.world_id == world_id,
            MonthRunRow.month_index == month_index,
        )
        row = await self._session.scalar(stmt)
        return month_run_to_record(row) if row is not None else None

    async def insert(self, month_run: MonthRunPersistenceRecord) -> MonthRunPersistenceRecord:
        row = MonthRunRow(
            id=month_run.id,
            world_id=month_run.world_id,
            month_index=month_run.month_index,
            status=month_run.status,
            start_day_index=month_run.start_day_index,
            end_day_index=month_run.end_day_index,
            idempotency_key=month_run.idempotency_key,
            metrics=dict(month_run.metrics),
            completed_at=month_run.completed_at,
        )
        self._session.add(row)
        await self._session.flush()
        return month_run_to_record(row)

    async def list_for_world(self, world_id: UUID) -> Sequence[MonthRunPersistenceRecord]:
        stmt = (
            select(MonthRunRow)
            .where(MonthRunRow.world_id == world_id)
            .order_by(MonthRunRow.month_index.asc())
        )
        rows = (await self._session.scalars(stmt)).all()
        return [month_run_to_record(row) for row in rows]
