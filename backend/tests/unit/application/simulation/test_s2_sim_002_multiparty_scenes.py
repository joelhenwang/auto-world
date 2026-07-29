"""Unit tests for Stage 2 multi-party scene assembly (S2-SIM-002)."""

from __future__ import annotations

from uuid import UUID

import pytest

from fictional_world.application.simulation.beat_budget import (
    SceneType,
    beat_budget_for,
    exchange_rounds_for,
)
from fictional_world.application.simulation.priority import score_initiative
from fictional_world.application.simulation.scene_assembly import (
    MAX_DETAILED_NPCS_PER_SCENE,
    MAX_FOCUS_CHARACTERS,
    ParticipantKind,
    assemble_multiparty_scenes,
    assemble_scenes,
    concurrent_scene_batches,
    evaluate_beat_continuation,
    mark_continuation,
    scenes_are_independent,
)
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
    continuation_activity_id: UUID | None = None,
) -> ActionProposal:
    return ActionProposal(
        decision_request_id=UUID(int=request_id),
        actor_id=UUID(int=actor_id),
        action_family=action_family,
        description=f"{action_family.value} action",
        target_entity_ids=target_entity_ids,
        target_location_id=target_location_id,
        relevant_goal_ids=relevant_goal_ids,
        continuation_activity_id=continuation_activity_id,
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait safely.",
        ),
    )


def test_four_character_social_scene_uses_group_beat_budget() -> None:
    phase_id = UUID(int=100)
    snapshot_id = UUID(int=101)
    hall = UUID(int=200)
    focus = (UUID(int=1), UUID(int=2), UUID(int=3), UUID(int=4))
    proposals = tuple(
        _proposal(
            request_id=10 + index,
            actor_id=index + 1,
            action_family=ActionFamily.SOCIALIZE,
            target_location_id=hall,
        )
        for index in range(4)
    )
    locations = dict.fromkeys(focus, hall)

    scenes = assemble_multiparty_scenes(
        phase_id,
        snapshot_id,
        proposals,
        locations,
        focus_character_ids=focus,
    )

    assert len(scenes) == 1
    scene = scenes[0]
    assert scene.focus_participant_ids == focus
    assert scene.npc_participant_ids == ()
    assert scene.scene_type is SceneType.SOCIAL_INTERACTION
    assert scene.draft.beat_budget == 6
    assert scene.allows_hidden_reaction is False
    assert beat_budget_for(SceneType.SOCIAL_INTERACTION, 4) == 6


def test_two_independent_scenes_run_concurrently() -> None:
    library = UUID(int=201)
    barracks = UUID(int=202)
    proposals = (
        _proposal(
            request_id=10,
            actor_id=1,
            action_family=ActionFamily.INVESTIGATE,
            target_location_id=library,
        ),
        _proposal(
            request_id=11,
            actor_id=2,
            action_family=ActionFamily.TRAIN,
            target_location_id=barracks,
        ),
    )
    locations = {UUID(int=1): library, UUID(int=2): barracks}

    scenes = assemble_multiparty_scenes(
        UUID(int=100),
        UUID(int=101),
        proposals,
        locations,
        focus_character_ids=(UUID(int=1), UUID(int=2)),
    )

    assert len(scenes) == 2
    assert scenes_are_independent(scenes[0], scenes[1])
    batches = concurrent_scene_batches(scenes)
    assert len(batches) == 1
    assert len(batches[0]) == 2


def test_same_item_conflict_is_merged() -> None:
    sword = UUID(int=300)
    first = _proposal(
        request_id=10,
        actor_id=1,
        action_family=ActionFamily.USE_ITEM,
        target_entity_ids=(sword,),
    )
    second = _proposal(
        request_id=11,
        actor_id=2,
        action_family=ActionFamily.TRANSFER,
        target_entity_ids=(sword,),
    )

    scenes = assemble_multiparty_scenes(
        UUID(int=100),
        UUID(int=101),
        (first, second),
        {UUID(int=1): UUID(int=201), UUID(int=2): UUID(int=202)},
        focus_character_ids=(UUID(int=1), UUID(int=2)),
    )

    assert len(scenes) == 1
    assert scenes[0].draft.shared_entity_ids == (sword,)
    assert sword in scenes[0].mutable_write_set
    # Stage 1 path must also merge.
    drafts = assemble_scenes(
        UUID(int=100),
        UUID(int=101),
        (first, second),
        {UUID(int=1): UUID(int=201), UUID(int=2): UUID(int=202)},
    )
    assert len(drafts) == 1


