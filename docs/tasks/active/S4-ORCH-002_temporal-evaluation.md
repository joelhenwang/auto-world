# `S4-ORCH-002` — Temporal evaluation and adapter

**Stage:** 4  
**Workstream:** ORCH  
**Status:** COMPLETE  
**Priority:** P1  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s4-integration-8b4a`  
**Upstream commit:** after S4-ORCH-001  
**Target merge order:** after S4-ORCH-001 ADR evaluation  
**Completed:** 2026-07-30  
**Handoff:** `docs/handoffs/2026-07-30_S4-ORCH-002.md`  
**ADR:** `docs/adr/ADR-0003_temporal_orchestration.md` (**DEFERRED** adoption)

---

## 1. Objective

```text
Produce an ADR comparing the proven DB orchestrator vs Temporal Python SDK, and
implement a Temporal adapter interface. Adoption is optional and evidence-based;
the Stage 4 gate may pass on the DB orchestrator.
```

## 2. Required reading

1. `AGENTS.md`; `29` §7 S4-ORCH-002
2. Current `DeterministicPhaseRunner` + task queue
3. Temporal Python SDK docs at implementation time (verify versions)

## 3. Scope

In scope: evaluation ADR; adapter Protocol + optional stub/noop; if adopted: workflows
coordinate only, activities do I/O, canon in PostgreSQL, domain idempotency keys remain.

Out of scope: mandatory rewrite of phase runner; Kubernetes.

## 4. Acceptance criteria

- [x] ADR accept-or-defer with evidence — **DEFER** (ADR-0003); DB leases/fencing path
- [x] Interface exists even if Temporal deferred — `TemporalOrchestratorPort` +
  `NoopTemporalOrchestrator`
- [x] If deferred: gate documents DB orchestrator as production path — ADR-0003 + handoff
- [x] If adopted: migration/rollback path documented — N/A (deferred); future path in ADR
