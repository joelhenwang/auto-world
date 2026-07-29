# `S0-ENG-001` — Repository bootstrap

**Stage:** `0`  
**Workstream:** `ENG`  
**Status:** `IN_PROGRESS`  
**Priority:** `P0`  
**Owner:** parent coding agent  
**Reviewer(s):** parent/integration agent  
**Branch/worktree:** `cursor/s0-eng-001-repository-bootstrap-09ce` (cloud branch policy; AGENTS.md §9 conceptual name `task/S0-ENG-001-repository-bootstrap`)  
**Upstream commit:** `89960fb38dadc1e9026af6392d6b4a1519539854`  
**Target merge order:** first Stage 0 task; unblocks `S0-ENG-002`, `S0-DOM-001`, `S0-QA-001`

---

## 1. Objective

```text
Bootstrap the monorepo so a clean clone can `uv sync`, import the
`fictional_world` package, and validate a PostgreSQL+pgvector Compose
skeleton — without domain, ORM, migration, or agent code.
```

## 2. Why this task exists

- Requirements: reproducible development environment (Stage 0 §2); handbook layout (`19` §2).
- Stage gate items: Stage 0 §8 “clean clone/bootstrap succeeds”; foundation of all later Stage 0 work.
- Risks mitigated: inconsistent layouts; missing lockfile; agents inventing ad-hoc package trees.
- Upstream/downstream tasks: none upstream; downstream `S0-ENG-002`, `S0-DOM-001`, `S0-QA-001` (parallel per `25` §5).

## 3. Required reading

1. Repository `AGENTS.md`;
2. `25_STAGE_0_FOUNDATION.md` §6 S0-ENG-001, §7 sequence, §8 exit gate;
3. `19_REPOSITORY_STRUCTURE_ENGINEERING_STANDARDS_AND_CONFIG.md` §2–§3, §7–§8;
4. `20_LOCAL_DEVELOPMENT_DOCKER_CI_AND_DEPLOYMENT.md` §3–§5;
5. `24_MASTER_IMPLEMENTATION_PLAN.md`;
6. `35` / `36` / `34` templates for packets, status, handoff.

## 4. Frozen contracts

| Contract | Version/hash/commit | Owner | Allowed change |
|---|---|---|---|
| Monorepo layout (`19` §2) | handbook v1.0 | ENG | additive packages only |
| Package name `fictional_world` | handbook v1.0 | ENG | none without ADR |
| Domain schemas | N/A | DOM | not in this task |
| Database schema | N/A | DB | not in this task |

## 5. Scope

### In scope

- Root `pyproject.toml` + `uv.lock` (Python 3.12, uv-managed).
- `backend/src/fictional_world` package skeleton with top-level empty subpackages from `19` §2.
- `backend/tests/` folder tree + `conftest.py` placeholder.
- Root `.env.example`, `.gitignore`, `.editorconfig`, Makefile thin aliases, `compose.yaml` PostgreSQL+pgvector skeleton.
- README development quickstart.
- Minimal Ruff / basedpyright wiring (boundary: full static-quality gate is `S0-ENG-002`).
- `docs/status/*` Stage 0 kickoff files and this task packet.

### Explicitly out of scope

- Domain contracts / Pydantic models (`S0-DOM-001`).
- Alembic, ORM models, migrations (`S0-DB-*`).
- pydantic-settings profiles, pre-commit, full strict type gate (`S0-ENG-002`).
- Test harness / fakes / testcontainers (`S0-QA-001`).
- Model gateway, agents, LangGraph, FastAPI app body, seed importer.
- Frontend package bootstrap.

## 6. File/path ownership

### Writable

```text
pyproject.toml
uv.lock
compose.yaml
compose.override.yaml.example
.env.example
.gitignore
.editorconfig
Makefile
README.md
backend/**
docs/tasks/active/S0-ENG-001_repository-bootstrap.md
docs/status/**
docs/handoffs/**
AGENTS.md   # only if a genuine new Cursor Cloud caveat emerges
```

### Read-only dependencies

```text
AGENTS.md
autonomous_world_build_handbook_v1_0/19_*.md
autonomous_world_build_handbook_v1_0/20_*.md
autonomous_world_build_handbook_v1_0/24_*.md
autonomous_world_build_handbook_v1_0/25_*.md
autonomous_world_build_handbook_v1_0/34_*.md
autonomous_world_build_handbook_v1_0/35_*.md
autonomous_world_build_handbook_v1_0/36_*.md
prototypes/**   # existing map-ingestion prototype; do not relocate
seed/**         # existing seed assets; do not alter
docs/adr/**
docs/tasks/active/MAP-INGEST-001_*.md
```

### Shared/generated files

```text
uv.lock — produced by `uv sync`; committed with this task
```

## 7. Data and migration ownership

```text
New tables/columns/indexes: none
Migration revision reservation: none
Backfill/rebuild: none
Fixture updates: none
No database change: yes
```

## 8. Interface inputs and outputs

### Inputs