def test_conversation_continues_next_phase_rather_than_looping() -> None:
    hall = UUID(int=200)
    proposals = (
        _proposal(
            request_id=10,
            actor_id=1,
            action_family=ActionFamily.COMMUNICATE,
            target_entity_ids=(UUID(int=2),),
            target_location_id=hall,
        ),
        _proposal(
            request_id=11,
            actor_id=2,
            action_family=ActionFamily.COMMUNICATE,
            target_entity_ids=(UUID(int=1),),
            target_location_id=hall,
        ),
    )
    scenes = assemble_multiparty_scenes(
        UUID(int=100),
        UUID(int=101),
        proposals,
        {UUID(int=1): hall, UUID(int=2): hall},
        focus_character_ids=(UUID(int=1), UUID(int=2)),
    )
    assert len(scenes) == 1
    assert scenes[0].scene_type is SceneType.DIALOGUE
    assert scenes[0].draft.beat_budget == 4
    assert exchange_rounds_for(SceneType.DIALOGUE, 2) == 2

    decision = evaluate_beat_continuation(
        beats_used=scenes[0].draft.beat_budget,
        beat_budget=scenes[0].draft.beat_budget,
        unresolved=True,
    )
    assert decision.continue_next_phase is True
    assert decision.scene_concluded is False
    assert decision.recursive_loop_allowed is False

    continued = mark_continuation(scenes[0], unresolved=True)
    assert continued.continue_next_phase is True
    assert continued.allows_hidden_reaction is False

    concluded = evaluate_beat_continuation(
        beats_used=4,
        beat_budget=4,
        unresolved=False,
    )
    assert concluded.continue_next_phase is False
    assert concluded.scene_concluded is True
    assert concluded.recursive_loop_allowed is False


def test_npc_batch_respects_per_npc_knowledge_isolation() -> None:
    inn = UUID(int=200)
    focus_a = UUID(int=1)
    focus_b = UUID(int=2)
    npc_ids = tuple(UUID(int=50 + index) for index in range(3))
    proposals = (
        _proposal(
            request_id=10,
            actor_id=1,
            action_family=ActionFamily.SOCIALIZE,
            target_entity_ids=(npc_ids[0],),
            target_location_id=inn,
        ),
        _proposal(
            request_id=11,
            actor_id=2,
            action_family=ActionFamily.WAIT,
            target_location_id=inn,
        ),
    )
    locations = {focus_a: inn, focus_b: inn, **dict.fromkeys(npc_ids, inn)}
    npc_hashes = {
        npc_ids[0]: "npc-scope-0",
        npc_ids[1]: "npc-scope-1",
        npc_ids[2]: "npc-scope-2",
    }

    scenes = assemble_multiparty_scenes(
        UUID(int=100),
        UUID(int=101),
        proposals,
        locations,
        focus_character_ids=(focus_a, focus_b),
        npc_character_ids=npc_ids,
        knowledge_scope_hashes={focus_a: "focus-a", focus_b: "focus-b"},
        npc_knowledge_scope_hashes=npc_hashes,
    )

    assert len(scenes) == 1
    scene = scenes[0]
    assert set(scene.npc_participant_ids) == set(npc_ids)
    assert len(scene.npc_participant_ids) <= MAX_DETAILED_NPCS_PER_SCENE
    npc_metas = [meta for meta in scene.participants if meta.kind is ParticipantKind.NPC]
    assert len(npc_metas) == 3
    assert {meta.knowledge_scope_hash for meta in npc_metas} == set(npc_hashes.values())
    # Isolation: no NPC reuses a focus hash, and NPC hashes are unique.
    focus_hashes = {
        meta.knowledge_scope_hash
        for meta in scene.participants
        if meta.kind is ParticipantKind.FOCUS
    }
    assert focus_hashes.isdisjoint({meta.knowledge_scope_hash for meta in npc_metas})


