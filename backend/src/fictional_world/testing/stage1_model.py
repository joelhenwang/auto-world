"""Deterministic protocol-compatible fake for the Stage 1 first-day scenario."""

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


@dataclass
class Stage1FakeModelGateway:
    """Return grounded synthetic proposals without network or provider access."""

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
            }
        )
        if request.role == ModelRole.CHARACTER_DECISION.value:
            output: BaseModel = self._decision(request)
        elif request.role == ModelRole.CHARACTER_REACTION.value:
            output = self._reaction(request)
        elif request.role == ModelRole.RESOLVER.value:
            output = self._resolution(request)
        else:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
                f"Stage 1 fake has no script for role {request.role}",
                request_id=request.request_id,
                retryable=False,
            )
        return TextGenerationResult(
            provider_request_id=f"stage1-fake:{request.request_id}",
            resolved_model="fake/stage1-first-day-v1",
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
        phase_label = request.metadata["phase_label"]
        other_id = _DAIN if actor_id == _MIRA else _MIRA
        if phase_label == "dawn":
            family = ActionFamily.OBSERVE if actor_id == _MIRA else ActionFamily.REST
        elif phase_label == "morning":
            family = ActionFamily.COMMUNICATE if actor_id == _MIRA else ActionFamily.WAIT
        else:
            family = ActionFamily.REST if actor_id == _MIRA else ActionFamily.OBSERVE

        target_ids = (
            (other_id,) if family in {ActionFamily.OBSERVE, ActionFamily.COMMUNICATE} else ()
        )
        utterance = (
            "Is the east bridge open after the rain?"
            if family is ActionFamily.COMMUNICATE
            else None
        )
        return ActionProposal(
            decision_request_id=UUID(request.request_id),
            actor_id=actor_id,
            action_family=family,
            description=(
                f"The actor attempts a bounded {family.value} action "
                f"during {phase_label} without determining its outcome."
            ),
            utterance=utterance,
            target_entity_ids=target_ids,
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
        return SceneResolution(
            resolution_request_id=UUID(request.request_id),
            scene_id=UUID(request.metadata["scene_id"]),
            level=ResolutionLevel.SUCCESS,
            accepted_attempt_ids=attempt_ids,
            effects=(),
            canonical_summary="Mira asked about the bridge while Dain remained free to respond.",
            narration_constraints=NarrationConstraints(
                required_facts=("Mira asked about the bridge.",),
                forbidden_assertions=("Do not invent Dain's answer.",),
                tone_tags=("quiet", "grounded"),
                maximum_words=100,
            ),
            visual_significance=0.05,
            confidence=0.95,
        )


__all__ = ["Stage1FakeModelGateway"]
