"""Scripted fake implementing TextModelGateway / EmbeddingGateway."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.infrastructure.model_gateway.capabilities import CapabilityMode


class FakeScriptKind(StrEnum):
    VALID = "valid"
    MALFORMED_JSON = "malformed_json"
    SCHEMA_INVALID = "schema_invalid"
    SEMANTIC_INVALID = "semantic_invalid"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNSUPPORTED = "unsupported"
    CANCELLED = "cancelled"
    EMBED_OK = "embed_ok"
    EMBED_DIM_MISMATCH = "embed_dim_mismatch"


@dataclass
class FakeModelGatewayAdapter:
    """Deterministic adapter keyed by request_id or role."""

    scripts: dict[str, FakeScriptKind] = field(default_factory=dict)
    corpus_scripts: dict[str, str] = field(default_factory=dict)
    corpus_dir: Path | None = None
    default_kind: FakeScriptKind = FakeScriptKind.VALID
    valid_payload: str = '{"ok": true}'
    embed_dimensions: int = 2048
    capability_mode: str = CapabilityMode.JSON_OBJECT_PROMPTED.value
    resolved_model: str = "fake/stage0"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def script(self, *, key: str, kind: FakeScriptKind) -> None:
        self.scripts[key] = kind

    def script_corpus(self, *, key: str, filename: str) -> None:
        """Select a corpus file for a request-ID or role script key."""

        self.corpus_scripts[key] = filename

    def _resolve(self, *, role: str, request_id: str) -> FakeScriptKind:
        return self.scripts.get(request_id) or self.scripts.get(role) or self.default_kind

    def _resolve_corpus(self, *, role: str, request_id: str) -> str | None:
        return self.corpus_scripts.get(request_id) or self.corpus_scripts.get(role)

    def _load_corpus(self, filename: str) -> str:
        if self.corpus_dir is None:
            raise ValueError("corpus_dir is required for corpus scripts")
        root = self.corpus_dir.resolve()
        corpus_path = (root / filename).resolve()
        if not corpus_path.is_relative_to(root):
            raise ValueError("corpus filename escapes corpus_dir")
        return corpus_path.read_text(encoding="utf-8")

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        kind = self._resolve(role=request.role, request_id=request.request_id)
        corpus_filename = self._resolve_corpus(
            role=request.role,
            request_id=request.request_id,
        )
        self.calls.append(
            {
                "type": "text",
                "role": request.role,
                "request_id": request.request_id,
                "kind": kind,
                "corpus": corpus_filename,
            }
        )
        started = time.perf_counter()
        if kind is FakeScriptKind.TIMEOUT:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_TIMEOUT,
                "fake timeout",
                request_id=request.request_id,
                retryable=True,
            )
        if kind is FakeScriptKind.RATE_LIMITED:
            raise ModelGatewayError(
                ModelGatewayErrorCode.RATE_LIMIT_ERROR,
                "fake 429",
                request_id=request.request_id,
                retryable=True,
                retry_after_seconds=1.0,
            )
        if kind is FakeScriptKind.UNSUPPORTED:
            raise ModelGatewayError(
                ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR,
                "fake unsupported parameter",
                request_id=request.request_id,
                retryable=False,
            )
        if kind is FakeScriptKind.CANCELLED:
            raise ModelGatewayError(
                ModelGatewayErrorCode.CANCELLED,
                "fake cancelled",
                request_id=request.request_id,
                retryable=False,
            )

        raw = self.valid_payload
        if corpus_filename is not None:
            try:
                raw = self._load_corpus(corpus_filename)
            except (OSError, ValueError) as exc:
                raise ModelGatewayError(
                    ModelGatewayErrorCode.MALFORMED_RESPONSE,
                    f"fake corpus unavailable: {corpus_filename}",
                    request_id=request.request_id,
                    retryable=False,
                ) from exc
        if kind is FakeScriptKind.MALFORMED_JSON:
            raw = "{not-json"
        elif kind is FakeScriptKind.SCHEMA_INVALID:
            raw = "{}"
        elif kind is FakeScriptKind.SEMANTIC_INVALID:
            raw = '{"ok": false, "reason": "semantic"}'

        if kind is FakeScriptKind.SEMANTIC_INVALID:
            raise ModelGatewayError(
                ModelGatewayErrorCode.SEMANTIC_VALIDATION_ERROR,
                "semantic invalid",
                request_id=request.request_id,
                retryable=True,
            )

        parsed: BaseModel | None = None
        if request.output_schema is not None:
            try:
                raw_object: object = json.loads(raw)
            except JSONDecodeError as exc:
                raise ModelGatewayError(
                    ModelGatewayErrorCode.MALFORMED_RESPONSE,
                    "malformed JSON",
                    request_id=request.request_id,
                    retryable=True,
                ) from exc
            try:
                parsed = request.output_schema.model_validate(raw_object)
            except ValidationError as exc:
                raise ModelGatewayError(
                    ModelGatewayErrorCode.SCHEMA_VALIDATION_ERROR,
                    str(exc),
                    request_id=request.request_id,
                    retryable=True,
                ) from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        return TextGenerationResult(
            provider_request_id=f"fake-{request.request_id}",
            resolved_model=self.resolved_model,
            provider_name="fake",
            raw_text=raw,
            parsed=parsed,
            input_tokens=None,
            output_tokens=None,
            finish_reason="stop",
            capability_mode=self.capability_mode,
            latency_ms=latency_ms,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        kind = self._resolve(role="embed", request_id=request.request_id)
        self.calls.append(
            {
                "type": "embed",
                "request_id": request.request_id,
                "n": len(request.texts),
                "kind": kind,
            }
        )
        started = time.perf_counter()
        if kind is FakeScriptKind.RATE_LIMITED:
            raise ModelGatewayError(
                ModelGatewayErrorCode.RATE_LIMIT_ERROR,
                "fake embed 429",
                request_id=request.request_id,
                retryable=True,
                retry_after_seconds=1.0,
            )
        if kind is FakeScriptKind.TIMEOUT:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_TIMEOUT,
                "fake embed timeout",
                request_id=request.request_id,
                retryable=True,
            )
        dims = self.embed_dimensions
        if kind is FakeScriptKind.EMBED_DIM_MISMATCH:
            dims = 16
            raise ModelGatewayError(
                ModelGatewayErrorCode.EMBEDDING_DIMENSION_ERROR,
                f"expected {self.embed_dimensions}, got {dims}",
                request_id=request.request_id,
                retryable=False,
            )
        expected = request.dimensions or self.embed_dimensions
        vectors = tuple(tuple(float(i % 7) for i in range(expected)) for _ in request.texts)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return EmbeddingResult(
            vectors=vectors,
            resolved_model=self.resolved_model,
            dimensions=expected,
            input_tokens=None,
            latency_ms=latency_ms,
        )
