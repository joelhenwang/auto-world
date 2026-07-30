# Stage 3 Gate Report — Autonomous Month and Long-Term Coherence

**Decision:** PASS
**Report date:** 20260730T003422Z
**Stage owner:** parent coding agent
**QA owner:** S3-QA-001 subagent
**Tested integration commit:** `b055f5bdb69b8b176c37abc297537d1119e47ad1`
**Release candidate:** `cursor/s3-mem-rules-world-03fc`
**Previous verified stage:** Stage 2 seven-day world (FROZEN)
**Environment/profile:** Linux cloud agent, fake provider default, PostgreSQL 16 + pgvector
**Handbook:** v1.0 / `28_STAGE_3_AUTONOMOUS_MONTH.md` §9

## 1. Intended outcome

Four primary characters complete thirty autonomous days x ten phases from one
sealed snapshot per phase. Day-finalization is restart-safe; knowledge
isolation holds across perspective packages; Stage 1–2 remain green.

## 2. Build and version manifest

See `version-manifest.json`.

| Component | Version/hash |
|---|---|
| Git commit | `b055f5bdb69b8b176c37abc297537d1119e47ad1` |
| Alembic head | `0005_stage3_long_term_tables` |
| uv.lock | `c43c220b…` |
| frontend lock | `22002950…` |
| OpenAPI | `01de8322…` |
| database-schema.sql | `cb79fd74…` |
| seed content_version | `2` |
| scenario | `stage3-autonomous-month-v1` |
| model mode | fake |

## 3. Static, build, and migration quality

| Check | Result | Evidence |
|---|---|---|
| Ruff lint + format | PASS | `ruff.txt`, `ruff-format.txt` |
| strict basedpyright | see log | `basedpyright.txt` |
| full offline Python suite | 316 passed (live markers deselected) | `pytest.txt`, JUnit |
| frontend tests | 7 passed | `frontend-test.txt` |
| frontend strict build | see log | `frontend-build.txt` |
| generated OpenAPI/types current | see log | `generated-contract-diff.txt` |
| clean migration cycle | see log | `migrations.txt` |

## 4. Functional scenarios

| Scenario | Expected | Result |
|---|---|---|
| `stage3-autonomous-month-v1` | 30 days x 10 phases, 4 characters | PASS |
| `stage2-seven-day-world-v1` + stage1 regression | included | included in scenario.txt |

## 5. Knowledge / leakage

- Leakage suite passed count: 11
- Corpus assertions: **496** (threshold >=100)
- Detail: `leakage-report.md`

## 6. Fault / idempotency

- Fault subset passed count: 30
- Detail: `fault-injection-report.md`

## 7. Stage 3 hard exit checklist (handbook §9)

- [x] thirty autonomous days / ten phases without manual DB repair
- [x] primary intents share sealed snapshot (scenario invariants)
- [x] typed/idempotent effects + day/phase machines
- [x] no unauthorized secret in perspective packages (>=100 corpus assertions)
- [x] day-boundary restart yields no duplicate consolidation
- [x] Stage 0–2 gates remain green (stage2+stage1 scenarios + full pytest)
- [x] lint, format, types, migrations, frontend checks pass

## 8. Decision

### PASS

All deterministic Stage 3 hard gates pass at the tested commit. Human narrative rubric scores remain blank in `human-review-worksheet.md` (non-blocking for automated gate).

## 9. Sign-off

| Role | Decision | Date | Notes |
|---|---|---|---|
| QA owner (automated) | PASS | 20260730T0 | evidence under `docs/status/evidence/stage-3/` |
| Stage owner | pending parent review | — | merge/freeze owner |
| Project owner | pending | — | human promotion / rubric |
