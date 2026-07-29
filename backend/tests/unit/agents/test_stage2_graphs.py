"""Stage 2 graph integrations (S2-GRAPH-001)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from fictional_world.agents import (
    GraphTaskRole,
    effect_kind_allowed,
    restricted_effect_kinds,
    restricted_effect_schema,
)
from fictional_world.agents.character_decision import (
    DecisionGraphInput,
    run_decision_graph,
)
from fictional_world.agents.character_reaction import (
    ReactionGraphInput,
    run_reaction_graph,
)
from fictional_world.agents.director_proposal import (
    DirectorProposalGraphInput,
    run_director_proposal_graph,
)
from fictional_world.agents.memory_consolidation import (
    MemoryConsolidationGraphInput,
    run_memory_consolidation_graph,
)
from fictional_world.agents.npc_scene import NpcSceneGraphInput, run_npc_scene_graph
from fictional_world.application.context import ContextTaskType, assemble_character_context
from fictional_world.application.director.types import (
    DirectorProposal,
    DirectorWorldSnapshot,
    SecretHandlingPlan,
)
from fictional_world.application.npc import (
    BudgetSnapshot,
    NpcProposalInput,
    build_npc_knowledge_package,
    propose_or_register_npc,
)
from fictional_world.application.simulation.commit import EventCommitService
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.enums import ActionFamily, Visibility
from fictional_world.domain.knowledge.persistence import ObservationPersistenceRecord
from fictional_world.domain.scenes.proposals import ActionProposal, FallbackAction, ReactionProposal
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.seed.records import CharacterCardVersionRecord
from fictional_world.infrastructure.model_gateway.fake import (
    FakeModelGatewayAdapter,
    FakeScriptKind,
)
from fictional_world.prompts import PromptAsset, PromptRenderer

MIRA = seed_uuid("character/mira-talren")
DAIN = seed_uuid("character/dain-arcen")
INN = seed_uuid("location/veycross/cinder-lantern-inn")
CORPUS = Path(__file__).resolve().parents[2] / "fixtures" / "model_corpus" / "stage1"
MIRA_REQUEST = UUID("11111111-1111-4111-8111-111111111111")
IRI = uuid4()


def _card(character_id: UUID, name: str) -> CharacterCardVersionRecord:
    return CharacterCardVersionRecord(
        id=uuid4(),
        character_id=character_id,
        version_number=1,
        identity={"canonical_name": name},
        backstory=f"{name} backstory",
        appearance={},
        personality_traits={},
        values={},
        fears={},
        desires={},
        boundaries={},
        voice_profile={},
        initial_capabilities={"ordinary_movement": True},
        secret_manifest={},
        change_summary="v1",
        content_hash="test",
    )


def _state(character_id: UUID) -> CharacterStateRecord:
    return CharacterStateRecord(
        character_id=character_id,
        location_id=INN,
        life_status="alive",
        stamina=Decimal("50"),
        mana=Decimal("10"),
        energy=Decimal("50"),
        hunger=Decimal("10"),
        pain=Decimal("0"),
        stress=Decimal("0"),
        social_need=Decimal("20"),
        valence=Decimal("0"),
        arousal=Decimal("0"),
        dominance=Decimal("0"),
        current_card_version_id=uuid4(),
        version=0,
    )


def _context(
    character_id: UUID,
    *,
    task_type: ContextTaskType,
    snapshot_id: UUID,
    scene_working: dict[str, object] | None = None,
):
    name = "Mira" if character_id == MIRA else "Dain"
    return assemble_character_context(
        observer_id=character_id,
        phase_snapshot_id=snapshot_id,
        task_type=task_type,
        card=_card(character_id, name),
        state=_state(character_id),
        co_located_character_ids=(DAIN if character_id == MIRA else MIRA,),
        scene_working=scene_working,
    )


def _decision_input(**overrides: Any) -> DecisionGraphInput:
    snapshot_id = uuid4()
    base: dict[str, Any] = {
        "context": _context(
            MIRA,
            task_type=ContextTaskType.CHARACTER_DECISION,
            snapshot_id=snapshot_id,
        ),
        "phase_label": "dawn",
        "decision_request_id": MIRA_REQUEST,
        "allowed_entity_ids": frozenset({MIRA, DAIN, IRI}),
        "allowed_location_ids": frozenset({INN}),
        "other_character_names": ("Dain", "Iri"),
    }
    base.update(overrides)
    return DecisionGraphInput(**base)


@pytest.mark.unit
@pytest.mark.model_fake
async def test_decision_graph_accepts_goals_plans_claims_additive_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}
    original = PromptRenderer.render

    def _capture(self: PromptRenderer, asset: PromptAsset, variables: dict[str, Any]):
        captured.update({key: str(value) for key, value in variables.items()})
        return original(self, asset, variables)

    monkeypatch.setattr(PromptRenderer, "render", _capture)
    payload = (CORPUS / "quiet_mira_wait.json").read_text(encoding="utf-8")
    gateway = FakeModelGatewayAdapter(valid_payload=payload)
    graph_input = _decision_input(
        goals=({"goal_id": str(uuid4()), "title": "Learn the bridge schedule"},),
        plans=({"plan_id": str(uuid4()), "step": "Ask Dain at dawn"},),
        claims=({"proposition": "The east bridge was open at dawn", "source": "rumour"},),
    )

    proposal = await run_decision_graph(graph_input, gateway)

    assert proposal.action_family is ActionFamily.WAIT
    assert "Learn the bridge schedule" in captured["goals_and_plans"]
    assert "Ask Dain at dawn" in captured["goals_and_plans"]
    assert "east bridge was open" in captured["known_lore"]


@pytest.mark.unit
@pytest.mark.model_fake
async def test_decision_graph_malformed_output_repairs_with_goals_context() -> None:
    payload = (CORPUS / "quiet_mira_wait.json").read_text(encoding="utf-8")
    gateway = FakeModelGatewayAdapter(valid_payload=payload)
    gateway.script(key=str(MIRA_REQUEST), kind=FakeScriptKind.MALFORMED_JSON)

    proposal = await run_decision_graph(
        _decision_input(goals=({"title": "Keep the morning quiet"},)),
        gateway,
    )

    assert proposal.action_family is ActionFamily.WAIT
    assert [call["request_id"] for call in gateway.calls] == [
        str(MIRA_REQUEST),
        f"{MIRA_REQUEST}:regen",
    ]


@pytest.mark.unit
@pytest.mark.model_fake
async def test_reaction_graph_multiparty_participant_list() -> None:
    snapshot_id = uuid4()
    scene_id = uuid4()
    reaction_request_id = uuid4()
    attempt = ActionProposal(
        decision_request_id=uuid4(),
        actor_id=MIRA,
        action_family=ActionFamily.COMMUNICATE,
        description="Mira asks the table about the bridge.",
        utterance="Is the east bridge open?",
        target_entity_ids=(DAIN, IRI),
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait.",
        ),
    )
    valid = ReactionProposal(
        reaction_request_id=reaction_request_id,
        scene_id=scene_id,
        triggering_attempt_id=attempt.decision_request_id,
        reactor_id=DAIN,
        action_family=ActionFamily.COMMUNICATE,
        description="Dain answers within the multi-party scene.",
        utterance="It was open at dawn.",
        target_entity_ids=(MIRA,),
    )
    gateway = FakeModelGatewayAdapter(valid_payload=valid.model_dump_json())
    participants = frozenset({MIRA, DAIN, IRI})

    reaction = await run_reaction_graph(
        ReactionGraphInput(
            context=_context(
                DAIN,
                task_type=ContextTaskType.CHARACTER_REACTION,
                snapshot_id=snapshot_id,
                scene_working={
                    "scene_id": str(scene_id),
                    "visible_participants": [str(MIRA), str(IRI)],
                },
            ),
            scene_id=scene_id,
            reaction_request_id=reaction_request_id,
            perceived_attempt=attempt,
            remaining_beat_budget=3,
            allowed_entity_ids=participants,
            participant_ids=participants,
        ),
        gateway,
    )

    assert reaction.reactor_id == DAIN
    assert reaction.triggering_attempt_id == attempt.decision_request_id


@pytest.mark.unit
@pytest.mark.model_fake
async def test_reaction_graph_rejects_non_participant_target_then_falls_back() -> None:
    snapshot_id = uuid4()
    scene_id = uuid4()
    reaction_request_id = uuid4()
    outsider = uuid4()
    attempt = ActionProposal(
        decision_request_id=uuid4(),
        actor_id=MIRA,
        action_family=ActionFamily.COMMUNICATE,
        description="Mira speaks.",
        utterance="Hello?",
        target_entity_ids=(DAIN,),
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait.",
        ),
    )
    invalid = ReactionProposal(
        reaction_request_id=reaction_request_id,
        scene_id=scene_id,
        triggering_attempt_id=attempt.decision_request_id,
        reactor_id=DAIN,
        action_family=ActionFamily.COMMUNICATE,
        description="Dain addresses someone outside the scene.",
        target_entity_ids=(outsider,),
    )
    gateway = FakeModelGatewayAdapter(valid_payload=invalid.model_dump_json())
    participants = frozenset({MIRA, DAIN, IRI})

    reaction = await run_reaction_graph(
        ReactionGraphInput(
            context=_context(
                DAIN,
                task_type=ContextTaskType.CHARACTER_REACTION,
                snapshot_id=snapshot_id,
                scene_working={"scene_id": str(scene_id)},
            ),
            scene_id=scene_id,
            reaction_request_id=reaction_request_id,
            perceived_attempt=attempt,
            remaining_beat_budget=2,
            allowed_entity_ids=participants | {outsider},
            participant_ids=participants,
        ),
        gateway,
    )

    assert reaction.action_family is ActionFamily.WAIT
    assert len(gateway.calls) == 2


@pytest.mark.unit
def test_restricted_effect_schema_excludes_unrelated_kinds() -> None:
    conversation = restricted_effect_kinds(GraphTaskRole.RESOLVER_CONVERSATION)
    assert "create_claim" in conversation
    assert "apply_injury" not in conversation
    assert "mark_death" not in conversation
    assert not effect_kind_allowed("apply_injury", GraphTaskRole.RESOLVER)
    assert not effect_kind_allowed("register_npc", GraphTaskRole.RESOLVER)

    schema = restricted_effect_schema(GraphTaskRole.NPC_SCENE)
    assert schema["allows_effects"] is True
    assert "mark_death" not in schema["enum"]
    assert "register_npc" not in schema["enum"]

    memory_schema = restricted_effect_schema(GraphTaskRole.MEMORY_CONSOLIDATION)
    assert memory_schema["enum"] == []
    assert memory_schema["allows_effects"] is False


@pytest.mark.unit
async def test_director_proposal_graph_trigger_validate_no_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world_id = uuid4()
    phase_id = uuid4()
    snapshot = DirectorWorldSnapshot(
        world_id=world_id,
        current_phase_index=40,
        phases_since_meaningful_choice=12,
        recent_location_keys=("inn", "inn", "inn", "inn", "inn"),
        recent_participant_keys=("a|b", "a|b", "a|b", "a|b", "a|b"),
        recent_action_families=("talk", "talk", "talk", "talk", "talk"),
        goal_progress_delta=0.0,
        unresolved_hook_count=3,
        emotional_intensity_history=(0.4, 0.41, 0.39, 0.4),
        protected_secret_keys=("mira.father.true_name",),
    )
    proposal = DirectorProposal(
        proposal_id=uuid4(),
        phase_id=phase_id,
        world_id=world_id,
        trigger_type="STAGNATION_RISK",
        proposal_kind="SOCIAL_OPPORTUNITY",
        title="Courier notice",
        intent="Offer a low-stakes information opportunity at the inn.",
        causal_basis_event_ids=(uuid4(),),
        proposed_event_facts=("A courier posts a notice at the inn.",),
        proposed_effect_types=("observe",),
        secret_handling=SecretHandlingPlan(),
    )

    commits: list[str] = []

    def _forbid_commit(self: EventCommitService, *args: object, **kwargs: object) -> None:
        commits.append("commit")
        raise AssertionError("DirectorProposalGraph must not commit domain state")

    monkeypatch.setattr(EventCommitService, "commit", _forbid_commit)

    result = await run_director_proposal_graph(
        DirectorProposalGraphInput(world_snapshot=snapshot, proposal=proposal)
    )

    assert result.trigger.should_call is True
    assert result.accepted_proposal is not None
    assert result.fallback is None
    assert commits == []

    healthy = DirectorWorldSnapshot(
        world_id=world_id,
        current_phase_index=20,
        phases_since_meaningful_choice=1,
        recent_location_keys=("inn", "market", "bridge", "archive", "orchard"),
        recent_participant_keys=("a|b", "a|c", "b|d", "a|b|c", "c|d"),
        recent_action_families=("talk", "travel", "work", "observe", "rest"),
        goal_progress_delta=0.85,
        unresolved_hook_count=0,
        emotional_intensity_history=(0.2, 0.45, 0.7, 0.55),
    )
    quiet = await run_director_proposal_graph(
        DirectorProposalGraphInput(world_snapshot=healthy, proposal=proposal)
    )
    assert quiet.trigger.should_call is False
    assert quiet.accepted_proposal is None
    assert quiet.fallback is not None
    assert commits == []


@pytest.mark.unit
async def test_director_invalid_proposal_uses_no_event_fallback() -> None:
    world_id = uuid4()
    snapshot = DirectorWorldSnapshot(
        world_id=world_id,
        current_phase_index=40,
        phases_since_meaningful_choice=12,
        recent_location_keys=("inn", "inn", "inn", "inn", "inn"),
        recent_participant_keys=("a|b", "a|b", "a|b", "a|b", "a|b"),
        recent_action_families=("talk", "talk", "talk", "talk", "talk"),
        goal_progress_delta=0.0,
        unresolved_hook_count=2,
        emotional_intensity_history=(0.4, 0.4, 0.4, 0.4),
        protected_secret_keys=("mira.father.true_name",),
    )
    bad = DirectorProposal(
        proposal_id=uuid4(),
        phase_id=uuid4(),
        world_id=world_id,
        trigger_type="STAGNATION_RISK",
        proposal_kind="SOCIAL_OPPORTUNITY",
        title="Secret leak",
        intent="Leak a sealed identity without a path.",
        causal_basis_event_ids=(uuid4(),),
        proposed_event_facts=("mira.father.true_name is revealed aloud.",),
        secret_handling=SecretHandlingPlan(reveals_secret=True, disclosure_path=None),
    )

    result = await run_director_proposal_graph(
        DirectorProposalGraphInput(world_snapshot=snapshot, proposal=bad)
    )

    assert result.accepted_proposal is None
    assert result.fallback is not None
    assert result.validation is not None
    assert not result.validation.ok


@pytest.mark.unit
async def test_memory_consolidation_graph_returns_records_without_commit() -> None:
    world_id = uuid4()
    owner = uuid4()
    obs = ObservationPersistenceRecord(
        id=uuid4(),
        world_event_id=uuid4(),
        observer_id=owner,
        observation_type="scene",
        perceived_summary="Mira noticed rain on the inn shutters.",
        perceived_facts={"weather": "rain"},
        omitted_fact_keys=(),
        confidence=Decimal("0.80"),
        visibility_reason="direct_witness",
        source_sense_tags=("sight",),
        content_hash=uuid4().hex,
    )

    result = await run_memory_consolidation_graph(
        MemoryConsolidationGraphInput(
            world_id=world_id,
            day_index=0,
            character_ids=(owner,),
            observations=(obs,),
        )
    )

    assert result.world_id == world_id
    assert len(result.characters) == 1
    assert result.characters[0].summary.content
    assert result.day_run.idempotency_key.startswith("day-consolidation:")


@pytest.mark.unit
@pytest.mark.model_fake
async def test_npc_scene_graph_uses_knowledge_packages_and_repairs_malformed() -> None:
    world_id = uuid4()
    registered = propose_or_register_npc(
        NpcProposalInput(
            proposed_name="Harn the Blacksmith",
            role_tags=("blacksmith",),
            traits=("sturdy",),
            location_key="embervale.forge",
            source_hook_key="forge_day",
            narrative_purpose="Repair tools.",
        ),
        world_id=world_id,
        current_phase_index=10,
        existing=(),
        budgets=BudgetSnapshot(
            detailed_npcs_in_scene=0,
            active_detailed_in_region=0,
            new_named_today=0,
        ),
    )
    assert registered.entry is not None
    entry = registered.entry
    package = build_npc_knowledge_package(entry, beliefs=(), secret_access=())
    request_id = uuid4()
    wait = ActionProposal(
        decision_request_id=request_id,
        actor_id=entry.character_id,
        action_family=ActionFamily.WAIT,
        description="Harn waits by the forge.",
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Continue waiting.",
        ),
    )
    gateway = FakeModelGatewayAdapter(valid_payload=wait.model_dump_json())
    gateway.script(key=str(request_id), kind=FakeScriptKind.MALFORMED_JSON)

    result = await run_npc_scene_graph(
        NpcSceneGraphInput(
            scene_id=uuid4(),
            knowledge_packages=(package,),
            decision_request_ids={entry.character_id: request_id},
            allowed_entity_ids=frozenset({entry.character_id, MIRA}),
        ),
        gateway,
    )

    assert len(result.proposals) == 1
    assert result.proposals[0].actor_id == entry.character_id
    assert result.proposals[0].action_family is ActionFamily.WAIT
    assert [call["request_id"] for call in gateway.calls] == [
        str(request_id),
        f"{request_id}:regen",
    ]


@pytest.mark.unit
async def test_npc_scene_graph_skips_ineligible_and_defaults_without_gateway() -> None:
    world_id = uuid4()
    registered = propose_or_register_npc(
        NpcProposalInput(
            proposed_name="Lira Porter",
            role_tags=("porter",),
            traits=("alert",),
            location_key="veycross.gate",
            narrative_purpose="Watch the gate.",
        ),
        world_id=world_id,
        current_phase_index=5,
        existing=(),
        budgets=BudgetSnapshot(
            detailed_npcs_in_scene=0,
            active_detailed_in_region=0,
            new_named_today=0,
        ),
    )
    assert registered.entry is not None
    entry = registered.entry
    package = build_npc_knowledge_package(entry, beliefs=(), secret_access=())
    request_id = uuid4()

    result = await run_npc_scene_graph(
        NpcSceneGraphInput(
            scene_id=uuid4(),
            knowledge_packages=(package,),
            decision_request_ids={entry.character_id: request_id},
            allowed_entity_ids=frozenset({entry.character_id}),
        ),
        gateway=None,
    )

    assert len(result.proposals) == 1
    assert result.proposals[0].action_family is ActionFamily.WAIT
    assert result.skipped_character_ids == ()
