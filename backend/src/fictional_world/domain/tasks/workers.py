"""Host and worker registry domain records (S4-ORCH-001)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class HostRecord(StrictContract):
    """A physical or virtual machine that runs worker processes."""

    id: UUID
    host_key: str = Field(min_length=1, max_length=300)
    capabilities: tuple[str, ...] = ()
    status: str = Field(default="active", max_length=50)
    first_seen_at: datetime
    last_seen_at: datetime


class WorkerRecord(StrictContract):
    """A single worker process registered to claim and execute tasks."""

    id: UUID
    host_id: UUID
    worker_key: str = Field(min_length=1, max_length=300)
    capabilities: tuple[str, ...] = ()
    status: str = Field(default="active", max_length=50)
    heartbeat_at: datetime
    registered_at: datetime
    drain_requested_at: datetime | None = None
    last_task_claimed_at: datetime | None = None
