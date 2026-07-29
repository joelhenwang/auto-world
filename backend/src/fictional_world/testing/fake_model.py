"""Minimal fake model gateway for tests (refined by S0-MODEL-001/002)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal, Protocol


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
    """Minimal port used by the Stage 0 fake; S0-MODEL-001 owns the real protocol."""

    async def generate_text(self, request: FakeTextRequest) -> FakeTextResult: ...

    async def embed(self, request: FakeEmbedRequest) -> FakeEmbedResult: ...


@dataclass
class FakeModelGateway:
    """Scripted gateway keyed by role and/or request_id."""

    scripts: dict[str, FakeResponseKind] = field(default_factory=dict)
    default_kind: FakeResponseKind = FakeResponseKind.VALID
    calls: list[dict[str, Any]] = field(default_factory=list)
    valid_payload: str = '{"ok": true}'
    embed_dimensions: int = 2048

    def script(self, *, key: str, kind: FakeResponseKind) -> None:
        self.scripts[key] = kind

    def _resolve(self, *, role: str, request_id: str) -> FakeResponseKind:
        return self.scripts.get(request_id) or self.scripts.get(role) or self.default_kind

    async def generate_text(self, request: FakeTextRequest) -> FakeTextResult:
        kind = self._resolve(role=request.role, request_id=request.request_id)
        self.calls.append({"type": "text", "role": request.role, "request_id": request.request_id})
        if kind is FakeResponseKind.VALID:
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
        if kind is FakeResponseKind.LATE:
            return FakeTextResult(kind=kind, payload=self.valid_payload, error_message="late")
        if kind is FakeResponseKind.CANCELLED:
            return FakeTextResult(kind=kind, error_message="cancelled")
        return FakeTextResult(kind=kind, error_message=f"unhandled kind {kind}")

    async def embed(self, request: FakeEmbedRequest) -> FakeEmbedResult:
        kind = self._resolve(role="embed", request_id=request.request_id)
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
        # Default / EMBED_OK
        vectors = tuple(
            tuple(float(i % 7) for i in range(self.embed_dimensions)) for _ in request.texts
        )
        return FakeEmbedResult(
            kind=FakeResponseKind.EMBED_OK,
            vectors=vectors,
            dimensions=self.embed_dimensions,
        )


ProviderMode = Literal["fake"]
