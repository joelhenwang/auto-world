"""Bounded CharacterDecisionGraph implemented as a plain async pipeline."""

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
from fictional_world.domain.common.enums import ActionFamily, Visibility
from fictional_world.domain.scenes.proposals import ActionProposal, FallbackAction
from fictional_world.prompts import (
    PromptRegistry,
    PromptRenderer,
    validate_no_authored_other_reaction,
)

_ALLOWED_ACTIONS = frozenset(ActionFamily(value) for value in STAGE1_ACTION_FAMILIES)


@dataclass(frozen=True, slots=True)
class DecisionGraphInput:
    """All authority available to one Stage 1 character decision."""

    context: SealedContextPackage
    phase_label: str
    decision_request_id: UUID
    allowed_entity_ids: frozenset[UUID]
    allowed_location_ids: frozenset[UUID] = frozenset()
    allowed_goal_ids: frozenset[UUID] = frozenset()
    allowed_activity_ids: frozenset[UUID] = frozenset()
    other_character_names: tuple[str, ...] = ()
    continuation_activity_id: UUID | None = None
    can_rest: bool = True
    can_observe: bool = True
    model_profile_id: str = "stage0-character_decision-v1"


def _validate_input(graph_input: DecisionGraphInput) -> None:
    package = graph_input.context
    if package.task_type is not ContextTaskType.CHARACTER_DECISION:
        raise ValueError("decision graph requires a character_decision context")
    if package.observer_id not in graph_input.allowed_entity_ids:
        raise ValueError("decision actor must be present in allowed_entity_ids")
    if (
        graph_input.continuation_activity_id is not None
        and graph_input.continuation_activity_id not in graph_input.allowed_activity_ids
    ):
        raise ValueError("continuation activity is not allowed")


def _render_request(
    graph_input: DecisionGraphInput,
    *,
    registry: PromptRegistry,
    renderer: PromptRenderer,
) -> TextGenerationRequest:
    sections = context_sections(graph_input.context)
    known_lore = {
        "private_beliefs": sections.get(ContextSectionId.PRIVATE_BELIEFS, []),
        "known_local_map": sections.get(ContextSectionId.KNOWN_LOCAL_MAP, []),
    }
    allowed_ids = {
        "actor_id": str(graph_input.context.observer_id),
        "entity_ids": sorted(str(value) for value in graph_input.allowed_entity_ids),
        "location_ids": sorted(str(value) for value in graph_input.allowed_location_ids),
        "goal_ids": sorted(str(value) for value in graph_input.allowed_goal_ids),
        "activity_ids": sorted(str(value) for value in graph_input.allowed_activity_ids),
        "action_families": list(STAGE1_ACTION_FAMILIES),
        "decision_request_id": str(graph_input.decision_request_id),
    }
    variables = {
        "phase_label": graph_input.phase_label,
        "stable_identity": json_text(sections.get(ContextSectionId.STABLE_IDENTITY, {})),
        "current_state": json_text(sections.get(ContextSectionId.CURRENT_STATE, {})),
        "current_perception": json_text(sections.get(ContextSectionId.CURRENT_PERCEPTION, [])),
        "goals_and_plans": json_text(sections.get(ContextSectionId.GOALS_AND_PLANS, [])),
        "relationships": json_text(sections.get(ContextSectionId.RELATIONSHIPS, [])),
        "recent_memory": json_text(sections.get(ContextSectionId.RECENT_MEMORY, [])),
        "capabilities": json_text(sections.get(ContextSectionId.CAPABILITIES, {})),
        "known_lore": json_text(known_lore),
        "allowed_ids": json_text(allowed_ids),
    }
    rendered = renderer.render(registry.load("character_decision_v1"), variables)
    sampling = sampling_for_role(ModelRole.CHARACTER_DECISION).to_options(
        seed=graph_input.decision_request_id.int & 0x7FFFFFFF
    )
    return TextGenerationRequest(
        request_id=str(graph_input.decision_request_id),
        role=ModelRole.CHARACTER_DECISION.value,
        model_profile_id=graph_input.model_profile_id,
        messages=(
            ModelMessage(role="system", content=rendered.system),
            ModelMessage(role="user", content=rendered.user),
        ),
        output_schema=ActionProposal,
        sampling=sampling,
        routing=ProviderRoutingOptions(),
        metadata={
            "context_package_id": str(graph_input.context.package_id),
            "context_hash": graph_input.context.package_hash,
            "phase_snapshot_id": str(graph_input.context.phase_snapshot_id),
            "phase_label": graph_input.phase_label,
            "actor_id": str(graph_input.context.observer_id),
            "allowed_entity_ids": ",".join(
                sorted(str(value) for value in graph_input.allowed_entity_ids)
            ),
            "prompt_id": rendered.prompt_id,
            "prompt_hash": rendered.content_hash,
        },
    )


