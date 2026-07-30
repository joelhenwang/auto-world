# Multi-Host Deployment — Overview

**Document version:** 1.0  
**Task:** S4-OPS-001  
**Updated:** 2026-07-30  
**Status:** NORMATIVE for Stage 4 distributed topology  
**Normative sources:** `29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §2–§3, §S4-OPS-001;
`22_OBSERVABILITY_SECURITY_PRIVACY_AND_OPERATIONS.md` §9–§11

---

## 1. Three-host topology

### 1.1 Strix Halo A (`strix-halo-a`)

| Attribute | Value |
|---|---|
| Memory | 128 GB unified |
| Primary roles | Large text-generation replica; Director/narrator overflow; optional local embedding/reranker; worker heartbeat and model inventory |
| May carry | Any focus character (context package only — no model affinity) |
| Must not hold | PostgreSQL data directory unless `rtx-4060-ti` is permanently decommissioned |

Halo A is the preferred first replica for all roles that require large context windows
(≥12 K tokens).

### 1.2 Strix Halo B (`strix-halo-b`)

| Attribute | Value |
|---|---|
| Memory | 128 GB unified |
| Primary roles | Second large text-generation replica; small-model services; summarization; evaluation overflow; failover for Halo A |
| May carry | Any focus character |
| Must not hold | PostgreSQL (same rule as Halo A) |

Halo B is architecturally symmetric with Halo A for text inference.  When Halo A is
unavailable the gateway promotes Halo B to primary automatically (see §3 Startup order
and `runbook-drain-failover.md`).

### 1.3 RTX 4060 Ti (`rtx-4060-ti`)

| Attribute | Value |
|---|---|
| VRAM | 16 GB |
| System RAM | 32 GB |
| Primary roles | ComfyUI image worker; optional vision-quality worker |
| Control-plane roles | FastAPI; PostgreSQL + pgvector; orchestration workers (coordination); model gateway/router; MinIO; Vue frontend |

This host is the recommended control-plane node when it is the most continuously
available machine.  All control-plane services co-locate here.

---

## 2. PostgreSQL single-host rule

> **PostgreSQL MUST run on exactly one host at a time.**  
> Do NOT distribute, replicate, or multi-primary PostgreSQL without a dedicated DBA review and a data-safety ADR.

Rationale: the entire simulation canonical state lives in one PostgreSQL instance.
Multi-master distributed PostgreSQL adds operational complexity, conflict resolution
risk, and migration hazards that are out of scope for Stage 4.

Tested physical backups (pg_basebackup or equivalent) are mandatory before any
multi-host soak test.  See `runbook-drain-failover.md §5` for the restore procedure.

Recommended host: `rtx-4060-ti` (runs continuously; Halos may be powered off when
not under active inference load).

---

## 3. Service map and startup order

Services must be started in the following dependency order.  A Compose override per
host encodes this via `depends_on` and `healthcheck`; see
`deploy/compose.host-roles.yaml` for annotated reference.

```
1.  rtx-4060-ti  ── postgres (port 5432)         → healthcheck: pg_isready
2.  rtx-4060-ti  ── minio (port 9000/9001)        → healthcheck: mc ready
3.  rtx-4060-ti  ── orchestration-worker           → depends_on: postgres
4.  rtx-4060-ti  ── model-gateway (router)         → depends_on: postgres
5.  rtx-4060-ti  ── api (FastAPI / Uvicorn)        → depends_on: postgres, model-gateway
6.  rtx-4060-ti  ── frontend (Vite / Caddy)        → depends_on: api
7.  rtx-4060-ti  ── comfyui                        → depends_on: minio
8.  strix-halo-a ── text-server (vLLM/llama.cpp)   → registers with gateway on startup
9.  strix-halo-b ── text-server (vLLM/llama.cpp)   → registers with gateway on startup
```

**Rule:** never start a character agent or phase runner before:
- `postgres` is healthy,
- at least one text-generation endpoint is registered and `healthy`,
- `model-gateway` has a non-empty capability registry.

---

## 4. Network assumptions

- All three hosts share a trusted LAN segment with static IP or DHCP reservations.
- Use hostnames `strix-halo-a`, `strix-halo-b`, `rtx-4060-ti` via `/etc/hosts` or
  a local DNS record.  Do not rely on mDNS under load.
- No host is directly internet-reachable.  OpenRouter access is egress-only from
  `model-gateway` and only for `synthetic_fiction` or explicitly permitted
  privacy-policy worlds.
- Time synchronisation: all three hosts must run `chrony` or `systemd-timesyncd`
  pointing to the same source; clock skew > 1 s can break lease/fencing logic.

---

## 5. Character identity and model affinity

> Characters are context packages.  They have no affinity to a physical host or loaded model instance.

A character perspective package (character card + memories + perceptions) is assembled
from PostgreSQL at phase start.  It is handed to whichever text endpoint the
health-aware gateway selects.  If that endpoint becomes unavailable mid-phase the
task lease expires and the orchestrator re-queues the task; the next available
endpoint picks it up with the identical package.

Never hard-code `character_id → host_id` mappings.

---

## 6. Related runbooks

| Topic | Document |
|---|---|
| Drain, reboot, Halo loss, both Halos down | `runbook-drain-failover.md` |
| TLS, service tokens, secret distribution | `secrets-and-network.md` |
| Structured logging, tracing, metrics | `observability.md` |
| Hardware inventory YAML | `../hardware/inventory.yaml` |
| Compose host-role overlay | `../../deploy/compose.host-roles.yaml` |
