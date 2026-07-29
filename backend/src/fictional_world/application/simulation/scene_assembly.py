"""Deterministic Stage 1 assembly of simultaneous action proposals."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from uuid import UUID, uuid5

from fictional_world.application.simulation.beat_budget import SceneType, beat_budget_for
from fictional_world.application.simulation.priority import score_priority
from fictional_world.domain.common.enums import ActionFamily
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    PriorityBreakdown,
    SceneDraft,
)

SCENE_ID_NAMESPACE = UUID("dbf26eb0-83d4-5d87-844c-23c47c83d64a")
_SOCIAL_FAMILIES = frozenset({ActionFamily.COMMUNICATE, ActionFamily.SOCIALIZE})
_DANGER_FAMILIES = frozenset({ActionFamily.ATTACK, ActionFamily.DEFEND})


def assemble_scenes(
    phase_id: UUID,
    snapshot_id: UUID,
    proposals: Sequence[ActionProposal],
    actor_locations: Mapping[UUID, UUID | None],
) -> tuple[SceneDraft, ...]:
    """Group proposals and return stable priority-ordered scene drafts."""

    ordered = tuple(
        sorted(
            proposals,
            key=lambda proposal: (proposal.actor_id.int, proposal.decision_request_id.int),
        )
    )
    _validate_unique_proposals(ordered)
    components = _proposal_components(ordered, actor_locations)
    scenes = tuple(
        _build_scene(
            phase_id=phase_id,
            snapshot_id=snapshot_id,
            proposals=component,
            actor_locations=actor_locations,
        )
        for component in components
    )
    return tuple(
        sorted(
            scenes,
            key=lambda scene: (-scene.priority.final_score, scene.participant_ids[0].int),
        )
    )


def _validate_unique_proposals(proposals: tuple[ActionProposal, ...]) -> None:
    actor_ids = [proposal.actor_id for proposal in proposals]
    if len(actor_ids) != len(set(actor_ids)):
        raise ValueError("each actor must have exactly one primary proposal")
    request_ids = [proposal.decision_request_id for proposal in proposals]
    if len(request_ids) != len(set(request_ids)):
        raise ValueError("decision_request_id values must be unique")


def _proposal_components(
    proposals: tuple[ActionProposal, ...],
    actor_locations: Mapping[UUID, UUID | None],
) -> tuple[tuple[ActionProposal, ...], ...]:
    parents = list(range(len(proposals)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = root(left)
        right_root = root(right)
        if left_root != right_root:
            parents[right_root] = left_root

    for left_index, left in enumerate(proposals):
        for right_index in range(left_index + 1, len(proposals)):
            right = proposals[right_index]
            if _should_group(left, right, actor_locations):
                union(left_index, right_index)

    grouped: dict[int, list[ActionProposal]] = {}
    for index, proposal in enumerate(proposals):
        grouped.setdefault(root(index), []).append(proposal)
    return tuple(
        tuple(component)
        for component in sorted(
            grouped.values(),
            key=lambda component: component[0].actor_id.int,
        )
    )


def _should_group(
    left: ActionProposal,
    right: ActionProposal,
    actor_locations: Mapping[UUID, UUID | None],
) -> bool:
    shared_targets = set(left.target_entity_ids).intersection(right.target_entity_ids)
    targets_other_actor = (
        right.actor_id in left.target_entity_ids or left.actor_id in right.target_entity_ids
    )
    if shared_targets or targets_other_actor:
        return True

    if left.target_location_id is not None and left.target_location_id == right.target_location_id:
        return True

    left_location = actor_locations.get(left.actor_id)
    right_location = actor_locations.get(right.actor_id)
    return (
        left_location is not None
        and left_location == right_location
        and (left.action_family in _SOCIAL_FAMILIES or right.action_family in _SOCIAL_FAMILIES)
    )


def _build_scene(
    *,
    phase_id: UUID,
    snapshot_id: UUID,
    proposals: tuple[ActionProposal, ...],
    actor_locations: Mapping[UUID, UUID | None],
) -> SceneDraft:
    participant_ids = tuple(
        sorted((proposal.actor_id for proposal in proposals), key=lambda x: x.int)
    )
    proposal_ids = tuple(
        sorted((proposal.decision_request_id for proposal in proposals), key=lambda x: x.int)
    )
    shared_entity_ids = _shared_entity_ids(proposals)
    scene_type = _scene_type(proposals, shared_entity_ids)
    priority = _scene_priority(proposals)
    scene_id = uuid5(
        SCENE_ID_NAMESPACE,
        f"{phase_id}:{snapshot_id}:{','.join(str(proposal_id) for proposal_id in proposal_ids)}",
    )
    return SceneDraft(
        scene_id=scene_id,
        phase_id=phase_id,
        snapshot_id=snapshot_id,
        location_id=_scene_location(proposals, actor_locations),
        participant_ids=participant_ids,
        action_proposal_ids=proposal_ids,
        shared_entity_ids=shared_entity_ids,
        priority=priority,
        beat_budget=beat_budget_for(scene_type, len(participant_ids)),
        high_impact=any(proposal.action_family in _DANGER_FAMILIES for proposal in proposals),
    )


def _shared_entity_ids(proposals: tuple[ActionProposal, ...]) -> tuple[UUID, ...]:
    references: Counter[UUID] = Counter()
    for proposal in proposals:
        references.update({proposal.actor_id, *proposal.target_entity_ids})
    return tuple(
        sorted(
            (entity_id for entity_id, count in references.items() if count > 1),
            key=lambda entity_id: entity_id.int,
        )
    )


def _scene_location(
    proposals: tuple[ActionProposal, ...],
    actor_locations: Mapping[UUID, UUID | None],
) -> UUID | None:
    target_locations = {
        proposal.target_location_id
        for proposal in proposals
        if proposal.target_location_id is not None
    }
    if len(target_locations) == 1:
        return next(iter(target_locations))
    if target_locations:
        return None

    current_locations = {
        location
        for proposal in proposals
        if (location := actor_locations.get(proposal.actor_id)) is not None
    }
    return next(iter(current_locations)) if len(current_locations) == 1 else None


def _scene_type(
    proposals: tuple[ActionProposal, ...],
    shared_entity_ids: tuple[UUID, ...],
) -> SceneType:
    if len(proposals) == 1:
        return SceneType.SOLO_ACTION
    if any(proposal.action_family in _SOCIAL_FAMILIES for proposal in proposals):
        return SceneType.SOCIAL_INTERACTION
    if shared_entity_ids:
        return SceneType.RESOURCE_CONFLICT
    if all(proposal.action_family is ActionFamily.MOVE for proposal in proposals):
        return SceneType.TRAVEL
    return SceneType.WORLD_EVENT_RESPONSE


def _scene_priority(proposals: tuple[ActionProposal, ...]) -> PriorityBreakdown:
    return score_priority(
        causal_urgency=float(any(not proposal.interruptible for proposal in proposals)),
        immediate_danger=float(
            any(proposal.action_family in _DANGER_FAMILIES for proposal in proposals)
        ),
        scheduled_commitment=float(
            any(proposal.continuation_activity_id is not None for proposal in proposals)
        ),
        unresolved_dependency=float(
            any(
                proposal.target_entity_ids or proposal.target_location_id is not None
                for proposal in proposals
            )
        ),
        goal_relevance=float(any(proposal.relevant_goal_ids for proposal in proposals)),
        starvation_fairness=0.0,
    )


__all__ = ["SCENE_ID_NAMESPACE", "assemble_scenes"]
