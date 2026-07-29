# `S2-SIM-001` — Calendar, activation, activities, travel

**Stage:** 2  
**Workstream:** SIM  
**Status:** READY  
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
