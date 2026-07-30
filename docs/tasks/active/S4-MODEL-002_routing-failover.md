# `S4-MODEL-002` — Health-aware model gateway routing and failover

**Stage:** 4  
**Workstream:** MODEL  
**Status:** READY  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s4-integration-8b4a`  
**Upstream commit:** after S4-MODEL-001  
**Target merge order:** after S4-MODEL-001

---

## 1. Objective

```text
Implement a gateway router that filters/scores healthy endpoints by role, privacy,
context, schema, quality, and deadline; reserves concurrency; executes with stable
request/idempotency IDs; fails over safely; and never reuses another request's KV state.
```

## 2. Required reading

1. `AGENTS.md`; `29` §7 S4-MODEL-002; `12`
2. S4-MODEL-001 registry contracts
3. Existing phase fan-out in `phase_runner.py` / Stage 3 ops

## 3. Scope

In scope: routing, health scoring, concurrency reservation, failover, provenance,
privacy policy gates (no silent OpenRouter for local-only worlds), tests for endpoint
death/stale health/OOM/context mismatch/structured-output mismatch/double completion.

Out of scope: worker leases (S4-ORCH-001); image routing (S4-IMG-*).

## 4. Acceptance criteria

- [x] Ten-step routing flow from handbook implemented
- [x] Simultaneous character intents can spread across replicas from one snapshot
- [x] Fault tests cover death, stale health, OOM, privacy, double completion
- [x] Offline by default
