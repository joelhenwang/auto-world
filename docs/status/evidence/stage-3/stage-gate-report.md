# Stage 3 Gate Report — Autonomous Month and Long-Term Coherence

**Decision:** FAIL
**Report date:** 20260730T003010Z
**Stage owner:** parent coding agent
**QA owner:** S3-QA-001 subagent
**Tested integration commit:** `9d62af8949c1a491bd57366b14cd3dd1048ed7c2`
**Release candidate:** `cursor/s2-qa-001-gate-085f`
**Previous verified stage:** Stage 1 first complete day (FROZEN)
**Environment/profile:** Linux cloud agent, fake provider default, PostgreSQL 16 + pgvector
**Handbook:** v1.0 / `28_STAGE_3_AUTONOMOUS_MONTH.md` §10

## 1. Intended outcome

Four primary characters complete thirty autonomous days x ten phases from one
sealed snapshot per phase. Day-finalization is restart-safe; knowledge
isolation holds across perspective packages; Stage 1 remains green.

## 2. Build and version manifest

See `version-manifest.json`.

| Component | Version/hash |
|---|---|
| Git commit | `9d62af8949c1a491bd57366b14cd3dd1048ed7c2` |
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
| Ruff lint + format | see logs | `ruff.txt`, `ruff-format.txt` |
| strict basedpyright | see log | `basedpyright.txt` |
| full offline Python suite | 313 passed (live markers deselected) | `pytest.txt`, JUnit |
| frontend tests | 7 passed | `frontend-test.txt` |
| frontend strict build | see log | `frontend-build.txt` |
| generated OpenAPI/types current | see log | `generated-contract-diff.txt` |
| clean migration cycle | see log | `migrations.txt` |

## 4. Functional scenarios

| Scenario | Expected | Result |
|---|---|---|
| `stage3-autonomous-month-v1` | 7 days x 10 phases, 4 characters | PASS |
| `stage1-first-day-v1` regression | dawn/morning/evening | included in scenario.txt |

## 5. Knowledge / leakage

- Leakage suite passed count: 11
- Corpus assertions: **496** (threshold >=100)
- Detail: `leakage-report.md`

## 6. Fault / idempotency

- Fault subset passed count: 30
- Detail: `fault-injection-report.md`

## 7. Stage 3 hard exit checklist (handbook §10)

- [ ] thirty autonomous days / ten phases without manual DB repair
- [ ] primary intents share sealed snapshot (scenario invariants)
- [ ] typed/idempotent effects + day/phase machines
- [ ] no unauthorized secret in perspective packages (>=100 corpus assertions)
- [ ] day-boundary restart yields no duplicate consolidation
- [ ] Stage 0/1 gates remain green (stage1 scenario + full pytest)
- [ ] lint, format, types, migrations, frontend checks pass

## 8. Decision

### FAIL

One or more Stage 2 gate checks failed. See evidence logs; do not freeze Stage 2 contracts.

## 9. Sign-off

| Role | Decision | Date | Notes |
|---|---|---|---|
| QA owner (automated) | FAIL | 20260730T0 | evidence under `docs/status/evidence/stage-2/` |
| Stage owner | pending parent review | — | merge/freeze owner |
| Project owner | pending | — | human promotion / rubric |
