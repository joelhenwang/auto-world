"""Audit event skeleton (S0-OPS-001)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fictional_world.observability.logging import get_correlation_id, redact_secrets

_AUDIT = logging.getLogger("fictional_world.audit")


@dataclass(frozen=True, slots=True)
class AuditEvent:
    action: str
    actor: str = "system"
    world_id: UUID | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    detail: dict[str, Any] | None = None


def emit_audit(event: AuditEvent) -> None:
    """Emit a structured audit line. Never log raw secrets."""

    detail = event.detail or {}
    safe_detail = {
        key: redact_secrets(value) if isinstance(value, str) else value
        for key, value in detail.items()
    }
    _AUDIT.info(
        "audit action=%s actor=%s world_id=%s resource=%s/%s correlation_id=%s detail=%s at=%s",
        event.action,
        event.actor,
        event.world_id,
        event.resource_type or "-",
        event.resource_id or "-",
        get_correlation_id() or "-",
        safe_detail,
        datetime.now(UTC).isoformat(),
    )
