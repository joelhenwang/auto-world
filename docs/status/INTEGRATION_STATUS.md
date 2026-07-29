# Integration Status

**Updated:** 2026-07-29T11:35:57Z
**Integration owner:** parent coding agent
**Integration branch/worktree:** `main` (task branch `cursor/s0-eng-001-repository-bootstrap-09ce`)
**Integration HEAD:** `0866d3743ef51874f42f7f817ba1ea6b4fa24d82` (task branch; awaiting merge to main)
**Target stage:** 0

## Contract baseline

| Contract | Frozen version/hash | Producer task | Consumers | Change allowed? |
|---|---|---|---|---|
| Monorepo layout | handbook v1.0 | S0-ENG-001 | all Stage 0 | additive packages |
| Domain contracts | — | S0-DOM-001 | DB/SIM/MODEL | not started |

## Task integration matrix

| Task ID | Branch | Owner | Status | Required predecessors | Files/contracts touched | Tests/evidence | Merge order |
|---|---|---|---|---|---|---|---:|
| S0-ENG-001 | `cursor/s0-eng-001-repository-bootstrap-09ce` | parent | IN_REVIEW | none | root bootstrap, `backend/**`, docs/status | uv sync / import / compose / ruff / basedpyright | 1 |
| S0-ENG-002 | — | — | BLOCKED | S0-ENG-001 | config/static quality | — | 2+ |
| S0-DOM-001 | — | — | BLOCKED | S0-ENG-001 | domain contracts | — | 2+ |
| S0-QA-001 | — | — | BLOCKED | S0-ENG-001 | test harness | — | 2+ |

## Pending generated artefacts

| Artefact | Producer | Expected path | Regeneration command | Required before task(s) |
|---|---|---|---|---|
| uv.lock | S0-ENG-001 | `/uv.lock` | `uv sync` | all Python tasks |
| JSON Schemas | S0-DOM-001 | `docs/generated/domain-schemas/` | TBD | consumers |
| OpenAPI/client | S0-API-001 | `docs/generated/openapi.json` | TBD | frontend |
| Migration SQL | S0-DB-* | `docs/generated/database-schema.sql` | TBD | gate |
| Seed manifest | S0-CONTENT-001 | `seed/` | TBD | runner |

## Known overlap/conflict plan

| Paths/contracts | Tasks | Designated final owner | Merge strategy |
|---|---|---|---|
| `pyproject.toml` / lockfile | S0-ENG-001 then S0-ENG-002 | ENG | sequential; ENG-002 extends tooling |
| `backend/tests/conftest.py` | S0-ENG-001 placeholder → S0-QA-001 | QA | QA owns fixtures after merge |

## Integration checkpoints

### Checkpoint 1 — contracts

- [ ] schema hashes match freeze;
- [ ] generated artefacts committed/reproducible;
- [ ] consumer compile tests pass.

### Checkpoint 2 — subsystem

- [ ] task tests pass on integration branch;
- [ ] migrations upgrade clean and fixture databases;
- [ ] no duplicate provider/domain abstractions.

### Checkpoint 3 — vertical slice

- [ ] stage scenario runs end to end;
- [ ] restart/idempotency/failure paths pass;
- [ ] evidence bundle updated.

## Exact integration commands

```bash
uv sync
uv run python -c "import fictional_world"
docker compose config
uv run ruff format --check .
uv run ruff check .
```

## Current failures

None recorded. See `KNOWN_FAILURES.md`.
