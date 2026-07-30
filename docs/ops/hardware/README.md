# Stage 4 target hardware inventory

**Document version:** 1.0  
**Task:** S4-BENCH-001  
**Updated:** 2026-07-30  
**Status:** TARGET topology (cloud CI does not host these GPUs)

This inventory describes the intended local distribution hosts from handbook
`29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §2. Benchmark runners record the
*actual* host they execute on; CI dry-runs set `environment_profile: ci-dry-run`.

## Hosts

| host_id | Hardware | Unified / VRAM | Preferred roles |
|---|---|---|---|
| `strix-halo-a` | AMD Strix Halo A | 128 GB unified | Large text replica, Director overflow, optional embed/rerank, inventory/heartbeats |
| `strix-halo-b` | AMD Strix Halo B | 128 GB unified | Second text replica / small models / summarization / failover for A |
| `rtx-4060-ti` | NVIDIA RTX 4060 Ti | 16 GB VRAM + 32 GB RAM | ComfyUI (+ optional vision QC); often control plane |

## Control-plane recommendation

Place PostgreSQL on the most continuously available host (commonly `rtx-4060-ti`
when Halos are dedicated to inference). Do **not** casually distribute PostgreSQL.
Tested backups are mandatory before multi-host soak.

Suggested control-plane co-location on `rtx-4060-ti` when it is the always-on box:

- FastAPI / frontend
- PostgreSQL + pgvector
- orchestration workers (coordination)
- model gateway/router
- MinIO
- ComfyUI (GPU)

## Memory / context budgets (planning defaults)

| Role | Target context window | Output profile |
|---|---|---|
| character_decision | 12K–20K | short structured |
| character_reaction | 4K–10K | short structured |
| director_proposal | 8K–16K | medium structured |
| resolver | 8K–16K | strict structured |
| scene_narrator | 8K–16K | prose |
| daily_summarizer / monthly_reflector | 16K–32K | medium structured/prose |
| quality_evaluator | 8K–16K | structured diagnostics |
| embedding | passage ≤8K | vectors |

Application-enforced limits remain in model profiles; server `context_limit` must
be ≥ application limits for advertised roles.

## Network assumptions

- Trusted LAN segment or mutual TLS between hosts
- Static names or DHCP reservations for `strix-halo-a`, `strix-halo-b`, `rtx-4060-ti`
- No public internet exposure without separate security review
- OpenRouter remains development/emergency only; private local-only worlds require
  explicit privacy policy approval before remote send

## Machine-readable companion

See `inventory.yaml` in this directory.
