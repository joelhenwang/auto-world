"""ComfyUI HTTP adapter — thin wrapper around the ComfyUI REST+WS API.

Handbook: 16 §8; S4-IMG-001.

Does NOT call any methods while a DB transaction is open (handbook §4.3 / §11).
Phase-critical paths must NOT await this adapter synchronously.

Endpoints used:
  GET  /system_stats          — health probe
  POST /prompt                — submit workflow
  GET  /history/{prompt_id}   — poll status
  POST /queue                 — cancel (interrupt/delete)
  GET  /view                  — download output image
"""

from __future__ import annotations

from typing import Any, cast

import httpx

from fictional_world.infrastructure.comfyui.protocol import (
    GeneratedAsset,
    ImageExecutionRequest,
    ImageExecutionStatus,
    ImageSubmission,
    ImageWorkerHealth,
)
from fictional_world.infrastructure.comfyui.workflow_registry import WorkflowRegistry


class ComfyUIHttpAdapter:
    """HTTP adapter for a single ComfyUI worker node.

    ``workflow_registry`` provides versioned workflow JSON by version string.
    """

    def __init__(
        self,
        *,
        base_url: str,
        workflow_registry: WorkflowRegistry,
        client_id: str = "worldsim",
        timeout: float = 30.0,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._registry = workflow_registry
        self._client_id = client_id
        self._client = httpx.AsyncClient(timeout=timeout)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health(self) -> ImageWorkerHealth:
        try:
            resp = await self._client.get(f"{self._base}/system_stats")
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            devices: list[dict[str, Any]] = data.get("devices", [])
            gpu: dict[str, Any] = devices[0] if devices else {}
            return ImageWorkerHealth(
                healthy=True,
                gpu_name=str(gpu.get("name", "unknown")),
                vram_total_mb=int(gpu.get("vram_total", 0)) // 1024 // 1024,
                vram_free_mb=int(gpu.get("vram_free", 0)) // 1024 // 1024,
                queue_pending=int(data.get("queue_remaining", 0)),
            )
        except Exception as exc:
            return ImageWorkerHealth(healthy=False, detail=str(exc))

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    async def submit(self, request: ImageExecutionRequest) -> ImageSubmission:
        workflow = self._registry.load(request.workflow_version)
        bound = _bind_prompt(workflow, request)
        payload: dict[str, Any] = {
            "prompt": bound,
            "client_id": self._client_id,
            "extra_data": {"idempotency_key": request.idempotency_key},
        }
        resp = await self._client.post(f"{self._base}/prompt", json=payload)
        resp.raise_for_status()
        result: dict[str, Any] = resp.json()
        prompt_id: str = result["prompt_id"]
        queue_remaining: int = int(result.get("number", 0))
        return ImageSubmission(
            external_prompt_id=prompt_id,
            queue_remaining=queue_remaining,
        )

    # ------------------------------------------------------------------
    # Status poll
    # ------------------------------------------------------------------

    async def get_status(self, external_id: str) -> ImageExecutionStatus:
        resp = await self._client.get(f"{self._base}/history/{external_id}")
        if resp.status_code == 404:
            return ImageExecutionStatus(external_prompt_id=external_id, status="unknown")
        resp.raise_for_status()
        history: dict[str, Any] = resp.json()
        entry = history.get(external_id, {})
        if not entry:
            return ImageExecutionStatus(external_prompt_id=external_id, status="pending")
        status_info = entry.get("status", {})
        if status_info.get("completed"):
            return ImageExecutionStatus(external_prompt_id=external_id, status="succeeded")
        messages: list[Any] = cast(list[Any], status_info.get("messages", []))
        for msg in messages:
            if isinstance(msg, list) and msg and msg[0] == "execution_error":
                msg_list: list[Any] = cast(list[Any], msg)
                error_detail = str(msg_list[1]) if len(msg_list) > 1 else "unknown error"
                return ImageExecutionStatus(
                    external_prompt_id=external_id,
                    status="failed",
                    error=error_detail,
                )
        return ImageExecutionStatus(external_prompt_id=external_id, status="running")

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    async def cancel(self, external_id: str) -> None:
        payload: dict[str, Any] = {"delete": [external_id]}
        resp = await self._client.post(f"{self._base}/queue", json=payload)
        if resp.status_code not in (200, 404):
            resp.raise_for_status()

    # ------------------------------------------------------------------
    # Fetch outputs
    # ------------------------------------------------------------------

    async def fetch_outputs(self, external_id: str) -> tuple[GeneratedAsset, ...]:
        resp = await self._client.get(f"{self._base}/history/{external_id}")
        if resp.status_code == 404:
            return ()
        resp.raise_for_status()
        history: dict[str, Any] = resp.json()
        entry = history.get(external_id, {})
        if not entry:
            return ()
        outputs: dict[str, Any] = entry.get("outputs", {})
        assets: list[GeneratedAsset] = []
        for _node_id, node_out in outputs.items():
            for img in node_out.get("images", []):
                filename: str = img.get("filename", "")
                subfolder: str = img.get("subfolder", "")
                folder_type: str = img.get("type", "output")
                params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
                dl = await self._client.get(f"{self._base}/view", params=params)
                if dl.status_code != 200:
                    continue
                content_type = dl.headers.get("content-type", "image/png")
                assets.append(
                    GeneratedAsset(
                        filename=filename,
                        subfolder=subfolder,
                        folder_type=folder_type,
                        data=dl.content,
                        content_type=content_type,
                    )
                )
        return tuple(assets)

    async def aclose(self) -> None:
        await self._client.aclose()


# ---------------------------------------------------------------------------
# Workflow binding helpers
# ---------------------------------------------------------------------------


def _bind_prompt(
    workflow: dict[str, Any],
    request: ImageExecutionRequest,
) -> dict[str, Any]:
    """Apply known semantic bindings to a copy of the workflow dict."""
    import copy

    bound: dict[str, Any] = copy.deepcopy(workflow)

    _set_nested(bound, "positive_prompt", request.positive_prompt)
    _set_nested(bound, "negative_prompt", request.negative_prompt)
    _set_nested(bound, "seed", request.seed)
    _set_nested(bound, "width", request.width)
    _set_nested(bound, "height", request.height)

    for field_path, value in request.extra_bindings.items():
        _set_by_path(bound, field_path, value)

    return bound


def _set_nested(
    workflow: dict[str, Any],
    semantic_key: str,
    value: object,
) -> None:
    """Set a value for a semantic key if a binding annotation is present."""
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        typed_node: dict[str, Any] = cast(dict[str, Any], node)
        raw_bindings = typed_node.get("_bindings", {})
        bindings: dict[str, str] = (
            {str(k): str(v) for k, v in cast(dict[Any, Any], raw_bindings).items()}
            if isinstance(raw_bindings, dict)
            else {}
        )
        if semantic_key in bindings:
            _set_by_path(typed_node, bindings[semantic_key], value)


def _set_by_path(obj: dict[str, Any], dot_path: str, value: object) -> None:
    """Set a value in a nested dict using dot notation (e.g. 'inputs.text')."""
    parts = dot_path.split(".")
    target = obj
    for part in parts[:-1]:
        if part not in target or not isinstance(target[part], dict):
            target[part] = {}
        target = target[part]  # type: ignore[assignment]
    target[parts[-1]] = value
