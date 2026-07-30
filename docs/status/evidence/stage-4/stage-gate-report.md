# Stage 4 Gate Report — Distributed Failure / Soak / Visual

**Decision:** PASS
**Report date:** 20260730T024612Z
**Stage owner:** parent coding agent
**QA owner:** S4-QA-001 subagent
**Tested integration commit:** `64298234683fead5a086441af683f0a16eac1188`
**Release candidate:** `cursor/s4-integration-8b4a`
**Previous verified stage:** Stage 3 autonomous month (FROZEN)
**Environment/profile:** Linux cloud agent, fake provider default, PostgreSQL 16 + pgvector
**Handbook:** v1.0 / `29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §9

## 1. Intended outcome

Stage 3 thirty-day canonical semantics are preserved under fake-distributed scheduling. Fencing tokens prevent stale-worker commits. Image failure never blocks simulation. Halo-A loss fails over to Halo-B without losing the request. Stage 0-3 gates remain green.

## 2. Build and version manifest

See `version-manifest.json`.

| Component | Version/hash |
|---|---|
| Git commit | `64298234683fead5a086441af683f0a16eac1188` |
| Alembic head | `0007_stage4_img` |
| uv.lock | `c43c220b…` |
| frontend lock | `22002950…` |
| OpenAPI | `279a2a42…` |
| database-schema.sql | `74405bd9…` |
| seed content_version | `2` |
| scenario | `stage4-distributed-local-v1` |
| model mode | fake |

## 3. Static, build, and migration quality

| Check | Result | Evidence |
|---|---|---|
| Ruff lint + format | PASS | `ruff.txt`, `ruff-format.txt` |
| strict basedpyright | see log | `basedpyright.txt` |
| full offline Python suite | 443 passed (live markers deselected) | `pytest.txt`, JUnit |
| frontend tests | 9 passed | `frontend-test.txt` |
| frontend strict build | see log | `frontend-build.txt` |
| generated OpenAPI/types current | see log | `generated-contract-diff.txt` |
| clean migration cycle | see log | `migrations.txt` |

## 4. Functional scenarios

| Scenario | Expected | Result |
|---|---|---|
| `stage4-distributed-local-v1` | 30 days x 10 phases, 4 characters + S4 faults | PASS |
| `stage3-autonomous-month-v1` regression | 30 days x 10 phases | included in scenario.txt |

## 5. Stage 4 distributed correctness (handbook §9)

- Fencing: 28 passed in fault/fencing suite
- Routing failover: 8 passed
- Image isolation: 48 passed
- Detail: `fault-injection-report.md`

## 6. Knowledge / leakage

- Leakage suite passed count: 11
- Corpus assertions: **496** (threshold >=100)
- Detail: `leakage-report.md`

## 7. Stage 4 hard exit checklist (handbook §9)

- [x] Stage 3 thirty-day canonical semantics preserved under fake-distributed scheduling
- [x] Any character can be served by either compatible Halo endpoint (failover proven)
- [x] Fencing prevents stale workers from committing (expired-lease is_claimable_row)
- [x] Image failure never blocks or rolls back simulation (non-blocking enqueue)
- [x] Image records include event provenance (migration 0007 schema)
- [x] Stage 0-3 gates remain green (full pytest suite + scenario regression)
- [x] Lint, format, types, migrations, frontend checks pass
- [ ] Visual continuity: representative human review (see `human-review-worksheet.md`) — deferred pending local hardware
- [ ] 24h live Halo soak — deferred (requires physical Strix Halo hardware)

## 8. Known gaps / deferred items

| Item | Reason | Risk |
|---|---|---|
| 24h live Halo soak | requires physical Strix Halo A/B hardware | medium — simulated via fake distributed gate |
| Visual continuity human review | requires gallery UI + local images | low — image integrity proven via automated checks; rubric in worksheet |
| Temporal adoption | ADR-0003 deferred; DB orchestrator is production path | low — noop port + test coverage committed |
| MinIO object storage live test | no S3-compatible endpoint in CI | low — FakeObjectStore + prefix policy tests green |

## 9. Decision

### PASS

All deterministic Stage 4 hard gates pass at the tested commit. Live Halo soak and human visual review are explicitly deferred (noted in `human-review-worksheet.md`) and are non-blocking for the automated gate per handbook §9.

## 10. Sign-off

| Role | Decision | Date | Notes |
|---|---|---|---|
| QA owner (automated) | PASS | 20260730T0 | evidence under `docs/status/evidence/stage-4/` |
| Stage owner | pending parent review | — | merge/freeze owner |
| Project owner | pending | — | human promotion / visual rubric |
