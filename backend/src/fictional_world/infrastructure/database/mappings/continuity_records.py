"""ORM <-> domain mappers for Stage 2 continuity / knowledge tables."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

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
    ClaimRow,
    SecretAccessRow,
)


def _json_obj(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def _uuid_tuple(value: list[UUID] | None) -> tuple[UUID, ...]:
    if not value:
        return ()
    return tuple(value)


def route_to_record(row: RouteRow) -> RoutePersistenceRecord:
    return RoutePersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        origin_location_id=row.origin_location_id,
        destination_location_id=row.destination_location_id,
        is_bidirectional=bool(row.is_bidirectional),
        distance_units=row.distance_units,
        base_duration_phases=int(row.base_duration_phases),
        allowed_travel_modes=tuple(row.allowed_travel_modes or ()),
        terrain_tags=tuple(row.terrain_tags or ()),
        danger_level=row.danger_level,
        seasonal_modifiers=_json_obj(row.seasonal_modifiers),
        status=row.status,
        created_event_id=row.created_event_id,
        version=int(row.version),
    )


def goal_to_record(row: GoalRow) -> GoalPersistenceRecord:
    return GoalPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        description=row.description,
        category=row.category,
        priority=row.priority,
        status=row.status,
        horizon=row.horizon,
        success_conditions=_json_obj(row.success_conditions),
        failure_conditions=_json_obj(row.failure_conditions),
        allows_alternative_plans=bool(row.allows_alternative_plans),
        source_event_id=row.source_event_id,
        version=int(row.version),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def plan_to_record(row: PlanRow) -> PlanPersistenceRecord:
    return PlanPersistenceRecord(
        id=row.id,
        goal_id=row.goal_id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        title=row.title,
        status=row.status,
        is_primary=bool(row.is_primary),
        expected_horizon=row.expected_horizon,
        commitment_level=row.commitment_level,
        revision_number=int(row.revision_number),
        source_event_id=row.source_event_id,
        version=int(row.version),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def plan_step_to_record(row: PlanStepRow) -> PlanStepPersistenceRecord:
    return PlanStepPersistenceRecord(
        id=row.id,
        plan_id=row.plan_id,
        step_index=int(row.step_index),
        description=row.description,
        status=row.status,
        target_entity_id=row.target_entity_id,
        target_location_id=row.target_location_id,
        activity_id=row.activity_id,
        prerequisites=_json_obj(row.prerequisites),
        expected_duration_phases=(
            None if row.expected_duration_phases is None else int(row.expected_duration_phases)
        ),
        version=int(row.version),
    )


def commitment_to_record(row: CommitmentRow) -> CommitmentPersistenceRecord:
    return CommitmentPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        debtor_character_id=row.debtor_character_id,
        beneficiary_character_id=row.beneficiary_character_id,
        description=row.description,
        due_condition=_json_obj(row.due_condition),
        status=row.status,
        created_event_id=row.created_event_id,
        fulfilled_event_id=row.fulfilled_event_id,
        version=int(row.version),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def relationship_edge_to_record(row: RelationshipEdgeRow) -> RelationshipEdgePersistenceRecord:
    return RelationshipEdgePersistenceRecord(
        source_character_id=row.source_character_id,
        target_character_id=row.target_character_id,
        world_id=row.world_id,
        familiarity=row.familiarity,
        trust=row.trust,
        affection=row.affection,
        attraction=row.attraction,
        respect=row.respect,
        fear=row.fear,
        resentment=row.resentment,
        dependency=row.dependency,
        loyalty=row.loyalty,
        perceived_reciprocity=row.perceived_reciprocity,
        last_meaningful_interaction_phase=(
            None
            if row.last_meaningful_interaction_phase is None
            else int(row.last_meaningful_interaction_phase)
        ),
        last_source_event_id=row.last_source_event_id,
        version=int(row.version),
        updated_at=row.updated_at,
    )


def activity_to_record(row: ActivityRow) -> ActivityPersistenceRecord:
    return ActivityPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        owner_entity_id=row.owner_entity_id,
        activity_type=row.activity_type,
        status=row.status,
        origin_location_id=row.origin_location_id,
        destination_location_id=row.destination_location_id,
        route_id=row.route_id,
        started_phase_index=int(row.started_phase_index),
        expected_end_phase_index=(
            None if row.expected_end_phase_index is None else int(row.expected_end_phase_index)
        ),
        progress=row.progress,
        interruption_conditions=_json_obj(row.interruption_conditions),
        activity_payload=_json_obj(row.activity_payload),
        last_source_event_id=row.last_source_event_id,
        version=int(row.version),
    )


def hook_to_record(row: HookRow) -> HookPersistenceRecord:
    return HookPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        hook_key=row.hook_key,
        title=row.title,
        status=row.status,
        premise=row.premise,
        prerequisites=_json_obj(row.prerequisites),
        scheduled_window=(
            None if row.scheduled_window is None else _json_obj(row.scheduled_window)
        ),
        involved_entity_ids=_uuid_tuple(row.involved_entity_ids),
        disclosure_state=row.disclosure_state,
        cooldown_until_phase=(
            None if row.cooldown_until_phase is None else int(row.cooldown_until_phase)
        ),
        director_profile_key=row.director_profile_key,
        source_event_id=row.source_event_id,
        version=int(row.version),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def npc_profile_to_record(row: NpcProfileRow) -> NpcProfilePersistenceRecord:
    return NpcProfilePersistenceRecord(
        character_id=row.character_id,
        world_id=row.world_id,
        display_name=row.display_name,
        role_tags=tuple(row.role_tags or ()),
        compact_card=_json_obj(row.compact_card),
        source_hook_id=row.source_hook_id,
        similarity_fingerprint=row.similarity_fingerprint,
        version=int(row.version),
        created_at=row.created_at,
    )


def npc_lifecycle_to_record(row: NpcLifecycleRow) -> NpcLifecyclePersistenceRecord:
    return NpcLifecyclePersistenceRecord(
        character_id=row.character_id,
        world_id=row.world_id,
        lifecycle_status=row.lifecycle_status,
        activated_phase_index=(
            None if row.activated_phase_index is None else int(row.activated_phase_index)
        ),
        archive_phase_index=(
            None if row.archive_phase_index is None else int(row.archive_phase_index)
        ),
        ttl_until_phase=None if row.ttl_until_phase is None else int(row.ttl_until_phase),
        relevance_score=row.relevance_score,
        archive_summary=row.archive_summary,
        last_scene_phase_index=(
            None if row.last_scene_phase_index is None else int(row.last_scene_phase_index)
        ),
        version=int(row.version),
        updated_at=row.updated_at,
    )


def summary_to_record(row: SummaryRow) -> SummaryPersistenceRecord:
    return SummaryPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        summary_type=row.summary_type,
        start_phase_index=int(row.start_phase_index),
        end_phase_index=int(row.end_phase_index),
        content=row.content,
        structured_extract=_json_obj(row.structured_extract),
        perspective=row.perspective,
        version_number=int(row.version_number),
        content_hash=row.content_hash,
        model_call_id=row.model_call_id,
        created_at=row.created_at,
    )


def diary_entry_to_record(row: DiaryEntryRow) -> DiaryEntryPersistenceRecord:
    return DiaryEntryPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        owner_character_id=row.owner_character_id,
        day_index=int(row.day_index),
        content=row.content,
        summary_id=row.summary_id,
        content_hash=row.content_hash,
        created_at=row.created_at,
        version=int(row.version),
    )


def day_run_to_record(row: DayRunRow) -> DayRunPersistenceRecord:
    return DayRunPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        day_index=int(row.day_index),
        status=row.status,
        started_at=row.started_at,
        completed_at=row.completed_at,
        recovery_snapshot_id=row.recovery_snapshot_id,
        idempotency_key=row.idempotency_key,
        version=int(row.version),
    )


def claim_to_record(
    row: ClaimRow, listener_ids: list[UUID] | None = None
) -> ClaimPersistenceRecord:
    return ClaimPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        source_event_id=row.source_event_id,
        speaker_id=row.speaker_id,
        proposition_key=row.proposition_key,
        proposition_text=row.proposition_text,
        truth_status=row.truth_status,
        intent_class=row.intent_class,
        confidence_expressed=row.confidence_expressed,
        created_at=row.created_at,
        listener_ids=tuple(listener_ids or ()),
    )


def belief_to_record(row: BeliefRow) -> BeliefPersistenceRecord:
    return BeliefPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        character_id=row.character_id,
        proposition_key=row.proposition_key,
        belief_text=row.belief_text,
        confidence=row.confidence,
        status=row.status,
        first_source_observation_id=row.first_source_observation_id,
        last_source_event_id=row.last_source_event_id,
        evidence_summary=_json_obj(row.evidence_summary),
        version=int(row.version),
        updated_at=row.updated_at,
        created_at=row.created_at,
    )


def secret_access_to_record(row: SecretAccessRow) -> SecretAccessPersistenceRecord:
    return SecretAccessPersistenceRecord(
        id=row.id,
        world_id=row.world_id,
        secret_key=row.secret_key,
        owner_character_id=row.owner_character_id,
        holder_character_id=row.holder_character_id,
        access_level=row.access_level,
        granted_event_id=row.granted_event_id,
        revoked_event_id=row.revoked_event_id,
        created_at=row.created_at,
    )
