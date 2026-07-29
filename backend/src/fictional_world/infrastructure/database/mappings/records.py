"""ORM <-> domain record mappers for Stage 0 repositories."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast
from uuid import UUID

from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.common.enums import BudgetStatus, TaskState
from fictional_world.domain.events.persistence import (
    EventEffectRecord,
    OutboxMessageRecord,
    WorldEventRecord,
)
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.phases.records import PhaseRunRecord
from fictional_world.domain.tasks.budget import RequestBudgetRecord
from fictional_world.domain.tasks.task_run import TaskRun
from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)
from fictional_world.infrastructure.database.models import (
    AggregateVersionRow,
    CharacterRow,
    CharacterStateRow,
    EntityRow,
    EventEffectRow,
    ObservationRow,
    OutboxMessageRow,
    PhaseRunRow,
    RecentMemoryRow,
    RequestBudgetLedgerRow,
    TaskRunRow,
    WorldClockRow,
    WorldEventRow,
    WorldRow,
)


def _json_obj(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def world_to_record(row: WorldRow) -> WorldRecord:
    return WorldRecord(
        id=row.id,
        slug=row.slug,
        name=row.name,
        status=row.status,
        language=row.language,
        content_rating=row.content_rating,
        current_event_sequence=int(row.current_event_sequence),
        version=int(row.version),
        created_at=row.created_at,
        ended_at=row.ended_at,
    )


def apply_world(row: WorldRow, record: WorldRecord) -> None:
    row.id = record.id
    row.slug = record.slug
    row.name = record.name
    row.status = record.status
    row.language = record.language
    row.content_rating = record.content_rating
    row.current_event_sequence = record.current_event_sequence
    row.version = record.version
    row.ended_at = record.ended_at


def clock_to_record(row: WorldClockRow) -> WorldClockRecord:
    return WorldClockRecord(
        world_id=row.world_id,
        generation_number=int(row.generation_number),
        year=int(row.year),
        month=int(row.month),
        day=int(row.day),
        phase_name=row.phase_name,
        phase_ordinal=int(row.phase_ordinal),
        absolute_day_index=int(row.absolute_day_index),
        absolute_phase_index=int(row.absolute_phase_index),
        resolution_mode=row.resolution_mode,
        last_event_id=row.last_event_id,
        version=int(row.version),
        updated_at=row.updated_at,
    )


def apply_clock(row: WorldClockRow, record: WorldClockRecord) -> None:
    row.world_id = record.world_id
    row.generation_number = record.generation_number
    row.year = record.year
    row.month = record.month
    row.day = record.day
    row.phase_name = record.phase_name
    row.phase_ordinal = record.phase_ordinal
    row.absolute_day_index = record.absolute_day_index
    row.absolute_phase_index = record.absolute_phase_index
    row.resolution_mode = record.resolution_mode
    row.last_event_id = record.last_event_id
    row.version = record.version


def entity_to_record(row: EntityRow) -> EntityRecord:
    return EntityRecord(
        id=row.id,
        world_id=row.world_id,
        entity_type=row.entity_type,
        canonical_name=row.canonical_name,
        normalized_name=row.normalized_name,
        lifecycle_status=row.lifecycle_status,
        created_event_id=row.created_event_id,
        archived_event_id=row.archived_event_id,
        created_at=row.created_at,
        archived_at=row.archived_at,
    )


def character_to_record(row: CharacterRow) -> CharacterRecord:
    return CharacterRecord(
        entity_id=row.entity_id,
        character_kind=row.character_kind,
        species_code=row.species_code,
        current_card_version_id=row.current_card_version_id,
        version=int(row.version),
    )


def character_state_to_record(row: CharacterStateRow) -> CharacterStateRecord:
    return CharacterStateRecord(
        character_id=row.character_id,
        location_id=row.location_id,
        life_status=row.life_status,
        stamina=Decimal(row.stamina),
        mana=Decimal(row.mana),
        energy=Decimal(row.energy),
        hunger=Decimal(row.hunger),
        pain=Decimal(row.pain),
        stress=Decimal(row.stress),
        social_need=Decimal(row.social_need),
        valence=Decimal(row.valence),
        arousal=Decimal(row.arousal),
        dominance=Decimal(row.dominance),
        active_activity_id=row.active_activity_id,
        current_card_version_id=row.current_card_version_id,
        last_source_event_id=row.last_source_event_id,
        version=int(row.version),
        updated_at=row.updated_at,
    )


def apply_character_state(row: CharacterStateRow, record: CharacterStateRecord) -> None:
    row.character_id = record.character_id
    row.location_id = record.location_id
    row.life_status = record.life_status
    row.stamina = record.stamina
    row.mana = record.mana
    row.energy = record.energy
    row.hunger = record.hunger
    row.pain = record.pain
    row.stress = record.stress
    row.social_need = record.social_need
    row.valence = record.valence
    row.arousal = record.arousal
    row.dominance = record.dominance
    row.active_activity_id = record.active_activity_id
    row.current_card_version_id = record.current_card_version_id
    row.last_source_event_id = record.last_source_event_id
    row.version = record.version


def phase_to_record(row: PhaseRunRow) -> PhaseRunRecord:
    detail = _json_obj(row.error_detail) if row.error_detail is not None else None
    return PhaseRunRecord(
        id=row.id,
        world_id=row.world_id,
        absolute_phase_index=int(row.absolute_phase_index),
        phase_name=row.phase_name,
        resolution_mode=row.resolution_mode,
        state=row.state,
        expected_character_count=int(row.expected_character_count),
        completed_character_count=int(row.completed_character_count),
        expected_scene_count=(
            int(row.expected_scene_count) if row.expected_scene_count is not None else None
        ),
        completed_scene_count=int(row.completed_scene_count),
        request_reservation_id=row.request_reservation_id,
        idempotency_key=row.idempotency_key,
        error_code=row.error_code,
        error_detail=detail,
        started_at=row.started_at,
        completed_at=row.completed_at,
        version=int(row.version),
    )


def apply_phase(row: PhaseRunRow, record: PhaseRunRecord) -> None:
    row.id = record.id
    row.world_id = record.world_id
    row.absolute_phase_index = record.absolute_phase_index
    row.phase_name = record.phase_name
    row.resolution_mode = record.resolution_mode
    row.state = record.state
    row.expected_character_count = record.expected_character_count
    row.completed_character_count = record.completed_character_count
    row.expected_scene_count = record.expected_scene_count
    row.completed_scene_count = record.completed_scene_count
    row.request_reservation_id = record.request_reservation_id
    row.idempotency_key = record.idempotency_key
    row.error_code = record.error_code
    row.error_detail = record.error_detail
    row.completed_at = record.completed_at
    row.version = record.version


def effect_to_record(row: EventEffectRow) -> EventEffectRecord:
    attempts = tuple(row.source_attempt_ids or ())
    return EventEffectRecord(
        id=row.id,
        world_event_id=row.world_event_id,
        effect_index=int(row.effect_index),
        effect_type=row.effect_type,
        target_entity_id=row.target_entity_id,
        effect_payload=_json_obj(row.effect_payload),
        previous_state=_json_obj(row.previous_state),
        resulting_state=_json_obj(row.resulting_state),
        target_version_before=row.target_version_before,
        target_version_after=row.target_version_after,
        source_attempt_ids=attempts,
        validation_manifest=_json_obj(row.validation_manifest),
    )


def event_to_record(
    row: WorldEventRow, effects: list[EventEffectRow] | None = None
) -> WorldEventRecord:
    effect_records = tuple(effect_to_record(e) for e in (effects or []))
    return WorldEventRecord(
        id=row.id,
        world_id=row.world_id,
        sequence_number=int(row.sequence_number),
        absolute_phase_index=int(row.absolute_phase_index),
        phase_run_id=row.phase_run_id,
        scene_id=row.scene_id,
        event_type=row.event_type,
        initiator_entity_id=row.initiator_entity_id,
        location_id=row.location_id,
        canonical_summary=row.canonical_summary,
        structured_facts=_json_obj(row.structured_facts),
        importance=Decimal(row.importance),
        visibility_class=row.visibility_class,
        source_kind=row.source_kind,
        source_model_profile_id=row.source_model_profile_id,
        prompt_version_id=row.prompt_version_id,
        random_seed=row.random_seed,
        idempotency_key=row.idempotency_key,
        supersedes_event_id=row.supersedes_event_id,
        consistency_status=row.consistency_status,
        committed_at=row.committed_at,
        effects=effect_records,
    )


def observation_to_record(row: ObservationRow) -> ObservationPersistenceRecord:
    return ObservationPersistenceRecord(
        id=row.id,
        world_event_id=row.world_event_id,
        observer_id=row.observer_id,
        observation_type=row.observation_type,
        perceived_summary=row.perceived_summary,
        perceived_facts=_json_obj(row.perceived_facts),
        omitted_fact_keys=tuple(row.omitted_fact_keys or ()),
        confidence=Decimal(row.confidence),
        visibility_reason=row.visibility_reason,
        source_sense_tags=tuple(row.source_sense_tags or ()),
        content_hash=row.content_hash,
        created_at=row.created_at,
    )


def memory_to_record(row: RecentMemoryRow) -> RecentMemoryRecord:
    return RecentMemoryRecord(
        id=row.id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        memory_type=row.memory_type,
        content=row.content,
        salience=Decimal(row.salience),
        confidence=Decimal(row.confidence),
        emotional_weight=Decimal(row.emotional_weight),
        visibility=row.visibility,
        occurred_phase_index=int(row.occurred_phase_index),
        created_phase_index=int(row.created_phase_index),
        last_recalled_phase_index=row.last_recalled_phase_index,
        recall_count=int(row.recall_count),
        decay_score=Decimal(row.decay_score),
        status=row.status,
        content_hash=row.content_hash,
        summary_version=int(row.summary_version),
        source_event_id=row.source_event_id,
        source_observation_id=row.source_observation_id,
        created_at=row.created_at,
    )


def aggregate_version_to_record(row: AggregateVersionRow) -> AggregateVersionRecord:
    return AggregateVersionRecord(
        world_id=row.world_id,
        aggregate_type=row.aggregate_type,
        aggregate_id=row.aggregate_id,
        version=int(row.version),
        updated_at=row.updated_at,
    )


def outbox_to_record(row: OutboxMessageRow) -> OutboxMessageRecord:
    return OutboxMessageRecord(
        id=row.id,
        world_event_id=row.world_event_id,
        message_type=row.message_type,
        payload=_json_obj(row.payload),
        idempotency_key=row.idempotency_key,
        state=row.state,
        attempt_count=int(row.attempt_count),
        available_at=row.available_at,
        claimed_by=row.claimed_by,
        claim_expires_at=row.claim_expires_at,
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


def task_to_record(row: TaskRunRow) -> TaskRun:
    return TaskRun(
        id=row.id,
        task_type=row.task_type,
        world_id=row.world_id,
        phase_run_id=row.phase_run_id,
        scene_id=row.scene_id,
        subject_entity_id=row.subject_entity_id,
        state=TaskState(row.state),
        priority=int(row.priority),
        payload=_json_obj(row.payload),
        idempotency_key=row.idempotency_key,
        attempt_count=int(row.attempt_count),
        max_attempts=int(row.max_attempts),
        available_at=row.available_at,
        lease_owner=row.lease_owner,
        lease_expires_at=row.lease_expires_at,
        heartbeat_at=row.heartbeat_at,
        result_reference=_json_obj(row.result_reference) if row.result_reference else None,
        error_code=row.error_code,
        error_detail=_json_obj(row.error_detail) if row.error_detail else None,
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


def budget_to_record(row: RequestBudgetLedgerRow) -> RequestBudgetRecord:
    return RequestBudgetRecord(
        id=row.id,
        reservation_key=row.reservation_key,
        required_request_count=int(row.required_request_count),
        provider_kind=row.provider_kind,
        model_slug=row.model_slug,
        status=BudgetStatus(row.status),
        world_id=row.world_id,
        phase_run_id=row.phase_run_id,
        task_run_id=row.task_run_id,
        reserved_at=row.reserved_at,
        expires_at=row.expires_at,
        consumed_at=row.consumed_at,
    )


def parse_aggregate_key(key: str) -> tuple[str, UUID]:
    aggregate_type, aggregate_id = key.split(":", 1)
    return aggregate_type, UUID(aggregate_id)
