"""ComfyUI execution gateway protocol and value types (handbook 16 §8)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ImageWorkerHealth:
    """Result of a health/capability probe against a ComfyUI worker."""

    healthy: bool
    gpu_name: str | None = None
    vram_total_mb: int | None = None
    vram_free_mb: int | None = None
    queue_pending: int = 0
    queue_running: int = 0
    detail: str | None = None


@dataclass(frozen=True)
class ImageExecutionRequest:
    """Parameters needed to submit a single image generation job."""

    idempotency_key: str
    workflow_version: str
    positive_prompt: str
    negative_prompt: str
    seed: int
    width: int
    height: int
    extra_bindings: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ImageSubmission:
    """Returned by ComfyUI after a successful /prompt POST."""

    external_prompt_id: str
    queue_remaining: int = 0


@dataclass(frozen=True)
class ImageExecutionStatus:
    """Polled status for a submitted prompt."""

    external_prompt_id: str
    status: str  # "pending" | "running" | "succeeded" | "failed" | "unknown"
    error: str | None = None


@dataclass(frozen=True)
class GeneratedAsset:
    """One output image file retrieved from ComfyUI."""

    filename: str
    subfolder: str
    folder_type: str  # "output" | "temp"
    data: bytes = field(default=b"")
    content_type: str = "image/webp"


class ImageExecutionGateway(Protocol):
    """Port for a ComfyUI image generation backend (handbook 16 §8.1)."""

    async def health(self) -> ImageWorkerHealth: ...

    async def submit(self, request: ImageExecutionRequest) -> ImageSubmission:
        """Submit a workflow and return the prompt ID.

        Must be idempotent: a duplicate idempotency_key returns the same
        submission without creating a duplicate job.
        """
        ...

    async def get_status(self, external_id: str) -> ImageExecutionStatus: ...

    async def cancel(self, external_id: str) -> None: ...

    async def fetch_outputs(self, external_id: str) -> tuple[GeneratedAsset, ...]: ...
