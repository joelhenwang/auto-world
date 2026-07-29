# `S2-ORCH-001` — Seven-day workflow

**Stage:** 2  
**Workstream:** ORCH  
**Status:** COMPLETE  
**Priority:** P0  
**Depends:** S2-SIM-001/002, S2-GRAPH-001  
**AGENTS conceptual branch:** `task/S2-ORCH-001-seven-day`

## Objective

Day workflow over ten phases with Director conditional task, four-character fan-out, day-finalization barrier, recovery snapshot, pause/resume, seven-day run command.

## In scope

- Stage 2 profile on DeterministicPhaseRunner (10 phases × 7 days)
- Day barrier + consolidation/diary/audit tasks
- Restart-safe at task boundaries; no time advance while stopped
- Progress projection

## Out of scope

- Temporal as required orchestrator
