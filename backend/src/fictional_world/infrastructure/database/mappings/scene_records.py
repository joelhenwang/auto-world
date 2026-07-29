"""ORM <-> domain mappers for Stage 1 scene/action tables."""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from fictional_world.domain.scenes.persistence import (
    ActionProposalRecord,
    ActionTargetRecord,
    NarrationRecord,
    PlayerControlSessionRecord,
    ReactionProposalRecord,
    SceneActionRecord,
    SceneParticipantRecord,
    SceneRecord,
    SceneResolutionRecord,
    SceneRunRecord,
    StreamEventRecord,
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


def _json_obj(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    return {}


def _uuid_tuple(value: list[UUID] | None) -> tuple[UUID, ...]:
    if not value:
        return ()
    return tuple(value)


def action_proposal_to_record(
    row: ActionProposalRow,
    targets: list[ActionTargetRow],
) -> ActionProposalRecord:
    return ActionProposalRecord(
        id=row.id,
        phase_run_id=row.phase_run_id,
        snapshot_id=row.snapshot_id,
        actor_id=row.actor_id,
        proposal_kind=row.proposal_kind,
        action_family=row.action_family,
        intent=row.intent,
        utterance=row.utterance,
        target_location_id=row.target_location_id,
        visibility=row.visibility,
        risk_tolerance=row.risk_tolerance,
        estimated_duration_phases=int(row.estimated_duration_phases),
        continuation_activity_id=row.continuation_activity_id,
        desired_effects=_json_obj(row.desired_effects),
        fallback_action=_json_obj(row.fallback_action),
        validation_status=row.validation_status,
        validation_errors=_json_obj(row.validation_errors) if row.validation_errors else None,
        model_call_id=row.model_call_id,
        generation=int(row.generation),
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
        targets=tuple(
            ActionTargetRecord(
                action_proposal_id=t.action_proposal_id,
                target_entity_id=t.target_entity_id,
                target_role=t.target_role,
                ordinal=int(t.ordinal),
            )
            for t in targets
        ),
    )


def scene_to_record(
    row: SceneRow,
    actions: list[SceneActionRow],
    participants: list[SceneParticipantRow],
) -> SceneRecord:
    return SceneRecord(
        id=row.id,
        phase_run_id=row.phase_run_id,
        snapshot_id=row.snapshot_id,
        location_id=row.location_id,
        scene_type=row.scene_type,
        state=row.state,
        priority_score=row.priority_score,
        priority_breakdown=_json_obj(row.priority_breakdown),
        beat_budget=int(row.beat_budget),
        high_impact=bool(row.high_impact),
        mutable_aggregate_ids=_uuid_tuple(row.mutable_aggregate_ids),
        idempotency_key=row.idempotency_key,
        started_at=row.started_at,
        completed_at=row.completed_at,
        version=int(row.version),
        actions=tuple(
            SceneActionRecord(
                scene_id=a.scene_id,
                proposal_id=a.proposal_id,
                role=a.role,
                ordinal=int(a.ordinal),
            )
            for a in actions
        ),
        participants=tuple(
            SceneParticipantRecord(
                scene_id=p.scene_id,
                entity_id=p.entity_id,
                participant_role=p.participant_role,
                reaction_eligible=bool(p.reaction_eligible),
                knowledge_scope_hash=p.knowledge_scope_hash,
                joined_at_beat=int(p.joined_at_beat),
                left_at_beat=None if p.left_at_beat is None else int(p.left_at_beat),
            )
            for p in participants
        ),
    )


def reaction_to_record(row: ReactionProposalRow) -> ReactionProposalRecord:
    return ReactionProposalRecord(
        id=row.id,
        scene_id=row.scene_id,
        phase_run_id=row.phase_run_id,
        snapshot_id=row.snapshot_id,
        triggering_attempt_id=row.triggering_attempt_id,
        reactor_id=row.reactor_id,
        beat_index=int(row.beat_index),
        action_family=row.action_family,
        description=row.description,
        utterance=row.utterance,
        target_entity_ids=_uuid_tuple(row.target_entity_ids),
        resource_intentions=_json_obj(row.resource_intentions),
        desired_outcomes=_json_obj(row.desired_outcomes),
        validation_status=row.validation_status,
        validation_errors=_json_obj(row.validation_errors) if row.validation_errors else None,
        model_call_id=row.model_call_id,
        source_kind=row.source_kind,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
    )


def scene_resolution_to_record(row: SceneResolutionRow) -> SceneResolutionRecord:
    return SceneResolutionRecord(
        id=row.id,
        scene_id=row.scene_id,
        resolution_level=row.resolution_level,
        accepted_attempt_ids=_uuid_tuple(row.accepted_attempt_ids),
        rejected_assumptions=_json_obj(row.rejected_assumptions),
        proposed_effects=_json_obj(row.proposed_effects),
        delayed_effects=_json_obj(row.delayed_effects),
        observation_seeds=_json_obj(row.observation_seeds),
        narration_constraints=_json_obj(row.narration_constraints),
        visual_significance=row.visual_significance,
        confidence=row.confidence,
        resolver_profile_id=row.resolver_profile_id,
        model_call_id=row.model_call_id,
        expected_aggregate_versions=_json_obj(row.expected_aggregate_versions),
        validation_status=row.validation_status,
        commit_event_id=row.commit_event_id,
        canonical_summary=row.canonical_summary,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
    )


def scene_run_to_record(row: SceneRunRow) -> SceneRunRecord:
    return SceneRunRecord(
        id=row.id,
        scene_id=row.scene_id,
        phase_run_id=row.phase_run_id,
        status=row.status,
        stage=row.stage,
        beat_count=int(row.beat_count),
        beat_budget=int(row.beat_budget),
        high_impact=bool(row.high_impact),
        resolution_id=row.resolution_id,
        committed_event_id=row.committed_event_id,
        attempt_count=int(row.attempt_count),
        error_code=row.error_code,
        error_detail=_json_obj(row.error_detail) if row.error_detail else None,
        idempotency_key=row.idempotency_key,
        started_at=row.started_at,
        completed_at=row.completed_at,
        version=int(row.version),
    )


def narration_to_record(row: NarrationRow) -> NarrationRecord:
    return NarrationRecord(
        id=row.id,
        world_id=row.world_id,
        scene_id=row.scene_id,
        world_event_id=row.world_event_id,
        perspective=row.perspective,
        body=row.body,
        source_kind=row.source_kind,
        model_call_id=row.model_call_id,
        is_fallback=bool(row.is_fallback),
        content_hash=row.content_hash,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
    )


def stream_event_to_record(row: StreamEventRow) -> StreamEventRecord:
    return StreamEventRecord(
        id=row.id,
        world_id=row.world_id,
        sequence=int(row.sequence),
        event_type=row.event_type,
        occurred_at=row.occurred_at,
        fictional_time=_json_obj(row.fictional_time),
        payload=_json_obj(row.payload),
        schema_version=row.schema_version,
        phase_run_id=row.phase_run_id,
        scene_id=row.scene_id,
        world_event_id=row.world_event_id,
        perspective_scope=row.perspective_scope,
        idempotency_key=row.idempotency_key,
        created_at=row.created_at,
    )


def player_control_to_record(row: PlayerControlSessionRow) -> PlayerControlSessionRecord:
    return PlayerControlSessionRecord(
        id=row.id,
        world_id=row.world_id,
        character_id=row.character_id,
        controller_id=row.controller_id,
        status=row.status,
        acquired_at=row.acquired_at,
        released_at=row.released_at,
        waiting_input=bool(row.waiting_input),
        phase_run_id=row.phase_run_id,
        last_command_id=row.last_command_id,
        idempotency_key=row.idempotency_key,
        version=int(row.version),
    )
