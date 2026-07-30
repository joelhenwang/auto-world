"""Map Stage 3 ORM rows to domain persistence records."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

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


def _dec(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _as_dict(value: object | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def _as_uuid_tuple(value: object | None) -> tuple[UUID, ...]:
    if isinstance(value, list):
        return tuple(cast(list[UUID], value))
    if isinstance(value, tuple):
        return cast(tuple[UUID, ...], value)
    return ()


def _as_str_tuple(value: object | None) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(cast(list[str], value))
    if isinstance(value, tuple):
        return cast(tuple[str, ...], value)
    return ()


def memory_to_record(row: MemoryRow) -> MemoryPersistenceRecord:
    return MemoryPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        memory_type=row.memory_type,
        content=row.content,
        salience=_dec(row.salience),
        confidence=_dec(row.confidence),
        emotional_weight=_dec(row.emotional_weight),
        visibility=row.visibility,
        occurred_phase_index=row.occurred_phase_index,
        created_phase_index=row.created_phase_index,
        last_recalled_phase_index=row.last_recalled_phase_index,
        recall_count=row.recall_count,
        decay_score=_dec(row.decay_score),
        status=row.status,
        content_hash=row.content_hash,
        summary_version=row.summary_version,
        goal_relevance=_dec(row.goal_relevance),
        emotional_resonance=_dec(row.emotional_resonance),
        unresolved_commitment=_dec(row.unresolved_commitment),
        referenced_entity_ids=_as_uuid_tuple(row.referenced_entity_ids),
        source_event_id=row.source_event_id,
        created_at=row.created_at,
    )


def memory_source_to_record(row: MemorySourceRow) -> MemorySourcePersistenceRecord:
    return MemorySourcePersistenceRecord(
        id=row.id,
        memory_id=row.memory_id,
        source_kind=row.source_kind,
        source_id=row.source_id,
        source_role=row.source_role,
        weight=_dec(row.weight),
        ordinal=row.ordinal,
    )


def embedding_model_version_to_record(
    row: EmbeddingModelVersionRow,
) -> EmbeddingModelVersionPersistenceRecord:
    return EmbeddingModelVersionPersistenceRecord(
        id=row.id,
        model_key=row.model_key,
        provider=row.provider,
        model_slug=row.model_slug,
        dimension=row.dimension,
        query_prefix=row.query_prefix,
        passage_prefix=row.passage_prefix,
        truncation_policy=row.truncation_policy,
        embedding_version=row.embedding_version,
        is_active=row.is_active,
        capability_probe=_as_dict(row.capability_probe),
        created_at=row.created_at,
    )


def _parse_embedding(raw: object) -> tuple[float, ...]:
    if raw is None:
        return ()
    if isinstance(raw, list):
        return tuple(float(x) for x in cast(list[float], raw))
    if isinstance(raw, tuple):
        return tuple(float(x) for x in cast(tuple[float, ...], raw))
    text = str(raw).strip()
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return ()
        return tuple(float(part) for part in inner.split(","))
    return ()


def memory_embedding_to_record(row: MemoryEmbeddingRow) -> MemoryEmbeddingPersistenceRecord:
    return MemoryEmbeddingPersistenceRecord(
        id=row.id,
        memory_id=row.memory_id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        embedding_model_key=row.embedding_model_key,
        embedding_version=row.embedding_version,
        dimension=row.dimension,
        prefix_type=row.prefix_type,
        embedded_content_hash=row.embedded_content_hash,
        embedding=_parse_embedding(row.embedding),
        is_active=row.is_active,
        created_at=row.created_at,
    )


def embedding_job_to_record(row: EmbeddingJobRow) -> EmbeddingJobPersistenceRecord:
    return EmbeddingJobPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        memory_id=row.memory_id,
        embedding_model_key=row.embedding_model_key,
        embedding_version=row.embedding_version,
        status=row.status,
        idempotency_key=row.idempotency_key,
        attempt_count=row.attempt_count,
        last_error=row.last_error,
        created_at=row.created_at,
        updated_at=row.updated_at,
        completed_at=row.completed_at,
    )


def stat_state_to_record(row: StatStateRow) -> StatStatePersistenceRecord:
    return StatStatePersistenceRecord(
        character_id=row.character_id,
        world_id=row.world_id,
        stat_code=row.stat_code,
        current_value=_dec(row.current_value),
        dynamic_potential_cap=_dec(row.dynamic_potential_cap),
        growth_rate=_dec(row.growth_rate),
        adaptability=_dec(row.adaptability),
        last_source_event_id=row.last_source_event_id,
        version=row.version,
        updated_at=row.updated_at,
    )


def injury_to_record(row: InjuryRow) -> InjuryPersistenceRecord:
    return InjuryPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        character_id=row.character_id,
        body_region=row.body_region,
        injury_type=row.injury_type,
        severity=_dec(row.severity),
        bleeding=_dec(row.bleeding),
        pain=_dec(row.pain),
        mobility_penalty=_dec(row.mobility_penalty),
        consciousness_impact=_dec(row.consciousness_impact),
        infection_risk=_dec(row.infection_risk),
        healing_progress=_dec(row.healing_progress),
        treatment=_as_dict(row.treatment),
        permanent_consequence=row.permanent_consequence,
        status=row.status,
        inflicted_event_id=row.inflicted_event_id,
        healed_event_id=row.healed_event_id,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def faction_to_record(row: FactionRow) -> FactionPersistenceRecord:
    return FactionPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        faction_key=row.faction_key,
        name=row.name,
        faction_type=row.faction_type,
        status=row.status,
        leadership=_as_dict(row.leadership),
        territory_location_ids=_as_uuid_tuple(row.territory_location_ids),
        goals=_as_dict(row.goals),
        resources=_as_dict(row.resources),
        plans=_as_dict(row.plans),
        plot_armour_bias=_dec(row.plot_armour_bias),
        created_event_id=row.created_event_id,
        version=row.version,
        created_at=row.created_at,
    )


def arc_to_record(row: ArcRow) -> ArcPersistenceRecord:
    return ArcPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        arc_key=row.arc_key,
        title=row.title,
        arc_scope=row.arc_scope,
        status=row.status,
        premise=row.premise,
        objective=row.objective,
        milestones=_as_dict(row.milestones),
        prerequisites=_as_dict(row.prerequisites),
        closure_conditions=_as_dict(row.closure_conditions),
        participant_entity_ids=_as_uuid_tuple(row.participant_entity_ids),
        dominant_genres=_as_str_tuple(row.dominant_genres),
        progress=_dec(row.progress),
        deadline_phase_index=row.deadline_phase_index,
        start_phase_index=row.start_phase_index,
        end_phase_index=row.end_phase_index,
        director_profile_key=row.director_profile_key,
        source_event_id=row.source_event_id,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def evaluator_run_to_record(row: EvaluatorRunRow) -> EvaluatorRunPersistenceRecord:
    return EvaluatorRunPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        scope=row.scope,
        target_ref=row.target_ref,
        status=row.status,
        idempotency_key=row.idempotency_key,
        findings_summary=_as_dict(row.findings_summary),
        requested_narration_regen=row.requested_narration_regen,
        model_call_id=row.model_call_id,
        created_at=row.created_at,
    )


def quality_finding_to_record(row: QualityFindingRow) -> QualityFindingPersistenceRecord:
    return QualityFindingPersistenceRecord(
        id=row.id,
        evaluator_run_id=row.evaluator_run_id,
        world_id=row.world_id,
        finding_code=row.finding_code,
        severity=row.severity,
        message=row.message,
        evidence_refs=_as_dict(row.evidence_refs),
        can_mutate_canon=row.can_mutate_canon,
        created_at=row.created_at,
    )


def month_run_to_record(row: MonthRunRow) -> MonthRunPersistenceRecord:
    return MonthRunPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        month_index=row.month_index,
        status=row.status,
        start_day_index=row.start_day_index,
        end_day_index=row.end_day_index,
        idempotency_key=row.idempotency_key,
        metrics=_as_dict(row.metrics),
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


def format_vector(values: tuple[float, ...] | list[float], *, dimension: int) -> str:
    """Format a Python sequence as a pgvector literal."""
    if len(values) != dimension:
        msg = f"embedding length {len(values)} != dimension {dimension}"
        raise ValueError(msg)
    return "[" + ",".join(str(float(v)) for v in values) + "]"


def as_uuid_list(values: tuple[UUID, ...] | list[UUID]) -> list[UUID]:
    return list(values)
