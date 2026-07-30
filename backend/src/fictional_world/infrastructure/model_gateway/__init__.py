"""Model gateway adapters (S0-MODEL-002)."""

from fictional_world.infrastructure.model_gateway.capabilities import (
    CapabilityMode,
    CapabilityProbeResult,
    CapabilityProbeStub,
)
from fictional_world.infrastructure.model_gateway.errors import (
    map_http_error,
    map_openrouter_error_body,
)
from fictional_world.infrastructure.model_gateway.fake import FakeModelGatewayAdapter
from fictional_world.infrastructure.model_gateway.local import LocalOpenAICompatibleGateway
from fictional_world.infrastructure.model_gateway.openrouter import OpenRouterGateway

__all__ = [
    "CapabilityMode",
    "CapabilityProbeResult",
    "CapabilityProbeStub",
    "FakeModelGatewayAdapter",
    "LocalOpenAICompatibleGateway",
    "OpenRouterGateway",
    "map_http_error",
    "map_openrouter_error_body",
]
