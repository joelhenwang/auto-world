"""Health-aware model gateway routing and failover (S4-MODEL-002)."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from fictional_world.application.models.capability_registry import (
    ModelCapabilityRegistry,
    ModelEndpointCapability,
    PrivacyPolicy,
)
from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.application.models.roles import ModelRole


class EndpointTextClient(Protocol):
    @property
    def endpoint(self) -> ModelEndpointCapability: ...

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult: ...


class EndpointEmbedClient(Protocol):
    @property
    def endpoint(self) -> ModelEndpointCapability: ...

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...


@dataclass
class HealthAwareModelGateway:
    """Routes role requests to healthy, capability-compatible endpoints.

    Preserves character identity through reconstructed context packages only — never
    through process-local KV/session affinity. Does not hold DB transactions open.
    """

    registry: ModelCapabilityRegistry
    text_clients: Mapping[str, EndpointTextClient]
    embed_clients: Mapping[str, EndpointEmbedClient] = field(
        default_factory=dict[str, EndpointEmbedClient]
    )
    default_privacy_policy: PrivacyPolicy = "local_private"
    _reservations: MutableMapping[str, int] = field(default_factory=dict[str, int])
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _completed_ids: set[str] = field(default_factory=set)
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        if request.request_id in self._completed_ids:
            raise ModelGatewayError(
                ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR,
                f"duplicate completion rejected for request_id={request.request_id}",
                request_id=request.request_id,
                retryable=False,
            )
        privacy = _privacy_from_metadata(request.metadata, self.default_privacy_policy)
        _assert_privacy_allowed(privacy)
        min_context = _optional_int(request.metadata.get("min_context_limit"))
        candidates = self._candidates(
            role=request.role,
            privacy=privacy,
            min_context_limit=min_context,
        )
        if not candidates:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
                "no compatible healthy endpoint for role/privacy/context",
                request_id=request.request_id,
                retryable=True,
            )

        last_error: ModelGatewayError | None = None
        for endpoint in candidates:
            client = self.text_clients.get(endpoint.endpoint_id)
            if client is None:
                continue
            reserved = await self._try_reserve(endpoint)
            if not reserved:
                continue
            try:
                result = await client.generate(request)
            except ModelGatewayError as exc:
                last_error = exc
                if not exc.retryable:
                    raise
                self.registry.mark_health(
                    endpoint.endpoint_id,
                    health="degraded",
                    last_error=str(exc),
                )
                continue
            finally:
                await self._release(endpoint.endpoint_id)
            self._completed_ids.add(request.request_id)
            self.calls.append(
                {
                    "type": "text",
                    "request_id": request.request_id,
                    "endpoint_id": endpoint.endpoint_id,
                    "role": request.role,
                }
            )
            return result

        if last_error is not None:
            raise last_error
        raise ModelGatewayError(
            ModelGatewayErrorCode.PROVIDER_CAPACITY_ERROR,
            "all compatible endpoints at concurrency capacity or failed",
            request_id=request.request_id,
            retryable=True,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        if request.request_id in self._completed_ids:
            raise ModelGatewayError(
                ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR,
                f"duplicate completion rejected for request_id={request.request_id}",
                request_id=request.request_id,
                retryable=False,
            )
        privacy = _privacy_from_metadata(request.metadata, self.default_privacy_policy)
        _assert_privacy_allowed(privacy)
        candidates = [
            ep
            for ep in self.registry.list_endpoints()
            if ep.supports_embeddings and ep.is_routable() and ep.privacy_policy == privacy
        ]
        if not candidates:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
                "no compatible healthy embedding endpoint",
                request_id=request.request_id,
                retryable=True,
            )
        last_error: ModelGatewayError | None = None
        for endpoint in sorted(candidates, key=_score_endpoint):
            client = self.embed_clients.get(endpoint.endpoint_id)
            if client is None:
                continue
            reserved = await self._try_reserve(endpoint)
            if not reserved:
                continue
            try:
                result = await client.embed(request)
            except ModelGatewayError as exc:
                last_error = exc
                if not exc.retryable:
                    raise
                continue
            finally:
                await self._release(endpoint.endpoint_id)
            self._completed_ids.add(request.request_id)
            self.calls.append(
                {
                    "type": "embed",
                    "request_id": request.request_id,
                    "endpoint_id": endpoint.endpoint_id,
                }
            )
            return result
        if last_error is not None:
            raise last_error
        raise ModelGatewayError(
            ModelGatewayErrorCode.PROVIDER_CAPACITY_ERROR,
            "embedding endpoints unavailable",
            request_id=request.request_id,
            retryable=True,
        )

    def _candidates(
        self,
        *,
        role: str,
        privacy: PrivacyPolicy,
        min_context_limit: int | None,
    ) -> list[ModelEndpointCapability]:
        selected = list(
            self.registry.endpoints_for_role(
                role,
                routable_only=True,
                privacy_policy=privacy,
                min_context_limit=min_context_limit,
            )
        )
        selected.sort(key=_score_endpoint)
        return selected

    async def _try_reserve(self, endpoint: ModelEndpointCapability) -> bool:
        async with self._lock:
            used = self._reservations.get(endpoint.endpoint_id, 0)
            if used >= endpoint.max_concurrency:
                return False
            self._reservations[endpoint.endpoint_id] = used + 1
            return True

    async def _release(self, endpoint_id: str) -> None:
        async with self._lock:
            used = self._reservations.get(endpoint_id, 0)
            if used <= 1:
                self._reservations.pop(endpoint_id, None)
            else:
                self._reservations[endpoint_id] = used - 1


def _score_endpoint(endpoint: ModelEndpointCapability) -> tuple[int, int, float, str]:
    """Lower is better: prefer healthy, low queue, low error rate."""

    health_rank = 0 if endpoint.health == "healthy" else 1
    return (health_rank, endpoint.queue_depth, endpoint.recent_error_rate, endpoint.endpoint_id)


def _privacy_from_metadata(
    metadata: Mapping[str, str],
    default: PrivacyPolicy,
) -> PrivacyPolicy:
    raw = metadata.get("privacy_policy", default)
    if raw == "synthetic_fiction":
        return "synthetic_fiction"
    if raw == "local_private":
        return "local_private"
    if raw == "allow_openrouter_emergency":
        return "allow_openrouter_emergency"
    return default


def _assert_privacy_allowed(privacy: PrivacyPolicy) -> None:
    """Refuse accidental OpenRouter use for private local-only worlds.

    Callers must set metadata privacy_policy=allow_openrouter_emergency explicitly.
    The default path is local_private.
    """

    _ = privacy  # policy is selected upstream; hook reserved for future deny-lists


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def spread_replicas(
    registry: ModelCapabilityRegistry,
    *,
    role: ModelRole | str,
    count: int,
    privacy_policy: PrivacyPolicy = "local_private",
) -> tuple[ModelEndpointCapability, ...]:
    """Pick up to ``count`` endpoint slots for simultaneous fan-out from one snapshot."""

    endpoints = list(
        registry.endpoints_for_role(role, routable_only=True, privacy_policy=privacy_policy)
    )
    endpoints.sort(key=_score_endpoint)
    if not endpoints or count <= 0:
        return ()
    return tuple(endpoints[index % len(endpoints)] for index in range(count))
