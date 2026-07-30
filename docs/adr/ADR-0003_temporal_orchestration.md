# ADR-0003 — Temporal Python SDK evaluation for Stage 4 outer orchestration

**Status:** DEFERRED (accept DB orchestrator as Stage 4 production path)  
**Date:** 2026-07-30  
**Decision owners:** Stage 4 parent coding agent, orchestration owner  
**Reviewers:** OPS, QA, architecture  
**Decision deadline/checkpoint:** S4-ORCH-002 / Stage 4 gate (`S4-QA-001`)  
**Supersedes:** NONE  
**Superseded by:** NONE  
**Related change request:** NONE  
**Related requirements:** handbook `14` §18; `29` §7 S4-ORCH-002; `AGENTS.md` §4.3–§4.5  
**Related tasks/stages:** S4-ORCH-001, S4-ORCH-002, S4-OPS-001, S4-QA-001

## Context

Stage 4 requires durable outer orchestration across a three-host LAN (two Strix Halo
hosts + one RTX 4060 Ti) without changing canonical semantics. Handbook `29` treats
Temporal as a **target option after evaluation**, not a mandatory rewrite: the
interface and ADR are mandatory; adoption is evidence-based.

Observed facts:

- Stages 0–3 production path is `DeterministicPhaseRunner` + PostgreSQL task/outbox
  rows with opaque `worker_id` leases, heartbeats, claim/complete, and domain
  idempotency keys (`world:{id}:phase:{n}:…`).
- S4-ORCH-001 extends that path with host/worker registry, fencing tokens, drain,
  reconciliation, and multi-host fan-out/fan-in — still PostgreSQL-authoritative.
- `features.temporal` remains `false` in config profiles; no `temporalio` dependency
  is present in `pyproject.toml`.