def _validate_proposal(proposal: ActionProposal, graph_input: DecisionGraphInput) -> None:
    if proposal.decision_request_id != graph_input.decision_request_id:
        raise ValueError("decision_request_id does not match the graph request")
    if proposal.actor_id != graph_input.context.observer_id:
        raise ValueError("proposal actor does not match the sealed observer")
    if proposal.action_family not in _ALLOWED_ACTIONS:
        raise ValueError("proposal action family is outside Stage 1")
    if proposal.fallback.action_family not in _ALLOWED_ACTIONS:
        raise ValueError("proposal fallback action family is outside Stage 1")
    if not set(proposal.target_entity_ids).issubset(graph_input.allowed_entity_ids):
        raise ValueError("proposal contains an unknown target entity")
    if (
        proposal.target_location_id is not None
        and proposal.target_location_id not in graph_input.allowed_location_ids
    ):
        raise ValueError("proposal contains an unknown target location")
    if not set(proposal.relevant_goal_ids).issubset(graph_input.allowed_goal_ids):
        raise ValueError("proposal contains an unknown goal")
    if (
        proposal.continuation_activity_id is not None
        and proposal.continuation_activity_id not in graph_input.allowed_activity_ids
    ):
        raise ValueError("proposal contains an unknown activity")
    for outcome in proposal.desired_outcomes:
        if not set(outcome.target_entity_ids).issubset(graph_input.allowed_entity_ids):
            raise ValueError("desired outcome contains an unknown target entity")
    validate_no_authored_other_reaction(
        proposal,
        other_character_names=graph_input.other_character_names,
    )


def _fallback(graph_input: DecisionGraphInput) -> ActionProposal:
    if graph_input.continuation_activity_id is not None:
        family = ActionFamily.CONTINUE_ACTIVITY
        description = "Continue the already established activity without extending its scope."
        continuation_id = graph_input.continuation_activity_id
    elif graph_input.can_rest:
        family = ActionFamily.REST
        description = "Rest cautiously for this phase."
        continuation_id = None
    elif graph_input.can_observe:
        family = ActionFamily.OBSERVE
        description = "Observe the immediate surroundings without drawing conclusions."
        continuation_id = None
    else:
        family = ActionFamily.WAIT
        description = "Wait safely for this phase."
        continuation_id = None
    return ActionProposal(
        decision_request_id=graph_input.decision_request_id,
        actor_id=graph_input.context.observer_id,
        action_family=family,
        description=description,
        continuation_activity_id=continuation_id,
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Wait safely if the proposed action cannot proceed.",
        ),
    )


async def run_decision_graph(
    graph_input: DecisionGraphInput,
    gateway: TextModelGateway,
    *,
    registry: PromptRegistry | None = None,
    renderer: PromptRenderer | None = None,
) -> ActionProposal:
    """Run validate → prompt → invoke → parse/domain-check → regen → fallback."""

    _validate_input(graph_input)
    request = _render_request(
        graph_input,
        registry=registry or PromptRegistry(),
        renderer=renderer or PromptRenderer(),
    )
    proposal = await invoke_with_one_regeneration(
        gateway=gateway,
        request=request,
        output_type=ActionProposal,
        domain_validator=lambda value: _validate_proposal(value, graph_input),
    )
    return proposal if proposal is not None else _fallback(graph_input)


__all__ = ["DecisionGraphInput", "run_decision_graph"]
