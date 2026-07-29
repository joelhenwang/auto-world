# Coding-Agent Task Packet Template

Copy this file into `docs/tasks/active/<TASK_ID>_<slug>.md`. The parent/integration agent fills it before delegation. A task is not ready while required fields are unresolved.

---

# `<TASK_ID>` — `<Concise task title>`

**Stage:** `<0–5>`  
**Workstream:** `<ARCH/ENG/DB/SIM/CHAR/KNOW/MODEL/GRAPH/ORCH/API/UI/WORLD/RULES/IMG/OPS/QA/CONTENT/MACRO>`  
**Status:** `<CONTRACT_DRAFT | READY | IN_PROGRESS | BLOCKED | IN_REVIEW | VERIFIED>`  
**Priority:** `<P0/P1/P2>`  
**Owner:** `<agent/person>`  
**Reviewer(s):** `<roles>`  
**Branch/worktree:** `<branch/path>`  
**Upstream commit:** `<SHA>`  
**Target merge order:** `<after/before task IDs>`

---

## 1. Objective

State one testable outcome:

```text
<Implement X so that Y can do Z under constraints Q.>
```

## 2. Why this task exists

Link it to requirements and stage proof:

- Requirements: `<FR-... / NFR-... / PRN-...>`
- Stage gate items: `<exact bullets/sections>`
- Risks mitigated: `<R-...>`
- Upstream/downstream tasks: `<IDs>`

## 3. Required reading

Read before editing:

1. `01_AGENTS.md` or repository `AGENTS.md`;
2. `<current stage document and sections>`;
3. `<subsystem docs>`;
4. `<frozen contract files/schemas>`;
5. `<neighboring code/tests/examples>`;
6. `<latest relevant handoff/status/ADR>`.

## 4. Frozen contracts

| Contract | Version/hash/commit | Owner | Allowed change |
|---|---|---|---|
| `<name/path>` | `<value>` | `<owner>` | `<none/additive-only/etc.>` |

A breaking change requires the change-control process in `33`.

## 5. Scope

### In scope

- `<specific behavior/file/layer>`
- `<specific behavior/file/layer>`

### Explicitly out of scope

- `<adjacent behavior another task owns>`
- `<future-stage work>`
- `<refactor not required>`

## 6. File/path ownership

### Writable

```text
<paths/globs>
```

### Read-only dependencies

```text
<paths/globs>
```

### Shared/generated files

```text
<file, generating owner, command, merge protocol>
```

Do not edit outside writable paths without parent approval recorded in the task/handoff.

## 7. Data and migration ownership

```text
New tables/columns/indexes:
Migration revision reservation:
Backfill/rebuild:
Fixture updates:
No database change: yes/no
```

If another task owns the migration, name the repository/protocol this task targets.

## 8. Interface inputs and outputs

### Inputs

```text
<types, commands, DB records, context, API payloads>
```

### Outputs

```text
<types, events/effects, rows, task results, DTOs>
```

### Errors/fallbacks

```text
<typed errors, retryability, fallback behavior>
```

### Idempotency/concurrency

```text
<key, lease/fencing, optimistic version, duplicate behavior>
```

## 9. Security, privacy, perspective, and content constraints

Check all relevant items:

- [ ] No cross-character access beyond frozen policy.
- [ ] Server-side role authorization.
- [ ] Model/memory/user text treated as untrusted.
- [ ] No secret/key/raw sensitive prompt logging.
- [ ] Remote-provider data profile is allowed.
- [ ] No model direct state mutation.
- [ ] High-impact effect privilege enforced.
- [ ] Young-adult/soft-dark content policy maintained.
- [ ] Not applicable items explained below.

Notes:

```text
<details>
```

## 10. Implementation sequence

1. `<write/confirm failing contract test>`
2. `<implement pure domain behavior>`
3. `<persistence/migration if applicable>`
4. `<application/orchestration integration>`
5. `<API/UI/model adapter if applicable>`
6. `<fault/security/observability>`
7. `<docs/generated artefacts>`
8. `<acceptance run>`

This sequence may be refined by the owner but scope may not expand silently.

## 11. Test matrix

| Test type | Scenario | Expected result | File/command |
|---|---|---|---|
| Unit | `<scenario>` | `<expected>` | `<path/command>` |
| Property/invariant | `<scenario>` | `<expected>` | `<path/command>` |
| Integration | `<scenario>` | `<expected>` | `<path/command>` |
| Migration | `<scenario>` | `<expected>` | `<path/command>` |
| Fault/idempotency | `<scenario>` | `<expected>` | `<path/command>` |
| Security/leakage | `<scenario>` | `<expected>` | `<path/command>` |
| API/UI/E2E | `<scenario>` | `<expected>` | `<path/command>` |

Remove genuinely irrelevant rows and state why.

## 12. Required commands

```bash
# environment/bootstrap
<command>

# targeted tests
<command>

# formatting/lint/type
<command>

# integration/migration/fault
<command>

# generated artefact no-diff
<command>
```

Commands must be valid for the repository; do not leave generic placeholders when assigning the task.

## 13. Acceptance criteria

- [ ] `<observable behavior>`
- [ ] `<constraint/invariant>`
- [ ] `<failure path>`
- [ ] `<test/static result>`
- [ ] `<migration/generated artefact>`
- [ ] `<observability/provenance>`
- [ ] `<documentation/traceability>`
- [ ] No Critical/High reviewer finding remains.

## 14. Deliverables

- code: `<paths>`;
- migrations: `<paths or none>`;
- tests: `<paths>`;
- fixtures: `<paths>`;
- generated artefacts: `<paths>`;
- docs/ADR: `<paths>`;
- evidence: `<paths>`;
- handoff: `docs/handoffs/<...>.md`.

## 15. Known risks and likely pitfalls

- `<risk and prevention>`
- `<risk and prevention>`

Reference risk IDs from `32` where possible.

## 16. Blocker/escalation rule

- solve `B0` locally;
- report `B1–B5` using the format in `31`;
- do not invent a breaking workaround;
- continue independent work where safe;
- stop immediately for canonical corruption, secret leakage, or unsafe privilege behavior.

## 17. Handoff requirements

The owner must complete `34_SESSION_HANDOFF_TEMPLATE.md` and include:

- final commits/diff paths;
- migrations/generated artefacts;
- all commands/results;
- tests not run;
- contract deviations;
- integration order/conflicts;
- next exact action.

## 18. Parent verification

To be filled after integration:

```text
Reviewed by:
Merged commit:
Acceptance commands rerun:
Findings:
Traceability updated:
Status: VERIFIED / RETURNED
```
