"""Bounded CharacterReactionGraph implemented as a plain async pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fictional_world.agents._pipeline import (
    context_sections,
    invoke_with_one_regeneration,
    json_text,
)
from fictional_world.application.context.types import (
    STAGE1_ACTION_FAMILIES,
    ContextSectionId,
    ContextTaskType,
    SealedContextPackage,
)
from fictional_world.application.models.messages import (
    ModelMessage,
    ProviderRoutingOptions,
    TextGenerationRequest,
)
from fictional_world.application.models.protocols import TextModelGateway
from fictional_world.application.models.roles import ModelRole
from fictional_world.application.models.sampling import sampling_for_role
from fictional_world.domain.common.enums import ActionFamily
from fictional_world.domain.scenes.proposals import ActionProposal, ReactionProposal
from fictional_world.prompts import PromptRegistry, PromptRenderer

_ALLOWED_ACTIONS = frozenset(ActionFamily(value) for value in STAGE1_ACTION_FAMILIES)


@dataclass(frozen=True, slots=True)
class ReactionGraphInput:
    """Authority for one reactor responding to one perceived attempt."""

    context: SealedContextPackage
    scene_id: UUID
    reaction_request_id: UUID
    perceived_attempt: ActionProposal
    remaining_beat_budget: int
    allowed_entity_ids: frozenset[UUID]
    model_profile_id: str = "stage0-character_reaction-v1"


def _validate_input(graph_input: ReactionGraphInput) -> None:
    package = graph_input.context
    if package.task_type is not ContextTaskType.CHARACTER_REACTION:
        raise ValueError("reaction graph requires a character_reaction context")
    if package.observer_id not in graph_input.allowed_entity_ids:
        raise ValueError("reactor must be present in allowed_entity_ids")
    if graph_input.perceived_attempt.actor_id == package.observer_id:
        raise ValueError("a character cannot react to its own primary attempt")
    if graph_input.perceived_attempt.actor_id not in graph_input.allowed_entity_ids:
        raise ValueError("perceived attempt actor is not allowed")
    if not 1 <= graph_input.remaining_beat_budget <= 12:
        raise ValueError("remaining beat budget must be between 1 and 12")


def _render_request(
    graph_input: ReactionGraphInput,
    *,
    registry: PromptRegistry,
    renderer: PromptRenderer,
) -> TextGenerationRequest:
    sections = context_sections(graph_input.context)
    attempt = graph_input.perceived_attempt
    perceived_attempt = {
        "attempt_id": str(attempt.decision_request_id),
        "actor_id": str(attempt.actor_id),
        "action_family": attempt.action_family.value,
        "description": attempt.description,
        "utterance": attempt.utterance,
        "target_entity_ids": [str(value) for value in attempt.target_entity_ids],
        "target_location_id": (
            None if attempt.target_location_id is None else str(attempt.target_location_id)
        ),
    }
    variables = {
        "reactor_identity": json_text(sections.get(ContextSectionId.STABLE_IDENTITY, {})),
        "perceived_attempt": json_text(perceived_attempt),
        "scene_state": json_text(sections.get(ContextSectionId.SCENE_WORKING, {})),
        "capabilities": json_text(sections.get(ContextSectionId.CAPABILITIES, {})),
        "prepared_actions": json_text([]),
        "relationship_context": json_text(sections.get(ContextSectionId.RELATIONSHIPS, [])),
        "remaining_beat_budget": str(graph_input.remaining_beat_budget),
        "allowed_ids": json_text(
            {
                "scene_id": str(graph_input.scene_id),
                "reaction_request_id": str(graph_input.reaction_request_id),
                "triggering_attempt_id": str(attempt.decision_request_id),
                "reactor_id": str(graph_input.context.observer_id),
                "entity_ids": sorted(str(value) for value in graph_input.allowed_entity_ids),
                "action_families": list(STAGE1_ACTION_FAMILIES),
            }
        ),
    }
    rendered = renderer.render(registry.load("character_reaction_v1"), variables)
    sampling = sampling_for_role(ModelRole.CHARACTER_REACTION).to_options(
        seed=graph_input.reaction_request_id.int & 0x7FFFFFFF
    )
    return TextGenerationRequest(
        request_id=str(graph_input.reaction_request_id),
        role=ModelRole.CHARACTER_REACTION.value,
        model_profile_id=graph_input.model_profile_id,
        messages=(
            ModelMessage(role="system", content=rendered.system),
            ModelMessage(role="user", content=rendered.user),
        ),
        output_schema=ReactionProposal,
        sampling=sampling,
        routing=ProviderRoutingOptions(),
        metadata={
            "context_package_id": str(graph_input.context.package_id),
            "context_hash": graph_input.context.package_hash,
            "phase_snapshot_id": str(graph_input.context.phase_snapshot_id),
            "scene_id": str(graph_input.scene_id),
            "triggering_attempt_id": str(attempt.decision_request_id),
            "reactor_id": str(graph_input.context.observer_id),
            "attempt_actor_id": str(attempt.actor_id),
            "prompt_id": rendered.prompt_id,
            "prompt_hash": rendered.content_hash,
        },
    )


def _validate_proposal(proposal: ReactionProposal, graph_input: ReactionGraphInput) -> None:
    if proposal.reaction_request_id != graph_input.reaction_request_id:
        raise ValueError("reaction_request_id does not match the graph request")
    if proposal.scene_id != graph_input.scene_id:
        raise ValueError("reaction scene does not match the active scene")
    if proposal.triggering_attempt_id != graph_input.perceived_attempt.decision_request_id:
        raise ValueError("reaction references an unperceived attempt")
    if proposal.reactor_id != graph_input.context.observer_id:
        raise ValueError("reactor does not match the sealed observer")
    if proposal.action_family not in _ALLOWED_ACTIONS:
        raise ValueError("reaction action family is outside Stage 1")
    if not set(proposal.target_entity_ids).issubset(graph_input.allowed_entity_ids):
        raise ValueError("reaction contains an unknown target entity")
    for outcome in proposal.desired_outcomes:
        if not set(outcome.target_entity_ids).issubset(graph_input.allowed_entity_ids):
            raise ValueError("reaction outcome contains an unknown target entity")


def _fallback(graph_input: ReactionGraphInput) -> ReactionProposal:
    return ReactionProposal(
        reaction_request_id=graph_input.reaction_request_id,
        scene_id=graph_input.scene_id,
        triggering_attempt_id=graph_input.perceived_attempt.decision_request_id,
        reactor_id=graph_input.context.observer_id,
        action_family=ActionFamily.WAIT,
        description="Take no additional action beyond the already perceived scene.",
    )


async def run_reaction_graph(
    graph_input: ReactionGraphInput,
    gateway: TextModelGateway,
    *,
    registry: PromptRegistry | None = None,
    renderer: PromptRenderer | None = None,
) -> ReactionProposal:
    """Run a bounded reaction pipeline and conservatively fall back to waiting."""

    _validate_input(graph_input)
    request = _render_request(
        graph_input,
        registry=registry or PromptRegistry(),
        renderer=renderer or PromptRenderer(),
    )
    proposal = await invoke_with_one_regeneration(
        gateway=gateway,
        request=request,
        output_type=ReactionProposal,
        domain_validator=lambda value: _validate_proposal(value, graph_input),
    )
    return proposal if proposal is not None else _fallback(graph_input)


__all__ = ["ReactionGraphInput", "run_reaction_graph"]
