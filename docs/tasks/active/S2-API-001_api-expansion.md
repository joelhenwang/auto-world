# `S2-API-001` — Stage 2 API expansion

**Stage:** 2  
**Workstream:** API  
**Status:** COMPLETE  
**Depends:** S2-ORCH-001  
**AGENTS conceptual branch:** `task/S2-API-001-api-expansion`  
**Implementation branch:** `cursor/s2-api-001-expansion-085f`

## Objective

Additive REST/WebSocket queries for clock/day progress, map/routes, goals/plans/commitments, beliefs, relationships, NPCs, diaries, Director hooks (mode-gated), advance day/run-until, pause/resume.

## Delivered

- `GET /api/v1/worlds/{id}/day-progress`
- `GET /api/v1/worlds/{id}/map`
- `GET /api/v1/worlds/{id}/characters/{cid}` (+ beliefs, relationships, diaries)
- `GET /api/v1/worlds/{id}/npcs` (+ detail)
- `GET /api/v1/worlds/{id}/director` (watcher|director)
- `GET /api/v1/worlds/{id}/tasks/failures`
- `POST /api/v1/worlds/{id}/run-day`, `run-until-day`, `director/propose-event`
- Existing advance/pause/resume select Stage 2 runner for stage2 fixtures
- OpenAPI + frontend generated types updated
- Integration: `backend/tests/integration/test_stage2_api.py`

## Handoff

`docs/handoffs/2026-07-29_S2-API-001.md`
