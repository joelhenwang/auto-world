# Stage 2 fault, retry, and day-boundary restart report

**Result:** PASS
**Raw evidence:** `fault-and-retry.txt` — 30 passed

| Boundary | Injection/proof | Recovery |
|---|---|---|
| day finalize after process restart | `test_process_restart_at_day_boundary_reuses_day_run` | same day_run/summary/diary IDs |
| daily consolidation retry | prior day_run reuse | no duplicate summaries/diaries |
| travel mid-route restart | seed modifier travel progress | progress preserved |
| Stage 0 snapshot/outbox faults | `test_stage0_faults` | idempotent inserts |
| Stage 1 scene commit duplicate | same idempotency key | original event IDs |

The default fault suite makes no external provider calls.
