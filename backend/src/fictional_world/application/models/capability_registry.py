"""Local endpoint capability registry (S4-MODEL-001 / handbook ``12`` §16.6).

Capability discovery is explicit: a local server does not automatically receive every
role merely because it can answer a chat request. Character identity is never bound
to a host or loaded model instance.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from fictional_world.application.models.roles import ModelRole

EndpointHealth = Literal["healthy", "degraded", "unhealthy", "unknown", "draining"]
LoadedState = Literal["unloaded", "loading", "loaded", "error"]
PrivacyPolicy = Literal[
    "synthetic_fiction",
    "local_private",
    "allow_openrouter_emergency",
]
CostClass = Literal["local_gpu", "local_cpu", "openrouter_free", "openrouter_paid"]
StructuredOutputMode = Literal[
    "NATIVE_STRICT",
    "NATIVE_BEST_EFFORT",
    "JSON_OBJECT_PROMPTED",
    "TEXT_REPAIR_REQUIRED",
]


class EndpointProviderKind(StrEnum):
    LOCAL_OPENAI_COMPAT = "local_openai_compat"
    OPENROUTER = "openrouter"
    FAKE = "fake"


@dataclass(frozen=True, slots=True)
class ModelEndpointCapability:
    """Advertised capability record for one reachable endpoint."""

    endpoint_id: str
    host_id: str
    provider_kind: EndpointProviderKind
    base_url: str
    model_id: str
    model_hash: str | None
    roles: tuple[ModelRole, ...]
    context_limit: int
    structured_output_mode: StructuredOutputMode
    quantization: str | None
    max_concurrency: int
    health: EndpointHealth
    loaded_state: LoadedState
    software_versions: tuple[tuple[str, str], ...]
    privacy_policy: PrivacyPolicy
    cost_class: CostClass
    supports_embeddings: bool = False
    embedding_dimensions: int | None = None
    last_probe_at: datetime | None = None
    last_error: str | None = None
    queue_depth: int = 0
    recent_error_rate: float = 0.0
    available_memory_bytes: int | None = None

    def supports_role(self, role: ModelRole | str) -> bool:
        role_value = role if isinstance(role, ModelRole) else ModelRole(role)
        return role_value in self.roles

    def is_routable(self) -> bool:
        return (
            self.health in {"healthy", "degraded"}
            and self.loaded_state == "loaded"
            and self.max_concurrency > 0
        )


@dataclass
class ModelCapabilityRegistry:
    """In-memory registry of explicit endpoint capabilities."""

    _endpoints: dict[str, ModelEndpointCapability] = field(default_factory=dict)

    def upsert(self, endpoint: ModelEndpointCapability) -> None:
        if not endpoint.roles and not endpoint.supports_embeddings:
            raise ValueError(
                f"endpoint {endpoint.endpoint_id} must advertise at least one role "
                "or embedding support"
            )
        self._endpoints[endpoint.endpoint_id] = endpoint

    def get(self, endpoint_id: str) -> ModelEndpointCapability | None:
        return self._endpoints.get(endpoint_id)

    def list_endpoints(self) -> tuple[ModelEndpointCapability, ...]:
        return tuple(self._endpoints[key] for key in sorted(self._endpoints))

    def endpoints_for_role(
        self,
        role: ModelRole | str,
        *,
        routable_only: bool = True,
        privacy_policy: PrivacyPolicy | None = None,
        min_context_limit: int | None = None,
    ) -> tuple[ModelEndpointCapability, ...]:
        role_value = role if isinstance(role, ModelRole) else ModelRole(role)
        selected: list[ModelEndpointCapability] = []
        for endpoint in self.list_endpoints():
            if not endpoint.supports_role(role_value):
                continue
            if routable_only and not endpoint.is_routable():
                continue
            if privacy_policy is not None and endpoint.privacy_policy != privacy_policy:
                continue
            if min_context_limit is not None and endpoint.context_limit < min_context_limit:
                continue
            selected.append(endpoint)
        return tuple(selected)

    def mark_health(
        self,
        endpoint_id: str,
        *,
        health: EndpointHealth,
        loaded_state: LoadedState | None = None,
        last_error: str | None = None,
        queue_depth: int | None = None,
        recent_error_rate: float | None = None,
    ) -> ModelEndpointCapability:
        current = self._endpoints.get(endpoint_id)
        if current is None:
            raise KeyError(endpoint_id)
        updated = replace(
            current,
            health=health,
            loaded_state=loaded_state if loaded_state is not None else current.loaded_state,
            last_error=last_error,
            queue_depth=queue_depth if queue_depth is not None else current.queue_depth,
            recent_error_rate=(
                recent_error_rate
                if recent_error_rate is not None
                else current.recent_error_rate
            ),
            last_probe_at=datetime.now(tz=UTC),
        )
        self._endpoints[endpoint_id] = updated
        return updated

    def to_diagnostic_dict(self) -> dict[str, object]:
        generated = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return {
            "generated_at": generated,
            "endpoints": [
                {
                    "endpoint_id": ep.endpoint_id,
                    "host_id": ep.host_id,
                    "provider_kind": ep.provider_kind.value,
                    "base_url": ep.base_url,
                    "model_id": ep.model_id,
                    "model_hash": ep.model_hash,
                    "roles": [role.value for role in ep.roles],
                    "context_limit": ep.context_limit,
                    "structured_output_mode": ep.structured_output_mode,
                    "quantization": ep.quantization,
                    "max_concurrency": ep.max_concurrency,
                    "health": ep.health,
                    "loaded_state": ep.loaded_state,
                    "software_versions": dict(ep.software_versions),
                    "privacy_policy": ep.privacy_policy,
                    "cost_class": ep.cost_class,
                    "supports_embeddings": ep.supports_embeddings,
                    "embedding_dimensions": ep.embedding_dimensions,
                }
                for ep in self.list_endpoints()
            ],
        }
