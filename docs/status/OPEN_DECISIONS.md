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
