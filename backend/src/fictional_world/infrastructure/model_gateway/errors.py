"""Map provider HTTP failures onto ModelGatewayError (handbook ``12`` §12)."""

from __future__ import annotations

from typing import Any, cast

from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode


def map_http_error(
    status_code: int,
    *,
    message: str,
    provider_code: str | None = None,
    request_id: str | None = None,
    retry_after_seconds: float | None = None,
) -> ModelGatewayError:
    """Normalize HTTP status codes into the Stage 0 error taxonomy."""

    if status_code in {401, 403}:
        return ModelGatewayError(
            ModelGatewayErrorCode.AUTHENTICATION_ERROR,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=False,
        )
    if status_code == 402:
        return ModelGatewayError(
            ModelGatewayErrorCode.CREDIT_LIMIT_ERROR,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=False,
        )
    if status_code == 429:
        return ModelGatewayError(
            ModelGatewayErrorCode.RATE_LIMIT_ERROR,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=True,
            retry_after_seconds=retry_after_seconds,
        )
    if status_code == 404:
        return ModelGatewayError(
            ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=False,
        )
    if status_code == 400 and provider_code in {"unsupported_parameter", "invalid_request"}:
        return ModelGatewayError(
            ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=False,
        )
    if status_code == 400 and "content" in message.lower():
        return ModelGatewayError(
            ModelGatewayErrorCode.CONTENT_REJECTED,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=False,
        )
    if status_code in {502, 503, 504}:
        return ModelGatewayError(
            ModelGatewayErrorCode.PROVIDER_CAPACITY_ERROR,
            message,
            provider_code=provider_code,
            request_id=request_id,
            retryable=True,
            retry_after_seconds=retry_after_seconds,
        )
    return ModelGatewayError(
        ModelGatewayErrorCode.UNKNOWN_PROVIDER_ERROR,
        message,
        provider_code=provider_code,
        request_id=request_id,
        retryable=status_code >= 500,
    )


def map_openrouter_error_body(
    status_code: int,
    body: dict[str, Any] | None,
    *,
    request_id: str | None = None,
    retry_after_seconds: float | None = None,
) -> ModelGatewayError:
    """Parse an OpenRouter JSON error payload when present."""

    error_obj: dict[str, Any] = {}
    if isinstance(body, dict):
        raw = body.get("error")
        if isinstance(raw, dict):
            error_obj = cast(dict[str, Any], raw)
        elif isinstance(raw, str):
            error_obj = {"message": raw}
    message = str(error_obj.get("message") or body or f"HTTP {status_code}")
    provider_code = None
    if "code" in error_obj:
        provider_code = str(error_obj["code"])
    elif "type" in error_obj:
        provider_code = str(error_obj["type"])
    return map_http_error(
        status_code,
        message=message,
        provider_code=provider_code,
        request_id=request_id,
        retry_after_seconds=retry_after_seconds,
    )
