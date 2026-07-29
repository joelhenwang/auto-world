# Stage 1 fault, retry, and restart report

**Result:** PASS
**Raw evidence:** `fault-and-retry.txt` — 16 passed

| Boundary | Injection/proof | Recovery |
|---|---|---|
| malformed model response | invalid fake corpus | one regeneration, then safe fallback |
| provider timeout | fake `TIMEOUT` response | bounded fallback action |
| provider 429 | fake `RATE_LIMITED` response | bounded fallback action |
| semantic invalid proposal/effect | graph domain validation | rejection or conservative fallback |
| effect failure inside scene transaction | impossible resource spend | all proposals/scenes/events roll back |
| duplicate scene commit after acknowledgement loss | same idempotency key twice | original event/stream IDs returned |
| restart after snapshot | pause with `stop_after_snapshot`, fresh UoW resume | same phase/snapshot, one world tick |
| restart at phase boundaries | fresh UoW for each first-day step | dawn, morning, evening complete once |

The default fault suite makes no external provider calls.
