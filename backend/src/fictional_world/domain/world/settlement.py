"""Settlement indicator aggregate updates (pure / deterministic)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.domain.common.errors import InvalidAction
from fictional_world.domain.stage3.persistence import SettlementIndicatorPersistenceRecord


def apply_settlement_indicator_update(
    current: SettlementIndicatorPersistenceRecord | None,
    *,
    world_id: UUID,
    location_id: UUID,
    indicator_key: str,
    day_index: int,
    delta: Decimal,
    source_event_id: UUID | None = None,
    indicator_id: UUID | None = None,
    absolute_value: Decimal | None = None,
) -> SettlementIndicatorPersistenceRecord:
    """Create or advance a settlement indicator for a location/day.

    When ``absolute_value`` is provided it replaces the prior value; otherwise
    ``delta`` is applied to the previous value (or zero).
    """
    if day_index < 0:
        raise InvalidAction("day_index must be >= 0")
    if not indicator_key.strip():
        raise InvalidAction("indicator_key must be non-empty")

    if absolute_value is not None:
        next_value = Decimal(str(absolute_value))
        version = 0 if current is None else current.version + 1
        record_id = indicator_id or (current.id if current is not None else uuid4())
    elif current is None:
        next_value = Decimal(str(delta))
        version = 0
        record_id = indicator_id or uuid4()
    else:
        if current.location_id != location_id or current.indicator_key != indicator_key:
            raise InvalidAction(
                "current settlement indicator does not match location_id/indicator_key"
            )
        next_value = current.value + Decimal(str(delta))
        version = current.version + 1
        record_id = current.id

    return SettlementIndicatorPersistenceRecord(
        id=record_id,
        world_id=world_id,
        location_id=location_id,
        indicator_key=indicator_key,
        value=next_value,
        day_index=day_index,
        source_event_id=source_event_id,
        version=version,
    )
