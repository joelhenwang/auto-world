"""Application model-gateway contracts (S0-MODEL-001)."""

from fictional_world.application.models.capability_registry import (
    EndpointHealth,
    EndpointProviderKind,
    LoadedState,
    ModelCapabilityRegistry,
    ModelEndpointCapability,
    PrivacyPolicy,
)
from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    ModelMessage,
    ProviderRoutingOptions,
    SamplingOptions,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.application.models.profiles import ModelProfile, ModelProfileRegistry
from fictional_world.application.models.protocols import EmbeddingGateway, TextModelGateway
from fictional_world.application.models.roles import ModelRole
from fictional_world.application.models.routing import HealthAwareModelGateway, spread_replicas
from fictional_world.application.models.sampling import DEFAULT_SAMPLING, sampling_for_role

__all__ = [
    "DEFAULT_SAMPLING",
    "EmbeddingGateway",
    "EmbeddingRequest",
    "EmbeddingResult",
    "EndpointHealth",
    "EndpointProviderKind",
    "HealthAwareModelGateway",
    "LoadedState",
    "ModelCapabilityRegistry",
    "ModelEndpointCapability",
    "ModelGatewayError",
    "ModelGatewayErrorCode",
    "ModelMessage",
    "ModelProfile",
    "ModelProfileRegistry",
    "ModelRole",
    "PrivacyPolicy",
    "ProviderRoutingOptions",
    "SamplingOptions",
    "TextGenerationRequest",
    "TextGenerationResult",
    "TextModelGateway",
    "sampling_for_role",
    "spread_replicas",
]
