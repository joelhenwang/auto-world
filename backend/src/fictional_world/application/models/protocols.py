"""Provider-neutral gateway protocols (handbook ``12`` §4)."""

from __future__ import annotations

from typing import Protocol

from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)


class TextModelGateway(Protocol):
    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult: ...


class EmbeddingGateway(Protocol):
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...
