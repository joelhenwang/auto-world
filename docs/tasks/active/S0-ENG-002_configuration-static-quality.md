# `S0-ENG-002` — Configuration and static quality

**Stage:** `0`  
**Workstream:** `ENG`  
**Status:** `IN_PROGRESS`  
**Priority:** `P0`  
**Owner:** parent coding agent (integrated)  
**Branch/worktree:** `cursor/s0-eng002-dom001-qa001-09ce`  
**Upstream commit:** `f65fb4ab18c780c351aba479a4ec276d258052c4`  
**Target merge order:** with S0-DOM-001 / S0-QA-001

---

## 1. Objective

```text
Provide pydantic-settings AppSettings + stage0/test profiles, startup validation
(embedding dim / public bind), strict basedpyright, expanded Ruff, and pre-commit.
```

## 2. Why this task exists

- `25` §6 S0-ENG-002; `19` §8/§15; `20` §4.

## 5. Scope

### In scope

- `fictional_world/config/{settings,profiles,validation}.py`
- `config/profiles/{stage0,test}.toml`
- Ruff rule expansion; basedpyright `strict`; `.pre-commit-config.yaml`
- Generated-artefact Makefile/script hooks (`generate_json_schemas`)
- Unit tests for valid/invalid profile & bind/embedding validation

### Out of scope

- Domain contracts; full OpenAPI gen; CI workflows (optional stub ok)

## 6. Writable

```text
backend/src/fictional_world/config/**
config/profiles/**
.pre-commit-config.yaml
pyproject.toml (tooling + deps groups)
Makefile
backend/tests/unit/test_settings*.py
docs/tasks/active/S0-ENG-002_*.md
```

## Tests / acceptance

```bash
uv run ruff format --check . && uv run ruff check .
uv run basedpyright
uv run pytest backend/tests/unit -q -k settings
```

- [ ] stage0 profile loads
- [ ] public bind without auth rejected
- [ ] embedding dimension ≠ 2048 rejected when embeddings enabled
- [ ] lint + strict typecheck pass
