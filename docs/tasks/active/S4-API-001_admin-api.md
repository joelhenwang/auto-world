# `S4-API-001` — Model/worker/image administration API

**Stage:** 4  
**Workstream:** API  
**Status:** COMPLETE  
**Priority:** P0  
**Completed:** 2026-07-30 by S4-OPS-001/S4-API-001 subagent

## Objective

Additive authorized admin endpoints for endpoints/health, queues/leases, host drain,
image jobs, visual profiles, storage integrity. OpenAPI additive only.

## Acceptance

- [x] Admin router additive OpenAPI
- [x] Contract/API tests offline (31 unit tests, all passing)
- [x] No Stage 0–3 breaking changes

## Deliverables

- `backend/src/fictional_world/interfaces/http/routes/admin_stage4.py` — admin router
- `backend/tests/unit/test_admin_stage4_api.py` — 31 offline unit tests
- Router mounted in `app.py` at `/admin/v1`

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/admin/v1/model-endpoints` | List capability registry endpoints |
| GET | `/admin/v1/workers` | List all registered workers |
| POST | `/admin/v1/hosts/{host_key}/drain` | Drain all workers on a host |
| GET | `/admin/v1/image-jobs?world_id=` | List image jobs (filterable by status) |
| POST | `/admin/v1/image-jobs/{job_id}/retry` | Re-queue failed job |
| POST | `/admin/v1/image-jobs/{job_id}/cancel` | Cancel queued/running job |
| POST | `/admin/v1/image-jobs/{job_id}/approve` | Approve gallery item |
| POST | `/admin/v1/image-jobs/{job_id}/reject` | Reject gallery item |
| GET | `/admin/v1/gallery?world_id=` | List gallery items |
| GET | `/admin/v1/visual-profiles?world_id=` | List visual profiles |

## Known follow-ups

- `WorkerRepository.list_all()` — current implementation uses `find_lost` with 10-year grace period as a workaround; a dedicated method would be cleaner.
- `VisualProfileRepository.list_for_world()` — world-wide listing returns empty until this method is added to the Protocol and SQLAlchemy implementation.
