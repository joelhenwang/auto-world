"""Normalized model-gateway error taxonomy (handbook ``12`` §12)."""

from __future__ import annotations

from enum import StrEnum


class ModelGatewayErrorCode(StrEnum):
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    CREDIT_LIMIT_ERROR = "CREDIT_LIMIT_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    PROVIDER_CAPACITY_ERROR = "PROVIDER_CAPACITY_ERROR"
    UNSUPPORTED_PARAMETER_ERROR = "UNSUPPORTED_PARAMETER_ERROR"
    MODEL_NOT_AVAILABLE = "MODEL_NOT_AVAILABLE"
    CONTENT_REJECTED = "CONTENT_REJECTED"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    SEMANTIC_VALIDATION_ERROR = "SEMANTIC_VALIDATION_ERROR"
    EMBEDDING_DIMENSION_ERROR = "EMBEDDING_DIMENSION_ERROR"
    CANCELLED = "CANCELLED"
    UNKNOWN_PROVIDER_ERROR = "UNKNOWN_PROVIDER_ERROR"


class ModelGatewayError(Exception):
    """Provider-neutral gateway failure."""

    def __init__(
        self,
        code: ModelGatewayErrorCode,
        message: str,
        *,
        provider_code: str | None = None,
        request_id: str | None = None,
        retryable: bool = False,
        retry_after_seconds: float | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.provider_code = provider_code
        self.request_id = request_id
        self.retryable = retryable
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"{code}: {message}")
