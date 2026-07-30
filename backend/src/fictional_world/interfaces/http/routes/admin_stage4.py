"""Stage 4 admin API — model endpoints, workers, image jobs, gallery, visual profiles.

Handbook: 29 §S4-API-001; 17 §admin; 22 §7.

All endpoints require the local admin password when ``auth.enabled`` is True.
When ``auth.enabled`` is False the dependency is a no-op (development mode only).

The capability registry is in-memory state stored at ``app.state.capability_registry``.
If the registry is absent (gateway not wired yet) model-endpoint listing returns [].

Worker and host records are backed by PostgreSQL via the UoW.  Image job, gallery, and
visual-profile records likewise.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, ConfigDict, Field

from fictional_world.application.images.qc import ImageQCService
from fictional_world.application.models.capability_registry import ModelCapabilityRegistry
from fictional_world.interfaces.http.dependencies import SettingsDep, UowDep

router = APIRouter(prefix="/admin/v1", tags=["admin-stage4"])

_http_basic = HTTPBasic(auto_error=False)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------


def _check_admin_auth(
    credentials: Annotated[HTTPBasicCredentials | None, Depends(_http_basic)],
    settings: SettingsDep,
) -> None:
    """Require HTTP Basic auth when ``auth.enabled`` is True.

    Username is ignored; only the password is checked against
    ``auth.local_admin_password``.  Uses constant-time comparison to
    prevent timing attacks.
    """
    if not settings.auth.enabled:
        return
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )
    expected = settings.auth.local_admin_password
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin password not configured on this server",
        )
    if not secrets.compare_digest(credentials.password.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


AdminAuth = Annotated[None, Depends(_check_admin_auth)]


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class _ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelEndpointRead(_ApiModel):
    endpoint_id: str
    host_id: str
    provider_kind: str
    base_url: str
    model_id: str
    model_hash: str | None = None
    roles: list[str]
    context_limit: int
    structured_output_mode: str
    quantization: str | None = None
    max_concurrency: int
    health: str
    loaded_state: str
    privacy_policy: str
    cost_class: str
    supports_embeddings: bool
    embedding_dimensions: int | None = None
    last_probe_at: datetime | None = None
    last_error: str | None = None
    queue_depth: int
    recent_error_rate: float
    available_memory_bytes: int | None = None


class WorkerRead(_ApiModel):
    id: UUID
    host_id: UUID
    worker_key: str
    capabilities: list[str]
    status: str
    heartbeat_at: datetime
    registered_at: datetime
    drain_requested_at: datetime | None = None
    last_task_claimed_at: datetime | None = None


class DrainHostResponse(_ApiModel):
    host_key: str
    host_id: UUID
    drained_workers: int
    status: str


class ImageJobRead(_ApiModel):
    id: UUID
    world_id: UUID
    idempotency_key: str
    source_event_id: UUID | None = None
    source_scene_id: UUID | None = None
    asset_class: str
    status: str
    priority: int
    generation_number: int
    attempt: int
    max_attempts: int
    workflow_version: str | None = None
    external_prompt_id: str | None = None
    seed: int | None = None
    width_px: int | None = None
    height_px: int | None = None
    error_class: str | None = None
    error_detail: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    version: int


class ImageJobActionResponse(_ApiModel):
    job_id: UUID
    action: str
    status: str
    message: str


class GalleryItemRead(_ApiModel):
    id: UUID
    world_id: UUID
    image_job_id: UUID
    asset_object_id: UUID
    source_event_id: UUID | None = None
    source_scene_id: UUID | None = None
    asset_class: str
    display_status: str
    is_canonical_illustration: bool
    qc_passed: bool
    qc_report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    version: int


class VisualProfileRead(_ApiModel):
    id: UUID
    world_id: UUID
    subject_type: str
    subject_id: UUID
    profile_version: int
    valid_from_event_id: UUID | None = None
    supersedes_profile_id: UUID | None = None
    style_spec: dict[str, Any] = Field(default_factory=dict)
    negative_constraints: list[str] = Field(default_factory=list)
    reference_asset_ids: list[UUID] = Field(default_factory=list)
    status: str
    created_at: datetime | None = None
    version: int


# ---------------------------------------------------------------------------
# Helper to retrieve the optional in-memory capability registry
# ---------------------------------------------------------------------------


def _get_registry(request: Request) -> ModelCapabilityRegistry | None:
    return getattr(request.app.state, "capability_registry", None)


# Effective "all workers" scan window — 10 years of heartbeat grace covers every
# registered worker regardless of last heartbeat time.
_ALL_WORKERS_GRACE = timedelta(days=365 * 10)

_JOB_STATUSES = frozenset(
    {
        "queued",
        "running",
        "succeeded",
        "failed",
        "rejected",
        "approved",
        "cancelled",
        "dead_letter",
    }
)


# ---------------------------------------------------------------------------
# GET /admin/v1/model-endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/model-endpoints",
    response_model=list[ModelEndpointRead],
    summary="List all model endpoints from the capability registry",
)
async def list_model_endpoints(
    _auth: AdminAuth,
    request: Request,
) -> list[ModelEndpointRead]:
    """Return all registered model endpoints with health and capability details.

    Returns an empty list when the capability registry is not yet wired
    (e.g. before S4-MODEL-001 integration).
    """
    registry = _get_registry(request)
    if registry is None:
        return []
    return [
        ModelEndpointRead(
            endpoint_id=ep.endpoint_id,
            host_id=ep.host_id,
            provider_kind=ep.provider_kind.value,
            base_url=ep.base_url,
            model_id=ep.model_id,
            model_hash=ep.model_hash,
            roles=[r.value for r in ep.roles],
            context_limit=ep.context_limit,
            structured_output_mode=ep.structured_output_mode,
            quantization=ep.quantization,
            max_concurrency=ep.max_concurrency,
            health=ep.health,
            loaded_state=ep.loaded_state,
            privacy_policy=ep.privacy_policy,
            cost_class=ep.cost_class,
            supports_embeddings=ep.supports_embeddings,
            embedding_dimensions=ep.embedding_dimensions,
            last_probe_at=ep.last_probe_at,
            last_error=ep.last_error,
            queue_depth=ep.queue_depth,
            recent_error_rate=ep.recent_error_rate,
            available_memory_bytes=ep.available_memory_bytes,
        )
        for ep in registry.list_endpoints()
    ]


# ---------------------------------------------------------------------------
# GET /admin/v1/workers
# ---------------------------------------------------------------------------


@router.get(
    "/workers",
    response_model=list[WorkerRead],
    summary="List all registered workers",
)
async def list_workers(
    _auth: AdminAuth,
    uow: UowDep,
) -> list[WorkerRead]:
    """Return all workers currently registered in the worker registry.

    Workers with status ``draining`` or ``drained`` are included so the operator can
    monitor drain progress.

    Uses ``find_lost`` with a very large grace period to enumerate all workers;
    a dedicated ``list_all`` repository method is deferred to a follow-up task.
    """
    all_workers = await uow.workers.find_lost(
        now=datetime.now(tz=UTC),
        heartbeat_grace=_ALL_WORKERS_GRACE,
    )
    return [
        WorkerRead(
            id=w.id,
            host_id=w.host_id,
            worker_key=w.worker_key,
            capabilities=list(w.capabilities),
            status=w.status,
            heartbeat_at=w.heartbeat_at,
            registered_at=w.registered_at,
            drain_requested_at=w.drain_requested_at,
            last_task_claimed_at=w.last_task_claimed_at,
        )
        for w in all_workers
    ]


# ---------------------------------------------------------------------------
# POST /admin/v1/hosts/{host_key}/drain
# ---------------------------------------------------------------------------


@router.post(
    "/hosts/{host_key}/drain",
    response_model=DrainHostResponse,
    summary="Drain all workers on a named host",
)
async def drain_host(
    host_key: str,
    _auth: AdminAuth,
    uow: UowDep,
) -> DrainHostResponse:
    """Mark all workers on ``host_key`` as draining.

    New tasks will not be routed to draining workers.  In-flight tasks complete
    or their leases expire and are re-queued.

    Handbook: 29 §S4-OPS-001; runbook-drain-failover.md §1.
    """
    host = await uow.hosts.find_by_key(host_key)
    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"host '{host_key}' not found in registry",
        )

    now = datetime.now(tz=UTC)
    workers_on_host = await uow.workers.find_lost(
        now=now,
        heartbeat_grace=_ALL_WORKERS_GRACE,
    )
    active_workers = [w for w in workers_on_host if w.host_id == host.id]

    drained_count = 0
    for worker in active_workers:
        if worker.status not in {"drained", "lost"}:
            await uow.workers.drain(worker.id, now=now)
            drained_count += 1

    await uow.commit()

    return DrainHostResponse(
        host_key=host_key,
        host_id=host.id,
        drained_workers=drained_count,
        status="draining",
    )


# ---------------------------------------------------------------------------
# GET /admin/v1/image-jobs
# ---------------------------------------------------------------------------


@router.get(
    "/image-jobs",
    response_model=list[ImageJobRead],
    summary="List image jobs for a world",
)
async def list_image_jobs(
    _auth: AdminAuth,
    uow: UowDep,
    world_id: Annotated[UUID, Query(description="World UUID to filter image jobs")],
    *,
    job_status: Annotated[
        str | None,
        Query(
            alias="status",
            description=(
                "Filter by job status: queued|running|succeeded|failed"
                "|rejected|approved|cancelled|dead_letter"
            ),
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ImageJobRead]:
    """Return image jobs for the given world, optionally filtered by status."""
    if job_status is not None and job_status not in _JOB_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"unknown status '{job_status}'; valid: {sorted(_JOB_STATUSES)}",
        )
    effective_status = job_status or "queued"
    jobs = await uow.image_jobs.list_by_status(world_id, status=effective_status, limit=limit)
    return [
        ImageJobRead(
            id=j.id,
            world_id=j.world_id,
            idempotency_key=j.idempotency_key,
            source_event_id=j.source_event_id,
            source_scene_id=j.source_scene_id,
            asset_class=j.asset_class,
            status=j.status,
            priority=j.priority,
            generation_number=j.generation_number,
            attempt=j.attempt,
            max_attempts=j.max_attempts,
            workflow_version=j.workflow_version,
            external_prompt_id=j.external_prompt_id,
            seed=j.seed,
            width_px=j.width_px,
            height_px=j.height_px,
            error_class=j.error_class,
            error_detail=j.error_detail,
            created_at=j.created_at,
            started_at=j.started_at,
            completed_at=j.completed_at,
            version=j.version,
        )
        for j in jobs
    ]


# ---------------------------------------------------------------------------
# POST /admin/v1/image-jobs/{job_id}/retry|cancel|approve|reject
# ---------------------------------------------------------------------------


@router.post(
    "/image-jobs/{job_id}/retry",
    response_model=ImageJobActionResponse,
    summary="Retry a failed or dead-letter image job",
)
async def retry_image_job(
    job_id: UUID,
    _auth: AdminAuth,
    uow: UowDep,
) -> ImageJobActionResponse:
    """Reset a failed job to 'queued' for regeneration (if attempts allow).

    Delegates to ``ImageQCService.mark_regenerate``.
    """
    svc = ImageQCService(uow)
    try:
        updated = await svc.mark_regenerate(job_id=job_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ImageJobActionResponse(
        job_id=job_id,
        action="retry",
        status=updated.status,
        message="job re-queued for regeneration",
    )


@router.post(
    "/image-jobs/{job_id}/cancel",
    response_model=ImageJobActionResponse,
    summary="Cancel a queued or running image job",
)
async def cancel_image_job(
    job_id: UUID,
    _auth: AdminAuth,
    uow: UowDep,
) -> ImageJobActionResponse:
    """Cancel an image job that has not yet completed."""
    job = await uow.image_jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"image_job {job_id} not found",
        )
    if job.status not in {"queued", "running"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"cannot cancel job in status '{job.status}'; must be queued or running",
        )
    updated = await uow.image_jobs.update_status(
        job_id, status="cancelled", expected_version=job.version
    )
    await uow.commit()
    return ImageJobActionResponse(
        job_id=job_id,
        action="cancel",
        status=updated.status,
        message="job cancelled",
    )


@router.post(
    "/image-jobs/{job_id}/approve",
    response_model=ImageJobActionResponse,
    summary="Manually approve an image job's gallery item",
)
async def approve_image_job(
    job_id: UUID,
    _auth: AdminAuth,
    uow: UowDep,
) -> ImageJobActionResponse:
    """Find the gallery item linked to this job and approve it.

    Delegates to ``ImageQCService.approve`` on the most-recent gallery item
    for the job.
    """
    job = await uow.image_jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"image_job {job_id} not found",
        )
    items = await uow.gallery_items.list_for_world(
        job.world_id, source_event_id=job.source_event_id
    )
    matched = [i for i in items if i.image_job_id == job_id]
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no gallery item found for image_job {job_id}",
        )
    svc = ImageQCService(uow)
    try:
        updated = await svc.approve(item_id=matched[-1].id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ImageJobActionResponse(
        job_id=job_id,
        action="approve",
        status=updated.display_status,
        message="gallery item approved",
    )


@router.post(
    "/image-jobs/{job_id}/reject",
    response_model=ImageJobActionResponse,
    summary="Manually reject an image job's gallery item",
)
async def reject_image_job(
    job_id: UUID,
    _auth: AdminAuth,
    uow: UowDep,
) -> ImageJobActionResponse:
    """Find the gallery item linked to this job and reject it."""
    job = await uow.image_jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"image_job {job_id} not found",
        )
    items = await uow.gallery_items.list_for_world(
        job.world_id, source_event_id=job.source_event_id
    )
    matched = [i for i in items if i.image_job_id == job_id]
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no gallery item found for image_job {job_id}",
        )
    svc = ImageQCService(uow)
    try:
        updated = await svc.reject(item_id=matched[-1].id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ImageJobActionResponse(
        job_id=job_id,
        action="reject",
        status=updated.display_status,
        message="gallery item rejected",
    )


# ---------------------------------------------------------------------------
# GET /admin/v1/gallery
# ---------------------------------------------------------------------------


@router.get(
    "/gallery",
    response_model=list[GalleryItemRead],
    summary="List gallery items for a world",
)
async def list_gallery(
    _auth: AdminAuth,
    uow: UowDep,
    world_id: Annotated[UUID, Query(description="World UUID")],
    *,
    display_status: Annotated[
        str | None,
        Query(
            description=(
                "Filter by display_status: auto_selected|user_selected|rejected|hidden|superseded"
            )
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[GalleryItemRead]:
    """Return gallery items for the given world, optionally filtered by display_status."""
    items = await uow.gallery_items.list_for_world(
        world_id,
        display_status=display_status,
        limit=limit,
        offset=offset,
    )
    return [
        GalleryItemRead(
            id=i.id,
            world_id=i.world_id,
            image_job_id=i.image_job_id,
            asset_object_id=i.asset_object_id,
            source_event_id=i.source_event_id,
            source_scene_id=i.source_scene_id,
            asset_class=i.asset_class,
            display_status=i.display_status,
            is_canonical_illustration=i.is_canonical_illustration,
            qc_passed=i.qc_passed,
            qc_report=dict(i.qc_report),
            created_at=i.created_at,
            version=i.version,
        )
        for i in items
    ]


# ---------------------------------------------------------------------------
# GET /admin/v1/visual-profiles
# ---------------------------------------------------------------------------


@router.get(
    "/visual-profiles",
    response_model=list[VisualProfileRead],
    summary="List visual profiles for a world",
)
async def list_visual_profiles(
    _auth: AdminAuth,
    uow: UowDep,
    world_id: Annotated[UUID, Query(description="World UUID")],
    *,
    subject_type: Annotated[
        str | None,
        Query(description="Filter by subject_type: character|location|world"),
    ] = None,
    subject_id: Annotated[
        UUID | None,
        Query(description="Filter to a specific subject entity UUID"),
    ] = None,
) -> list[VisualProfileRead]:
    """Return visual profiles for the given world.

    If both ``subject_type`` and ``subject_id`` are provided, returns the active
    profile for that subject.  World-wide listing is not yet exposed by the
    VisualProfileRepository Protocol; returns empty list in that case.
    A follow-up task should add ``list_for_world()`` to the Protocol.
    """
    if subject_type is not None and subject_id is not None:
        profile = await uow.visual_profiles.get_active(world_id, subject_type, subject_id)
        if profile is None:
            return []
        return [_profile_read(profile)]

    return []


def _profile_read(p: Any) -> VisualProfileRead:
    return VisualProfileRead(
        id=p.id,
        world_id=p.world_id,
        subject_type=p.subject_type,
        subject_id=p.subject_id,
        profile_version=p.profile_version,
        valid_from_event_id=p.valid_from_event_id,
        supersedes_profile_id=p.supersedes_profile_id,
        style_spec=dict(p.style_spec),
        negative_constraints=list(p.negative_constraints),
        reference_asset_ids=list(p.reference_asset_ids),
        status=p.status,
        created_at=p.created_at,
        version=p.version,
    )


__all__ = ["router"]
