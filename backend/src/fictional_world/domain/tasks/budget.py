"""Model request budget reservation records (handbook ``06`` §16.5)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.common.enums import BudgetStatus


class RequestBudgetRecord(StrictContract):
    id: UUID
    reservation_key: str = Field(min_length=1, max_length=200)
    required_request_count: int = Field(ge=1)
    provider_kind: str = Field(min_length=1, max_length=100)
    model_slug: str = Field(min_length=1, max_length=200)
    status: BudgetStatus
    world_id: UUID | None = None
    phase_run_id: UUID | None = None
    task_run_id: UUID | None = None
    reserved_at: datetime | None = None
    expires_at: datetime
    consumed_at: datetime | None = None
