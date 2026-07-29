# `S0-DOM-001` — Domain primitives and contracts

**Stage:** `0`  
**Workstream:** `DOM`  
**Status:** `IN_PROGRESS`  
**Priority:** `P0`  
**Owner:** parent coding agent (integrated with S0-ENG-002 / S0-QA-001)  
**Reviewer(s):** parent/integration  
**Branch/worktree:** `cursor/s0-eng002-dom001-qa001-09ce`  
**Upstream commit:** `f65fb4ab18c780c351aba479a4ec276d258052c4`  
**Target merge order:** with S0-ENG-002 and S0-QA-001 (shared `pyproject.toml`)

---

## 1. Objective

```text
Ship Stage 0 Pydantic domain contracts (IDs, enums, time, phase/scene/task/event/
effect/observation/recent-memory) so DB/SIM/MODEL tasks validate against typed schemas.
```

## 2. Why this task exists

- Stage gate: `25` §8 strict contracts generate schemas; foundation for S0-DB/SIM/MODEL.
- Source: `05` §7, `06` §17.1 (task DTO), `07` time/phase vocabulary.
- Unlocks: `S0-DB-001`, `S0-SIM-001`, `S0-MODEL-001`.

## 3. Required reading

`AGENTS.md`; `25` §6 S0-DOM-001; `05` §6–§9; `19` §5–§6; `06` §17.1.

## 4. Frozen contracts

| Contract | Version | Owner | Allowed change |
|---|---|---|---|
| Handbook `05` §7 skeleton | v1.0 | DOM | additive Stage-0 effect kinds (ASSUMP-S0-001) |
| StrictContract (`19`) | v1.0 | DOM | none |

## 5. Scope

### In scope

- `domain/common` (StrictContract, ids, enums, errors)
- FictionalTime; PhaseRun/SceneRun; EffectCommand (+ Stage-0 wait/observe/rest/create_recent_memory)
- CommittedWorldEvent, ObservationRecord, MemoryRecord; TaskRun DTO; supporting types from `05` §7 needed by those
- JSON Schema generation script + `docs/generated/domain-schemas/`
- Contract tests (schema gen, extras forbid, ranges)

### Explicitly out of scope

- ORM/migrations; state-machine transition tables (S0-SIM-001); model gateway protocols (S0-MODEL-001)

## 6. File/path ownership

### Writable

```text
backend/src/fictional_world/domain/**
backend/tests/contract/**
scripts/generate_json_schemas.py
docs/generated/domain-schemas/**
docs/tasks/active/S0-DOM-001_*.md
```

### Shared

```text
pyproject.toml — parent adds pydantic; ENG-002 owns tooling sections
```

## 7. Data and migration ownership

```text
No database change: yes
```

## 8–13. Tests / acceptance

```bash
uv run pytest backend/tests/contract -q
uv run python scripts/generate_json_schemas.py
```

- [ ] Strict contracts forbid extras; ranges/enums enforce
- [ ] JSON schemas generated and committed
- [ ] No ORM in domain
- [ ] Stage-0 effect kinds documented (ASSUMP-S0-001)

## Assumptions

**ASSUMP-S0-001:** `05` EffectCommand union lacks wait/observe/rest/create_recent_memory required by `25` §2. Add those four kinds to the discriminated union; keep all handbook variants.
