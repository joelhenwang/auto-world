"""Shared bounded model-invocation helpers for Stage 1 agent pipelines."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import replace

from pydantic import BaseModel, ValidationError

from fictional_world.application.context.types import ContextSectionId, SealedContextPackage
from fictional_world.application.models.errors import ModelGatewayError
from fictional_world.application.models.messages import ModelMessage, TextGenerationRequest
from fictional_world.application.models.protocols import TextModelGateway


def json_text(value: object) -> str:
    """Serialize sealed prompt data deterministically."""

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def context_sections(package: SealedContextPackage) -> Mapping[ContextSectionId, object]:
    """Index a sealed package without introducing data outside that package."""

    return {section.section_id: section.content for section in package.sections}


async def invoke_with_one_regeneration[OutputT: BaseModel](
    *,
    gateway: TextModelGateway,
    request: TextGenerationRequest,
    output_type: type[OutputT],
    domain_validator: Callable[[OutputT], None],
) -> OutputT | None:
    """Invoke, validate, repair once, then return ``None`` for caller fallback."""

    current = request
    for attempt in range(2):
        try:
            result = await gateway.generate(current)
            parsed = (
                result.parsed
                if isinstance(result.parsed, output_type)
                else output_type.model_validate_json(result.raw_text)
            )
            domain_validator(parsed)
            return parsed
        except (ModelGatewayError, ValidationError, ValueError) as exc:
            if attempt == 1:
                return None
            current = replace(
                request,
                request_id=f"{request.request_id}:regen",
                messages=(
                    *request.messages,
                    ModelMessage(
                        role="user",
                        content=(
                            "The prior response was invalid. Regenerate exactly one JSON object "
                            "matching the schema and supplied IDs. Error category: "
                            f"{type(exc).__name__}."
                        ),
                    ),
                ),
                metadata={**request.metadata, "regeneration": "1"},
            )
    return None