def test_shared_npc_knowledge_hash_rejected() -> None:
    inn = UUID(int=200)
    npc_a = UUID(int=50)
    npc_b = UUID(int=51)
    proposals = (
        _proposal(
            request_id=10,
            actor_id=1,
            action_family=ActionFamily.SOCIALIZE,
            target_entity_ids=(npc_a, npc_b),
            target_location_id=inn,
        ),
    )
    with pytest.raises(ValueError, match="knowledge_scope_hash"):
        assemble_multiparty_scenes(
            UUID(int=100),
            UUID(int=101),
            proposals,
            {UUID(int=1): inn, npc_a: inn, npc_b: inn},
            focus_character_ids=(UUID(int=1),),
            npc_character_ids=(npc_a, npc_b),
            npc_knowledge_scope_hashes={npc_a: "shared-omniscient", npc_b: "shared-omniscient"},
        )


def test_focus_and_npc_budgets_enforced() -> None:
    with pytest.raises(ValueError, match="focus characters"):
        assemble_multiparty_scenes(
            UUID(int=100),
            UUID(int=101),
            (),
            {},
            focus_character_ids=tuple(UUID(int=i) for i in range(1, MAX_FOCUS_CHARACTERS + 2)),
        )

    hall = UUID(int=200)
    npc_ids = tuple(UUID(int=100 + i) for i in range(MAX_DETAILED_NPCS_PER_SCENE + 1))
    proposal = _proposal(
        request_id=10,
        actor_id=1,
        action_family=ActionFamily.SOCIALIZE,
        target_location_id=hall,
    )
    with pytest.raises(ValueError, match="detailed NPC budget"):
        assemble_multiparty_scenes(
            UUID(int=100),
            UUID(int=101),
            (proposal,),
            {UUID(int=1): hall, **dict.fromkeys(npc_ids, hall)},
            focus_character_ids=(UUID(int=1),),
            npc_character_ids=npc_ids,
        )


def test_stage2_beat_budget_table() -> None:
    assert beat_budget_for(SceneType.DIALOGUE, 2) == 4
    assert exchange_rounds_for(SceneType.DIALOGUE, 2) == 2
    assert beat_budget_for(SceneType.SOCIAL_INTERACTION, 4) == 6
    assert beat_budget_for(SceneType.NEGOTIATION, 3) == 7
    assert beat_budget_for(SceneType.NONLETHAL_CONFLICT, 2) == 6
    assert exchange_rounds_for(SceneType.NONLETHAL_CONFLICT, 2) == 3
    assert beat_budget_for(SceneType.NPC_BATCH, 6) == 1
    assert beat_budget_for(SceneType.BACKGROUND, 4) == 1


def test_initiative_distinct_from_global_priority() -> None:
    score = score_initiative(preparation=1.0, dexterity=0.5)
    assert score == pytest.approx(0.20 + 0.075)
    hall = UUID(int=200)
    proposals = (
        _proposal(
            request_id=10,
            actor_id=2,
            action_family=ActionFamily.SOCIALIZE,
            target_entity_ids=(UUID(int=1),),
            target_location_id=hall,
        ),
        _proposal(
            request_id=11,
            actor_id=1,
            action_family=ActionFamily.WAIT,
            target_location_id=hall,
        ),
    )
    scenes = assemble_multiparty_scenes(
        UUID(int=100),
        UUID(int=101),
        proposals,
        {UUID(int=1): hall, UUID(int=2): hall},
        focus_character_ids=(UUID(int=1), UUID(int=2)),
        initiative_factors={
            UUID(int=1): {"dexterity": 1.0},
            UUID(int=2): {"dexterity": 0.0},
        },
    )
    # Social initiator (actor 2) opens despite lower dexterity.
    assert scenes[0].initiative_order[0] == UUID(int=2)
