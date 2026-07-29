"""Deterministic protocol-compatible fake for the Stage 2 seven-day scenario."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import BaseModel

from fictional_world.application.models.errors import (
    ModelGatewayError,
    ModelGatewayErrorCode,
)
from fictional_world.application.models.messages import (
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.application.models.roles import ModelRole
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

_MIRA = seed_uuid("character/mira-talren")
_DAIN = seed_uuid("character/dain-arcen")
_IRI = seed_uuid("character/iri-voss")
_TORREN = seed_uuid("character/torren-kest")

_QUIET_DECISION_BY_ACTOR: dict[UUID, ActionFamily] = {
    _MIRA: ActionFamily.WAIT,
    _DAIN: ActionFamily.OBSERVE,
    _IRI: ActionFamily.REST,
    _TORREN: ActionFamily.WAIT,
}


@dataclass
class Stage2FakeModelGateway:
    """Pattern-based quiet scripts for Stage 2 (no network / provider access)."""

    before_generate: Callable[[], None] | None = None
    calls: list[dict[str, str]] = field(default_factory=list)

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        if self.before_generate is not None:
            self.before_generate()
        self.calls.append(
            {
                "role": request.role,
                "request_id": request.request_id,
                "phase_label": request.metadata.get("phase_label", ""),
                "scene_id": request.metadata.get("scene_id", ""),
                "actor_id": request.metadata.get("actor_id", ""),
            }
        )
        if request.role == ModelRole.CHARACTER_DECISION.value:
            output: BaseModel = self._decision(request)
        elif request.role == ModelRole.CHARACTER_REACTION.value:
            output = self._reaction(request)
        elif request.role == ModelRole.RESOLVER.value:
            output = self._resolution(request)
        elif request.role == ModelRole.DIRECTOR_PROPOSAL.value:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
                "Stage 2 quiet script never calls Director models",
                request_id=request.request_id,
                retryable=False,
            )
        else:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
                f"Stage 2 fake has no script for role {request.role}",
                request_id=request.request_id,
                retryable=False,
            )
        return TextGenerationResult(
            provider_request_id=f"stage2-fake:{request.request_id}",
            resolved_model="fake/stage2-seven-day-v1",
            provider_name="fake",
            raw_text=output.model_dump_json(),
            parsed=output,
            input_tokens=None,
            output_tokens=None,
            finish_reason="stop",
            capability_mode="json_schema_native",
            latency_ms=0,
        )

    @staticmethod
    def _decision(request: TextGenerationRequest) -> ActionProposal:
        actor_id = UUID(request.metadata["actor_id"])
        phase_label = request.metadata.get("phase_label", "dawn")
        family = _QUIET_DECISION_BY_ACTOR.get(actor_id, ActionFamily.WAIT)
        # Slight phase variation without targeting others (avoids reaction fan-out).
        if phase_label in {"morning", "afternoon"} and actor_id == _MIRA:
            family = ActionFamily.OBSERVE
        elif phase_label in {"evening", "dusk"} and actor_id == _DAIN:
            family = ActionFamily.REST
        return ActionProposal(
            decision_request_id=UUID(request.request_id),
            actor_id=actor_id,
            action_family=family,
            description=(
                f"Quiet Stage 2 {family.value} during {phase_label} "
                "without determining outcomes for others."
            ),
            utterance=None,
            target_entity_ids=(),
            visibility=Visibility.OBSERVABLE,
            fallback=FallbackAction(
                action_family=ActionFamily.WAIT,
                description="Wait safely if the attempt cannot proceed.",
            ),
        )

    @staticmethod
    def _reaction(request: TextGenerationRequest) -> ReactionProposal:
        return ReactionProposal(
            reaction_request_id=UUID(request.request_id),
            scene_id=UUID(request.metadata["scene_id"]),
            triggering_attempt_id=UUID(request.metadata["triggering_attempt_id"]),
            reactor_id=UUID(request.metadata["reactor_id"]),
            action_family=ActionFamily.WAIT,
            description="The reactor makes no additional outcome claim.",
        )

    @staticmethod
    def _resolution(request: TextGenerationRequest) -> SceneResolution:
        attempt_ids = tuple(
            UUID(value) for value in request.metadata.get("attempt_ids", "").split(",") if value
        )
        phase_label = request.metadata.get("phase_label", "phase")
        return SceneResolution(
            resolution_request_id=UUID(request.request_id),
            scene_id=UUID(request.metadata["scene_id"]),
            level=ResolutionLevel.SUCCESS,
            accepted_attempt_ids=attempt_ids,
            effects=(),
            canonical_summary=(
                f"Quiet resolution for {phase_label}: participants act without conflict."
            ),
            narration_constraints=NarrationConstraints(
                required_facts=("A quiet beat completed without conflict.",),
                forbidden_assertions=("Do not invent secret disclosures.",),
                tone_tags=("quiet", "grounded"),
                maximum_words=80,
            ),
            visual_significance=0.02,
            confidence=0.95,
        )


__all__ = ["Stage2FakeModelGateway"]
