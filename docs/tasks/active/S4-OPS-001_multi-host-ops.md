# `S4-OPS-001` — Multi-host deployment, network, secrets, observability

**Stage:** 4  
**Workstream:** OPS  
**Status:** COMPLETE  
**Priority:** P0  
**Completed:** 2026-07-30 by S4-OPS-001/S4-API-001 subagent

## Objective

Per-host Compose/manifests, runbooks, secrets guidance, observability hooks, backup
locations, drain/maintenance procedures. PostgreSQL single-host only.

## Acceptance

- [x] docs/ops runbooks for three-host topology
- [x] Compose overlays / host roles documented
- [x] Observability correlation notes (phase→task→model→event→image)

## Deliverables

- `docs/ops/multi-host/README.md` — host roles, startup order, postgres single-host rule, network assumptions
- `docs/ops/multi-host/runbook-drain-failover.md` — drain, reboot, Halo loss, both Halos down pause policy, PG backup/restore
- `docs/ops/multi-host/secrets-and-network.md` — TLS/trusted LAN, service tokens, secret never in logs, audit checklist
- `docs/ops/multi-host/observability.md` — phase→task→model→event→image correlation, Prometheus metric hints, alerts
- `deploy/compose.host-roles.yaml` — annotated overlay example with startup order and host-role comments
