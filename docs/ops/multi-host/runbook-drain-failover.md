# Runbook — Drain, Failover, and Disaster Recovery

**Document version:** 1.0  
**Task:** S4-OPS-001  
**Updated:** 2026-07-30  
**Status:** NORMATIVE — consult before any planned maintenance or unplanned failure  
**Normative sources:** `29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §S4-OPS-001;
`22_OBSERVABILITY_SECURITY_PRIVACY_AND_OPERATIONS.md` §12

---

## 1. Drain a single inference host (planned maintenance)

Use this procedure when rebooting or upgrading `strix-halo-a` or `strix-halo-b`.

### 1.1 Trigger drain via admin API

```bash
# Replace <host_key> with strix-halo-a or strix-halo-b
curl -s -u admin:<ADMIN_PASSWORD> -X POST \
  http://rtx-4060-ti:8000/admin/v1/hosts/<host_key>/drain

# Expected: {"host_key":"<host_key>","drained_workers":<N>,"status":"draining"}
```

This marks all workers on that host as `draining`.  The orchestrator stops routing
new tasks to them.  In-flight tasks complete naturally or their leases expire.

### 1.2 Wait for active tasks to finish

Monitor task queue depth on the draining host:

```bash
watch -n 5 'curl -s -u admin:<ADMIN_PASSWORD> \
  http://rtx-4060-ti:8000/admin/v1/workers | \
  python3 -m json.tool | grep -A5 "<host_key>"'
```

Wait until `active_tasks == 0` for all workers on the host, or until the configured
`DRAIN_TIMEOUT_SECONDS` elapses.  If tasks do not finish within the timeout the
orchestrator's lease-expiry reconciler will re-queue them on remaining hosts.

### 1.3 Stop the text server and perform maintenance

```bash
ssh <host_key> 'sudo systemctl stop text-server'
# — or —
ssh <host_key> 'docker compose -f compose.inference.yaml stop'
```

### 1.4 Restore the host

```bash
ssh <host_key> 'sudo systemctl start text-server'
# Wait for startup probe (takes 30–120 s depending on model load)
curl -s http://<host_key>:11434/health   # llama.cpp example
curl -s http://<host_key>:8000/health    # vLLM example
```

The text server re-registers with the gateway on first successful request.  The admin
API will show the endpoint health transition from `unknown` → `healthy`.

---

## 2. Reboot `rtx-4060-ti` (control-plane host)

### 2.1 Before rebooting

1. Confirm no phase is `running` (check `/api/v1/worlds/<world_id>/phases/active`).
2. Confirm image queue is empty or acceptable to pause:
   ```bash
   curl -s -u admin:<ADMIN_PASSWORD> \
     "http://rtx-4060-ti:8000/admin/v1/image-jobs?world_id=<world_id>&status=queued"
   ```
3. Pause the simulation via the world-status API if in doubt.
4. Confirm PostgreSQL has checkpointed: `sudo -u postgres psql -c "CHECKPOINT;"`.

### 2.2 Reboot

```bash
sudo reboot
```

### 2.3 After reboot — startup order

Services auto-start if `Restart=always` / `restart: unless-stopped` is configured.
Verify each step:

```bash
# 1. PostgreSQL
pg_isready -h localhost -U fictional_world

# 2. MinIO
mc ready local   # or: curl -s http://localhost:9000/minio/health/live

# 3. Orchestration worker
sudo journalctl -u orchestration-worker --since "1 min ago"

# 4. Model gateway / API
curl -s http://localhost:8000/health/ready

