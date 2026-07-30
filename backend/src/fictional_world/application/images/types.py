"""Value types shared across image application services."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class EnqueueImageJobRequest:
    """Parameters for enqueueing a new image generation job.

    ``source_event_id`` must be a committed event (handbook 16 §2 / §4.5).
    ``idempotency_key`` is caller-controlled; duplicate keys are no-ops.
    """

    world_id: UUID
    idempotency_key: str
    source_event_id: UUID
    asset_class: str = "EVENT_CG"
    source_scene_id: UUID | None = None
    workflow_version: str = "stub_v1"
    priority: int = 50
    max_attempts: int = 3
    prompt_spec: dict[str, object] = field(default_factory=dict)
    visual_profile_versions: dict[str, object] = field(default_factory=dict)
    seed: int | None = None
    width_px: int | None = None
    height_px: int | None = None


@dataclass(frozen=True)
class QCReport:
    """Result of technical quality control checks."""

    passed: bool
    checks: dict[str, bool]
    reasons: list[str]
