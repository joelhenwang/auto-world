# Stage 4 fault, fencing, and routing failover report

**Result:** PASS
**Raw evidence — fencing/fault:** `fault-and-fencing.txt` — 28 passed
**Raw evidence — routing/failover:** `routing-failover.txt` — 8 passed
**Raw evidence — image isolation:** `image-isolation.txt` — 48 passed

| Boundary | Proof | Result |
|---|---|---|
| Stale worker fencing | `test_stage4_fencing_rejects_stale_worker` — expired lease is_claimable_row, active lease blocked | PASS |
| Image enqueue non-blocking | `test_stage4_image_enqueue_non_blocking` — idempotent re-enqueue without phase exception | PASS |
| Halo-A death failover | `test_stage4_halo_loss_failover` — NETWORK_ERROR routes to Halo-B, unhealthy filtered | PASS |
| Unhealthy endpoint skipped | `test_stale_unhealthy_endpoint_skipped` | PASS |
| Incompatible context filtered | `test_incompatible_context_filtered` | PASS |
| Double-completion rejected | `test_double_completion_rejected` | PASS |
| Worker lease/fencing token | `test_worker_fencing.py` suite | PASS |
| Stage 0 idempotency/snapshot | `test_stage0_faults.py` | PASS |

The default Stage 4 fault suite makes no external provider calls.
