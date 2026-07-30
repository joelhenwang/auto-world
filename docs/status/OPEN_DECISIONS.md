# Open Decisions

## DEC-2026-001 — Cloud branch naming vs AGENTS.md §9

**Status:** ACCEPTED
**Opened:** 2026-07-29T11:32:18Z
**Owner:** parent coding agent
**Decision deadline/integration checkpoint:** S0-ENG-001
**Affected requirements:** AGENTS.md §9; Cursor Cloud branch policy
**Affected tasks/contracts:** all cloud-agent task branches
**Blocking:** no — decision taken for this environment

### Question

Which branch naming scheme applies when Cursor Cloud requires `cursor/<name>-<suffix>` and AGENTS.md §9 requires `task/<task-id>-<slug>`?

### Constraints

- Cursor Cloud agents must use `cursor/` prefix and the run-specific suffix.
- Handbook still documents `task/<id>-<slug>` for non-cloud workflows.

### Options

| Option | Benefits | Costs/risks | Evidence needed |
|---|---|---|---|
| A Use cloud `cursor/...` and record AGENTS name in task packet | Unblocks cloud PRs | Dual naming in docs | cloud instructions |
| B Force `task/...` on cloud | Matches handbook | Violates cloud policy | — |

### Current evidence

Cloud task instructions mandate `cursor/<descriptive-name>-09ce` for this run.

### Default safe fallback

Option A.

### Decision

Use `cursor/s0-eng-001-repository-bootstrap-09ce` for this run; document the AGENTS.md conceptual name in the task packet and handoff.

### Follow-up changes

Optional later ADR if dual naming becomes confusing; no ADR required for Stage 0 bootstrap.

---

## DEC-2026-002 — Stage 0 effect kinds missing from handbook §7 union

**Status:** ACCEPTED
**Opened:** 2026-07-29T12:37:28Z
**Owner:** parent coding agent
**Affected tasks/contracts:** S0-DOM-001 EffectCommand; S0-SIM-001
**Blocking:** no

### Question

`25` §2 requires typed effects for WAIT/OBSERVE/REST/MOVE/resource/recent-memory, but `05` §7 EffectCommand omits wait/observe/rest/create_recent_memory.

### Decision

**ASSUMP-S0-001:** Add `wait`, `observe`, `rest`, and `create_recent_memory` kinds to the discriminated union while retaining all handbook §7 variants.

### Follow-up

S0-SIM-001 implements validators/projectors for these kinds.

---

## DEC-2026-003 — StrictContract `strict=True` vs JSON UUID coercion

**Status:** ACCEPTED
**Opened:** 2026-07-29T12:37:28Z
**Owner:** parent coding agent
**Affected tasks/contracts:** S0-DOM-001 StrictContract
**Blocking:** no

### Decision

Use `extra=forbid` + `frozen=True` (handbook `05`) without global `strict=True`, so JSON string→UUID/datetime coercion works at boundaries. Callers may still `model_validate(..., strict=True)` for model-output paths.

---

## DEC-2026-004 — Stage 4 local serving stack pin without Halo silicon in CI

**Status:** ACCEPTED  
**Opened:** 2026-07-30T01:25:00Z  
**Owner:** Stage 4 parent  
**Affected tasks/contracts:** S4-BENCH-001; ADR-0002; S4-MODEL-001/002  
**Blocking:** no for software integration; yes for claiming live GPU soak

### Question

Can Stage 4 accept a serving-stack ADR when the cloud agent lacks Strix Halo / RTX 4060 Ti?

### Decision

Accept **provisional** preference (llama.cpp primary; vLLM upgrade gated on live soak) via
ADR-0002. Require `local_model_live` evidence on target hosts before production pin
promotion. Do not invent GPU soak metrics. OpenRouter remains emergency/dev only.

