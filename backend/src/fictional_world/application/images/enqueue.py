"""ImageEnqueueService — create image_job rows after canonical event commit.

Rules:
- Called only AFTER the source event has been committed to the DB.
- Does NOT submit to ComfyUI; it only inserts the DB row.
- Idempotent: duplicate idempotency_key returns the existing record.
- NEVER called synchronously from the phase-critical path.
  (handbook 16 §2; 29 S4-IMG-001)
"""

from __future__ import annotations

import uuid

from fictional_world.application.images.types import EnqueueImageJobRequest
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.images.persistence import ImageJobRecord


class ImageEnqueueService:
    """Insert image_job rows in the outbox/task style, never blocking phases."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def enqueue(self, request: EnqueueImageJobRequest) -> ImageJobRecord:
        """Return existing job if idempotency_key already present, else insert.

        The caller must be OUTSIDE an open DB transaction (handbook §11).
        """
        async with self._uow as uow:
            existing = await uow.image_jobs.get_by_idempotency_key(
                request.world_id, request.idempotency_key
            )
            if existing is not None:
                return existing

            record = ImageJobRecord(
                id=uuid.uuid4(),
                world_id=request.world_id,
                idempotency_key=request.idempotency_key,
                source_event_id=request.source_event_id,
                source_scene_id=request.source_scene_id,
                asset_class=request.asset_class,
                status="queued",
                priority=request.priority,
                generation_number=1,
                attempt=0,
                max_attempts=request.max_attempts,
                workflow_version=request.workflow_version,
                seed=request.seed,
                width_px=request.width_px,
                height_px=request.height_px,
                prompt_spec=dict(request.prompt_spec),
                visual_profile_versions=dict(request.visual_profile_versions),
                version=1,
            )
            inserted = await uow.image_jobs.insert(record)
            await uow.commit()
            return inserted
