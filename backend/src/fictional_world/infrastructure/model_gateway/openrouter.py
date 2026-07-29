"""OpenRouter HTTP adapter skeleton (handbook ``12`` sections 6-10)."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from typing import Any, cast

import httpx
from pydantic import BaseModel, ValidationError

from fictional_world.application.models.errors import ModelGatewayError, ModelGatewayErrorCode
from fictional_world.application.models.messages import (
    EmbeddingRequest,
    EmbeddingResult,
    TextGenerationRequest,
    TextGenerationResult,
)
from fictional_world.application.models.profiles import ModelProfile
from fictional_world.infrastructure.model_gateway.capabilities import CapabilityMode
from fictional_world.infrastructure.model_gateway.errors import map_openrouter_error_body

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterGateway:
    """Thin async OpenRouter client. Does not hold DB transactions open."""

    def __init__(
        self,
        *,
        api_key: str,
        profiles: Mapping[str, ModelProfile],
        base_url: str = DEFAULT_BASE_URL,
        http_client: httpx.AsyncClient | None = None,
        app_title: str = "Autonomous Fictional World",
        http_referer: str | None = None,
        capability_mode: CapabilityMode = CapabilityMode.JSON_OBJECT_PROMPTED,
        expected_embedding_dimensions: int = 2048,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        self._api_key = api_key
        self._profiles = dict(profiles)
        self._base_url = base_url.rstrip("/")
        self._app_title = app_title
        self._http_referer = http_referer
        self._capability_mode = capability_mode
        self._expected_embedding_dimensions = expected_embedding_dimensions
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout or httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0),
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Title": self._app_title,
        }
        if self._http_referer:
            headers["HTTP-Referer"] = self._http_referer
        return headers

    def _profile(self, profile_id: str) -> ModelProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.MODEL_NOT_AVAILABLE,
                f"unknown profile_id={profile_id}",
                request_id=None,
                retryable=False,
            ) from exc

    async def generate(self, request: TextGenerationRequest) -> TextGenerationResult:
        profile = self._profile(request.model_profile_id)
        payload: dict[str, Any] = {
            "model": profile.model_slug,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.sampling.temperature,
            "top_p": request.sampling.top_p,
            "max_tokens": request.sampling.max_output_tokens,
            "provider": {
                "require_parameters": request.routing.require_parameters,
                "allow_fallbacks": request.routing.allow_fallbacks,
            },
        }
        if request.sampling.seed is not None and profile.supports_seed:
            payload["seed"] = request.sampling.seed
        if request.sampling.stop:
            payload["stop"] = list(request.sampling.stop)
        if request.output_schema is not None and profile.supports_json_schema:
            schema = request.output_schema.model_json_schema()
            if self._capability_mode is CapabilityMode.NATIVE_STRICT:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": request.output_schema.__name__,
                        "strict": True,
                        "schema": schema,
                    },
                }
            elif self._capability_mode is CapabilityMode.NATIVE_BEST_EFFORT:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": request.output_schema.__name__,
                        "schema": schema,
                    },
                }
            elif self._capability_mode is CapabilityMode.JSON_OBJECT_PROMPTED:
                payload["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        response = await self._post("/chat/completions", payload, request_id=request.request_id)
        data = _response_object(response)
        raw_text = _extract_chat_text(data)
        parsed_model: BaseModel | None = None
        if request.output_schema is not None:
            try:
                parsed_model = request.output_schema.model_validate_json(raw_text)
            except (ValidationError, json.JSONDecodeError) as exc:
                code = (
                    ModelGatewayErrorCode.MALFORMED_RESPONSE
                    if isinstance(exc, json.JSONDecodeError)
                    else ModelGatewayErrorCode.SCHEMA_VALIDATION_ERROR
                )
                raise ModelGatewayError(
                    code,
                    str(exc),
                    request_id=request.request_id,
                    retryable=True,
                ) from exc

        usage = data.get("usage")
        choices = data.get("choices")
        choice0: dict[str, object] = {}
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            choice0 = cast(dict[str, object], choices[0])
        finish = choice0.get("finish_reason")
        latency_ms = int((time.perf_counter() - started) * 1000)
        provider_id = data.get("id")
        model_name = data.get("model")
        return TextGenerationResult(
            provider_request_id=str(provider_id) if provider_id is not None else None,
            resolved_model=str(model_name or profile.model_slug),
            provider_name="openrouter",
            raw_text=raw_text,
            parsed=parsed_model,
            input_tokens=_usage_int(usage, "prompt_tokens"),
            output_tokens=_usage_int(usage, "completion_tokens"),
            finish_reason=str(finish) if isinstance(finish, str) else None,
            capability_mode=self._capability_mode.value,
            latency_ms=latency_ms,
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        profile = self._profile(request.model_profile_id)
        texts = list(request.texts)
        if request.input_type == "query":
            texts = [t if t.startswith("query: ") else f"query: {t}" for t in texts]
        else:
            texts = [t if t.startswith("passage: ") else f"passage: {t}" for t in texts]
        payload: dict[str, Any] = {
            "model": profile.model_slug,
            "input": texts,
            "encoding_format": "float",
        }
        started = time.perf_counter()
        response = await self._post("/embeddings", payload, request_id=request.request_id)
        data = _response_object(response)
        items_raw = data.get("data")
        if not isinstance(items_raw, list) or len(cast(list[object], items_raw)) != len(
            request.texts
        ):
            raise ModelGatewayError(
                ModelGatewayErrorCode.MALFORMED_RESPONSE,
                "embedding response count mismatch",
                request_id=request.request_id,
                retryable=True,
            )
        items = cast(list[object], items_raw)
        expected = (
            request.dimensions
            or profile.embedding_dimensions
            or self._expected_embedding_dimensions
        )
        indexed: list[tuple[int, tuple[float, ...]]] = []
        for raw_item in items:
            if not isinstance(raw_item, dict):
                raise ModelGatewayError(
                    ModelGatewayErrorCode.MALFORMED_RESPONSE,
                    "embedding item not an object",
                    request_id=request.request_id,
                    retryable=True,
                )
            item = cast(dict[str, object], raw_item)
            index_val = item.get("index", 0)
            index = int(index_val) if isinstance(index_val, int | float) else 0
            embedding_raw = item.get("embedding")
            if not isinstance(embedding_raw, list):
                raise ModelGatewayError(
                    ModelGatewayErrorCode.EMBEDDING_DIMENSION_ERROR,
                    f"expected dim {expected}, got None",
                    request_id=request.request_id,
                    retryable=False,
                )
            embedding_list = cast(list[object], embedding_raw)
            floats: list[float] = []
            for value in embedding_list:
                if not isinstance(value, int | float):
                    raise ModelGatewayError(
                        ModelGatewayErrorCode.MALFORMED_RESPONSE,
                        "non-numeric embedding value",
                        request_id=request.request_id,
                        retryable=True,
                    )
                floats.append(float(value))
            if len(floats) != expected:
                raise ModelGatewayError(
                    ModelGatewayErrorCode.EMBEDDING_DIMENSION_ERROR,
                    f"expected dim {expected}, got {len(floats)}",
                    request_id=request.request_id,
                    retryable=False,
                )
            indexed.append((index, tuple(floats)))
        indexed.sort(key=lambda pair: pair[0])
        vectors = tuple(vec for _, vec in indexed)
        usage = data.get("usage")
        model_name = data.get("model")
        latency_ms = int((time.perf_counter() - started) * 1000)
        return EmbeddingResult(
            vectors=vectors,
            resolved_model=str(model_name or profile.model_slug),
            dimensions=expected,
            input_tokens=_usage_int(usage, "prompt_tokens") or _usage_int(usage, "total_tokens"),
            latency_ms=latency_ms,
        )

    async def _post(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        request_id: str,
    ) -> httpx.Response:
        try:
            response = await self._client.post(path, headers=self._headers(), json=payload)
        except httpx.TimeoutException as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_TIMEOUT,
                "OpenRouter timeout",
                request_id=request_id,
                retryable=True,
            ) from exc
        except httpx.HTTPError as exc:
            raise ModelGatewayError(
                ModelGatewayErrorCode.NETWORK_ERROR,
                str(exc),
                request_id=request_id,
                retryable=True,
            ) from exc
        if response.status_code >= 400:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            body = _optional_error_body(response)
            raise map_openrouter_error_body(
                response.status_code,
                body,
                request_id=request_id,
                retry_after_seconds=retry_after,
            )
        return response


def _optional_error_body(response: httpx.Response) -> dict[str, Any] | None:
    try:
        parsed: object = response.json()
    except Exception:
        return None
    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed)
    return None


def _response_object(response: httpx.Response) -> dict[str, object]:
    parsed: object = response.json()
    if not isinstance(parsed, dict):
        raise ModelGatewayError(
            ModelGatewayErrorCode.MALFORMED_RESPONSE,
            "response not an object",
            retryable=True,
        )
    return cast(dict[str, object], parsed)


def _extract_chat_text(data: dict[str, object]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ModelGatewayError(
            ModelGatewayErrorCode.MALFORMED_RESPONSE,
            "missing choices",
            retryable=True,
        )
    first_obj: object = cast(list[object], choices)[0]
    if not isinstance(first_obj, dict):
        raise ModelGatewayError(
            ModelGatewayErrorCode.MALFORMED_RESPONSE,
            "choice not an object",
            retryable=True,
        )
    first = cast(dict[str, object], first_obj)
    message_obj = first.get("message")
    if not isinstance(message_obj, dict):
        raise ModelGatewayError(
            ModelGatewayErrorCode.MALFORMED_RESPONSE,
            "missing message content",
            retryable=True,
        )
    content = cast(dict[str, object], message_obj).get("content")
    if not isinstance(content, str):
        raise ModelGatewayError(
            ModelGatewayErrorCode.MALFORMED_RESPONSE,
            "missing message content",
            retryable=True,
        )
    return content


def _usage_int(usage: object, key: str) -> int | None:
    if not isinstance(usage, dict):
        return None
    value = cast(dict[str, object], usage).get(key)
    return int(value) if isinstance(value, int | float) else None


def _parse_retry_after(raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None
