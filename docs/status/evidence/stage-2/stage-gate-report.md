# Stage 2 Gate Report — Coherent Seven-Day World

**Decision:** PASS
**Report date:** 20260729T232111Z
**Stage owner:** parent coding agent
**QA owner:** S2-QA-001 subagent
**Tested integration commit:** `5322d9de0e6da9a342e1deb5922ea2ab7f207fc0`
**Release candidate:** `cursor/s2-qa-001-gate-085f`
**Previous verified stage:** Stage 1 first complete day (FROZEN)
**Environment/profile:** Linux cloud agent, fake provider default, PostgreSQL 16 + pgvector
**Handbook:** v1.0 / `27_STAGE_2_SEVEN_DAY_WORLD.md` §10

## 1. Intended outcome

Four primary characters complete seven full days x ten phases from one
sealed snapshot per phase. Day-finalization is restart-safe; knowledge
isolation holds across perspective packages; Stage 1 remains green.

## 2. Build and version manifest

See `version-manifest.json`.

| Component | Version/hash |
|---|---|
| Git commit | `5322d9de0e6da9a342e1deb5922ea2ab7f207fc0` |
| Alembic head | `0004_stage2_continuity_tables` |
| uv.lock | `c43c220b…` |
| frontend lock | `22002950…` |
| OpenAPI | `ec9569b3…` |
| database-schema.sql | `08236d04…` |
| seed content_version | `2` |
| scenario | `stage2-seven-day-world-v1` |
| model mode | fake |

## 3. Static, build, and migration quality

| Check | Result | Evidence |
|---|---|---|
| Ruff lint + format | PASS | `ruff.txt`, `ruff-format.txt` |
| strict basedpyright | see log | `basedpyright.txt` |
| full offline Python suite | 269 passed (live markers deselected) | `pytest.txt`, JUnit |
| frontend tests | 6 passed | `frontend-test.txt` |
| frontend strict build | see log | `frontend-build.txt` |
| generated OpenAPI/types current | see log | `generated-contract-diff.txt` |
| clean migration cycle | see log | `migrations.txt` |

## 4. Functional scenarios

| Scenario | Expected | Result |
|---|---|---|
| `stage2-seven-day-world-v1` | 7 days x 10 phases, 4 characters | PASS |
| `stage1-first-day-v1` regression | dawn/morning/evening | included in scenario.txt |

## 5. Knowledge / leakage

- Leakage suite passed count: 11
- Corpus assertions: **496** (threshold >=100)
- Detail: `leakage-report.md`

## 6. Fault / idempotency

- Fault subset passed count: 30
- Detail: `fault-injection-report.md`

## 7. Stage 2 hard exit checklist (handbook §10)

- [x] seven full days / ten phases without manual DB repair
- [x] primary intents share sealed snapshot (scenario invariants)
- [x] typed/idempotent effects + day/phase machines
- [x] no unauthorized secret in perspective packages (>=100 corpus assertions)
- [x] day-boundary restart yields no duplicate consolidation
- [x] Stage 0/1 gates remain green (stage1 scenario + full pytest)
- [x] lint, format, types, migrations, frontend checks pass

## 8. Decision

### PASS

All deterministic Stage 2 hard gates pass at the tested commit. Human narrative rubric scores remain blank in `human-review-worksheet.md` (non-blocking for automated gate).

## 9. Sign-off

| Role | Decision | Date | Notes |
|---|---|---|---|
| QA owner (automated) | PASS | 20260729T2 | evidence under `docs/status/evidence/stage-2/` |
| Stage owner | pending parent review | — | merge/freeze owner |
| Project owner | pending | — | human promotion / rubric |
