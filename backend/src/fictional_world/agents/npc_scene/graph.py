"""NPCSceneGraph — bounded NPC actor stub using perspective knowledge packages.

Produces ActionProposal outputs only. Never commits registry rows, effects, or
events. Omniscient Director context is never accepted as input.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from fictional_world.agents._pipeline import invoke_with_one_regeneration, json_text
from fictional_world.agents.restricted_effects import GraphTaskRole, restricted_effect_kinds
from fictional_world.application.models.messages import (
    ModelMessage,
    ProviderRoutingOptions,
    TextGenerationRequest,
)
from fictional_world.application.models.protocols import TextModelGateway
from fictional_world.application.models.roles import ModelRole
from fictional_world.application.models.sampling import sampling_for_role
from fictional_world.application.npc.types import NpcKnowledgePackage
from fictional_world.domain.common.enums import ActionFamily, Visibility
from fictional_world.domain.scenes.proposals import ActionProposal, FallbackAction

_ALLOWED_ACTIONS = frozenset(
    {
        ActionFamily.WAIT,
        ActionFamily.OBSERVE,
        ActionFamily.REST,
        ActionFamily.MOVE,
        ActionFamily.COMMUNICATE,
        ActionFamily.SOCIALIZE,
        ActionFamily.INTERACT_ENVIRONMENT,
    }
)


@dataclass(frozen=True, slots=True)
class NpcSceneGraphInput:
    """Multi-NPC scene inputs keyed by perspective knowledge packages only."""

    scene_id: UUID
    knowledge_packages: tuple[NpcKnowledgePackage, ...]
    decision_request_ids: Mapping[UUID, UUID]
    allowed_entity_ids: frozenset[UUID]
    allowed_location_ids: frozenset[UUID] = frozenset()
    model_profile_id: str = "stage0-npc_actor-v1"


@dataclass(frozen=True, slots=True)
class NpcSceneGraphResult:
    """One proposal per eligible NPC. Ineligible packages are omitted."""

    scene_id: UUID
    proposals: tuple[ActionProposal, ...]
    skipped_character_ids: tuple[UUID, ...] = ()


def _validate_input(graph_input: NpcSceneGraphInput) -> None:
    if not graph_input.knowledge_packages:
        raise ValueError("npc scene graph requires at least one knowledge package")
    package_ids = {package.character_id for package in graph_input.knowledge_packages}
    if not package_ids.issubset(graph_input.allowed_entity_ids):
        raise ValueError("npc knowledge package character outside allowed_entity_ids")
    for character_id in package_ids:
        if character_id not in graph_input.decision_request_ids:
            raise ValueError(f"missing decision_request_id for npc {character_id}")


def _fallback_wait(package: NpcKnowledgePackage, request_id: UUID) -> ActionProposal:
    return ActionProposal(
        decision_request_id=request_id,
        actor_id=package.character_id,
        action_family=ActionFamily.WAIT,
        description=(
            f"{package.compact_card.display_name} waits without extending the scene scope."
        ),
        visibility=Visibility.OBSERVABLE,
        fallback=FallbackAction(
            action_family=ActionFamily.WAIT,
            description="Continue waiting safely.",
        ),
    )


def _validate_proposal(
    proposal: ActionProposal,
    *,
    package: NpcKnowledgePackage,
    request_id: UUID,
    graph_input: NpcSceneGraphInput,
) -> None:
    if proposal.decision_request_id != request_id:
        raise ValueError("npc decision_request_id does not match")
    if proposal.actor_id != package.character_id:
        raise ValueError("npc proposal actor does not match knowledge package")
    if proposal.action_family not in _ALLOWED_ACTIONS:
        raise ValueError("npc action family is outside the scene envelope")
    if not set(proposal.target_entity_ids).issubset(graph_input.allowed_entity_ids):
        raise ValueError("npc proposal contains an unknown target entity")
    if (
        proposal.target_location_id is not None
        and proposal.target_location_id not in graph_input.allowed_location_ids
    ):
        raise ValueError("npc proposal contains an unknown target location")


def _render_request(
    *,
    package: NpcKnowledgePackage,
    request_id: UUID,
    graph_input: NpcSceneGraphInput,
) -> TextGenerationRequest:
    card = package.compact_card
    variables = {
        "npc_id": str(package.character_id),
        "scene_id": str(graph_input.scene_id),
        "compact_card": json_text(card.model_dump(mode="json")),
        "beliefs": json_text(list(package.beliefs)),
        "secret_keys": json_text(list(package.secret_keys)),
        "allowed_ids": json_text(
            {
                "actor_id": str(package.character_id),
                "decision_request_id": str(request_id),
                "entity_ids": sorted(str(value) for value in graph_input.allowed_entity_ids),
                "location_ids": sorted(str(value) for value in graph_input.allowed_location_ids),
                "effect_kinds": sorted(restricted_effect_kinds(GraphTaskRole.NPC_SCENE)),
                "action_families": sorted(family.value for family in _ALLOWED_ACTIONS),
            }
        ),
    }
    system = (
        "You are acting as one temporary fictional NPC from a sealed knowledge package. "
        "Do not use omniscient Director knowledge. Do not create additional named NPCs. "
        "Produce exactly one ActionProposal JSON object. Do not determine outcomes or "
        "commit state."
    )
    user = (
        f"<NPC_PACKAGE>\n{json_text(variables)}\n</NPC_PACKAGE>\n"
        "Return one ActionProposal for this NPC only."
    )
    sampling = sampling_for_role(ModelRole.CHARACTER_DECISION).to_options(
        seed=request_id.int & 0x7FFFFFFF
    )
    return TextGenerationRequest(
        request_id=str(request_id),
        role=ModelRole.CHARACTER_DECISION.value,
        model_profile_id=graph_input.model_profile_id,
        messages=(
            ModelMessage(role="system", content=system),
            ModelMessage(role="user", content=user),
        ),
        output_schema=ActionProposal,
        sampling=sampling,
        routing=ProviderRoutingOptions(),
        metadata={
            "scene_id": str(graph_input.scene_id),
            "npc_id": str(package.character_id),
            "graph": "npc_scene",
        },
    )


async def run_npc_scene_graph(
    graph_input: NpcSceneGraphInput,
    gateway: TextModelGateway | None = None,
) -> NpcSceneGraphResult:
    """Produce bounded NPC proposals from knowledge packages only.

    Ineligible (archived / non-actor) packages are skipped. Model failure follows
    Stage 1 repair → one regeneration → WAIT fallback. Never commits.
    """

    _validate_input(graph_input)
    proposals: list[ActionProposal] = []
    skipped: list[UUID] = []

    for package in graph_input.knowledge_packages:
        request_id = graph_input.decision_request_ids[package.character_id]
        if not package.may_receive_ordinary_actor_task:
            skipped.append(package.character_id)
            continue

        if gateway is None:
            proposals.append(_fallback_wait(package, request_id))
            continue

        request = _render_request(
            package=package,
            request_id=request_id,
            graph_input=graph_input,
        )

        def _domain_check(
            value: ActionProposal,
            *,
            pkg: NpcKnowledgePackage = package,
            rid: UUID = request_id,
        ) -> None:
            _validate_proposal(
                value,
                package=pkg,
                request_id=rid,
                graph_input=graph_input,
            )

        proposal = await invoke_with_one_regeneration(
            gateway=gateway,
            request=request,
            output_type=ActionProposal,
            domain_validator=_domain_check,
        )
        proposals.append(proposal if proposal is not None else _fallback_wait(package, request_id))

    return NpcSceneGraphResult(
        scene_id=graph_input.scene_id,
        proposals=tuple(proposals),
        skipped_character_ids=tuple(skipped),
    )


__all__ = [
    "NpcSceneGraphInput",
    "NpcSceneGraphResult",
    "run_npc_scene_graph",
]
