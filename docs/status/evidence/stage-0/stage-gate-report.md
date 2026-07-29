# Stage 0 Gate Report — Foundation

**Decision:** PASS  
**Report date:** 2026-07-29T17:45:02Z  
**Stage owner:** parent coding agent  
**QA owner:** parent coding agent  
**Integration commit:** `6b54e4771fc3668e3e288eef99ca31ee514165af` (S0-QA-002 tip; promote after merge to main)  
**Release/tag candidate:** Stage 0 foundation (post-merge main)  
**Previous verified stage/tag:** none (first stage)  
**Environment/profile:** `stage0` / development  
**Handbook/stage version:** autonomous_world_build_handbook_v1_0 / `25_STAGE_0_FOUNDATION.md`

## 1. Intended outcome

Stage 0 delivers a durable foundation: PostgreSQL canon, atomic event commit, task/outbox leases, Caldris seed, deterministic phase runner, minimal API/CLI, and observability baseline — without live-model character loops.

Demonstrated vertical slice: seed Caldris → advance one scripted phase → seal snapshot → write Mira memory → pause/resume and reconcile without duplicate events.

## 2. Scope delivered

| Task ID | Status | Deliverable | Evidence |
|---|---|---|---|
| S0-ENG-001..002 | VERIFIED | bootstrap + config/static quality | prior PRs on main |
| S0-DOM-001 | VERIFIED | domain contracts + schemas | `docs/generated/domain-schemas/` |
| S0-QA-001 | VERIFIED | harness/fakes | `backend/tests/unit/test_harness.py` |
| S0-DB-001..003 | VERIFIED | Alembic + core schema + UoW | `0002_core_stage0_tables` |
| S0-SIM-001..002 | VERIFIED | effects + event commit | `test_event_commit.py` |
| S0-ORCH-001..002 | VERIFIED | tasks/outbox + phase runner | `test_phase_runner.py` |
| S0-MODEL-001..002 | VERIFIED | gateway + fake/OpenRouter | contract/unit tests |
| S0-CONTENT-001 | VERIFIED | Caldris seed importer | `test_seed_import.py` |
| S0-API-001 | VERIFIED | FastAPI/CLI | `test_api_*.py` |
| S0-OPS-001 | VERIFIED | logging/redaction/bind safety | `test_logging_redaction.py` |
| S0-QA-002 | IN_REVIEW | gate scenario + evidence | this report |

## 3. Explicit exclusions

Still excluded (Stage 0 non-goals): character LLM graphs, WebSocket UI, Temporal, images/ComfyUI, long-term RAG, multi-day soak. No accidental premature Stage 1 dependencies introduced.

## 4. Build and version manifest

See `docs/status/evidence/stage-0/version-manifest.json`.

| Component | Version/hash |
|---|---|
| Git commit | `6b54e4771fc3668e3e288eef99ca31ee514165af` |
| uv.lock | `d2ecd55bfc6fdf56f4c36ebaa22f764a5ee11c5e05858c1b0f293eaeeed93c2d` |
| PostgreSQL/pgvector | `pgvector/pgvector:pg16` |
| Alembic head | `0002_core_stage0_tables` |
| OpenAPI | `9b2ae479a4c60a9adf4e4f0d7c82af99250dcb2e34e3e2efb316ab32dbbe2641` |
| DB schema SQL | `5f8b48b8c892d4af439128444a95d2abe70bb8be173018c96b9cc6a03365a4a1` |
| Seed | `caldris-embervale-v1` / fixture `stage0` |
| Orchestrator adapter | `DeterministicPhaseRunner` |

## 5. Environment and data

- Linux cloud agent / Docker Engine with fuse-overlayfs  
- Feature flags: Stage 0 profile (director/images/temporal off)  
- Model mode: fake for default tests; OpenRouter live opt-in only  
- Network blocked in ordinary tests (`pytest-socket` / `block_network`)  
- Seed pack deterministic UUIDv5 keys  

## 6. Static and build quality

| Check | Command | Result | Artefact |
|---|---|---|---|
| Ruff | `uv run ruff check backend scripts tools` | PASS | `evidence/stage-0/ruff.txt` |
| Ruff format | `uv run ruff format --check …` | PASS | `evidence/stage-0/ruff-format.txt` |
| basedpyright | `uv run basedpyright` | PASS | `evidence/stage-0/basedpyright.txt` |
| Pytest | `uv run pytest` | **99 passed, 1 deselected** | `evidence/stage-0/pytest.txt`, `pytest-junit.xml` |
| Architecture imports | `test_import_boundaries.py` | PASS | pytest junit |
| Secret hygiene | `test_secret_hygiene.py` | PASS | pytest junit |

## 7. Migration and persistence evidence

- [x] clean upgrade (`verify_migrations.py`)  
- [x] downgrade -1 + re-upgrade  
- [x] generated SQL present  
- [x] constraints covered by schema tests  

| Scenario | Command | Result | Evidence |
|---|---|---|---|
| Alembic cycle | `uv run python scripts/verify_migrations.py` | PASS | `evidence/stage-0/migrations.txt` |