# 5. Frontend
curl -s http://localhost:5173/   # or configured Caddy port
```

In-flight phase tasks that lost their lease are re-queued automatically by the
reconciler within `RECONCILE_INTERVAL_SECONDS` (default 60 s).

---

## 3. Unplanned Halo A loss

When `strix-halo-a` becomes unreachable without a prior drain:

1. The gateway marks the endpoint as `unhealthy` when consecutive health probes fail
   (default: 3 consecutive failures within 90 s, configurable via gateway settings).
2. All tasks currently leased to Halo A workers have their leases expire at their
   `lease_expires_at` timestamp.
3. The orchestrator's reconcile loop re-queues those tasks.
4. Halo B (if healthy) picks up the re-queued tasks automatically.
5. The world continues with increased per-task latency; no simulation data is lost.

**Operator action required:**

- Check model-gateway logs for endpoint downgrade events:
  ```
  grep '"event":"model.endpoint.unhealthy"' /var/log/fictional-world/gateway.jsonl
  ```
- Inspect Halo A remotely or physically.
- Do NOT manually re-enqueue tasks; the reconciler handles re-queuing.
- Once Halo A is restored, the gateway re-admits it automatically on next probe.

**Affected metrics to watch:**

- `model_fallback_total` — increases while Halo A is down.
- `task_wait_seconds` — rises if Halo B is saturated.
- `worker_heartbeat_age_seconds{host="strix-halo-a"}` — spikes and stays elevated.

---

## 4. Both Halos down — pause policy

When **both** `strix-halo-a` and `strix-halo-b` are unavailable:

### 4.1 Automatic behaviour

The model gateway returns `MODEL_NOT_AVAILABLE` for all text-generation requests.
The phase runner catches this error and:

1. Does **not** commit a failed phase;
2. Marks the current task as `RETRY_SCHEDULED` with exponential back-off;
3. Emits a `world.paused` log event with `reason: no_text_endpoint_available`.

The world enters a paused / stalled state.  No canonical state is mutated.  No
data is lost.

### 4.2 OpenRouter emergency fallback

If the active world's privacy policy allows `allow_openrouter_emergency`:

```toml
# config/profiles/stage4.toml
[model_gateway]
provider_mode = "openrouter"
```

The gateway will route to OpenRouter.  This requires `OPENROUTER__API_KEY` to be set.

> **Warning:** Never enable OpenRouter for worlds with `privacy_policy = "local_private"`.
> The privacy policy is checked per-request by the gateway; enabling it globally for a
> local-private world is a misconfiguration.

### 4.3 Operator checklist

- [ ] Confirm both Halos are actually down (not a network issue between RTX and Halos).
- [ ] Decide whether to resume with OpenRouter or wait for hardware recovery.
- [ ] If waiting: notify any observers; document expected downtime.
- [ ] If using OpenRouter: set the environment variable and restart `model-gateway`.
- [ ] Once Halos recover: restore `provider_mode = "local"` and restart gateway.
- [ ] Review re-queued tasks; confirm no duplicates in task/outbox tables.

---

## 5. PostgreSQL backup and restore

### 5.1 Backup procedure (run nightly via cron)

```bash
#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR=/var/backups/fictional-world/postgres
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$BACKUP_DIR"

pg_basebackup \
  -h localhost \
  -U fictional_world_backup \
  -D "$BACKUP_DIR/$TIMESTAMP" \
  -Ft -z -P

# Keep last 7 days; remove older
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
```

Verify backup integrity after creation:
```bash
pg_restore --list "$BACKUP_DIR/$TIMESTAMP/base.tar.gz" | head -20
```

### 5.2 Restore procedure

```bash
# Stop the application first
sudo systemctl stop fictional-world-api fictional-world-orchestration

# Stop PostgreSQL
sudo systemctl stop postgresql

# Clear data directory (DESTRUCTIVE — confirm before running)
sudo rm -rf /var/lib/postgresql/16/main/*

# Restore from backup
sudo -u postgres tar -xzf /var/backups/fictional-world/postgres/<timestamp>/base.tar.gz \
  -C /var/lib/postgresql/16/main/

# Start PostgreSQL
sudo systemctl start postgresql
pg_isready -U fictional_world

# Run Alembic to confirm migrations match
uv run alembic -c backend/alembic.ini upgrade head
uv run alembic -c backend/alembic.ini check

# Restart services
sudo systemctl start fictional-world-orchestration fictional-world-api
```

### 5.3 Point-in-time recovery

Enable WAL archiving in `postgresql.conf`:
```conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/backups/fictional-world/wal/%f'
```

Restore to a specific LSN using `recovery_target_lsn` in `recovery.conf` /
PostgreSQL 12+ primary signal file.  Consult the PostgreSQL documentation for the
installed version.

---

## 6. Emergency contacts and escalation

This is a local single-user deployment.  Escalation is to the project owner.

Document the following for each incident:

- Time range affected
- Host(s) involved
- Services impacted
- World IDs affected and their phase/day at time of failure
- Canonical events committed after last backup
- Actions taken and timestamps
- Resolution
