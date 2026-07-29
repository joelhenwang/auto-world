"""Deterministic-first Stage 1 scene resolution pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from fictional_world.agents._pipeline import invoke_with_one_regeneration, json_text
from fictional_world.application.models.messages import (
    ModelMessage,
    ProviderRoutingOptions,
    TextGenerationRequest,
)
from fictional_world.application.models.protocols import TextModelGateway
from fictional_world.application.models.roles import ModelRole
from fictional_world.application.models.sampling import sampling_for_role
from fictional_world.domain.common.enums import (
    ActionFamily,
    ObservationChannel,
    ResolutionLevel,
    ResourceKind,
)
from fictional_world.domain.effects.commands import (
    AdvanceActivityEffect,
    CreateClaimEffect,
    CreateRecentMemoryEffect,
    MoveEntityEffect,
    ObserveEffect,
    RestEffect,
    ScheduleEffect,
    SpendResourceEffect,
    WaitEffect,
)
from fictional_world.domain.scenes.proposals import (
    ActionProposal,
    NarrationConstraints,
    ReactionProposal,
    SceneDraft,
    SceneResolution,
)
from fictional_world.prompts import PromptRegistry, PromptRenderer

_DETERMINISTIC_FAMILIES = frozenset(
    {
        ActionFamily.WAIT,
        ActionFamily.REST,
        ActionFamily.OBSERVE,
        ActionFamily.MOVE,
    }
)


@dataclass(frozen=True, slots=True)
class ResolutionGraphInput:
    """Sealed scene inputs and the complete feasible-ID envelope."""

    scene: SceneDraft
    proposals: tuple[ActionProposal, ...]
    reactions: tuple[ReactionProposal, ...]
    resolution_request_id: UUID
    actor_locations: Mapping[UUID, UUID | None]
    allowed_entity_ids: frozenset[UUID]
    allowed_location_ids: frozenset[UUID]
    random_values: tuple[float, ...] = ()
    model_profile_id: str = "stage0-resolver-v1"


def _validate_input(graph_input: ResolutionGraphInput) -> None:
    scene = graph_input.scene
    proposal_ids = {proposal.decision_request_id for proposal in graph_input.proposals}
    if proposal_ids != set(scene.action_proposal_ids):
        raise ValueError("resolver proposals do not match the scene draft")
    actor_ids = {proposal.actor_id for proposal in graph_input.proposals}
    if actor_ids != set(scene.participant_ids):
        raise ValueError("resolver actors do not match scene participants")
    if not actor_ids.issubset(graph_input.allowed_entity_ids):
        raise ValueError("scene contains an entity outside the feasible envelope")
    if any(reaction.scene_id != scene.scene_id for reaction in graph_input.reactions):
        raise ValueError("reaction belongs to a different scene")
    if any(
        reaction.triggering_attempt_id not in proposal_ids for reaction in graph_input.reactions
    ):
        raise ValueError("reaction references an attempt outside the scene")


def _deterministic_resolution(
    graph_input: ResolutionGraphInput,
) -> SceneResolution | None:
    if not all(
        proposal.action_family in _DETERMINISTIC_FAMILIES for proposal in graph_input.proposals
    ):
        return None

    effects: list[WaitEffect | RestEffect | ObserveEffect | MoveEntityEffect] = []
    for proposal in graph_input.proposals:
        effect_prefix = f"{graph_input.scene.scene_id}:{proposal.decision_request_id}"
        source_ids = (proposal.decision_request_id,)
        if proposal.action_family is ActionFamily.WAIT:
            effects.append(
                WaitEffect(
                    effect_key=f"{effect_prefix}:wait",
                    source_attempt_ids=source_ids,
                    justification="Waiting is deterministic and uncontested.",
                    entity_id=proposal.actor_id,
                )
            )
        elif proposal.action_family is ActionFamily.REST:
            effects.append(
                RestEffect(
                    effect_key=f"{effect_prefix}:rest",
                    source_attempt_ids=source_ids,
                    justification="A quiet rest attempt can recover bounded stamina.",
                    entity_id=proposal.actor_id,
                    stamina_recovery=5.0,
                )
            )
        elif proposal.action_family is ActionFamily.OBSERVE:
            effects.append(
                ObserveEffect(
                    effect_key=f"{effect_prefix}:observe",
                    source_attempt_ids=source_ids,
                    justification="Observation records an attempt without inventing findings.",
                    observer_id=proposal.actor_id,
                    target_entity_ids=proposal.target_entity_ids,
                    channels=(ObservationChannel.SIGHT, ObservationChannel.HEARING),
                )
            )
        else:
            from_location = graph_input.actor_locations.get(proposal.actor_id)
            to_location = proposal.target_location_id
            if (
                from_location is None
                or to_location is None
                or to_location not in graph_input.allowed_location_ids
                or from_location == to_location
            ):
                return None
            effects.append(
                MoveEntityEffect(
                    effect_key=f"{effect_prefix}:move",
                    source_attempt_ids=source_ids,
                    justification="The simple movement attempt is feasible and uncontested.",
                    entity_id=proposal.actor_id,
                    from_location_id=from_location,
                    to_location_id=to_location,
                )
            )

    families = ", ".join(proposal.action_family.value for proposal in graph_input.proposals)
    return SceneResolution(
        resolution_request_id=graph_input.resolution_request_id,
        scene_id=graph_input.scene.scene_id,
        level=ResolutionLevel.SUCCESS,
        accepted_attempt_ids=tuple(
            proposal.decision_request_id for proposal in graph_input.proposals
        ),
        effects=tuple(effects),
        canonical_summary=f"The scene completed deterministic actions: {families}.",
        narration_constraints=NarrationConstraints(
            required_facts=(f"Deterministic actions completed: {families}.",),
            forbidden_assertions=("Do not invent discoveries, dialogue, or reactions.",),
            tone_tags=("grounded", "concise"),
            maximum_words=120,
        ),
        visual_significance=0.05,
        confidence=1.0,
    )


def _render_request(
    graph_input: ResolutionGraphInput,
    *,
    registry: PromptRegistry,
    renderer: PromptRenderer,
) -> TextGenerationRequest:
    scene = graph_input.scene
    allowed_effects = (
        "wait",
        "observe",
        "rest",
        "move_entity",
        "spend_resource(stamina_only)",
        "advance_activity",
        "create_claim",
        "create_recent_memory",
        "schedule_effect",
    )
    variables = {
        "scene_snapshot": json_text(
            {
                "scene": scene.model_dump(mode="json"),
                "actor_locations": {
                    str(key): None if value is None else str(value)
                    for key, value in graph_input.actor_locations.items()
                },
            }
        ),
        "accepted_attempts": json_text(
            {
                "proposals": [
                    proposal.model_dump(mode="json") for proposal in graph_input.proposals
                ],
                "reactions": [
                    reaction.model_dump(mode="json") for reaction in graph_input.reactions
                ],
            }
        ),
        "deterministic_results": json_text({"applicable": False}),
        "feasible_outcome_envelope": json_text(
            {
                "resolution_request_id": str(graph_input.resolution_request_id),
                "scene_id": str(scene.scene_id),
                "entity_ids": sorted(str(value) for value in graph_input.allowed_entity_ids),
                "location_ids": sorted(str(value) for value in graph_input.allowed_location_ids),
                "high_impact": scene.high_impact,
            }
        ),
        "allowed_effect_commands": json_text(allowed_effects),
        "random_values": json_text(graph_input.random_values),
        "observation_candidates": json_text(
            {"participant_ids": [str(value) for value in scene.participant_ids]}
        ),
        "impact_class": "high" if scene.high_impact else "ordinary",
    }
    rendered = renderer.render(registry.load("scene_resolver_v1"), variables)
    sampling = sampling_for_role(ModelRole.RESOLVER).to_options(
        seed=graph_input.resolution_request_id.int & 0x7FFFFFFF
    )
    return TextGenerationRequest(
        request_id=str(graph_input.resolution_request_id),
        role=ModelRole.RESOLVER.value,
        model_profile_id=graph_input.model_profile_id,
        messages=(
            ModelMessage(role="system", content=rendered.system),
            ModelMessage(role="user", content=rendered.user),
        ),
        output_schema=SceneResolution,
        sampling=sampling,
        routing=ProviderRoutingOptions(),
        metadata={
            "scene_id": str(scene.scene_id),
            "phase_id": str(scene.phase_id),
            "snapshot_id": str(scene.snapshot_id),
            "prompt_id": rendered.prompt_id,
            "prompt_hash": rendered.content_hash,
        },
    )


def _validate_resolution(
    resolution: SceneResolution,
    graph_input: ResolutionGraphInput,
) -> None:
    if resolution.resolution_request_id != graph_input.resolution_request_id:
        raise ValueError("resolution_request_id does not match the graph request")
    if resolution.scene_id != graph_input.scene.scene_id:
        raise ValueError("resolution belongs to a different scene")
    attempt_ids = {
        *(proposal.decision_request_id for proposal in graph_input.proposals),
        *(reaction.reaction_request_id for reaction in graph_input.reactions),
    }
    if not set(resolution.accepted_attempt_ids).issubset(attempt_ids):
        raise ValueError("resolution accepts an attempt outside the scene")
    participant_ids = set(graph_input.scene.participant_ids)
    continuation_ids = {
        proposal.continuation_activity_id
        for proposal in graph_input.proposals
        if proposal.continuation_activity_id is not None
    }
    utterances = {
        utterance
        for utterance in (
            *(proposal.utterance for proposal in graph_input.proposals),
            *(reaction.utterance for reaction in graph_input.reactions),
        )
        if utterance is not None
    }
    proposals_by_actor = {proposal.actor_id: proposal for proposal in graph_input.proposals}

    for effect in resolution.effects:
        if not set(effect.source_attempt_ids).issubset(attempt_ids):
            raise ValueError("effect provenance references an attempt outside the scene")
        if isinstance(effect, (WaitEffect, RestEffect)):
            if effect.entity_id not in participant_ids:
                raise ValueError("effect targets a non-participant")
        elif isinstance(effect, ObserveEffect):
            if effect.observer_id not in participant_ids or not set(
                effect.target_entity_ids
            ).issubset(graph_input.allowed_entity_ids):
                raise ValueError("observation effect exceeds the feasible envelope")
        elif isinstance(effect, MoveEntityEffect):
            proposal = proposals_by_actor.get(effect.entity_id)
            if (
                proposal is None
                or proposal.action_family is not ActionFamily.MOVE
                or effect.from_location_id != graph_input.actor_locations.get(effect.entity_id)
                or effect.to_location_id != proposal.target_location_id
                or effect.to_location_id not in graph_input.allowed_location_ids
            ):
                raise ValueError("movement effect exceeds the proposed movement envelope")
        elif isinstance(effect, SpendResourceEffect):
            if (
                effect.entity_id not in participant_ids
                or effect.resource is not ResourceKind.STAMINA
            ):
                raise ValueError("only participant stamina spending is allowed")
        elif isinstance(effect, AdvanceActivityEffect):
            if effect.activity_id not in continuation_ids:
                raise ValueError("activity effect references an unproposed activity")
        elif isinstance(effect, CreateClaimEffect):
            if (
                effect.speaker_id not in participant_ids
                or not set(effect.listener_ids).issubset(participant_ids)
                or effect.proposition not in utterances
            ):
                raise ValueError("claim effect invents a speaker, listener, or utterance")
        elif isinstance(effect, CreateRecentMemoryEffect):
            if effect.owner_character_id not in participant_ids:
                raise ValueError("memory effect targets a non-participant")
        elif isinstance(effect, ScheduleEffect):
            if not set(effect.target_entity_ids).issubset(graph_input.allowed_entity_ids):
                raise ValueError("scheduled effect targets an unknown entity")
        else:
            raise ValueError(f"effect kind is outside Stage 1: {effect.kind}")


def _conservative_fallback(graph_input: ResolutionGraphInput) -> SceneResolution:
    return SceneResolution(
        resolution_request_id=graph_input.resolution_request_id,
        scene_id=graph_input.scene.scene_id,
        level=ResolutionLevel.FAILURE,
        accepted_attempt_ids=(),
        rejected_assumptions=(
            "The proposed outcome could not be validated inside the Stage 1 envelope.",
        ),
        effects=(),
        canonical_summary="No uncertain state change was committed for this scene.",
        narration_constraints=NarrationConstraints(
            required_facts=("No uncertain state change occurred.",),
            forbidden_assertions=("Do not invent success, movement, dialogue, or discovery.",),
            tone_tags=("conservative", "grounded"),
            maximum_words=100,
        ),
        visual_significance=0.0,
        confidence=1.0,
    )


async def run_resolution_graph(
    graph_input: ResolutionGraphInput,
    gateway: TextModelGateway | None = None,
    *,
    registry: PromptRegistry | None = None,
    renderer: PromptRenderer | None = None,
) -> SceneResolution:
    """Resolve deterministic scenes locally; bound all other scenes to one regeneration."""

    _validate_input(graph_input)
    deterministic = _deterministic_resolution(graph_input)
    if deterministic is not None:
        return deterministic
    if gateway is None or graph_input.scene.high_impact:
        return _conservative_fallback(graph_input)

    request = _render_request(
        graph_input,
        registry=registry or PromptRegistry(),
        renderer=renderer or PromptRenderer(),
    )
    resolution = await invoke_with_one_regeneration(
        gateway=gateway,
        request=request,
        output_type=SceneResolution,
        domain_validator=lambda value: _validate_resolution(value, graph_input),
    )
    return resolution if resolution is not None else _conservative_fallback(graph_input)


__all__ = ["ResolutionGraphInput", "run_resolution_graph"]
