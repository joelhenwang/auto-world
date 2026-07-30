# Secrets, Network Security, and Service Tokens

**Document version:** 1.0  
**Task:** S4-OPS-001  
**Updated:** 2026-07-30  
**Status:** NORMATIVE — apply before Stage 4 soak  
**Normative sources:** `22_OBSERVABILITY_SECURITY_PRIVACY_AND_OPERATIONS.md` §9–§11;
`29_STAGE_4_LOCAL_DISTRIBUTION_AND_IMAGES.md` §S4-OPS-001

---

## 1. Network perimeter

### 1.1 Trusted LAN segment

All three hosts (`strix-halo-a`, `strix-halo-b`, `rtx-4060-ti`) share a dedicated LAN
segment (dedicated VLAN or physical switch) that is **not** reachable from the public
internet.

Minimum firewall rules on each host:

```
# Allow all inbound from trusted LAN (192.168.100.0/24 — adjust to your range)
iptables -A INPUT -s 192.168.100.0/24 -j ACCEPT

# Drop all other inbound except loopback and established connections
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -j DROP
```

Use `ufw` or `nftables` equivalents.  Apply persistently via `iptables-save` /
`ufw enable`.

### 1.2 TLS within the LAN

**Minimum requirement:** mutual TLS between FastAPI (control plane) and text-server
endpoints on Halo A / Halo B.

Generate a local CA and per-host certificates:

```bash
# One-time: create local CA
openssl genrsa -out /etc/ssl/fictional-world/ca.key 4096
openssl req -x509 -new -nodes \
  -key /etc/ssl/fictional-world/ca.key \
  -sha256 -days 3650 \
  -out /etc/ssl/fictional-world/ca.crt \
  -subj "/CN=FictionalWorldLocalCA"

# Per-host: sign a server cert (repeat for each hostname)
openssl genrsa -out /etc/ssl/fictional-world/<host>.key 2048
openssl req -new \
  -key /etc/ssl/fictional-world/<host>.key \
  -out /etc/ssl/fictional-world/<host>.csr \
  -subj "/CN=<host>"
openssl x509 -req \
  -in /etc/ssl/fictional-world/<host>.csr \
  -CA /etc/ssl/fictional-world/ca.crt \
  -CAkey /etc/ssl/fictional-world/ca.key \
  -CAcreateserial \
  -out /etc/ssl/fictional-world/<host>.crt \
  -days 365 -sha256
```

Distribute `ca.crt` to all three hosts; each service verifies peer certificates
against this CA.

**Documented exception:** if all three hosts share a single physically locked rack
with no cross-VLAN routes to untrusted networks, TLS may be deferred to a follow-up
ADR, provided the network segment is documented as trusted.  Record this exception
in the operations log.

---

## 2. Service tokens

### 2.1 Roles and tokens

| Service | Token role | Scope |
|---|---|---|
| orchestration-worker | `WORKER_TOKEN` | claim/complete tasks, heartbeat |
| text-server (Halo A/B) | `TEXT_SERVER_TOKEN` | register endpoints, submit results |
| comfyui | `COMFYUI_TOKEN` | submit/poll image jobs |
| model-gateway | `GATEWAY_TOKEN` | query capability registry, route |
| admin API callers | `ADMIN_PASSWORD` | all `/admin/v1/*` endpoints |

### 2.2 Token format

Use randomly generated 256-bit hex strings:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Store in `/etc/fictional-world/secrets/<service>.token` with mode `0600`, owned by
the service user.  Never store in Git, environment files committed to source control,
or Docker images.

### 2.3 Environment injection

Each service reads its token from the environment.  The Compose or systemd unit
injects the secret from a host-local file:

```yaml
# docker-compose service fragment
environment:
  - WORKER_TOKEN_FILE=/run/secrets/worker_token
secrets:
  worker_token:
    file: /etc/fictional-world/secrets/worker.token
```

Or for systemd:
```ini
[Service]
EnvironmentFile=/etc/fictional-world/secrets/service.env
```

### 2.4 Token rotation

1. Generate a new token for the service.
2. Update the secret file on the target host.
3. Restart the service; it will pick up the new token.
4. Update any callers that hold the old token (gateway config, admin scripts).
5. Confirm the old token rejects requests by monitoring `401` responses in logs.

---

## 3. Secrets that must never appear in logs

The following values must **never** appear in application logs, structured log events,
tracing attributes, metric labels, or error messages:

| Secret | Log-safe substitute |
|---|---|
| `OPENROUTER__API_KEY` | `"[REDACTED]"` or omit field |
| `AUTH__LOCAL_ADMIN_PASSWORD` | Never log; validate server-side only |
| `DATABASE__PASSWORD` | `"[REDACTED]"` |
| Worker / service tokens | Record token `prefix[:8]` for audit, not full value |
| Object storage credentials | `"[REDACTED]"` |
| TLS private key material | Never log |
| Signed object URLs | Omit or log URL without query string |
| Full raw prompts (production) | Log `prompt_id` / hash; full text to access-controlled store only |
| Private character memories (shared ops log) | Log `memory_id`; content in per-character audit channel |

The `ruff` rule `S105` (hardcoded passwords) and the secret-hygiene test in
`backend/tests/security/test_secret_hygiene.py` enforce these rules statically.

Redaction is implemented in `backend/src/fictional_world/observability/logging.py`.
Add any new secret fields to `REDACTED_FIELDS` if they pass through the log pipeline.

---

## 4. Database credentials

PostgreSQL credentials are set at bootstrap and must satisfy:

- Password length ≥ 24 characters.
- Dedicated application user `fictional_world` with `LOGIN`, `CONNECT`, and
  schema-level privileges only; no `SUPERUSER` or `CREATEDB`.
- Separate backup user `fictional_world_backup` with `REPLICATION` privilege only.
- No credentials in `compose.yaml` or Alembic config; read from environment:
  ```
  DATABASE__HOST, DATABASE__PORT, DATABASE__NAME, DATABASE__USER, DATABASE__PASSWORD
  ```

---

## 5. OpenRouter key

`OPENROUTER__API_KEY` is required only when `model_gateway.provider_mode = "openrouter"`
or when the emergency-fallback policy applies.

- Store in `rtx-4060-ti:/etc/fictional-world/secrets/openrouter.env` (mode `0600`).
- Do not copy to Halo A or Halo B; only `model-gateway` on the control-plane host
  needs it.
- Rotate by generating a new key in the OpenRouter dashboard, updating the file,
  and restarting `model-gateway`.

---

## 6. Secret audit checklist (run before every soak test)

```bash
# Check no .env files committed
git status | grep -E '\.env$'

# Check no token-like strings in source files
cd /workspace && uv run python -m pytest backend/tests/security/ -q

# Verify file permissions
ls -l /etc/fictional-world/secrets/
# All files: -rw------- (0600), owner = service user

# Confirm REDACTED fields in a sample log line
curl -s http://localhost:8000/health/live \
  | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
# Should not contain any credential values
```
