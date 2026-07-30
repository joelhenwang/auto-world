"""Assert that image failure does not propagate into the phase runner.

Handbook: 16 §2 — image errors must NEVER raise into phase critical path.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from fictional_world.application.images.enqueue import ImageEnqueueService
from fictional_world.application.images.qc import ImageQCService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_enqueue_failure_does_not_raise_into_caller_if_key_exists() -> None:
    """If the job already exists, enqueue() returns without error."""
    from fictional_world.domain.images.persistence import ImageJobRecord

    existing_job = ImageJobRecord(
        id=uuid.uuid4(),
        world_id=uuid.uuid4(),
        idempotency_key="existing-key",
        status="queued",
        asset_class="EVENT_CG",
        version=1,
    )

    uow_mock = MagicMock()
    uow_mock.__aenter__ = AsyncMock(return_value=uow_mock)
    uow_mock.__aexit__ = AsyncMock(return_value=None)
    uow_mock.image_jobs.get_by_idempotency_key = AsyncMock(return_value=existing_job)

    svc = ImageEnqueueService(uow=uow_mock)

    from fictional_world.application.images.types import EnqueueImageJobRequest

    req = EnqueueImageJobRequest(
        world_id=existing_job.world_id,
        idempotency_key="existing-key",
        source_event_id=uuid.uuid4(),
    )
    result = await svc.enqueue(req)
    assert result.idempotency_key == "existing-key"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_qc_failure_does_not_propagate_outside_service() -> None:
    """QC failure transitions job to 'failed' — callers see the record, not an exception."""
    from fictional_world.domain.images.persistence import (
        AssetObjectRecord,
        GalleryItemRecord,
        ImageJobRecord,
    )

    job_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    world_id = uuid.uuid4()

    job = ImageJobRecord(
        id=job_id,
        world_id=world_id,
        idempotency_key="k",
        status="running",
        asset_class="EVENT_CG",
        attempt=0,
        max_attempts=3,
        version=1,
    )
    asset = AssetObjectRecord(
        id=asset_id,
        world_id=world_id,
        bucket="b",
        object_key="k",
        content_type="image/png",
        byte_size=200,
        checksum_sha256="a" * 64,
        asset_class="EVENT_CG",
        version=1,
    )
    failed_job = job.model_copy(update={"status": "failed", "version": 2})
    gallery = GalleryItemRecord(
        id=uuid.uuid4(),
        world_id=world_id,
        image_job_id=job_id,
        asset_object_id=asset_id,
        asset_class="EVENT_CG",
        display_status="rejected",
        version=1,
    )

    uow_mock = MagicMock()
    uow_mock.__aenter__ = AsyncMock(return_value=uow_mock)
    uow_mock.__aexit__ = AsyncMock(return_value=None)
    uow_mock.image_jobs.get = AsyncMock(return_value=job)
    uow_mock.asset_objects.get = AsyncMock(return_value=asset)
    uow_mock.image_jobs.update_status = AsyncMock(return_value=failed_job)
    uow_mock.gallery_items.insert = AsyncMock(return_value=gallery)
    uow_mock.commit = AsyncMock()

    svc = ImageQCService(uow=uow_mock)

    # Garbage bytes → QC fails
    returned_job, returned_gallery = await svc.run_technical_qc_and_record(
        job_id=job_id,
        asset_object_id=asset_id,
        data=b"",  # fails non_empty check
        content_type="image/png",
    )
    # Must not raise; returns updated records
    assert returned_job.status == "failed"
    assert returned_gallery.display_status == "rejected"
