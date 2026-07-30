"""Technical quality control and gallery lifecycle service.

Handbook: 16 §13; S4-IMG-003.

Technical QC is deterministic (no model calls required).  Vision-assisted QC
is an optional stub; the interface is present but the implementation defers
to a future model call.

Image failure NEVER raises into the phase runner (handbook 16 §2 / §8.5).
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fictional_world.application.images.types import QCReport
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.domain.images.persistence import (
    GalleryItemRecord,
    ImageJobRecord,
)

_MIN_BYTE_SIZE = 100
_MIN_DIMENSION_PX = 64

RETRY_STATUSES = {"queued", "running"}


def technical_qc(
    data: bytes,
    *,
    filename: str = "",
    expected_content_type: str | None = None,
    min_width: int = _MIN_DIMENSION_PX,
    min_height: int = _MIN_DIMENSION_PX,
    width_px: int | None = None,
    height_px: int | None = None,
) -> QCReport:
    """Run deterministic technical checks on raw image bytes.

    Handbook 16 §13.1.  Does NOT call any external service.
    """
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    # Non-empty bytes
    checks["non_empty"] = len(data) >= _MIN_BYTE_SIZE
    if not checks["non_empty"]:
        reasons.append(f"byte_size {len(data)} < minimum {_MIN_BYTE_SIZE}")

    # Valid file signature (PNG or JPEG or WEBP)
    checks["valid_format"] = _check_image_header(data)
    if not checks["valid_format"]:
        reasons.append("unrecognised image format header")

    # Dimensions present (if provided by caller)
    if width_px is not None and height_px is not None:
        checks["min_dimensions"] = width_px >= min_width and height_px >= min_height
        if not checks["min_dimensions"]:
            reasons.append(
                f"dimensions {width_px}x{height_px} below minimum {min_width}x{min_height}"
            )
    else:
        checks["min_dimensions"] = True

    # Content-type plausibility
    if expected_content_type is not None:
        ct = expected_content_type.lower()
        checks["content_type_plausible"] = any(
            ct.startswith(p) for p in ("image/png", "image/jpeg", "image/webp", "image/gif")
        )
        if not checks["content_type_plausible"]:
            reasons.append(f"content_type '{expected_content_type}' not a recognised image type")
    else:
        checks["content_type_plausible"] = True

    passed = all(checks.values())
    return QCReport(passed=passed, checks=checks, reasons=reasons)


def _check_image_header(data: bytes) -> bool:
    """Return True if *data* starts with a known image magic bytes sequence."""
    if len(data) < 8:
        return False
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:2] in (b"\xff\xd8", b"\xff\xe0", b"\xff\xe1"):
        return True
    return data[:4] == b"RIFF" and data[8:12] == b"WEBP"


class ImageQCService:
    """Approve/reject/regenerate image jobs and manage gallery lifecycle."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def run_technical_qc_and_record(
        self,
        *,
        job_id: UUID,
        asset_object_id: UUID,
        data: bytes,
        content_type: str,
        width_px: int | None = None,
        height_px: int | None = None,
    ) -> tuple[ImageJobRecord, GalleryItemRecord]:
        """Run technical QC, create gallery item, and update job status.

        On QC pass  → job becomes 'approved', gallery display_status='auto_selected'.
        On QC fail  → job becomes 'failed' (or 'dead_letter' if max attempts exceeded).
        Returns updated (job, gallery_item).
        Image failure is captured here; callers must NOT propagate it to phases.
        """
        report = technical_qc(
            data,
            expected_content_type=content_type,
            width_px=width_px,
            height_px=height_px,
        )

        async with self._uow as uow:
            job = await uow.image_jobs.get(job_id)
            if job is None:
                raise ValueError(f"image_job {job_id} not found")
            asset = await uow.asset_objects.get(asset_object_id)
            if asset is None:
                raise ValueError(f"asset_object {asset_object_id} not found")

            if report.passed:
                job = await uow.image_jobs.update_status(
                    job_id, status="approved", expected_version=job.version
                )
                display_status = "auto_selected"
            else:
                next_status = _next_fail_status(job)
                job = await uow.image_jobs.update_status(
                    job_id,
                    status=next_status,
                    error_class="QC_FAILED",
                    error_detail="; ".join(report.reasons) or "technical qc failed",
                    expected_version=job.version,
                )
                display_status = "rejected"

            gallery_item = GalleryItemRecord(
                id=uuid4(),
                world_id=job.world_id,
                image_job_id=job.id,
                asset_object_id=asset_object_id,
                source_event_id=job.source_event_id,
                source_scene_id=job.source_scene_id,
                asset_class=job.asset_class,
                display_status=display_status,
                is_canonical_illustration=False,
                qc_passed=report.passed,
                qc_report={
                    "passed": report.passed,
                    "checks": report.checks,
                    "reasons": report.reasons,
                },
                version=1,
            )
            gallery_item = await uow.gallery_items.insert(gallery_item)
            await uow.commit()

        return job, gallery_item

    async def approve(self, *, item_id: UUID) -> GalleryItemRecord:
        """Manually approve a gallery item (user override)."""
        async with self._uow as uow:
            item = await uow.gallery_items.get(item_id)
            if item is None:
                raise ValueError(f"gallery_item {item_id} not found")
            updated = await uow.gallery_items.update_display_status(
                item_id,
                display_status="user_selected",
                qc_passed=True,
                expected_version=item.version,
            )
            await uow.commit()
        return updated

    async def reject(self, *, item_id: UUID) -> GalleryItemRecord:
        """Manually reject a gallery item."""
        async with self._uow as uow:
            item = await uow.gallery_items.get(item_id)
            if item is None:
                raise ValueError(f"gallery_item {item_id} not found")
            updated = await uow.gallery_items.update_display_status(
                item_id,
                display_status="rejected",
                expected_version=item.version,
            )
            await uow.commit()
        return updated

    async def mark_regenerate(self, *, job_id: UUID) -> ImageJobRecord:
        """Reset a failed job to 'queued' for regeneration if attempts allow."""
        async with self._uow as uow:
            job = await uow.image_jobs.get(job_id)
            if job is None:
                raise ValueError(f"image_job {job_id} not found")
            if job.attempt >= job.max_attempts:
                raise ValueError(
                    f"image_job {job_id} has exhausted {job.max_attempts} attempts"
                )
            updated = await uow.image_jobs.update_status(
                job_id, status="queued", expected_version=job.version
            )
            await uow.commit()
        return updated


def _next_fail_status(job: ImageJobRecord) -> str:
    """Return 'dead_letter' if max attempts exceeded, else 'failed'."""
    if job.attempt >= job.max_attempts:
        return "dead_letter"
    return "failed"
