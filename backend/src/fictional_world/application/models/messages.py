"""Request/result DTOs for provider-neutral model gateways."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class SamplingOptions:
    temperature: float
    top_p: float
    max_output_tokens: int
    seed: int | None = None
    stop: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProviderRoutingOptions:
    require_parameters: bool = True
    allow_fallbacks: bool = True
    data_collection: str | None = None


@dataclass(frozen=True, slots=True)
class TextGenerationRequest:
    request_id: str
    role: str
    model_profile_id: str
    messages: tuple[ModelMessage, ...]
    output_schema: type[BaseModel] | None
    sampling: SamplingOptions
    routing: ProviderRoutingOptions
    metadata: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class TextGenerationResult:
    provider_request_id: str | None
    resolved_model: str
    provider_name: str | None
    raw_text: str
    parsed: BaseModel | None
    input_tokens: int | None
    output_tokens: int | None
    finish_reason: str | None
    capability_mode: str
    latency_ms: int


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    request_id: str
    model_profile_id: str
    texts: tuple[str, ...]
    input_type: Literal["query", "passage"]
    dimensions: int | None
    metadata: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    vectors: tuple[tuple[float, ...], ...]
    resolved_model: str
    dimensions: int
    input_tokens: int | None
    latency_ms: int