## 8. Functional scenarios

| Scenario ID | Seed/model | Expected | Actual | Result | Artefact |
|---|---|---|---|---|---|
| `stage0-foundation-v1` | caldris / none | seed+advance+invariants | passed | PASS | `test_stage0_foundation.py` |
| API world advance | caldris / none | reads + 2 advances | passed | PASS | `test_api_worlds.py` |
| Phase runner suite | caldris / none | pause/resume/idempotent | passed | PASS | `test_phase_runner.py` |

## 9. Hard invariants and consistency

| Invariant/test | Result | Evidence |
|---|---|---|
| Atomic event commit | PASS | `test_event_commit.py` |
| Duplicate delivery safe | PASS | event/task/outbox/phase tests |
| Task lease exclusive | PASS | `test_two_workers_cannot_claim_same_task` |
| Snapshot insert-once | PASS | `test_snapshot_insert_once_is_idempotent` |
| Consistency audit empty | PASS | `test_consistency_audit.py` / `audit_stage0_consistency()` |

Hard findings: **none**.

## 10. Knowledge, privacy, and security

| Test | Result | Evidence |
|---|---|---|
| Secret/log redaction | PASS | `test_logging_redaction.py`, `test_secret_hygiene.py` |
| Loopback bind default | PASS | `test_settings.py` |
| Cross-character LLM leakage | N/A Stage 0 (no character graphs) | waived as not applicable |
| Player perspective filtering | N/A Stage 0 | Stage 1 |

## 11. Restart, idempotency, and fault injection

| Failure point | Method | Result | Evidence |
|---|---|---|---|
| after snapshot / before ack | `stop_after_snapshot` + resume | PASS | `test_crash_after_snapshot_then_resume_no_duplicate_tick` |
| duplicate phase advance | re-advance / reconcile | PASS | `test_phase_runner.py` |
| duplicate event idempotency | commit twice | PASS | `test_event_commit.py` |
| two-worker claim | concurrent claim | PASS | `test_task_queue.py` |
| provider timeout/429 | fake gateway scripts | PASS | model fake contract tests |

## 12. Performance and growth

Not gated for Stage 0. No soak budgets claimed.

## 13. Model and narrative quality

Deterministic/fake paths only for promotion. Live OpenRouter remains opt-in (`openrouter_live` deselected in default suite).

## 14. Human review

Not required for Stage 0 durability gate (intentionally boring demonstration).

## 15. Open failures, risks, and technical debt

| ID | Severity | Impact | Blocks promotion? | Follow-up |
|---|---|---|---|---|
| APP↔sqlalchemy.exc coupling | low | application imports IntegrityError | no | Stage 1 ports cleanup |
| Scenario harness sync runner | low | async-only foundation runner | no | optional sync façade |

## 16. Waivers

| Gate | Reason | Risk | Expiry/follow-up | Approved by |
|---|---|---|---|---|
| Character secrecy/leakage suite | no Stage 0 character graphs | low | Stage 1 | stage owner |
| Live OpenRouter smoke as hard gate | opt-in only by design | low | periodic manual | stage owner |
| Frontend lint/build | no frontend yet | none | Stage 1 UI | stage owner |

Hard canon/idempotency/security gates are **not** waived.

## 17. Gate checklist (`25` §8)

- [x] clean clone/bootstrap succeeds  
- [x] empty and prior-fixture migrations succeed  
- [x] seed imports atomically and idempotently  
- [x] one deterministic phase advances with events/effects/memory  
- [x] repeated command/task produces no duplicate effect/event  
- [x] process termination after commit recovers (snapshot pause/resume)  
- [x] two workers cannot own same task lease  
- [x] phase snapshot seals and cannot be modified (insert-once)  
- [x] strict contracts generate schemas  
- [x] fake provider paths work; OpenRouter live opt-in  
- [x] default tests make no external requests  
- [x] consistency audit reports zero hard violations  
- [x] lint/type/architecture tests pass  
- [x] no secret appears in logs/generated docs  

## 18. Decision

### PASS

Every hard Stage 0 exit gate has automated evidence under `docs/status/evidence/stage-0/`. After this PR merges to main, Stage 0 is eligible for promotion freeze and Stage 1 kickoff.

## 19. Promotion/rollback actions

- merge `cursor/s0-qa002-stage-gate-09ce`  
- update `CONTRACT_FREEZE.md` to FROZEN  
- tag optional `stage-0-foundation` on main tip after merge  
- open Stage 1 context pack next session  

## 20. Sign-off

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Stage owner | parent coding agent | PASS | 2026-07-29 | automated evidence |
| QA owner | parent coding agent | PASS | 2026-07-29 | |
| Contract/architecture reviewer | parent coding agent | PASS | 2026-07-29 | import boundaries |
| Knowledge/security reviewer | parent coding agent | PASS | 2026-07-29 | Stage 0 N/A leakage |
| Project owner | pending human | | | approve merge/tag |
