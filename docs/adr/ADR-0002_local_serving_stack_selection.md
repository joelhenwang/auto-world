# ADR-0002 — Local text serving stack selection for Stage 4

**Status:** ACCEPTED (provisional pin + live confirmation path)  
**Date:** 2026-07-30  
**Decision owners:** Stage 4 parent coding agent, model-gateway owner  
**Reviewers:** OPS, QA, architecture  
**Decision deadline/checkpoint:** S4-BENCH-001 / before S4-MODEL-001 hard-wires a server  
**Supersedes:** NONE  
**Superseded by:** NONE  
**Related change request:** NONE  
**Related requirements:** handbook `29` §6–§7, `12` local migration; `AGENTS.md` §4.4  
**Related tasks/stages:** S4-BENCH-001, S4-MODEL-001/002, S4-OPS-001, S4-QA-001

## Context

Stage 4 must run the proven Stage 3 thirty-day world across two Strix Halo hosts and one
RTX 4060 Ti without changing canonical semantics. The handbook forbids hard-coding
vLLM, llama.cpp, SGLang, Transformers, or a quantization before benchmarking the exact
hardware/software combination (`29` §6).

Observed facts:

- Stage 3 gate PASS on main `05db78a` with fake provider; Alembic head `0005`.
- Cloud CI agents do not host Strix Halo / RTX 4060 Ti GPUs.
- S4-BENCH-001 froze corpus `stage4-bench-stage3-rep-v1` and a dry-run harness that
  records environment/model/server versions when live URLs are supplied.
- Application already speaks provider-neutral `TextModelGateway` / `EmbeddingGateway`
  with OpenAI-compatible OpenRouter adapter patterns.

Hypothesis (to confirm on target hosts via `local_model_live`): llama.cpp GGUF is the
most reproducible conservative pin on gfx1151; vLLM ROCm is preferred if repeated
startup + 24h soak succeed on the pinned image.

## Decision drivers

1. correctness/canon safety — structured-output validity; no silent corruption;
2. restart/idempotency — clean startup across restarts; OOM recovery;
3. privacy — never silently route private local-only worlds to OpenRouter;
4. measured quality/performance — Stage 3 role mix latency/throughput;
5. operational complexity — pinned images, rollback, dual-replica compatibility;
6. reversibility — can change pin without rewriting domain contracts.

## Constraints

- No character↔machine affinity for text models.
- No canonical state in model-server KV/session memory.
- Default CI must remain offline (no live OpenRouter).
- Selection must list rejected alternatives and rollback.
- Live Halo/4060 Ti confirmation is required before declaring a **production** pin for
  multi-host soak on real silicon; CI dry-run alone is insufficient for that claim.

## Options considered

### Option A — llama.cpp (GGUF) as conservative primary pin

**Description:** Serve quantized GGUF via llama.cpp’s OpenAI-compatible HTTP server on
both Halos; advertise roles explicitly via capability registry.

**Advantages:** mature CPU/GPU quantization story; reproducible artefacts; simpler
operational surface; easy dual-replica parity.

**Disadvantages/risks:** may trail vLLM throughput at high concurrency; structured
output modes need probing.

**Evidence:** dry-run harness green for stack label `llamacpp`; published llama.cpp
OpenAI server compatibility; gfx1151 support treated as must-verify on hardware.

**Migration/rollback:** swap `base_url`/model hash in capability registry; retain
OpenRouter emergency path behind privacy policy.

### Option B — vLLM (ROCm) as high-throughput primary pin

**Description:** vLLM on Halo A/B when the selected build/model/quant supports gfx1151
reliably.

**Advantages:** better concurrent decode for four-character fan-out; continuous batching.

**Disadvantages/risks:** ROCm/gfx1151 build fragility; larger operational surface;
startup/OOM behaviour must be soak-proven.

**Evidence:** dry-run harness green for stack label `vllm`; **live** startup×10 and
24h soak still required on target hosts before promoting above provisional.

**Migration/rollback:** fall back to Option A pin without domain changes.

### Option C — Transformers/PyTorch baseline only

**Description:** Hugging Face generate loop behind a thin OpenAI shim.

**Advantages:** simplest debug path; useful for correctness bisects.

