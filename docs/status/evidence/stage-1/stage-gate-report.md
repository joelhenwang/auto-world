# Stage 1 Gate Report — First Complete Three-Phase Day

**Decision:** PASS
**Report date:** 2026-07-29T20:14:53Z
**Stage owner:** parent coding agent
**QA owner:** integration subagent
**Tested integration commit:** `846fe53a44eef93fc03d7466150a6c59c4b4cca9`
**Release candidate:** `cursor/s1-integration-5704` pending parent merge/review
**Previous verified stage:** Stage 0 foundation
**Environment/profile:** Linux cloud agent, fake provider default, PostgreSQL 16 + pgvector
**Handbook:** v1.0 / `26_STAGE_1_FIRST_COMPLETE_DAY.md`

## 1. Intended outcome

Mira Talren and Dain Arcen complete dawn → morning → evening from one sealed
snapshot per phase. Their isolated model contexts produce simultaneous primary
intents; scenes resolve through validated typed effects and atomic event
commits; tasks restart safely; REST/WebSocket projections and the Vue client
show the resulting day.

## 2. Scope delivered

| Tasks | Status | Deliverable | Evidence |
|---|---|---|---|
| S1-GRAPH-001/002 | VERIFIED | bounded decision/reaction/resolver pipelines | graph tests |
| S1-SIM-002 | VERIFIED | atomic idempotent scene transaction | scene commit tests |
| S1-ORCH-001 | VERIFIED | three-phase fake-model workflow | scenario/phase tests |
| S1-API-001 | VERIFIED | runtime, reads, player commands, replay WebSocket | API tests/OpenAPI |
| S1-UI-001 | VERIFIED | strict Vue runtime/timeline/player shell | frontend tests/build |
| S1-QA-001 | VERIFIED | scenario, leakage/fault/live smoke, evidence | this bundle |

Excluded as required: LangGraph, autonomous Director, combat/injury/inventory,
Stage 2 belief engine, images, distributed workers, and production auth.

## 3. Build and version manifest

See `version-manifest.json`.

| Component | Version/hash |
|---|---|
| Git commit | `846fe53a44eef93fc03d7466150a6c59c4b4cca9` |
| Alembic head | `0003_stage1_action_scene_tables` |
| uv lock | `c43c220b…5454e` |
| frontend lock | `22002950…32ac` |
| OpenAPI | `7ca48ab0…f63a` |
| seed / fixture | `caldris-embervale-v1` / `stage1` |
| fake model | `fake/stage1-first-day-v1` |
| orchestrator | extended `DeterministicPhaseRunner` |

## 4. Static, build, and migration quality

| Check | Result | Evidence |
|---|---|---|
| Ruff lint + format | PASS | `ruff.txt`, `ruff-format.txt` |
| strict basedpyright | PASS, 0 errors | `basedpyright.txt` |
| full offline Python suite | PASS, 154 passed / 2 live deselected | `pytest.txt`, JUnit |
| frontend tests | PASS, 5 tests | `frontend-test.txt` |
| frontend strict build | PASS | `frontend-build.txt` |
| generated OpenAPI/types current | PASS, zero diff | `generated-contract-diff.txt` |
| clean migration cycle | PASS, upgrade → downgrade → upgrade | `migrations.txt` |

Two non-blocking Starlette deprecation warnings are recorded in `pytest.txt`.

## 5. Functional scenarios

| Scenario | Expected | Actual | Result |
|---|---|---|---|
| `stage1-first-day-v1` | dawn, morning, evening | all complete; 3 unique snapshots | PASS |
| pause after snapshot/resume | same phase/snapshot; no duplicate tick | observed | PASS |
| duplicate scene delivery | one event/projection set | original IDs returned | PASS |
| player control/action | exclusive control; action remains pending attempt | observed | PASS |
| WebSocket reconnect | replay after durable sequence | observed | PASS |
| provider unavailable | bounded graph fallback; UI history stays text-first | observed | PASS |

## 6. Hard invariants and consistency

| Invariant | Result | Evidence |
|---|---|---|
| no model-direct state mutation | PASS | graph outputs + `SceneCommitService` |
| no transaction across model calls | PASS | phase-runner assertion |
| two intents share one snapshot | PASS | scenario/phase assertions |
| atomic event/effects/projections | PASS | rollback fault test |
| retries produce no duplicates | PASS | scene/task/phase tests |
| isolated observations/memories | PASS | `leakage-report.md` |
| one durable stream sequence | PASS | API/WebSocket test |

Hard findings: **none**. See `consistency-audit.md`.

## 7. Restart, leakage, and model evidence

- Leakage suite: 7 passed (`leakage.txt`, `leakage-report.md`).
- Fault/retry suite: 16 passed (`fault-and-retry.txt`,
  `fault-injection-report.md`).
- Default model mode: deterministic fake, no external requests.
- Separate OpenRouter sample: 2 passed, including one provider-produced,
  domain-valid `ActionProposal` (`openrouter-live-smoke.txt`).

## 8. UI and performance evidence

The Vue 3/TypeScript client uses generated OpenAPI types and exposes runtime
controls, timeline, Mira/Dain summaries, watcher/player mode, action composer,
text-first image placeholders, and connection status. A browser render against
the complete seeded day is stored as the Cursor artifact
`stage1_first_day_runtime.png`.

Bounded fixture measures are recorded in `performance-summary.md`; no
production p95 or long-horizon soak claim is made.

## 9. Stage 1 hard exit checklist

- [x] full three-phase day completes without manual repair
- [x] both primary actions reference one sealed snapshot per phase
- [x] characters do not author another's reaction/outcome
- [x] accepted state changes use typed effects and canonical commit service
- [x] player action is an attempt and is server-validated
- [x] perspective contexts/API omit private cross-character truth
- [x] malformed output follows repair/regeneration/fallback
- [x] quota reservation precedes unsafe partial phase execution
- [x] phase/task/commit retries complete without duplicates
- [x] WebSocket reconnect replays missed durable events
- [x] minimal UI works without images and preserves text history
- [x] fake-model scenario is deterministic and invariant-clean
- [x] separate live OpenRouter smoke returns a valid action proposal
- [x] lint, type, migration, architecture, and security checks remain green

## 10. Open risks and human review

| Risk | Severity | Blocks promotion? | Follow-up |
|---|---|---|---|
| Starlette/httpx deprecation warnings | low | no | dependency maintenance |
| WebSocket live updates use explicit client poll plus reconnect replay | low | no | push dispatcher after Stage 1 |
| Three-day human narrative rubric sample not performed in this agent run | low | no deterministic gate impact | parent/product review before prompt v2 |

No waiver covers canon, isolation, idempotency, migration safety, or security.

## 11. Decision

### PASS

All deterministic Stage 1 hard gates pass at the tested commit. The live
provider compatibility sample also passes separately. Parent review may merge
the integration branch and freeze the Stage 1 contracts; project-owner
promotion/sign-off remains a human action.

## 12. Sign-off

| Role | Decision | Date | Notes |
|---|---|---|---|
| Stage owner | pending parent review | 2026-07-29 | merge/freeze owner |
| QA owner | PASS | 2026-07-29 | automated evidence complete |
| Knowledge/security | PASS | 2026-07-29 | zero hard leakage findings |
| Project owner | pending | — | human promotion approval |
