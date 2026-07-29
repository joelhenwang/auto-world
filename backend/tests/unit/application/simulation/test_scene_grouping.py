"""Unit tests for deterministic Stage 1 scene grouping."""

from __future__ import annotations

from uuid import UUID

from fictional_world.application.simulation.conflict_sets import (
    mutable_write_set,
    read_set,
)
from fictional_world.application.simulation.scene_assembly import assemble_scenes
from fictional_world.domain.common.enums import ActionFamily, Visibility
from fictional_world.domain.scenes.proposals import ActionProposal, FallbackAction


def _proposal(
    *,
    request_id: int,
    actor_id: int,
    action_family: ActionFamily,
    target_entity_ids: tuple[UUID, ...] = (),
    target_location_id: UUID | None = None,
    relevant_goal_ids: tuple[UUID, ...] = (),
) -> ActionProposal:
    return ActionProposal(
        decision_request_id=UUID(int=request_id),
        actor_id=UUID(int=actor_id),
        action_family=action_family,
        description=f"{action_family.value} action",
        target_entity_ids=target_entity_ids,
        target_location_id=target_location_id,
        relevant_goal_ids=relevant_goal_ids,
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait safely.",
        ),
    )


def test_visit_and_wait_merge_into_one_social_scene() -> None:
    phase_id = UUID(int=100)
    snapshot_id = UUID(int=101)
    inn_id = UUID(int=200)
    visitor = _proposal(
        request_id=10,
        actor_id=1,
        action_family=ActionFamily.SOCIALIZE,
        target_entity_ids=(UUID(int=2),),
        target_location_id=inn_id,
    )
    waiting_character = _proposal(
        request_id=11,
        actor_id=2,
        action_family=ActionFamily.WAIT,
    )
    locations = {UUID(int=1): inn_id, UUID(int=2): inn_id}

    scenes = assemble_scenes(
        phase_id,
        snapshot_id,
        (waiting_character, visitor),
        locations,
    )
    repeated = assemble_scenes(
        phase_id,
        snapshot_id,
        (visitor, waiting_character),
        locations,
    )

    assert scenes == repeated
    assert len(scenes) == 1
    scene = scenes[0]
    assert scene.participant_ids == (UUID(int=1), UUID(int=2))
    assert scene.shared_entity_ids == (UUID(int=2),)
    assert scene.location_id == inn_id
    assert scene.beat_budget == 4


def test_independent_actions_at_different_locations_remain_solo() -> None:
    phase_id = UUID(int=100)
    snapshot_id = UUID(int=101)
    first = _proposal(
        request_id=10,
        actor_id=1,
        action_family=ActionFamily.WAIT,
    )
    second = _proposal(
        request_id=11,
        actor_id=2,
        action_family=ActionFamily.OBSERVE,
    )

    scenes = assemble_scenes(
        phase_id,
        snapshot_id,
        (second, first),
        {UUID(int=1): UUID(int=201), UUID(int=2): UUID(int=202)},
    )

    assert len(scenes) == 2
    assert tuple(scene.participant_ids for scene in scenes) == (
        (UUID(int=1),),
        (UUID(int=2),),
    )
    assert all(scene.beat_budget == 1 for scene in scenes)


def test_proposals_for_same_target_merge_and_sort_before_unrelated_solo() -> None:
    shared_target = UUID(int=300)
    first = _proposal(
        request_id=10,
        actor_id=1,
        action_family=ActionFamily.INTERACT_ENVIRONMENT,
        target_entity_ids=(shared_target,),
    )
    second = _proposal(
        request_id=11,
        actor_id=2,
        action_family=ActionFamily.INTERACT_ENVIRONMENT,
        target_entity_ids=(shared_target,),
    )
    unrelated = _proposal(
        request_id=12,
        actor_id=3,
        action_family=ActionFamily.WAIT,
    )

    scenes = assemble_scenes(
        UUID(int=100),
        UUID(int=101),
        (unrelated, second, first),
        {
            UUID(int=1): UUID(int=201),
            UUID(int=2): UUID(int=202),
            UUID(int=3): UUID(int=203),
        },
    )

    assert len(scenes) == 2
    assert scenes[0].participant_ids == (UUID(int=1), UUID(int=2))
    assert scenes[0].shared_entity_ids == (shared_target,)
    assert scenes[0].priority.final_score == 0.15
    assert scenes[1].participant_ids == (UUID(int=3),)


def test_proposal_conflict_sets_are_immutable_and_include_referenced_aggregates() -> None:
    target_id = UUID(int=300)
    location_id = UUID(int=301)
    goal_id = UUID(int=302)
    proposal = _proposal(
        request_id=10,
        actor_id=1,
        action_family=ActionFamily.INTERACT_ENVIRONMENT,
        target_entity_ids=(target_id,),
        target_location_id=location_id,
        relevant_goal_ids=(goal_id,),
    )

    assert mutable_write_set(proposal) == frozenset({UUID(int=1), target_id, location_id})
    assert read_set(proposal) == frozenset({UUID(int=1), target_id, location_id, goal_id})
