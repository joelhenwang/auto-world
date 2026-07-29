# Integration Status

**Updated:** 2026-07-29T18:45:00Z  
**Integration owner:** parent coding agent  
**Integration branch/worktree:** `main` + `cursor/s1-db-001-5704`  
**Integration HEAD:** pending S1-DB-001 merge  
**Target stage:** 1

## Contract baseline

| Contract | Frozen version/hash | Producer task | Consumers | Change allowed? |
|---|---|---|---|---|
| Stage 0 foundation | FROZEN (S0-QA-002) | Stage 0 | Stage 1 | additive only |
| Stage 1 action/scene schema | `0003_stage1_action_scene_tables` | S1-DB-001 | SIM-002/ORCH/API | in review |

## Task integration matrix

| Task ID | Branch | Owner | Status | Required predecessors | Files/contracts touched | Tests/evidence | Merge order |
|---|---|---|---|---|---|---|---:|
| S1-DB-001 | `cursor/s1-db-001-5704` | parent | IN_REVIEW | S0-QA-002 | migration 0003, scene repos | integration schema tests | 1 |
| S1-KNOW-001 | — | — | READY | DB contracts sketched | context assembler | — | 2 |
| S1-MODEL-001 | — | — | READY | Stage 0 gateway | prompts/corpus | — | 2 |
| S1-SIM-001 | — | — | READY | ActionProposal domain | pure assembly | — | 2 |
| remaining Stage 1 | — | — | BLOCKED | per `26` graph | — | — | 3+ |

## Exact integration commands

```bash
uv sync
uv run ruff check backend scripts tools
uv run basedpyright
uv run pytest
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini check
```

## Current failures

None for S1-DB-001 scope.
