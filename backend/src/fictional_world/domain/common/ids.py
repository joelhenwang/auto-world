"""Branded identifier NewTypes for domain aggregates."""

from __future__ import annotations

from typing import NewType
from uuid import UUID

WorldId = NewType("WorldId", UUID)
CharacterId = NewType("CharacterId", UUID)
SceneId = NewType("SceneId", UUID)
EventId = NewType("EventId", UUID)
PhaseId = NewType("PhaseId", UUID)
TaskId = NewType("TaskId", UUID)
ObservationId = NewType("ObservationId", UUID)
MemoryId = NewType("MemoryId", UUID)
SnapshotId = NewType("SnapshotId", UUID)
