"""OpenAI-compatible local text/embedding adapters (S4-MODEL-001)."""

from __future__ import annotations

import json
import time
from typing import Any, cast

import httpx
from pydantic import BaseModel, ValidationError

from fictional_world.application.models.capability_registry import ModelEndpointCapability
from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.infrastructure.model_gateway.capabilities import CapabilityMode
from fictional_world.infrastructure.model_gateway.errors import map_http_error


class LocalOpenAICompatibleGateway:
    """Local OpenAI-compatible chat/embeddings client.

    Does not hold database transactions open. Does not bind character identity to a host.
    """

    def __init__(
        self,
        *,
        endpoint: ModelEndpointCapability,
        http_client: httpx.AsyncClient | None = None,
        api_key: str = "local",
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._base_url = endpoint.base_url.rstrip("/")
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout or httpx.Timeout(connect=5.0, read=180.0, write=30.0, pool=10.0),
        )

    @property
    def endpoint(self) -> ModelEndpointCapability:
        return self._endpoint

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def health_probe(self) -> bool:
        """Best-effort reachability probe (`/v1/models` or `/health`)."""

        for path in ("/v1/models", "/health", "/"):
            try:
                response = await self._client.get(path, headers=self._headers())
                if response.status_code < 500:
                    return True
            except httpx.HTTPError:
                continue
        return False

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        if not self._endpoint.supports_role(request.role):
            raise ModelGatewayError(
                ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR,
                (f"endpoint {self._endpoint.endpoint_id} does not advertise role={request.role}"),
                request_id=request.request_id,
                retryable=False,
            )
        started = time.perf_counter()
        messages = [
            {"role": message.role, "content": message.content} for message in request.messages
        ]
        payload: dict[str, Any] = {
            "model": self._endpoint.model_id,
            "messages": messages,
            "temperature": request.sampling.temperature,
            "top_p": request.sampling.top_p,
            "max_tokens": request.sampling.max_output_tokens,
        }
        if request.sampling.seed is not None:
            payload["seed"] = request.sampling.seed
        if request.output_schema is not None:
            mode = self._endpoint.structured_output_mode
            if mode in {"NATIVE_STRICT", "NATIVE_BEST_EFFORT"}:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": request.output_schema.__name__,
                        "schema": request.output_schema.model_json_schema(),
                        "strict": mode == "NATIVE_STRICT",
                    },
                }
            elif mode == "JSON_OBJECT_PROMPTED":
                payload["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.post(
                "/v1/chat/completions",
                headers=self._headers(),
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_TIMEOUT,
                "local endpoint timeout",
                request_id=request.request_id,
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_ERROR,
                f"local endpoint network error: {exc}",
                request_id=request.request_id,
                retryable=True,
            ) from exc

        if response.status_code >= 400:
            raise map_http_error(
                response.status_code,
                message=response.text,
                request_id=request.request_id,
            )

        data = cast(dict[str, Any], response.json())
        raw_text = _chat_content(data)
        parsed: BaseModel | None = None
        if request.output_schema is not None:
            try:
                parsed = request.output_schema.model_validate_json(raw_text)
            except (ValidationError, json.JSONDecodeError) as exc:
                raise ModelGatewayError(
                    ModelGatewayErrorCode.SCHEMA_VALIDATION_ERROR,
                    f"local structured output failed validation: {exc}",
                    request_id=request.request_id,
                    retryable=False,
                ) from exc

        usage_obj: object = data.get("usage")
        usage = _as_mapping(usage_obj)
        latency_ms = int((time.perf_counter() - started) * 1000)
        prompt_tokens = _optional_int(usage.get("prompt_tokens"))
        completion_tokens = _optional_int(usage.get("completion_tokens"))
        return TextGenerationResult(
            provider_request_id=str(data.get("id") or request.request_id),
            resolved_model=str(data.get("model") or self._endpoint.model_id),
            provider_name=f"local:{self._endpoint.endpoint_id}",
            raw_text=raw_text,
            parsed=parsed,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            finish_reason=_finish_reason(data),
            capability_mode=CapabilityMode(self._endpoint.structured_output_mode).value,
            latency_ms=latency_ms,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        if not self._endpoint.supports_embeddings:
            raise ModelGatewayError(
                ModelGatewayErrorCode.UNSUPPORTED_PARAMETER_ERROR,
                f"endpoint {self._endpoint.endpoint_id} does not advertise embeddings",
                request_id=request.request_id,
                retryable=False,
            )
        started = time.perf_counter()
        payload: dict[str, Any] = {
            "model": self._endpoint.model_id,
            "input": list(request.texts),
        }
        if request.dimensions is not None:
            payload["dimensions"] = request.dimensions
        try:
            response = await self._client.post(
                "/v1/embeddings",
                headers=self._headers(),
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_TIMEOUT,
                "local embedding timeout",
                request_id=request.request_id,
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_ERROR,
                f"local embedding network error: {exc}",
                request_id=request.request_id,
                retryable=True,
            ) from exc
        if response.status_code >= 400:
            raise map_http_error(
                response.status_code,
                message=response.text,
                request_id=request.request_id,
            )
        data = cast(dict[str, Any], response.json())
        vectors = _embedding_vectors(data)
        if not vectors:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MALFORMED_RESPONSE,
                "local embedding response missing vectors",
                request_id=request.request_id,
                retryable=True,
            )
        dims = len(vectors[0])
        expected = self._endpoint.embedding_dimensions
        if expected is not None and dims != expected:
            raise ModelGatewayError(
                ModelGatewayErrorCode.EMBEDDING_DIMENSION_ERROR,
                f"expected {expected} dims, got {dims}",
                request_id=request.request_id,
                retryable=False,
            )
        usage_obj: object = data.get("usage")
        usage = _as_mapping(usage_obj)
        prompt_tokens = _optional_int(usage.get("prompt_tokens"))
        return EmbeddingResult(
            vectors=vectors,
            resolved_model=str(data.get("model") or self._endpoint.model_id),
            dimensions=dims,
            input_tokens=prompt_tokens,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )


