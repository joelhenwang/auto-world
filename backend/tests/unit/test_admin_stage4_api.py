"""Offline unit tests for the Stage 4 admin API (S4-API-001).

These tests run without PostgreSQL or external services.  All repositories are
mocked via AsyncMock.  The capability registry is injected directly into app.state.

Tests cover:
- auth enforcement (enabled / disabled)
- model-endpoint listing (registry present / absent)
- worker listing
- host drain
- image-job listing, retry, cancel, approve, reject
- gallery listing
- visual-profile listing
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from fictional_world.application.models.capability_registry import (
    EndpointProviderKind,
    ModelCapabilityRegistry,
    ModelEndpointCapability,
)
from fictional_world.application.models.roles import ModelRole
from fictional_world.config.settings import ApiSettings, AppSettings, AuthSettings
from fictional_world.domain.images.persistence import (
    GalleryItemRecord,
    ImageJobRecord,
    VisualProfileRecord,
)
from fictional_world.domain.tasks.workers import HostRecord, WorkerRecord
from fictional_world.interfaces.http.app import create_app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 7, 30, 10, 0, 0, tzinfo=UTC)

WORLD_ID = uuid4()
HOST_ID = uuid4()
WORKER_ID = uuid4()
JOB_ID = uuid4()
GALLERY_ID = uuid4()
ASSET_ID = uuid4()
PROFILE_ID = uuid4()
ENTITY_ID = uuid4()
EVENT_ID = uuid4()


def _basic_auth_header(password: str, username: str = "admin") -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def _make_settings(*, auth_enabled: bool = False, password: str = "") -> AppSettings:
    return AppSettings(
        api=ApiSettings(bind_host="127.0.0.1", bind_port=8000),
        auth=AuthSettings(
            enabled=auth_enabled,
            local_admin_password=password,
            allow_insecure_public_bind=True,
        ),
    )


def _make_uow() -> MagicMock:
    """Return a minimal mock UoW with async repo attributes."""
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    # Image repos
    uow.image_jobs = MagicMock()
    uow.image_jobs.get = AsyncMock(return_value=None)
    uow.image_jobs.list_by_status = AsyncMock(return_value=[])
    uow.image_jobs.update_status = AsyncMock()

    uow.gallery_items = MagicMock()
    uow.gallery_items.list_for_world = AsyncMock(return_value=[])
    uow.gallery_items.get = AsyncMock(return_value=None)
    uow.gallery_items.update_display_status = AsyncMock()

    uow.visual_profiles = MagicMock()
    uow.visual_profiles.get_active = AsyncMock(return_value=None)

    # Worker / host repos
    uow.workers = MagicMock()
    uow.workers.find_lost = AsyncMock(return_value=[])
    uow.workers.drain = AsyncMock()

    uow.hosts = MagicMock()
    uow.hosts.find_by_key = AsyncMock(return_value=None)

    return uow


def _make_image_job(
    *,
    job_id: UUID = JOB_ID,
    world_id: UUID = WORLD_ID,
    job_status: str = "queued",
    attempt: int = 0,
    max_attempts: int = 3,
) -> ImageJobRecord:
    return ImageJobRecord(
        id=job_id,
        world_id=world_id,
        idempotency_key=f"test-key-{job_id}",
        source_event_id=EVENT_ID,
        asset_class="event_cg",
        status=job_status,
        priority=50,
        generation_number=1,
        attempt=attempt,
        max_attempts=max_attempts,
        version=1,
    )


def _make_gallery_item(
    *,
    item_id: UUID = GALLERY_ID,
    job_id: UUID = JOB_ID,
    world_id: UUID = WORLD_ID,
    display_status: str = "auto_selected",
) -> GalleryItemRecord:
    return GalleryItemRecord(
        id=item_id,
        world_id=world_id,
        image_job_id=job_id,
        asset_object_id=ASSET_ID,
        source_event_id=EVENT_ID,
        asset_class="event_cg",
        display_status=display_status,
        qc_passed=True,
        version=1,
    )


def _make_worker_record(
    *,
    worker_id: UUID = WORKER_ID,
    host_id: UUID = HOST_ID,
    status: str = "active",
) -> WorkerRecord:
    return WorkerRecord(
        id=worker_id,
        host_id=host_id,
        worker_key=f"worker-{worker_id}",
        capabilities=("text_large",),
        status=status,
        heartbeat_at=_NOW,
        registered_at=_NOW,
    )


def _make_host_record(
    *,
    host_id: UUID = HOST_ID,
    host_key: str = "strix-halo-a",
) -> HostRecord:
    return HostRecord(
        id=host_id,
        host_key=host_key,
        capabilities=("text_large",),
        status="active",
        first_seen_at=_NOW,
        last_seen_at=_NOW,
    )


def _make_endpoint_capability() -> ModelEndpointCapability:
    return ModelEndpointCapability(
        endpoint_id="halo-a-1",
        host_id="strix-halo-a",
        provider_kind=EndpointProviderKind.LOCAL_OPENAI_COMPAT,
        base_url="http://strix-halo-a:8080",
        model_id="model-7b-q4",
        model_hash=None,
        roles=(ModelRole.CHARACTER_DECISION,),
        context_limit=20480,
        structured_output_mode="NATIVE_STRICT",
        quantization="Q4_K_M",
        max_concurrency=2,
        health="healthy",
        loaded_state="loaded",
        software_versions=(("vllm", "0.4.0"),),
        privacy_policy="local_private",
        cost_class="local_gpu",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_uow() -> MagicMock:
    return _make_uow()


@pytest.fixture
async def client_no_auth(mock_uow: MagicMock) -> AsyncClient:
    """App with auth disabled; UoW patched."""
    settings = _make_settings(auth_enabled=False)
    engine = MagicMock()
    app = create_app(settings=settings, engine=engine)
    with patch(
        "fictional_world.interfaces.http.dependencies.SqlAlchemyUnitOfWork",
        return_value=mock_uow,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
async def client_auth_enabled(mock_uow: MagicMock) -> AsyncClient:
    """App with auth enabled; password = 'test-secret'."""
    settings = _make_settings(auth_enabled=True, password="test-secret")  # noqa: S106
    engine = MagicMock()
    app = create_app(settings=settings, engine=engine)
    with patch(
        "fictional_world.interfaces.http.dependencies.SqlAlchemyUnitOfWork",
        return_value=mock_uow,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_model_endpoints_no_auth_disabled(client_no_auth: AsyncClient) -> None:
    """When auth is disabled, /admin endpoints are accessible without credentials."""
    resp = await client_no_auth.get("/admin/v1/model-endpoints")
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.unit
async def test_model_endpoints_auth_required(client_auth_enabled: AsyncClient) -> None:
    """When auth is enabled, missing credentials returns 401."""
    resp = await client_auth_enabled.get("/admin/v1/model-endpoints")
    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
async def test_model_endpoints_wrong_password(client_auth_enabled: AsyncClient) -> None:
    """Wrong password returns 401."""
    resp = await client_auth_enabled.get(
        "/admin/v1/model-endpoints",
        headers={"Authorization": _basic_auth_header("wrong-password")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
async def test_model_endpoints_correct_password(client_auth_enabled: AsyncClient) -> None:
    """Correct password returns 200."""
    resp = await client_auth_enabled.get(
        "/admin/v1/model-endpoints",
        headers={"Authorization": _basic_auth_header("test-secret")},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /admin/v1/model-endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_model_endpoints_empty_no_registry(client_no_auth: AsyncClient) -> None:
    """Returns empty list when capability registry is not in app.state."""
    resp = await client_no_auth.get("/admin/v1/model-endpoints")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_model_endpoints_with_registry() -> None:
    """Returns serialised endpoints from the registry."""
    settings = _make_settings()
    engine = MagicMock()
    app = create_app(settings=settings, engine=engine)

    registry = ModelCapabilityRegistry()
    registry.upsert(_make_endpoint_capability())
    app.state.capability_registry = registry

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/admin/v1/model-endpoints")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    ep = data[0]
    assert ep["endpoint_id"] == "halo-a-1"
    assert ep["host_id"] == "strix-halo-a"
    assert ep["health"] == "healthy"
    assert ep["roles"] == ["character_decision"]
    assert ep["context_limit"] == 20480


# ---------------------------------------------------------------------------
# GET /admin/v1/workers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_workers_empty(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    mock_uow.workers.find_lost = AsyncMock(return_value=[])
    resp = await client_no_auth.get("/admin/v1/workers")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_workers_returns_records(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    worker = _make_worker_record()
    mock_uow.workers.find_lost = AsyncMock(return_value=[worker])

    resp = await client_no_auth.get("/admin/v1/workers")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["worker_key"] == worker.worker_key
    assert data[0]["status"] == "active"
    assert data[0]["host_id"] == str(HOST_ID)


# ---------------------------------------------------------------------------
# POST /admin/v1/hosts/{host_key}/drain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_drain_host_not_found(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    mock_uow.hosts.find_by_key = AsyncMock(return_value=None)
    resp = await client_no_auth.post("/admin/v1/hosts/nonexistent-host/drain")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_drain_host_success(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    host = _make_host_record(host_key="strix-halo-a")
    worker = _make_worker_record(host_id=host.id)
    mock_uow.hosts.find_by_key = AsyncMock(return_value=host)
    mock_uow.workers.find_lost = AsyncMock(return_value=[worker])
    drained_worker = WorkerRecord(
        **{**worker.model_dump(), "status": "draining", "drain_requested_at": _NOW}
    )
    mock_uow.workers.drain = AsyncMock(return_value=drained_worker)

    resp = await client_no_auth.post("/admin/v1/hosts/strix-halo-a/drain")
    assert resp.status_code == 200
    body = resp.json()
    assert body["host_key"] == "strix-halo-a"
    assert body["drained_workers"] == 1
    assert body["status"] == "draining"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_drain_host_skips_already_drained(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    host = _make_host_record(host_key="strix-halo-b")
    already_drained = _make_worker_record(host_id=host.id, status="drained")
    mock_uow.hosts.find_by_key = AsyncMock(return_value=host)
    mock_uow.workers.find_lost = AsyncMock(return_value=[already_drained])

    resp = await client_no_auth.post("/admin/v1/hosts/strix-halo-b/drain")
    assert resp.status_code == 200
    body = resp.json()
    assert body["drained_workers"] == 0
    mock_uow.workers.drain.assert_not_awaited()


# ---------------------------------------------------------------------------
# GET /admin/v1/image-jobs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_image_jobs_empty(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    resp = await client_no_auth.get(f"/admin/v1/image-jobs?world_id={WORLD_ID}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_image_jobs_returns_records(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    job = _make_image_job()
    mock_uow.image_jobs.list_by_status = AsyncMock(return_value=[job])

    resp = await client_no_auth.get(f"/admin/v1/image-jobs?world_id={WORLD_ID}&status=queued")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(JOB_ID)
    assert data[0]["status"] == "queued"
    assert data[0]["asset_class"] == "event_cg"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_image_jobs_unknown_status(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    resp = await client_no_auth.get(f"/admin/v1/image-jobs?world_id={WORLD_ID}&status=bogus_status")
    assert resp.status_code == 422


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_image_jobs_missing_world_id(client_no_auth: AsyncClient) -> None:
    resp = await client_no_auth.get("/admin/v1/image-jobs")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /admin/v1/image-jobs/{job_id}/retry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_retry_image_job_not_found(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    mock_uow.image_jobs.get = AsyncMock(return_value=None)
    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/retry")
    assert resp.status_code == 409
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_retry_image_job_exhausted_attempts(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    job = _make_image_job(job_status="dead_letter", attempt=3, max_attempts=3)
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/retry")
    assert resp.status_code == 409
    assert "exhausted" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_retry_image_job_success(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    job = _make_image_job(job_status="failed", attempt=1, max_attempts=3)
    updated_job = _make_image_job(job_status="queued", attempt=1, max_attempts=3)
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    mock_uow.image_jobs.update_status = AsyncMock(return_value=updated_job)

    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/retry")
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "retry"
    assert body["status"] == "queued"


# ---------------------------------------------------------------------------
# POST /admin/v1/image-jobs/{job_id}/cancel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_image_job_not_found(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    mock_uow.image_jobs.get = AsyncMock(return_value=None)
    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/cancel")
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_image_job_already_completed(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    job = _make_image_job(job_status="approved")
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/cancel")
    assert resp.status_code == 409
    assert "cannot cancel" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_cancel_image_job_success(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    job = _make_image_job(job_status="queued")
    cancelled_job = _make_image_job(job_status="cancelled")
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    mock_uow.image_jobs.update_status = AsyncMock(return_value=cancelled_job)

    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/cancel")
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "cancel"
    assert body["status"] == "cancelled"


# ---------------------------------------------------------------------------
# POST /admin/v1/image-jobs/{job_id}/approve
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_approve_image_job_no_gallery_item(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    job = _make_image_job(job_status="approved")
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    mock_uow.gallery_items.list_for_world = AsyncMock(return_value=[])

    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/approve")
    assert resp.status_code == 404
    assert "gallery item" in resp.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_approve_image_job_success(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    job = _make_image_job(job_status="approved")
    gallery_item = _make_gallery_item()
    approved_item = _make_gallery_item(display_status="user_selected")
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    mock_uow.gallery_items.list_for_world = AsyncMock(return_value=[gallery_item])
    mock_uow.gallery_items.get = AsyncMock(return_value=gallery_item)
    mock_uow.gallery_items.update_display_status = AsyncMock(return_value=approved_item)

    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/approve")
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "approve"
    assert body["status"] == "user_selected"


# ---------------------------------------------------------------------------
# POST /admin/v1/image-jobs/{job_id}/reject
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_reject_image_job_success(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    job = _make_image_job(job_status="approved")
    gallery_item = _make_gallery_item(display_status="user_selected")
    rejected_item = _make_gallery_item(display_status="rejected")
    mock_uow.image_jobs.get = AsyncMock(return_value=job)
    mock_uow.gallery_items.list_for_world = AsyncMock(return_value=[gallery_item])
    mock_uow.gallery_items.get = AsyncMock(return_value=gallery_item)
    mock_uow.gallery_items.update_display_status = AsyncMock(return_value=rejected_item)

    resp = await client_no_auth.post(f"/admin/v1/image-jobs/{JOB_ID}/reject")
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] == "reject"
    assert body["status"] == "rejected"


# ---------------------------------------------------------------------------
# GET /admin/v1/gallery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_gallery_empty(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    resp = await client_no_auth.get(f"/admin/v1/gallery?world_id={WORLD_ID}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_gallery_returns_items(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    item = _make_gallery_item()
    mock_uow.gallery_items.list_for_world = AsyncMock(return_value=[item])

    resp = await client_no_auth.get(f"/admin/v1/gallery?world_id={WORLD_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(GALLERY_ID)
    assert data[0]["display_status"] == "auto_selected"
    assert data[0]["qc_passed"] is True


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_gallery_missing_world_id(client_no_auth: AsyncClient) -> None:
    resp = await client_no_auth.get("/admin/v1/gallery")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /admin/v1/visual-profiles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_visual_profiles_empty(client_no_auth: AsyncClient, mock_uow: MagicMock) -> None:
    resp = await client_no_auth.get(f"/admin/v1/visual-profiles?world_id={WORLD_ID}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_visual_profiles_with_subject_not_found(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    mock_uow.visual_profiles.get_active = AsyncMock(return_value=None)
    resp = await client_no_auth.get(
        f"/admin/v1/visual-profiles?world_id={WORLD_ID}"
        f"&subject_type=character&subject_id={ENTITY_ID}"
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_visual_profiles_with_subject_found(
    client_no_auth: AsyncClient, mock_uow: MagicMock
) -> None:
    profile = VisualProfileRecord(
        id=PROFILE_ID,
        world_id=WORLD_ID,
        subject_type="character",
        subject_id=ENTITY_ID,
        profile_version=1,
        style_spec={"style": "fantasy"},
        negative_constraints=["blurry"],
        reference_asset_ids=[],
        status="active",
        version=1,
    )
    mock_uow.visual_profiles.get_active = AsyncMock(return_value=profile)

    resp = await client_no_auth.get(
        f"/admin/v1/visual-profiles?world_id={WORLD_ID}"
        f"&subject_type=character&subject_id={ENTITY_ID}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(PROFILE_ID)
    assert data[0]["subject_type"] == "character"
    assert data[0]["style_spec"] == {"style": "fantasy"}
    assert data[0]["negative_constraints"] == ["blurry"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_visual_profiles_missing_world_id(client_no_auth: AsyncClient) -> None:
    resp = await client_no_auth.get("/admin/v1/visual-profiles")
    assert resp.status_code == 422
