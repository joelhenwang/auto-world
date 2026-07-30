# Observability — Correlation, Metrics, and Distributed Tracing

**Document version:** 1.0  
**Task:** S4-OPS-001  
**Updated:** 2026-07-30  
**Status:** NORMATIVE for Stage 4 multi-host operation  
**Normative sources:** `22_OBSERVABILITY_SECURITY_PRIVACY_AND_OPERATIONS.md` §2–§6;
`29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §S4-OPS-001

---

## 1. Correlation chain: phase → task → model → event → image

Every log event, trace span, and metric data point must carry the chain of IDs that
connects it to the simulation state.  This is the core principle: any anomaly must
be traceable from a visible symptom back to a canonical world event.

```
world_id
  └── phase_run_id          (one per phase, e.g. "Morning / Exploration")
        └── task_id         (one per worker task: character_decide, scene_assemble, …)
              └── model_call_id   (one per LLM request)
              └── scene_id        (one per assembled scene)
                    └── world_event_id  (one per committed canonical event)
                          └── image_job_id    (one per enqueued image job)
                                └── gallery_item_id  (one per accepted output)
```

### 1.1 Common log fields

Every structured JSON log line from every service must include:

```json
{
  "timestamp": "2026-07-30T10:00:01.234Z",
  "level": "INFO",
  "service": "fictional-world-api",
  "host_id": "rtx-4060-ti",
  "request_id": "<UUID>",
  "world_id": "<UUID or null>",
  "phase_run_id": "<UUID or null>",
  "task_id": "<UUID or null>",
  "model_call_id": "<UUID or null>",
  "event": "phase.created"
}
```

Optional fields (add when available):
`scene_id`, `character_id`, `image_job_id`, `worker_id`, `endpoint_id`.

Never include: API keys, passwords, tokens, full raw prompts, private memory content,
signed URLs.  See `secrets-and-network.md §3`.

### 1.2 Trace hierarchy

Use OpenTelemetry-compatible spans (or an abstraction that exports to it):

```
world.phase  [phase_run_id, world_id]
├── world.tick
├── director.evaluate
├── snapshot.build
├── character.decide × N  [character_id, task_id, endpoint_id]
│   ├── context.assemble
│   ├── memory.retrieve
│   └── model.generate  [model_call_id, role, token_counts]
├── scenes.assemble
├── scene.process × M  [scene_id]
│   ├── reaction.generate
│   ├── resolution.calculate
│   └── scene.commit  [world_event_id]
├── observations.write
├── phase.finalize
└── image.enqueue × K  [image_job_id]  ← async, linked not nested
```

Async image and outbox spans link to the source `world_event_id` via `span.link()`;
they do not pretend to be children of the phase span (the phase is long complete).

---

## 2. Key metrics per subsystem

All Prometheus-compatible metrics use snake_case labels.  Never use `character_id`
or `event_id` as label values — use `host_id`, `role`, `status`, `error_class` etc.

### 2.1 Phase runtime

| Metric | Labels | Purpose |
|---|---|---|
| `world_phase_duration_seconds` | `phase_name`, `world_id` | Phase wall-clock time |
| `world_phase_state_total` | `state` | Count by terminal state |
| `scene_duration_seconds` | `scene_type` | Per-scene latency |
| `world_paused_total` | `reason` | Pause reasons histogram |
| `world_consistency_warning_total` | `severity` | Audit findings |

### 2.2 Task queue and workers

| Metric | Labels | Purpose |
|---|---|---|
| `task_queue_depth` | `task_type`, `status` | Backlog by type |
| `task_wait_seconds` | `task_type` | Time from queued to claimed |
| `task_run_seconds` | `task_type` | Worker execution time |
| `task_retry_total` | `error_class` | Retry reasons |
| `task_dead_letter_total` | `task_type` | Permanently failed tasks |
| `worker_heartbeat_age_seconds` | `host_id`, `worker_key` | Time since last heartbeat |
| `worker_active_tasks` | `host_id` | Current concurrent load |

### 2.3 Model gateway

| Metric | Labels | Purpose |
|---|---|---|
| `model_request_total` | `role`, `endpoint_id`, `status` | Requests by role and outcome |
| `model_latency_seconds` | `role`, `endpoint_id` | p50/p95 latency histogram |
| `model_input_tokens_total` | `role`, `endpoint_id` | Context consumption |
| `model_output_tokens_total` | `role`, `endpoint_id` | Output size |
| `model_schema_rejection_total` | `role` | Structured-output parse failures |
| `model_fallback_total` | `from_endpoint`, `reason` | Failover events |
| `model_endpoint_health` | `endpoint_id`, `host_id` | 0=unhealthy, 1=degraded, 2=healthy |

Watch `model_fallback_total` and `model_endpoint_health` to detect Halo failures
before they escalate.

### 2.4 Image pipeline

| Metric | Labels | Purpose |
|---|---|---|
| `image_queue_depth` | `status` | Jobs awaiting processing |
| `image_generation_seconds` | `workflow_profile` | ComfyUI job duration |
| `image_retry_total` | `reason` | Retry causes |
| `image_quality_rejection_total` | `check_name` | QC failure breakdown |
| `comfyui_health` | `host_id` | 0/1 health of ComfyUI worker |

### 2.5 Database and API

| Metric | Labels | Purpose |
|---|---|---|
| `db_pool_in_use` | — | Active connections |
| `db_query_seconds` | `operation` | Query latency histogram |
| `api_request_seconds` | `method`, `path_template`, `status_code` | API latency |
| `api_error_total` | `status_code` | Error rate |

---

## 3. Correlating an image failure back to a canonical event

When an image job is stuck or rejected, use this lookup chain:

```sql
-- 1. Find the stuck job
SELECT id, source_event_id, source_scene_id, status, error_class, error_detail
  FROM worldsim.image_job
 WHERE world_id = '<world_id>'
   AND status IN ('failed', 'dead_letter')
 ORDER BY created_at DESC
 LIMIT 20;

