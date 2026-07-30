# `S4-QA-001` — Distributed failure/soak/visual gate

**Stage:** 4  
**Workstream:** QA  
**Status:** READY  
**Priority:** P0  

## Objective

`stage4-distributed-local-v1` multi-host failure/soak suite + visual continuity review
evidence under `docs/status/evidence/stage-4/`. Produce GATE_PASS and freeze Stages 0–4.

## Acceptance

- [ ] Gate script `scripts/run_stage4_gate.py`
- [ ] Failure/soak scenario tests (fake distributed)
- [ ] Visual continuity worksheet
- [ ] Stage 0–3 regression green
- [ ] CONTRACT_FREEZE updated for Stage 4
