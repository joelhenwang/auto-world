"""ComfyUI adapters (S4-IMG-001)."""

from fictional_world.infrastructure.comfyui.fake import FakeComfyUI
from fictional_world.infrastructure.comfyui.http_adapter import ComfyUIHttpAdapter
from fictional_world.infrastructure.comfyui.protocol import (
    GeneratedAsset,
    ImageExecutionGateway,
    ImageExecutionRequest,
    ImageExecutionStatus,
    ImageSubmission,
    ImageWorkerHealth,
)
from fictional_world.infrastructure.comfyui.workflow_registry import WorkflowRegistry

__all__ = [
    "ComfyUIHttpAdapter",
    "FakeComfyUI",
    "GeneratedAsset",
    "ImageExecutionGateway",
    "ImageExecutionRequest",
    "ImageExecutionStatus",
    "ImageSubmission",
    "ImageWorkerHealth",
    "WorkflowRegistry",
]