def _optional_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _as_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    items = cast(dict[object, object], value)
    return {str(key): val for key, val in items.items()}


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _chat_content(data: dict[str, Any]) -> str:
    choices_obj: object = data.get("choices")
    if not isinstance(choices_obj, list) or not choices_obj:
        return ""
    first_obj: object = cast(list[object], choices_obj)[0]
    if not isinstance(first_obj, dict):
        return ""
    first = cast(dict[object, object], first_obj)
    message_obj: object = first.get("message")
    if not isinstance(message_obj, dict):
        return ""
    message = cast(dict[object, object], message_obj)
    content_obj: object = message.get("content")
    return str(content_obj or "")


def _finish_reason(data: dict[str, Any]) -> str | None:
    choices_obj: object = data.get("choices")
    if not isinstance(choices_obj, list) or not choices_obj:
        return None
    first_obj: object = cast(list[object], choices_obj)[0]
    if not isinstance(first_obj, dict):
        return None
    first = cast(dict[object, object], first_obj)
    reason_obj: object = first.get("finish_reason")
    return str(reason_obj) if reason_obj is not None else None


def _embedding_vectors(data: dict[str, Any]) -> tuple[tuple[float, ...], ...]:
    items_obj: object = data.get("data")
    if not isinstance(items_obj, list):
        return ()
    vectors: list[tuple[float, ...]] = []
    for item_obj in cast(list[object], items_obj):
        if not isinstance(item_obj, dict):
            continue
        item = cast(dict[object, object], item_obj)
        embedding_obj: object = item.get("embedding")
        if not isinstance(embedding_obj, list):
            continue
        floats: list[float] = []
        for raw in cast(list[object], embedding_obj):
            parsed = _as_float(raw)
            if parsed is None:
                floats = []
                break
            floats.append(parsed)
        if floats:
            vectors.append(tuple(floats))
    return tuple(vectors)