**Disadvantages/risks:** poor throughput for production pacing; not dual-replica
friendly at Stage 4 load. **Rejected as production primary.**

### Option D — SGLang

**Description:** Optional if stable on pinned ROCm.

**Advantages:** potential structured/runtime features.

**Disadvantages/risks:** extra dependency; handbook marks optional. **Deferred** unless
live soak outperforms A/B with equal reliability.

### Option E — OpenRouter as default local path

**Description:** Keep calling OpenRouter free endpoints from the distributed topology.

**Advantages:** zero local GPU ops.

**Disadvantages/risks:** privacy, quota, and “local distribution” stage outcome fail.
**Rejected** as default; allowed only as development/emergency with explicit policy.

## Decision

1. **Interface pin (accepted now):** all local text/embedding servers are reached through
   an **OpenAI-compatible HTTP** adapter behind existing gateway protocols. Capability
   discovery is explicit (S4-MODEL-001); no auto-assignment of all roles.
2. **Provisional serving preference (accepted now for software integration):**
   - **Primary candidate:** llama.cpp GGUF on Halo A/B (Option A) for reliability-first
     dual replicas.
   - **Preferred upgrade path:** vLLM ROCm (Option B) **if and only if** live benchmarks
     on target hosts meet `29` §6.4 selection gate (startup×10, full context, no silent
     corruption, OOM recovery, structured validity, soak).
   - **Debug baseline:** Transformers (Option C) retained as runner only.
   - **SGLang:** deferred (Option D).
   - **OpenRouter:** emergency/dev only with privacy gate (Option E rejected as default).
3. **Production pin confirmation:** record live results under
   `docs/status/evidence/stage-4/benchmarks/` with `environment_profile` of
   `strix-halo-a` / `strix-halo-b` and update this ADR’s decision log. Until then,
   distributed correctness tests use fake/local dry adapters and must not claim GPU
   soak evidence they do not have.

## Detailed consequences

### Positive

- Unblocks S4-MODEL-001/002 without hard-coding a fragile ROCm stack.
- Preserves rollback and dual-replica symmetry.
- Keeps CI offline and reproducible via dry-run corpus.

### Negative / risks

- Real Halo throughput unknown until `local_model_live` runs.
- Risk of rework if vLLM proves clearly superior — mitigated by adapter boundary.

## Implementation plan

| Step | Owner | Notes |
|---|---|---|
| Freeze corpus + harness | S4-BENCH-001 | done with this ADR |
| Local adapters + registry | S4-MODEL-001 | OpenAI-compatible |
| Health-aware routing | S4-MODEL-002 | privacy + failover |
| Live hardware benches | OPS / QA | opt-in marker; update evidence |
| Promote/demote pin | parent | append decision log |

## Migration / rollback

- Rollback from vLLM → llama.cpp (or reverse) is configuration + capability registry
  only; no Alembic change.
- Emergency OpenRouter requires `privacy_policy` allow and operator approval; never
  silent.
- Prior model provenance remains on committed events/tasks.

## Validation evidence

- Corpus: `backend/tests/fixtures/benchmarks/stage4/`
- Dry-run reports: `docs/status/evidence/stage-4/benchmarks/`
- Unit/contract tests: `backend/tests/unit/benchmark/`, `backend/tests/contract/benchmark/`
- Hardware inventory: `docs/ops/hardware/`

## Acceptance criteria

- [x] Candidate runners exist for vLLM, llama.cpp, Transformers, optional SGLang
- [x] Selection documents rejected alternatives and rollback
- [x] No production hard-code of a stack inside domain/simulation code
- [ ] Live Halo confirmation recorded (ops follow-up; not blocking software integration)

## Revisit triggers

- Live gfx1151 vLLM soak passes with superior p95 fan-out → promote Option B.
- llama.cpp structured-output failure rate exceeds Stage 3 fake baseline → revisit.
- Quantization quality fails Stage 3 rubric → change model/quant, not domain prompts,
  without re-running Stage 3 quality comparisons if prompts were edited.

## Decision log

| Date | Note |
|---|---|
| 2026-07-30 | ACCEPTED provisional preference Option A; Option B upgrade gated on live soak. |
