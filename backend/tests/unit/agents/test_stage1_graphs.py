"""Focused path coverage for Stage 1 plain-async agent graphs."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from fictional_world.agents.character_decision import (
    DecisionGraphInput,
    run_decision_graph,
)
from fictional_world.agents.character_reaction import (
    ReactionGraphInput,
    run_reaction_graph,
)
from fictional_world.agents.resolver import ResolutionGraphInput, run_resolution_graph
from fictional_world.application.context import ContextTaskType, assemble_character_context
from fictional_world.application.simulation.scene_assembly import assemble_scenes
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.enums import (
    ActionFamily,
    ResolutionLevel,
    Visibility,
)
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    FallbackAction,
    NarrationConstraints,
    ReactionProposal,
    SceneResolution,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.seed.records import CharacterCardVersionRecord
from fictional_world.infrastructure.model_gateway.fake import (
    FakeModelGatewayAdapter,
    FakeScriptKind,
)

MIRA = seed_uuid("character/mira-talren")
DAIN = seed_uuid("character/dain-arcen")
INN = seed_uuid("location/veycross/cinder-lantern-inn")
MARKET = seed_uuid("location/veycross/market-square")
CORPUS = Path(__file__).resolve().parents[2] / "fixtures" / "model_corpus" / "stage1"
MIRA_REQUEST = UUID("11111111-1111-4111-8111-111111111111")


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


def _decision_input(
    *,
    request_id: UUID = MIRA_REQUEST,
    continuation_activity_id: UUID | None = None,
) -> DecisionGraphInput:
    snapshot_id = uuid4()
    activities = (
        frozenset({continuation_activity_id})
        if continuation_activity_id is not None
        else frozenset()
    )
    return DecisionGraphInput(
        context=_context(
            MIRA,
            task_type=ContextTaskType.CHARACTER_DECISION,
            snapshot_id=snapshot_id,
        ),
        phase_label="dawn",
        decision_request_id=request_id,
        allowed_entity_ids=frozenset({MIRA, DAIN}),
        allowed_location_ids=frozenset({INN, MARKET}),
        allowed_activity_ids=activities,
        other_character_names=("Dain",),
        continuation_activity_id=continuation_activity_id,
    )


@pytest.mark.unit
@pytest.mark.model_fake
async def test_decision_graph_accepts_valid_corpus_and_seals_provenance() -> None:
    gateway = FakeModelGatewayAdapter(corpus_dir=CORPUS)
    gateway.script_corpus(key=str(MIRA_REQUEST), filename="quiet_mira_wait.json")

    proposal = await run_decision_graph(_decision_input(), gateway)

    assert proposal.action_family is ActionFamily.WAIT
    assert proposal.actor_id == MIRA
    assert gateway.calls == [
        {
            "type": "text",
            "role": "character_decision",
            "request_id": str(MIRA_REQUEST),
            "kind": FakeScriptKind.VALID,
            "corpus": "quiet_mira_wait.json",
        }
    ]


@pytest.mark.unit
@pytest.mark.model_fake
async def test_decision_graph_repairs_once_then_returns_valid_regeneration() -> None:
    payload = (CORPUS / "quiet_mira_wait.json").read_text(encoding="utf-8")
    gateway = FakeModelGatewayAdapter(valid_payload=payload)
    gateway.script(key=str(MIRA_REQUEST), kind=FakeScriptKind.MALFORMED_JSON)

    proposal = await run_decision_graph(_decision_input(), gateway)

    assert proposal.action_family is ActionFamily.WAIT
    assert [call["request_id"] for call in gateway.calls] == [
        str(MIRA_REQUEST),
        f"{MIRA_REQUEST}:regen",
    ]


@pytest.mark.unit
@pytest.mark.model_fake
@pytest.mark.parametrize(
    "kind",
    [FakeScriptKind.SCHEMA_INVALID, FakeScriptKind.TIMEOUT, FakeScriptKind.RATE_LIMITED],
)
async def test_decision_graph_outage_or_invalid_output_uses_safe_fallback(
    kind: FakeScriptKind,
) -> None:
    gateway = FakeModelGatewayAdapter(default_kind=kind)

    proposal = await run_decision_graph(_decision_input(), gateway)

    assert proposal.action_family is ActionFamily.REST
    assert len(gateway.calls) == 2


@pytest.mark.unit
@pytest.mark.model_fake
async def test_decision_graph_domain_invalid_output_regenerates_then_falls_back() -> None:
    payload = (CORPUS / "authored_other_reaction_invalid.json").read_text(encoding="utf-8")
    gateway = FakeModelGatewayAdapter(valid_payload=payload)

    proposal = await run_decision_graph(_decision_input(), gateway)

    assert proposal.action_family is ActionFamily.REST
    assert len(gateway.calls) == 2


@pytest.mark.unit
@pytest.mark.model_fake
async def test_decision_fallback_prefers_existing_activity() -> None:
    activity_id = uuid4()
    gateway = FakeModelGatewayAdapter(default_kind=FakeScriptKind.SCHEMA_INVALID)

    proposal = await run_decision_graph(
        _decision_input(continuation_activity_id=activity_id),
        gateway,
    )

    assert proposal.action_family is ActionFamily.CONTINUE_ACTIVITY
    assert proposal.continuation_activity_id == activity_id


def _attempt(request_id: UUID, family: ActionFamily = ActionFamily.COMMUNICATE) -> ActionProposal:
    return ActionProposal(
        decision_request_id=request_id,
        actor_id=MIRA,
        action_family=family,
        description="Mira asks Dain whether the east bridge is open.",
        utterance="Is the east bridge open?",
        target_entity_ids=(DAIN,),
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait for another opportunity.",
        ),
    )


@pytest.mark.unit
@pytest.mark.model_fake
async def test_reaction_graph_accepts_only_the_perceived_attempt() -> None:
    snapshot_id = uuid4()
    scene_id = uuid4()
    reaction_request_id = uuid4()
    attempt = _attempt(uuid4())
    valid = ReactionProposal(
        reaction_request_id=reaction_request_id,
        scene_id=scene_id,
        triggering_attempt_id=attempt.decision_request_id,
        reactor_id=DAIN,
        action_family=ActionFamily.COMMUNICATE,
        description="Dain answers only with what he observed.",
        utterance="It was open at dawn.",
        target_entity_ids=(MIRA,),
    )
    gateway = FakeModelGatewayAdapter(valid_payload=valid.model_dump_json())
    graph_input = ReactionGraphInput(
        context=_context(
            DAIN,
            task_type=ContextTaskType.CHARACTER_REACTION,
            snapshot_id=snapshot_id,
            scene_working={"scene_id": str(scene_id), "visible_participants": [str(MIRA)]},
        ),
        scene_id=scene_id,
        reaction_request_id=reaction_request_id,
        perceived_attempt=attempt,
        remaining_beat_budget=2,
        allowed_entity_ids=frozenset({MIRA, DAIN}),
    )

    reaction = await run_reaction_graph(graph_input, gateway)

    assert reaction.triggering_attempt_id == attempt.decision_request_id
    assert reaction.reactor_id == DAIN


@pytest.mark.unit
@pytest.mark.model_fake
async def test_reaction_graph_rejects_unperceived_attempt_and_falls_back() -> None:
    snapshot_id = uuid4()
    scene_id = uuid4()
    reaction_request_id = uuid4()
    attempt = _attempt(uuid4())
    invalid = ReactionProposal(
        reaction_request_id=reaction_request_id,
        scene_id=scene_id,
        triggering_attempt_id=uuid4(),
        reactor_id=DAIN,
        action_family=ActionFamily.COMMUNICATE,
        description="Dain responds to a different event.",
    )
    gateway = FakeModelGatewayAdapter(valid_payload=invalid.model_dump_json())

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
            remaining_beat_budget=1,
            allowed_entity_ids=frozenset({MIRA, DAIN}),
        ),
        gateway,
    )

    assert reaction.action_family is ActionFamily.WAIT
    assert reaction.triggering_attempt_id == attempt.decision_request_id
    assert len(gateway.calls) == 2


def _resolution_input(
    proposal: ActionProposal,
    *,
    resolution_request_id: UUID | None = None,
    other_proposals: tuple[ActionProposal, ...] = (),
) -> ResolutionGraphInput:
    phase_id = uuid4()
    snapshot_id = uuid4()
    proposals = (proposal, *other_proposals)
    actor_locations = {item.actor_id: INN for item in proposals}
    scene = assemble_scenes(
        phase_id,
        snapshot_id,
        proposals,
        actor_locations,
    )[0]
    return ResolutionGraphInput(
        scene=scene,
        proposals=proposals,
        reactions=(),
        resolution_request_id=resolution_request_id or uuid4(),
        actor_locations=actor_locations,
        allowed_entity_ids=frozenset({MIRA, DAIN}),
        allowed_location_ids=frozenset({INN, MARKET}),
    )


@pytest.mark.unit
async def test_resolver_uses_no_model_for_simple_move() -> None:
    proposal = _attempt(uuid4(), ActionFamily.MOVE).model_copy(
        update={
            "description": "Mira walks to Market Square.",
            "utterance": None,
            "target_entity_ids": (),
            "target_location_id": MARKET,
        }
    )
    gateway = FakeModelGatewayAdapter(default_kind=FakeScriptKind.TIMEOUT)

    resolution = await run_resolution_graph(_resolution_input(proposal), gateway)

    assert resolution.level is ResolutionLevel.SUCCESS
    assert resolution.effects[0].kind == "move_entity"
    assert gateway.calls == []


@pytest.mark.unit
@pytest.mark.model_fake
async def test_resolver_accepts_restricted_social_claim() -> None:
    proposal = _attempt(uuid4())
    dain_waits = ActionProposal(
        decision_request_id=uuid4(),
        actor_id=DAIN,
        action_family=ActionFamily.WAIT,
        description="Dain remains available to answer.",
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Continue waiting.",
        ),
    )
    graph_input = _resolution_input(proposal, other_proposals=(dain_waits,))
    resolution = SceneResolution(
        resolution_request_id=graph_input.resolution_request_id,
        scene_id=graph_input.scene.scene_id,
        level=ResolutionLevel.SUCCESS,
        accepted_attempt_ids=(proposal.decision_request_id,),
        effects=(
            {
                "kind": "create_claim",
                "effect_key": "social-claim",
                "source_attempt_ids": [str(proposal.decision_request_id)],
                "justification": "The speaker's attempted words were accepted.",
                "speaker_id": str(MIRA),
                "listener_ids": [str(DAIN)],
                "proposition": proposal.utterance,
                "referenced_entity_ids": [],
            },
        ),
        canonical_summary="Mira asked Dain whether the east bridge was open.",
        narration_constraints=NarrationConstraints(maximum_words=100),
        visual_significance=0.0,
        confidence=0.9,
    )
    gateway = FakeModelGatewayAdapter(valid_payload=resolution.model_dump_json())

    result = await run_resolution_graph(graph_input, gateway)

    assert result.level is ResolutionLevel.SUCCESS
    assert result.effects[0].kind == "create_claim"
    assert len(gateway.calls) == 1


@pytest.mark.unit
@pytest.mark.model_fake
async def test_resolver_rejects_stage2_effect_and_falls_back() -> None:
    proposal = _attempt(uuid4())
    graph_input = _resolution_input(proposal)
    invalid = SceneResolution(
        resolution_request_id=graph_input.resolution_request_id,
        scene_id=graph_input.scene.scene_id,
        level=ResolutionLevel.SUCCESS,
        accepted_attempt_ids=(proposal.decision_request_id,),
        effects=(
            {
                "kind": "apply_injury",
                "effect_key": "forbidden-injury",
                "source_attempt_ids": [str(proposal.decision_request_id)],
                "justification": "Forbidden in Stage 1.",
                "entity_id": str(DAIN),
                "body_region": "arm",
                "injury_type": "bruise",
                "severity": 1,
            },
        ),
        canonical_summary="A forbidden effect was proposed.",
        narration_constraints=NarrationConstraints(maximum_words=100),
        visual_significance=0.0,
        confidence=0.9,
    )
    gateway = FakeModelGatewayAdapter(valid_payload=invalid.model_dump_json())

    result = await run_resolution_graph(graph_input, gateway)

    assert result.level is ResolutionLevel.FAILURE
    assert result.effects == ()
    assert len(gateway.calls) == 2
