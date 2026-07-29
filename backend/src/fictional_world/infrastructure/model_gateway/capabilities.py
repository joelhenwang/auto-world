"""Structured-output capability modes and probe stub (handbook ``12`` §8)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class CapabilityMode(StrEnum):
    NATIVE_STRICT = "NATIVE_STRICT"
    NATIVE_BEST_EFFORT = "NATIVE_BEST_EFFORT"
    JSON_OBJECT_PROMPTED = "JSON_OBJECT_PROMPTED"
    TEXT_REPAIR_REQUIRED = "TEXT_REPAIR_REQUIRED"


@dataclass(frozen=True, slots=True)
class CapabilityProbeResult:
    profile_id: str
    mode: CapabilityMode
    embedding_dimensions: int | None
    verified_at: datetime
    detail: str


class CapabilityProbeStub:
    """Stage 0 stub: records a configured mode without live HTTP."""

    def __init__(
        self,
        *,
        default_mode: CapabilityMode = CapabilityMode.JSON_OBJECT_PROMPTED,
        embedding_dimensions: int = 2048,
    ) -> None:
        self._default_mode = default_mode
        self._embedding_dimensions = embedding_dimensions
        self.results: list[CapabilityProbeResult] = []

    async def probe_text_profile(self, profile_id: str) -> CapabilityProbeResult:
        result = CapabilityProbeResult(
            profile_id=profile_id,
            mode=self._default_mode,
            embedding_dimensions=None,
            verified_at=datetime.now(tz=UTC),
            detail="stub: no live probe",
        )
        self.results.append(result)
        return result

    async def probe_embedding_profile(self, profile_id: str) -> CapabilityProbeResult:
        result = CapabilityProbeResult(
            profile_id=profile_id,
            mode=CapabilityMode.NATIVE_BEST_EFFORT,
            embedding_dimensions=self._embedding_dimensions,
            verified_at=datetime.now(tz=UTC),
            detail="stub: assumed embedding dimensions",
        )
        self.results.append(result)
        return result
