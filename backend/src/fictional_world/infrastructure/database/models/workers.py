"""ORM models for Stage 4 host/worker registry (S4-ORCH-001)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from fictional_world.infrastructure.database.base import Base
from fictional_world.infrastructure.database.naming import WORLDSIM_SCHEMA


class HostRegistryRow(Base):
    __tablename__ = "host_registry"
    __table_args__ = (
        UniqueConstraint("host_key", name="uq_host_registry_host_key"),
        CheckConstraint(
            "status IN ('active', 'lost', 'decommissioned')",
            name="ck_host_registry_status",
        ),
        Index("ix_host_registry_status", "status"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    host_key: Mapped[str] = mapped_column(Text, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class WorkerRegistryRow(Base):
    __tablename__ = "worker_registry"
    __table_args__ = (
        UniqueConstraint("worker_key", name="uq_worker_registry_worker_key"),
        CheckConstraint(
            "status IN ('active', 'draining', 'drained', 'lost')",
            name="ck_worker_registry_status",
        ),
        Index("ix_worker_registry_host_status", "host_id", "status"),
        Index("ix_worker_registry_heartbeat", "status", "heartbeat_at"),
        {"schema": WORLDSIM_SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    host_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            f"{WORLDSIM_SCHEMA}.host_registry.id",
            name="fk_worker_registry_host_id_host_registry",
        ),
        nullable=False,
    )
    worker_key: Mapped[str] = mapped_column(Text, nullable=False)
    capabilities: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'"))
    heartbeat_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    drain_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_task_claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_draining: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
