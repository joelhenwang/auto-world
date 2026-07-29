# Consistency audit — Stage 1

**Collected:** 2026-07-29T20:14:53Z
**Tested commit:** `8b641978f6a6ff4772118dce9c53b88454783275`
**Result:** zero hard findings

| Invariant | Result | Automated evidence |
|---|---|---|
| PostgreSQL events remain canonical | PASS | scene/phase integration tests |
| Model calls occur without an open transaction | PASS | `test_stage1_first_day_uses_sealed_snapshots_and_restart_safe_tasks` |
| Both primary intents use one sealed phase snapshot | PASS | scenario + phase-runner tests |
| Scene event/effects/projections commit atomically | PASS | scene commit rollback test |
| Duplicate scene delivery creates no duplicate records | PASS | scene commit retry test |
| Every phase task reaches one terminal state | PASS | first-day row-count assertions |
| Perspective observations and memories remain owner-scoped | PASS | scene commit + context leakage tests |
| Stream sequence is durable and replayable | PASS | API/WebSocket integration test |

The three-phase fixture produces 3 phases, 3 snapshots, 6 primary proposals,
3 scenes, 3 resolutions, 3 stream records, 8 observations, 6 recent memories,
and 30 succeeded task rows. No manual database repair is used.
