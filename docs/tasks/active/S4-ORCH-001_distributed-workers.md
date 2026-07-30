# `S4-ORCH-001` — Distributed workers, leases, heartbeats, reconciliation

**Stage:** 4  
**Workstream:** ORCH  
**Status:** READY  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s4-integration-8b4a`  
**Upstream commit:** after S4-MODEL-002 preferred; may parallelize if migrations owned here  
**Target merge order:** before S4-ORCH-002; owns migration `0006` if needed

---

## 1. Objective

```text
Extend the durable task system with host/worker registry, capability labels, leases
with fencing tokens, heartbeats, drain, cancellation, delayed retry, dead-letter,
reconciliation, and idempotent output acceptance across hosts.
```

## 2. Required reading

1. `AGENTS.md`; `29` §7 S4-ORCH-001; `06` task/outbox; existing `application/orchestration/**`
2. `docs/status/CONTRACT_FREEZE.md` — preserve Stage 0 idempotency key grammar

## 3. Data and migration ownership

```text
New tables/columns likely: host_registry, worker_registry, fencing_token columns
Migration revision reservation: 0006_stage4_distributed_workers (this task owns)
No reinterpretation of Stage 0–3 task semantics
```

## 4. Acceptance criteria

- [ ] Stale worker cannot commit after fencing token superseded
- [ ] Heartbeats, drain, reconciliation tested
- [ ] Phase fan-out/fan-in across workers
- [ ] Migration upgrade/downgrade cycle clean
- [ ] Stage 0–3 scenarios still green