-- 2. Trace back to the canonical event
SELECT sequence_number, event_type, canonical_summary, absolute_phase_index
  FROM worldsim.world_event
 WHERE id = '<source_event_id>';

-- 3. Find the phase that produced the event
SELECT phase_name, state, started_at, completed_at
  FROM worldsim.phase_run
 WHERE absolute_phase_index = (
   SELECT absolute_phase_index FROM worldsim.world_event WHERE id = '<source_event_id>'
 ) AND world_id = '<world_id>';
```

The `model_call_id` that produced the scene prompt is stored in `task_run.result_reference`
(JSONB field) for the `scene_image_enqueue` task type.

---

## 4. Per-host log aggregation

Each host writes structured JSON logs to a local file:

```
/var/log/fictional-world/<service>.jsonl
```

Forward to a central collector on `rtx-4060-ti` using `Vector`, `Promtail`, or
`Filebeat`.  Example Vector sink:

```toml
[sources.fictional_world_logs]
type = "file"
include = ["/var/log/fictional-world/*.jsonl"]

[transforms.add_host]
type = "remap"
inputs = ["fictional_world_logs"]
source = '''
.host_id = get_hostname!()
'''

[sinks.loki]
type = "loki"
inputs = ["add_host"]
endpoint = "http://rtx-4060-ti:3100"
labels.job = "fictional-world"
```

Alternatively, aggregate via `journald` forwarding if all services use systemd.

---

## 5. Alert thresholds (recommended starting points)

| Condition | Threshold | Action |
|---|---|---|
| Phase stuck | `world_phase_duration_seconds > 600` | Investigate model endpoint health |
| Dead-letter task | Any `task_dead_letter_total` increment | Review task error; manual retry or skip |
| No healthy endpoint | `model_endpoint_health == 0` for all endpoints | Both Halos down; see `runbook-drain-failover.md §4` |
| Image backlog high | `image_queue_depth{status="queued"} > 50` | Check ComfyUI health; consider cap |
| Worker lost heartbeat | `worker_heartbeat_age_seconds > 120` | Worker process dead; restart |
| DB pool exhausted | `db_pool_in_use >= pool_max` | Possible slow query or connection leak |
| Consistency violation | `world_consistency_warning_total{severity="CRITICAL"} > 0` | Pause simulation; audit |

---

## 6. Debug-level logging toggle (per-session)

Enable verbose model-call logging (without credential exposure) by setting:

```bash
APP_OBSERVABILITY__LOG_LEVEL=DEBUG
```

At DEBUG level, context-assembly details, token budget decisions, and structured
output validation steps are logged with their `model_call_id`.  Full prompt text is
written to the access-controlled model-call store (not the shared ops log).

Disable DEBUG before production soak; it generates high volume and may trigger
compliance concerns for some log-forwarding configurations.
