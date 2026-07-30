# `S4-ORCH-002` — Temporal evaluation and adapter

**Stage:** 4  
**Workstream:** ORCH  
**Status:** READY  
**Priority:** P1  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s4-integration-8b4a`  
**Upstream commit:** after S4-ORCH-001  
**Target merge order:** after S4-ORCH-001 ADR evaluation

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

- [ ] ADR accept-or-defer with evidence
- [ ] Interface exists even if Temporal deferred
- [ ] If deferred: gate documents DB orchestrator as production path
- [ ] If adopted: migration/rollback path documented
