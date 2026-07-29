# `S2-SIM-001` — Calendar, activation, activities, travel

**Stage:** 2  
**Workstream:** SIM  
**Status:** COMPLETE  
**Priority:** P0  
**Depends:** S2-DB-001, S2-CHAR-001  
**AGENTS conceptual branch:** `task/S2-SIM-001-calendar-travel`

## Objective

Ten-phase calendar, sleep/activation suppression, Activity state machine, route-based travel with restart-safe progress.

## In scope

- All ten phase transitions; sleep schedule + wake rules
- Deterministic SLEEP / CONTINUE_ACTIVITY / skip without LLM
- Activity + travel_progress updates; weather/route modifiers from stored seed
- Meeting on intersecting routes; invalidation interrupts safely
- Max task request estimation before phase

## Out of scope

- Multi-party dialogue budgets (S2-SIM-002); Temporal requirement

## Delivered

- `application/simulation/time.py` — Stage 1/2 phase profiles; full-day walk
- `application/simulation/activation.py` — Stage 2 `ActivationDecision` + sleep schedule
- `application/simulation/activity.py` — activity SM, travel progress, encounters, invalidation
- `application/simulation/request_estimate.py` — `estimate_phase_model_requests`
- Additive `stage2=` flag on `DeterministicPhaseRunner` (no Stage 1 filter)
- Unit tests in `tests/unit/application/simulation/test_s2_sim_001_calendar_travel.py`