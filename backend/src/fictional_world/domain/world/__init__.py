"""World domain package."""

from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)

__all__ = [
    "AggregateVersionRecord",
    "WorldClockRecord",
    "WorldRecord",
]
