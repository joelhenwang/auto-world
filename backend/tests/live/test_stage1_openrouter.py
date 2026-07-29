"""Opt-in Stage 1 OpenRouter structured-proposal smoke."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import httpx
import pytest

from fictional_world.agents.character_decision import DecisionGraphInput, run_decision_graph
from fictional_world.application.context.types import (
    ContextSection,
    ContextSectionId,
    ContextTaskType,
    SealedContextPackage,
)
from fictional_world.application.models.errors import ModelGatewayError
from fictional_world.application.models.messages import (
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.application.models.profiles import ModelProfile
from fictional_world.application.models.roles import ModelRole
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.infrastructure.model_gateway.capabilities import CapabilityMode
from fictional_world.infrastructure.model_gateway.openrouter import OpenRouterGateway

MIRA = seed_uuid("character/mira-talren")
DAIN = seed_uuid("character/dain-arcen")


class RecordingGateway:
    def __init__(self, delegate: OpenRouterGateway) -> None:
        self.delegate = delegate
        self.results: list[TextGenerationResult] = []
        self.errors: list[str] = []

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        try:
            result = await self.delegate.generate(request)
        except ModelGatewayError as exc:
            self.errors.append(exc.code.value)
            raise
        self.results.append(result)
        return result


def _section(section_id: ContextSectionId, content: dict[str, object]) -> ContextSection:
    return ContextSection(
        section_id=section_id,
        content=content,
        token_estimate=20,
        content_hash=f"live-{section_id.value}",
    )


def _context(snapshot_id: UUID) -> SealedContextPackage:
    return SealedContextPackage(
        package_id=uuid4(),
        observer_id=MIRA,
        phase_snapshot_id=snapshot_id,
        task_type=ContextTaskType.CHARACTER_DECISION,
        sections=(
            _section(
                ContextSectionId.STABLE_IDENTITY,
                {
                    "name": "Mira Talren",
                    "occupation": "innkeeper",
                    "voice": "warm, observant, practical",
                },
            ),
            _section(
                ContextSectionId.CURRENT_STATE,
                {
                    "location": "Cinder Lantern Inn",
                    "stamina": 80,
                    "energy": 70,
                    "stress": 10,
                },
            ),
            _section(
                ContextSectionId.CURRENT_PERCEPTION,
                {
                    "visible_character_ids": [str(DAIN)],
                    "observation": "Dain is nearby at the inn during dawn.",
                },
            ),
        ),
        token_estimate=60,
        package_hash="stage1-live-context",
        created_at=datetime.now(UTC),
    )


@pytest.mark.openrouter_live
@pytest.mark.asyncio
async def test_stage1_openrouter_produces_valid_action_proposal() -> None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    profile = ModelProfile(
        profile_id="stage1-live-character-decision-v1",
        provider_kind="openrouter",
        model_slug=os.environ.get(
            "OPENROUTER_TEXT_MODEL",
            "nvidia/nemotron-3-super-120b-a12b:free",
        ),
        role=ModelRole.CHARACTER_DECISION,
        enabled=True,
        context_limit=131_072,
        application_input_limit=8_000,
        max_output_tokens=900,
        supports_json_schema=True,
        supports_tools=False,
        supports_seed=False,
        supports_streaming=False,
        supports_embeddings=False,
        embedding_dimensions=None,
        sampling_profile_id="samp-character-decision-v1",
        privacy_class="synthetic_fiction",
        capability_probe_version="stage1-live-smoke",
    )
    gateway = OpenRouterGateway(
        api_key=api_key,
        profiles={profile.profile_id: profile},
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        timeout=httpx.Timeout(60.0),
        capability_mode=CapabilityMode.NATIVE_STRICT,
    )
    recording = RecordingGateway(gateway)
    request_id = uuid4()
    try:
        proposal = await run_decision_graph(
            DecisionGraphInput(
                context=_context(uuid4()),
                phase_label="dawn",
                decision_request_id=request_id,
                allowed_entity_ids=frozenset({MIRA, DAIN}),
                other_character_names=("Dain Arcen",),
                model_profile_id=profile.profile_id,
            ),
            recording,
        )
    finally:
        await gateway.aclose()

    assert proposal.decision_request_id == request_id
    assert proposal.actor_id == MIRA
    assert any(result.parsed == proposal for result in recording.results), {
        "errors": recording.errors,
        "outputs": [result.raw_text for result in recording.results],
    }