```text
Handbook layout and Stage 0 bootstrap commands; host Python 3.12 + uv + Docker.
```

### Outputs

```text
Installable `fictional_world` package; Compose Postgres skeleton; status/task docs.
```

### Errors/fallbacks

```text
Bootstrap failures surface as command exit codes (uv sync / import / compose config).
```

### Idempotency/concurrency

```text
Not applicable (no runtime mutation). Re-running `uv sync` must remain safe.
```

## 9. Security, privacy, perspective, and content constraints

- [x] No cross-character access beyond frozen policy. (N/A — no character runtime)
- [x] Server-side role authorization. (N/A)
- [x] Model/memory/user text treated as untrusted. (N/A)
- [x] No secret/key/raw sensitive prompt logging.
- [x] Remote-provider data profile is allowed. (N/A — key slot empty in `.env.example`)
- [x] No model direct state mutation. (N/A)
- [x] High-impact effect privilege enforced. (N/A)
- [x] Young-adult/soft-dark content policy maintained. (N/A)
- [x] Not applicable items explained below.

Notes:

```text
`.env.example` must contain placeholder names and safe defaults only — never real secrets.
Never commit a real `.env`.
```

## 10. Implementation sequence

1. Create task packet and Stage 0 status files.
2. Add `pyproject.toml` and `backend/src/fictional_world` skeleton.
3. Add test folder tree + `conftest.py`.
4. Add root config: `.gitignore`, `.editorconfig`, `.env.example`, `compose.yaml`, Makefile.
5. Update README with verified development quickstart.
6. Run `uv sync`; commit `uv.lock`.
7. Verify import + `docker compose config` (+ ruff if wired).
8. Write session handoff; open PR.

## 11. Test matrix

| Test type | Scenario | Expected result | File/command |
|---|---|---|---|
| Unit | N/A — no domain logic | — | — |
| Property/invariant | N/A | — | — |
| Integration | N/A (Compose validates only) | config valid | `docker compose config` |
| Migration | N/A | — | — |
| Fault/idempotency | N/A | — | — |
| Security/leakage | `.env.example` has no secrets | placeholders only | manual review |
| Bootstrap | clean uv sync + import | success | `uv sync`; `uv run python -c "import fictional_world"` |
| Static (minimal) | ruff format/check if wired | pass | `uv run ruff format --check .`; `uv run ruff check .` |

## 12. Required commands

```bash
# environment/bootstrap
uv sync

# targeted tests
uv run python -c "import fictional_world"
docker compose config

# formatting/lint/type (minimal; full gate is S0-ENG-002)
uv run ruff format --check .
uv run ruff check .

# integration/migration/fault
# not applicable for S0-ENG-001

# generated artefact no-diff
# uv.lock committed after sync
```

## 13. Acceptance criteria

- [ ] `uv sync` completes and `uv.lock` is committed.
- [ ] `uv run python -c "import fictional_world"` succeeds.
- [ ] `docker compose config` validates Compose skeleton.
- [ ] Top-level empty packages from `19` §2 exist under `backend/src/fictional_world/`.
- [ ] Test folders from `19` §2 exist with `conftest.py` placeholder.
- [ ] `.env.example` matches `20` §4 shape with no secrets.
- [ ] No domain/ORM/migration/agent code added.
- [ ] Task packet, status docs, and session handoff present.
- [ ] No Critical/High reviewer finding remains.

## 14. Deliverables

- code: `backend/src/fictional_world/**`, `backend/tests/**`, root bootstrap files;
- migrations: none;
- tests: folder skeleton + `conftest.py` only;
- fixtures: none;
- generated artefacts: `uv.lock`;
- docs/ADR: task packet, `docs/status/*`, handoff;
- evidence: command results in handoff;
- handoff: `docs/handoffs/2026-07-29_S0-ENG-001_repository-bootstrap.md`.

## 15. Known risks and likely pitfalls

- Creating deep domain placeholder trees contradicts `19` §3 (“do not create dozens of placeholder modules”); mitigate by adding only top-level packages from §2.
- Cloud branch naming (`cursor/...-09ce`) vs AGENTS.md `task/...`; document both in packet/handoff.
- Accidental commit of `.env` or Docker volume data; `.gitignore` must cover both.

## 16. Blocker/escalation rule

- solve `B0` locally;
- report `B1–B5` using the format in `31`;
- do not invent a breaking workaround;
- continue independent work where safe;
- stop immediately for canonical corruption, secret leakage, or unsafe privilege behavior.

## 17. Handoff requirements

The owner must complete `34_SESSION_HANDOFF_TEMPLATE.md` and include:

- final commits/diff paths;
- migrations/generated artefacts;
- all commands/results;
- tests not run;
- contract deviations;
- integration order/conflicts;
- next exact action.

## 18. Parent verification

To be filled after integration:

```text
Reviewed by:
Merged commit:
Acceptance commands rerun:
Findings:
Traceability updated:
Status: VERIFIED / RETURNED
```
