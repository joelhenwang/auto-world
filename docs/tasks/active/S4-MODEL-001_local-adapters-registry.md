# `S4-MODEL-001` — Local model adapters and capability registry

**Stage:** 4  
**Workstream:** MODEL  
**Status:** COMPLETE  
**Priority:** P0  
**Owner:** parent coding agent  
**Branch/worktree:** `cursor/s4-integration-8b4a`  
**Upstream commit:** after S4-BENCH-001  
**Target merge order:** after S4-BENCH-001; before S4-MODEL-002

---

## 1. Objective

```text
Implement OpenAI-compatible local text/embedding adapters and an explicit capability
registry so endpoints advertise roles, limits, health, privacy, and versions behind
existing TextModelGateway / EmbeddingGateway protocols.
```

## 2. Required reading

1. `AGENTS.md`; `29` §7 S4-MODEL-001; `12` §4–§8
2. `docs/adr/ADR-0002_*` (serving selection)
3. `application/models/**`, `infrastructure/model_gateway/**`
4. `docs/status/CONTRACT_FREEZE.md`

## 3. Frozen contracts

Stages 0–3 frozen; gateway protocols additive only; no character↔machine affinity.

## 4. Scope

In scope: local adapters, capability registry records (endpoint_id, host_id, roles,
context_limit, structured_output_mode, quantization, max_concurrency, health,
loaded_state, software versions, privacy policy, cost class), probes, fake/local tests.

Out of scope: health-aware scoring/failover (S4-MODEL-002); ComfyUI; OpenRouter as
default for private worlds.

## 5. Acceptance criteria

- [ ] Local adapters behind protocols
- [ ] Explicit capability discovery (no auto-all-roles)
- [ ] Tests with fake local HTTP / recorded responses
- [ ] Default CI remains offline
