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

- [x] Stale worker cannot commit after fencing token superseded
- [x] Heartbeats, drain, reconciliation tested
- [ ] Phase fan-out/fan-in across workers (deferred to S4-ORCH-002)
- [x] Migration upgrade/downgrade cycle clean
- [x] Stage 0–3 scenarios still green

## 5. Implementation notes (2026-07-30)

**Revision:** `0006_stage4_distributed_workers`  
**Branch:** `cursor/s4-integration-8b4a`

### What was delivered
- Alembic migration `0006` adding `worldsim.host_registry`, `worldsim.worker_registry`, and `worldsim.task_run.fencing_token (bigint DEFAULT 0)`.
- `HostRecord`, `WorkerRecord` Pydantic domain records in `domain/tasks/workers.py`.
- `HostRegistryRow`, `WorkerRegistryRow` SQLAlchemy ORM models in `infrastructure/database/models/workers.py`.
- `SqlAlchemyHostRepository`, `SqlAlchemyWorkerRepository` in `infrastructure/database/repositories/workers.py`.
- `fencing_token` parameter (optional, backward-compatible) added to `TaskRepository.heartbeat`, `mark_running`, `complete_success`, `fail_or_retry`. When provided, a mismatch raises `OptimisticConcurrencyError`.
- `TaskRepository.reset_abandoned_leases(worker_keys, now)` bulk-resets CLAIMED/RUNNING tasks back to PENDING.
- `WorkerLifecycleService` in `application/orchestration/worker_lifecycle.py`.
- `ReconcileAbandonedService` in `application/orchestration/reconcile.py`.
- `HostRepository`, `WorkerRepository` Protocol ports added; `UnitOfWork` extended.
- 20 unit tests + 7 integration tests (all green).
- `docs/generated/database-schema.sql` regenerated.

### Deferred
- Phase fan-out/fan-in task dispatch: deferred to S4-ORCH-002 which can use `claim_available` filtered by capabilities.
- Worker capability-based routing: the `capabilities` field is stored but routing logic is not yet wired into the phase runner.
