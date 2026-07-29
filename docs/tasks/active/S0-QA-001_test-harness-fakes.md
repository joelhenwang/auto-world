# `S0-QA-001` — Test harness and fakes

**Stage:** `0`  
**Workstream:** `QA`  
**Status:** `IN_PROGRESS`  
**Priority:** `P0`  
**Owner:** parent coding agent (integrated)  
**Branch/worktree:** `cursor/s0-eng002-dom001-qa001-09ce`  
**Upstream commit:** `f65fb4ab18c780c351aba479a4ec276d258052c4`  
**Target merge order:** with S0-DOM-001 / S0-ENG-002

---

## 1. Objective

```text
Provide fake clock, seeded random, fake model gateway, Postgres testcontainer fixture,
network-block fixture, and scenario harness skeleton with self-tests and clean teardown.
```

## 2. Why this task exists

- `25` §6 S0-QA-001; `21` §4–§5, §14.

## 5. Scope

### In scope

- `fictional_world/testing/**` fakes + helpers
- `backend/tests/conftest.py` fixtures + markers
- `tools/scenario_harness/` skeleton
- Fixture self-tests under `backend/tests/unit` / `integration`
- pytest-socket / network block for non-live tests

### Out of scope

- Full Stage 0 scenario gate (S0-QA-002); live OpenRouter suite body (S0-MODEL-002)

## 6. Writable

```text
backend/src/fictional_world/testing/**
backend/tests/conftest.py
backend/tests/unit/test_harness*.py
backend/tests/integration/test_postgres_fixture*.py
tools/scenario_harness/**
docs/tasks/active/S0-QA-001_*.md
pyproject.toml test deps (shared with ENG)
```

## Tests / acceptance

```bash
uv run pytest -m "not openrouter_live and not local_model_live and not image_live and not soak" -q
```

- [ ] Fake clock / seeded random / fake gateway self-test
- [ ] Network blocked unless live marker
- [ ] Postgres testcontainer fixture starts and tears down (skip if Docker unavailable)
- [ ] Scenario harness skeleton imports