- Temporal Python SDK current line at evaluation time: **1.30.x**
  (<https://docs.temporal.io/develop/python>; release 1.30.0 dated 2026-07-02).
- Official Temporal↔LangGraph integration remains optional/public-preview; handbook
  prefers ordinary Activities wrapping bounded LangGraph work (`14` §18.4).

Hypothesis under test: adding a Temporal cluster + worker fleet on a three-host LAN
improves visibility/retries enough to justify the ops footprint **before** the DB
lease/fencing path has been shown insufficient on Stage 4 failure/soak suites.

## Decision drivers

1. correctness/canon safety — no second source of fictional truth;
2. restart/idempotency — domain keys must remain authoritative under retries;
3. operational complexity — Temporal server + UI + worker processes vs Postgres already
   required for canon;
4. determinism restrictions — workflow code cannot do I/O; migration risk to phase
   runner;
5. LangGraph maturity — avoid depending on preview plugin;
6. reversibility — Stage 4 gate must remain passable on the proven DB path;
7. LAN scale — three hosts, not a large multi-tenant cluster.

## Constraints

- Canonical state and committed `world_event` history remain PostgreSQL (`AGENTS.md` §4.1).
- Models produce proposals only; orchestration never elevates narration/images to canon.
- Every externally retried mutation keeps a domain idempotency key (`AGENTS.md` §4.3).
- Do not hold DB transactions open during remote model inference.
- Interface must exist even if Temporal is deferred (`29` S4-ORCH-002).
- Do not rewrite `DeterministicPhaseRunner` as a Temporal workflow in this task.
- Migration `0006` (distributed workers) is owned by S4-ORCH-001 — out of scope here.

## Options considered

### Option A — Keep PostgreSQL-backed orchestrator (DB leases / fencing)

**Description:** Continue `DeterministicPhaseRunner` + `TaskQueueService` / outbox as the
outer orchestrator. S4-ORCH-001 supplies host/worker registry, fencing tokens,
heartbeats, drain, delayed retry, dead-letter, and reconciliation. Phase fan-out uses
task rows claimed across workers; stale workers cannot commit after fencing supersession.

**Advantages:** reuses proven Stage 0–3 semantics; no new distributed control plane;
canon and task durability share one store; ops surface stays Docker Compose Postgres +
app workers; Stage 4 gate can pass without Temporal.

**Disadvantages/risks:** less first-class workflow history/UI than Temporal; custom
signal/pause/versioning logic stays application-owned; must keep lease/fencing tests
tight.

**Evidence:** existing lease/heartbeat/claim path in `task_queue.py` and task repository;
phase/day/month idempotency keys in phase runner / stage2–3 ops; S4-ORCH-001 packet
explicitly owns fencing + multi-host reconciliation before Temporal evaluation.

**Migration/rollback:** N/A as status quo; Temporal adapter port remains available for
later promotion without domain rewrite.

### Option B — Adopt Temporal Python SDK now

**Description:** Run a Temporal cluster; implement `WorldOrchestrator` via workflows that
coordinate only and Activities that perform DB/model/graph I/O. Map world runtime →
workflow, phase → child/bounded workflow, pause → signals (`14` §18.2). Keep domain
idempotency keys inside Activities.

**Advantages:** durable workflow history, timers, visibility, standardized retries;
cleaner multi-process ownership story once mature.

**Disadvantages/risks:** additional cluster + persistence + worker topology on a
three-host LAN; workflow determinism constraints force a large refactor of the phase
runner; dual-orchestrator risk during migration; LangGraph plugin still preview;
ops/on-call burden without proven need after S4-ORCH-001.

**Evidence:** Temporal Python SDK 1.30.x docs confirm Activities for I/O and
deterministic Workflow restrictions; handbook explicitly allows gate pass on DB
orchestrator if Temporal adds more risk than value (`29` S4-ORCH-002; `40` §9.2).

**Migration/rollback:** would require conformance suite parity, cloned-DB migration,
versioning strategy, and rollback to DB orchestrator without dual ownership of one live
world (`14` §18.5). **Not justified for Stage 4 gate.**

### Option C — Dual-run Temporal + DB for every world

**Description:** Run both orchestrators in parallel for visibility.

**Advantages:** early comparison data.

**Disadvantages/risks:** dual ownership of phase creation; duplicate tasks/events unless
perfectly fenced. **Rejected** — violates single-owner rule (`14` §18.5 step 4).

## Decision

**DEFER Temporal adoption for the Stage 4 gate.**

1. **Production path (accepted now):** PostgreSQL-backed orchestrator —
   `DeterministicPhaseRunner` + durable task queue with leases/heartbeats and
   S4-ORCH-001 fencing/reconciliation — is the Stage 4 production outer orchestrator.
2. **Interface (mandatory):** ship `TemporalOrchestratorPort` + `NoopTemporalOrchestrator`
   documenting workflow-coordinates-only / activities-do-I/O / canon-in-PostgreSQL /
   domain idempotency keys, without adding a Temporal SDK dependency.
3. **Feature flag:** `features.temporal` remains `false` until a future ADR revisits
   adoption with soak evidence that the DB path is insufficient.
4. **LangGraph:** if Temporal is later adopted, call bounded graphs from ordinary
   Activities; do not depend on the preview LangGraph plugin without a separate ADR.

## Detailed consequences

### Positive

- Stage 4 gate is unblocked without Temporal ops footprint.
- Domain contracts and idempotency grammar stay stable.
- Future adoption has an explicit port and documented constraints.

### Negative / risks

- Workflow history/UI remain custom until revisit.
- Team must keep lease/fencing fault tests current (owned primarily by S4-ORCH-001 /
  S4-QA-001).

## Implementation plan

| Step | Owner | Notes |
|---|---|---|
| ADR accept-or-defer | S4-ORCH-002 | this document — DEFER |
| Adapter Protocol + noop | S4-ORCH-002 | `temporal_port.py` |
| Distributed leases/fencing | S4-ORCH-001 | migration `0006` if needed |
| Gate documents DB path | S4-QA-001 | cite this ADR |

## Migration / rollback

- **Now:** no Temporal cluster; noop port only; zero migration impact.
- **If later adopted:** implement adapter behind `WorldOrchestrator` /
  `TemporalOrchestratorPort`; run DB vs Temporal conformance suite; migrate cloned
  worlds first; never dual-own one live world; retain domain idempotency keys;
  rollback = flip feature flag / config to DB orchestrator and drain Temporal workers.
- **Rollback from a future adoption:** documented here as configuration + adapter swap;
  canonical rows remain in PostgreSQL so fictional state does not live in Temporal
  history.

## Validation evidence

- Code: `backend/src/fictional_world/application/orchestration/task_queue.py`,
  `phase_runner.py`, `temporal_port.py`
- Unit: `backend/tests/unit/application/orchestration/test_temporal_port.py`
- Handbook: `14` §18, `29` §7 S4-ORCH-002, `40` §9.2
- SDK reference pin (evaluation-time): Temporal Python **1.30.x**

## Acceptance criteria

- [x] ADR accept-or-defer with evidence
- [x] Interface exists even if Temporal deferred
- [x] Gate documents DB orchestrator as production path (this ADR + task/handoff)
- [x] Migration/rollback path documented for a future adoption (no Temporal deploy now)

## Revisit triggers

- S4-QA-001 multi-host soak shows systematic lease/fencing gaps that Temporal would
  materially fix at lower total risk.
- Operator demand for Temporal UI/history outweighs cluster ops on the three-host LAN.
- Temporal↔LangGraph integration leaves preview and passes a dedicated ADR.
- Stage 5 macro/generation workflow hierarchy needs Temporal child-workflow semantics
  that the DB path cannot express cleanly.

## Decision log

| Date | Note |
|---|---|
| 2026-07-30 | DEFERRED adoption; DB orchestrator is Stage 4 production path; port + noop shipped. |
