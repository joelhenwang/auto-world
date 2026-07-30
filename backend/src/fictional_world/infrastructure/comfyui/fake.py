"""In-memory fake ComfyUI adapter for offline tests (S4-IMG-001)."""

from __future__ import annotations

from fictional_world.infrastructure.comfyui.protocol import (
    GeneratedAsset,
    ImageExecutionRequest,
    ImageExecutionStatus,
    ImageSubmission,
    ImageWorkerHealth,
)

_STUB_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeComfyUI:
    """Deterministic stub that satisfies ImageExecutionGateway.

    Behaviour:
    - submit(): stores the request and returns a synthetic prompt_id.
    - get_status(): returns "succeeded" on the second call for the same id.
    - fetch_outputs(): returns a single 1x1 stub PNG.
    - cancel(): marks the job cancelled.

    Set ``FakeComfyUI.healthy = False`` to simulate a downed worker.
    """

    def __init__(self) -> None:
        self.healthy: bool = True
        self._submitted: dict[str, ImageExecutionRequest] = {}
        self._poll_counts: dict[str, int] = {}
        self._cancelled: set[str] = set()

    async def health(self) -> ImageWorkerHealth:
        return ImageWorkerHealth(
            healthy=self.healthy,
            gpu_name="FakeGPU",
            vram_total_mb=8192,
            vram_free_mb=6144 if self.healthy else 0,
            queue_pending=len(self._submitted),
            queue_running=0,
        )

    async def submit(self, request: ImageExecutionRequest) -> ImageSubmission:
        if not self.healthy:
            raise RuntimeError("ComfyUI worker is unavailable")
        external_id = f"fake-{request.idempotency_key}"
        if external_id not in self._submitted:
            self._submitted[external_id] = request
            self._poll_counts[external_id] = 0
        return ImageSubmission(external_prompt_id=external_id, queue_remaining=0)

    async def get_status(self, external_id: str) -> ImageExecutionStatus:
        if external_id in self._cancelled:
            return ImageExecutionStatus(external_prompt_id=external_id, status="failed")
        count = self._poll_counts.get(external_id, 0)
        self._poll_counts[external_id] = count + 1
        if count == 0:
            return ImageExecutionStatus(external_prompt_id=external_id, status="running")
        return ImageExecutionStatus(external_prompt_id=external_id, status="succeeded")

    async def cancel(self, external_id: str) -> None:
        self._cancelled.add(external_id)

    async def fetch_outputs(self, external_id: str) -> tuple[GeneratedAsset, ...]:
        if external_id not in self._submitted or external_id in self._cancelled:
            return ()
        return (
            GeneratedAsset(
                filename=f"{external_id}_0.png",
                subfolder="",
                folder_type="output",
                data=_STUB_PNG,
                content_type="image/png",
            ),
        )

    def reset(self) -> None:
        self._submitted.clear()
        self._poll_counts.clear()
        self._cancelled.clear()
        self.healthy = True

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def submitted_count(self) -> int:
        return len(self._submitted)

    def was_cancelled(self, external_id: str) -> bool:
        return external_id in self._cancelled
