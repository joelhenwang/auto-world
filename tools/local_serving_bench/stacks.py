"""Candidate stack adapters for local serving benchmarks."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol, cast

from tools.local_serving_bench.corpus import CorpusEntry


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items = cast(list[object], value)
    return [str(item) for item in items]


def _as_object_list(value: object) -> list[Any]:
    if not isinstance(value, list):
        return []
    return list(cast(list[object], value))


def _as_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    items = cast(dict[object, object], value)
    return {str(key): val for key, val in items.items()}


def _extract_chat_text(data: dict[str, Any]) -> str:
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


class StackAdapter(Protocol):
    stack_id: str

    async def execute(self, entry: CorpusEntry) -> tuple[bool, str, dict[str, Any]]:
        """Return (success, output_text_or_error, meta)."""

        raise NotImplementedError


@dataclass(slots=True)
class DryRunStackAdapter:
    """Offline adapter that simulates stack behaviour without network."""

    stack_id: str = "dry-run"
    base_latency_ms: float = 12.0

    async def execute(self, entry: CorpusEntry) -> tuple[bool, str, dict[str, Any]]:
        started = time.perf_counter()
        await asyncio.sleep(0)
        injection = _as_mapping(entry.raw.get("injection"))
        if entry.case_kind == "cancellation" or injection.get("cancel_after_ms") is not None:
            elapsed = (time.perf_counter() - started) * 1000.0
            return False, "cancelled", {"cancelled": True, "latency_ms": elapsed}
        if entry.case_kind == "malformed" or injection.get("simulate_response"):
            elapsed = (time.perf_counter() - started) * 1000.0
            payload = str(injection.get("simulate_response", "not-json{{"))
            return True, payload, {"structured_valid": False, "latency_ms": elapsed}
        if entry.role == "embedding":
            texts = _as_str_list(entry.raw.get("texts"))
            dims = 8
            vectors = [[0.01 * (i + 1)] * dims for i, _text in enumerate(texts)]
            elapsed = (time.perf_counter() - started) * 1000.0
            return (
                True,
                json.dumps({"vectors": vectors, "dimensions": dims}),
                {
                    "structured_valid": True,
                    "latency_ms": max(elapsed, self.base_latency_ms),
                },
            )
        schema = entry.expected_schema or "Prose"
        body: dict[str, Any] = {
            "schema_version": "1.0",
            "dry_run": True,
            "role": entry.role,
            "request_id": entry.request_id,
            "expected_schema": schema,
            "ok": True,
        }
        for field_name in _as_str_list(entry.raw.get("expected_fields")):
            if field_name == "schema_version":
                continue
            body[field_name] = f"dry-run-{field_name}"
        elapsed = (time.perf_counter() - started) * 1000.0
        return (
            True,
            json.dumps(body),
            {
                "structured_valid": entry.raw.get("expected_schema") is not None,
                "latency_ms": max(elapsed, self.base_latency_ms),
            },
        )


@dataclass(slots=True)
class OpenAICompatibleStackAdapter:
    """Live OpenAI-compatible HTTP adapter (opt-in; not used in default CI)."""

    stack_id: str
    base_url: str
    model: str
    api_key: str = "local"
    timeout_s: float = 120.0

    async def execute(self, entry: CorpusEntry) -> tuple[bool, str, dict[str, Any]]:
        import httpx

        started = time.perf_counter()
        injection = _as_mapping(entry.raw.get("injection"))
        if entry.case_kind == "cancellation" or injection.get("cancel_after_ms") is not None:
            return False, "cancelled", {"cancelled": True, "latency_ms": 0.0}

        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout_s) as client:
            if entry.role == "embedding":
                payload: dict[str, Any] = {
                    "model": self.model,
                    "input": _as_str_list(entry.raw.get("texts")),
                }
                response = await client.post("/v1/embeddings", json=payload, headers=headers)
                elapsed = (time.perf_counter() - started) * 1000.0
                if response.status_code >= 400:
                    return False, response.text, {"latency_ms": elapsed}
                return True, response.text, {"structured_valid": True, "latency_ms": elapsed}

            chat_payload: dict[str, Any] = {
                "model": self.model,
                "messages": _as_object_list(entry.raw.get("messages")),
                "temperature": 0.2,
            }
            response = await client.post(
                "/v1/chat/completions",
                json=chat_payload,
                headers=headers,
            )
            elapsed = (time.perf_counter() - started) * 1000.0
            if response.status_code >= 400:
                return False, response.text, {"latency_ms": elapsed}
            data = cast(dict[str, Any], response.json())
            text = _extract_chat_text(data)
            structured_valid: bool | None = None
            if entry.expected_schema is not None:
                try:
                    json.loads(text)
                    structured_valid = True
                except json.JSONDecodeError:
                    structured_valid = False
            return True, text, {"structured_valid": structured_valid, "latency_ms": elapsed}


STACK_IDS = ("vllm", "llamacpp", "transformers", "sglang", "dry-run")


def build_adapter(
    *,
    stack_id: str,
    base_url: str | None = None,
    model: str = "local-model",
) -> StackAdapter:
    if stack_id == "dry-run" or not base_url:
        return DryRunStackAdapter(stack_id=stack_id if stack_id != "dry-run" else "dry-run")
    return OpenAICompatibleStackAdapter(stack_id=stack_id, base_url=base_url, model=model)
