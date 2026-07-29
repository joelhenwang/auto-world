"""Minimal fake model gateway for tests — bridges to S0-MODEL-002 adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Protocol

from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.infrastructure.model_gateway.fake import (
    FakeModelGatewayAdapter,
    FakeScriptKind,
)


class FakeResponseKind(StrEnum):
    VALID = "valid"
    MALFORMED_JSON = "malformed_json"
    SCHEMA_INVALID = "schema_invalid"
    SEMANTIC_INVALID = "semantic_invalid"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNSUPPORTED = "unsupported"
    LATE = "late"
    CANCELLED = "cancelled"
    EMBED_OK = "embed_ok"
    EMBED_DIM_MISMATCH = "embed_dim_mismatch"


@dataclass(frozen=True, slots=True)
class FakeTextRequest:
    role: str
    request_id: str
    prompt: str


@dataclass(frozen=True, slots=True)
class FakeTextResult:
    kind: FakeResponseKind
    payload: str | None = None
    retry_after_seconds: float | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class FakeEmbedRequest:
    request_id: str
    texts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FakeEmbedResult:
    kind: FakeResponseKind
    vectors: tuple[tuple[float, ...], ...] = ()
    dimensions: int = 2048
    error_message: str | None = None


class ModelGatewayPort(Protocol):
    """Legacy harness port; prefer TextModelGateway / EmbeddingGateway."""

    async def generate_text(self, request: FakeTextRequest) -> FakeTextResult: ...

    async def embed(self, request: FakeEmbedRequest) -> FakeEmbedResult: ...


_KIND_MAP: dict[FakeResponseKind, FakeScriptKind] = {
    FakeResponseKind.VALID: FakeScriptKind.VALID,
    FakeResponseKind.MALFORMED_JSON: FakeScriptKind.MALFORMED_JSON,
    FakeResponseKind.SCHEMA_INVALID: FakeScriptKind.SCHEMA_INVALID,
    FakeResponseKind.SEMANTIC_INVALID: FakeScriptKind.SEMANTIC_INVALID,
    FakeResponseKind.TIMEOUT: FakeScriptKind.TIMEOUT,
    FakeResponseKind.RATE_LIMITED: FakeScriptKind.RATE_LIMITED,
    FakeResponseKind.UNSUPPORTED: FakeScriptKind.UNSUPPORTED,
    FakeResponseKind.LATE: FakeScriptKind.VALID,
    FakeResponseKind.CANCELLED: FakeScriptKind.CANCELLED,
    FakeResponseKind.EMBED_OK: FakeScriptKind.EMBED_OK,
    FakeResponseKind.EMBED_DIM_MISMATCH: FakeScriptKind.EMBED_DIM_MISMATCH,
}


@dataclass
class FakeModelGateway:
    """Harness wrapper retaining generate_text/embed shapes used by S0-QA-001 tests."""

    scripts: dict[str, FakeResponseKind] = field(default_factory=dict)
    default_kind: FakeResponseKind = FakeResponseKind.VALID
    calls: list[dict[str, Any]] = field(default_factory=list)
    valid_payload: str = '{"ok": true}'
    embed_dimensions: int = 2048
    _adapter: FakeModelGatewayAdapter = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._adapter = FakeModelGatewayAdapter(
            default_kind=_KIND_MAP[self.default_kind],
            valid_payload=self.valid_payload,
            embed_dimensions=self.embed_dimensions,
        )
        for key, kind in self.scripts.items():
            self._adapter.script(key=key, kind=_KIND_MAP[kind])

    def script(self, *, key: str, kind: FakeResponseKind) -> None:
        self.scripts[key] = kind
        self._adapter.script(key=key, kind=_KIND_MAP[kind])

    async def generate_text(self, request: FakeTextRequest) -> FakeTextResult:
        kind = (
            self.scripts.get(request.request_id)
            or self.scripts.get(request.role)
            or self.default_kind
        )
        self.calls.append({"type": "text", "role": request.role, "request_id": request.request_id})
        if kind is FakeResponseKind.VALID or kind is FakeResponseKind.LATE:
            return FakeTextResult(kind=kind, payload=self.valid_payload)
        if kind is FakeResponseKind.MALFORMED_JSON:
            return FakeTextResult(kind=kind, payload="{not-json")
        if kind is FakeResponseKind.SCHEMA_INVALID:
            return FakeTextResult(kind=kind, payload="{}")
        if kind is FakeResponseKind.SEMANTIC_INVALID:
            return FakeTextResult(kind=kind, payload='{"ok": false, "reason": "semantic"}')
        if kind is FakeResponseKind.TIMEOUT:
            return FakeTextResult(kind=kind, error_message="timeout")
        if kind is FakeResponseKind.RATE_LIMITED:
            return FakeTextResult(kind=kind, retry_after_seconds=1.0, error_message="429")
        if kind is FakeResponseKind.UNSUPPORTED:
            return FakeTextResult(kind=kind, error_message="unsupported parameter")
        if kind is FakeResponseKind.CANCELLED:
            return FakeTextResult(kind=kind, error_message="cancelled")
        return FakeTextResult(kind=kind, error_message=f"unhandled kind {kind}")

    async def embed(self, request: FakeEmbedRequest) -> FakeEmbedResult:
        kind = (
            self.scripts.get(request.request_id) or self.scripts.get("embed") or self.default_kind
        )
        self.calls.append(
            {"type": "embed", "request_id": request.request_id, "n": len(request.texts)}
        )
        if kind is FakeResponseKind.EMBED_DIM_MISMATCH:
            bad_dim = 16
            vectors = tuple(tuple(0.0 for _ in range(bad_dim)) for _ in request.texts)
            return FakeEmbedResult(
                kind=kind,
                vectors=vectors,
                dimensions=bad_dim,
                error_message="embedding dimension mismatch",
            )
        vectors = tuple(
            tuple(float(i % 7) for i in range(self.embed_dimensions)) for _ in request.texts
        )
        return FakeEmbedResult(
            kind=FakeResponseKind.EMBED_OK,
            vectors=vectors,
            dimensions=self.embed_dimensions,
        )

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        """Protocol-compatible path used by application code."""

        return await self._adapter.generate(request)

    async def embed_gateway(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Protocol EmbeddingGateway path (distinct from harness FakeEmbedRequest embed)."""

        return await self._adapter.embed(request)


ProviderMode = Literal["fake"]
