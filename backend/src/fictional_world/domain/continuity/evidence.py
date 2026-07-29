"""Relationship evidence input contract for bounded aggregation."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from fictional_world.domain.common.base import StrictContract


class RelationshipEvidenceInput(StrictContract):
    """Model-proposed evidence; the projector applies bounded deltas."""

    dimension: str = Field(min_length=1, max_length=100)
    signed_strength: Decimal = Field(ge=Decimal("-1"), le=Decimal("1"))
    evidence_tags: tuple[str, ...] = ()
    source_event_id: UUID | None = None
    phase_index: int | None = Field(default=None, ge=0)
    perceived: bool = True
    decay_policy: str = Field(default="default", min_length=1, max_length=50)
