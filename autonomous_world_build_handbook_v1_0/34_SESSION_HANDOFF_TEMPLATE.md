# Session / Task Handoff Template

Copy this file into `docs/handoffs/YYYY-MM-DD_<task-or-session>.md` and replace every placeholder. Do not leave ambiguous “continue from here” language. Update the applicable status files from `36_PROJECT_STATUS_TEMPLATES.md` in the same session.

---

# Handoff — `<TASK_ID or SESSION_NAME>`

**Date:** `<YYYY-MM-DD HH:MM timezone>`  
**Author/agent:** `<name or agent role>`  
**Stage:** `<0–5>`  
**Task packet:** `<path/ID>`  
**Status:** `<IN_PROGRESS | BLOCKED | IN_REVIEW | COMPLETE>`  
**Branch/worktree:** `<branch and path>`  
**Upstream commit:** `<SHA>`  
**Current/final commit(s):** `<SHA(s) or uncommitted>`

---

## 1. Objective

State the exact task outcome in two or three sentences.

```text
<What this session was supposed to produce and why.>
```

## 2. Scope completed

List concrete completed behavior—not intentions.

- `<behavior/API/schema/test>`
- `<behavior/API/schema/test>`

## 3. Scope not completed

- `<remaining item and exact reason>`
- `<whether it is inside the same task or a new packet>`

Use `None` when complete.

## 4. Files changed

| Path | Change | Ownership/notes |
|---|---|---|
| `<path>` | `<created/modified/deleted/generated>` | `<important details>` |

Include migrations, fixtures, generated schemas/clients, configuration, and docs.

## 5. Contracts and interfaces

### Used unchanged

- `<ContractName version / file / hash>`

### Added or changed

- `<ContractName before → after>`
- `<Breaking/additive and dependent tasks>`

### Deviations

```text
None
```

or explain the approved deviation and ADR/change-request ID.

## 6. Database and migrations

```text
Previous migration head:
New migration head:
Migration files:
Clean upgrade tested: yes/no
Previous-stage fixture upgrade tested: yes/no
Downgrade tested/required: yes/no/not required
Backfill/rebuild behavior:
Known data compatibility issue:
```

Use `Not applicable` for non-database tasks.

## 7. Generated artefacts

```text
JSON Schema:
OpenAPI:
Frontend client/types:
Database diagram:
Prompt snapshots:
Other:
```

State the exact regeneration command and whether a no-diff check passes.

## 8. Tests and checks run

| Command | Result | Notes/evidence |
|---|---|---|
| `<command>` | `<pass/fail>` | `<count/duration/path>` |

Include:

- targeted tests;
- integration/migration tests;
- formatting/lint/type checks;
- security/secret scan if relevant;
- fault/leakage tests if required.

## 9. Checks not run

- `<command/check>` — `<why>` — `<who/when must run>`

Never imply full verification when required tests were skipped.

## 10. Manual verification

Describe commands/actions and observed result:

```text
<seed/run/API/UI/provider smoke/manual scenario>
```

Attach paths to screenshots/log extracts/evidence, not secrets or full sensitive prompts.

## 11. Known issues and risks

| ID/severity | Issue | Reproducer/evidence | Recommended next action |
|---|---|---|---|
| `<ID>` | `<description>` | `<command/file/scenario>` | `<action>` |

Use `None` if no known issue.

## 12. Blockers / decisions required

Classify using `B0–B5` from `31_PARALLEL_SUBAGENT_AND_SESSION_PLAYBOOK.md`.

```text
Blocker:
Class:
Affected task/contract:
Evidence:
Minimal decision needed:
Safe work that can continue:
```

Use `None` if unblocked.

## 13. Cross-task findings

```text
XTF ID:
Affected contract/task:
Evidence:
Compatible or breaking:
Proposed resolution:
Workaround used:
```

Use `None` if there are no cross-task findings.

## 14. Integration and merge instructions

```text
Merge after:
Merge before:
Expected conflict paths:
Generated artefacts to regenerate after merge:
Integration tests to run:
Reviewer(s) required:
```

## 15. Runtime/environment state

```text
Services running/stopped:
Containers/volumes created:
Ports:
Database/fixture state:
Temporary files:
Worktree clean/dirty:
Secrets loaded only from:
```

Identify cleanup required.

## 16. Next exact action

Write the next useful action so a fresh agent can start immediately:

```text
1. Checkout/open ...
2. Run ...
3. Inspect ...
4. Implement/fix ...
5. Verify with ...
```

## 17. Required reading for the next agent

- `<task packet>`
- `<specific handbook sections>`
- `<specific code/contracts>`
- `<latest status/ADR>`

## 18. Final self-review

- [ ] Diff contains only scoped or documented changes.
- [ ] No secrets, `.env`, private prompts, model caches, DB volumes, or images were committed accidentally.
- [ ] Tests/results above are accurate.
- [ ] Migration/generated-artefact status is explicit.
- [ ] Breaking changes have approved change control.
- [ ] Handoff is sufficient without prior chat history.
