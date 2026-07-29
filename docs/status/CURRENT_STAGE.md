# Current Stage

**Updated:** 2026-07-29T11:32:18Z
**Updated by:** parent coding agent
**Repository:** autonomous-fictional-world (`/workspace`)
**Current branch:** `cursor/s0-eng-001-repository-bootstrap-09ce`
**HEAD:** `89960fb38dadc1e9026af6392d6b4a1519539854` (pre-bootstrap; update after commits)
**Working tree:** dirty during S0-ENG-001 implementation

## Stage

**Stage:** 0
**Stage name:** Foundation and Deterministic Contracts
**Stage status:** IN_PROGRESS
**Stage document:** `autonomous_world_build_handbook_v1_0/25_STAGE_0_FOUNDATION.md`
**Stage owner:** parent coding agent
**Target integration branch:** `main`
**Last verified stage tag:** NONE

## Current objective

Complete Stage 0 task `S0-ENG-001` (repository bootstrap): Python 3.12/uv project, importable `fictional_world` package skeleton, test folder tree, Compose PostgreSQL+pgvector skeleton, root config, and status docs — with no domain/ORM/agent code.

## Frozen contract versions

| Contract | Version/hash | Source path | Status | Owner |
|---|---|---|---|---|
| Domain schemas | — | — | DRAFT (not started) | S0-DOM-001 |
| Database schema/Alembic head | — | — | DRAFT (not started) | S0-DB-001 |
| Effect-command union | — | — | DRAFT (not started) | S0-DOM-001 / S0-SIM-001 |
| API/OpenAPI | — | — | DRAFT (not started) | S0-API-001 |
| Prompt catalog | — | — | DRAFT (not started) | later |
| Model capability snapshot | — | — | DRAFT (not started) | S0-MODEL-001 |
| Seed manifest | — | `seed/` assets only | DRAFT | S0-CONTENT-001 |
| Monorepo layout | handbook v1.0 | `19` §2 | CHANGING (bootstrap) | S0-ENG-001 |

## Runtime profile

| Item | Current value |
|---|---|
| Python/uv lock hash | pending `uv.lock` from S0-ENG-001 |
| Node/package lock hash | N/A (no frontend yet) |
| PostgreSQL version | Compose skeleton `pgvector/pgvector:pg16` (pinned image tag) |
| pgvector version | via `pgvector/pgvector:pg16` image |
| Orchestrator adapter | not started |
| Text provider/model | not started (OpenRouter smoke later) |
| Embedding provider/model | not started |
| Feature flags | not started (`S0-ENG-002`) |
| Migration head | none |
| Seed version | none (map asset only under `seed/assets/`) |

## Active tasks

| Task ID | Owner | Branch/worktree | Status | Dependencies | Next integration point |
|---|---|---|---|---|---|
| S0-ENG-001 | parent agent | `cursor/s0-eng-001-repository-bootstrap-09ce` | IN_PROGRESS | none | merge to `main` first |
| MAP-INGEST-001 | prior session | merged prototype on `main` | prototype complete | ADR-0001 | future MAP-INGEST-002 |

## Blocked tasks

| Task ID | Blocker ID | Evidence | Owner | Required decision/action |
|---|---|---|---|---|
| S0-ENG-002 | waits on S0-ENG-001 | `25` §4 graph | ENG | merge bootstrap |
| S0-DOM-001 | waits on S0-ENG-001 | `25` §4 graph | DOM | merge bootstrap |
| S0-QA-001 | waits on S0-ENG-001 | `25` §4 graph | QA | merge bootstrap |

## Latest verified baseline

```bash
# Pre-bootstrap: handbook integrity only
# From autonomous_world_build_handbook_v1_0/: sha256sum -c CHECKSUMS.sha256
# (00_README.md / 01_AGENTS.md relocated entries expected to fail-to-open)
```

**Result timestamp:** 2026-07-29T11:32:18Z
**Evidence path:** pending S0-ENG-001 handoff
**Known excluded tests:** no application test suite yet

## Current integration risks

- Branch naming: cloud agents must use `cursor/<name>-09ce`; handbook AGENTS.md §9 prefers `task/<id>-<slug>` — document both; do not dual-branch.
- Existing `prototypes/map_ingestion` is a separate uv project; root bootstrap must not break or absorb it silently.
- Do not let S0-ENG-001 grow into S0-ENG-002 (settings/pre-commit) or S0-DOM-001 (contracts).

## Next exact actions

1. Finish S0-ENG-001 deliverables; verify `uv sync`, import, `docker compose config`.
2. Merge/PR bootstrap; then open parallel packets for `S0-ENG-002`, `S0-DOM-001`, `S0-QA-001`.
3. Do not start `S0-DB-*` until `S0-DOM-001` contracts exist.

## Latest handoffs

- `docs/handoffs/2026-07-29_S0-ENG-001_repository-bootstrap.md` (created at session end)

## Notes that a fresh session must know

- Application code did not exist before this session; handbook + ADR-0001 map prototype only.
- Docker daemon does not auto-start on this VM; `sudo service docker start` then `sudo docker ...`.
- Package name is `fictional_world` under `backend/src/` per `19` §2 (not `worldsim`).
