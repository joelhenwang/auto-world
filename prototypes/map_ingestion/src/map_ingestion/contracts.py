"""Proposal-only contracts for world-map image ingestion.

This is a **prototype** for ADR-0001 / task MAP-INGEST-001. Everything here is a
*proposal* produced by a (future) multimodal model. Per the project canon rule
(README section 2, AGENTS.md section 4.1), a model may only propose; nothing in
this module writes canonical state, touches a database, or performs I/O. The
deterministic validator and atomic commit service (tasks MAP-INGEST-002/003) are
intentionally out of scope.

The shapes here map onto the canonical ``Location`` and ``Route`` definitions in
``09_WORLD_DIRECTOR_NPCS_LORE_MAP_AND_GENERATIONS.md`` section 11; they adapt to
those shapes and do not redefine them.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class MapExtractionParseError(Exception):
    """Raised when a raw model payload cannot be parsed into a ``MapExtraction``.

    Wraps both malformed JSON and contract-validation failures so callers can
    handle a single typed error at the boundary.
    """

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class LocationType(StrEnum):
    """Canonical location types from ``09`` section 11.1."""

    REALM = "realm"
    REGION = "region"
    SETTLEMENT = "settlement"
    DISTRICT = "district"
    BUILDING = "building"
    ROOM = "room"
    LANDMARK = "landmark"
    WILDERNESS_ZONE = "wilderness_zone"
    ROAD_SEGMENT = "road_segment"
    EXTRADIMENSIONAL_AREA = "extradimensional_area"


class Directionality(StrEnum):
    ONE_WAY = "one_way"
    TWO_WAY = "two_way"


# Normalized image-space coordinate components in [0, 1]. Canonical coordinates
# are optional (``09`` 11.1); when present they are normalized, not pixel values.
UnitFloat = Annotated[float, Field(ge=0.0, le=1.0)]
Confidence = Annotated[float, Field(ge=0.0, le=1.0)]
ProposalName = Annotated[str, Field(min_length=1, max_length=120)]


class _StrictModel(BaseModel):
    """Strict, immutable base: unknown fields are rejected (S0-DOM-001)."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Coordinate(_StrictModel):
    x: UnitFloat
    y: UnitFloat


class PointOfInterest(_StrictModel):
    """A proposed map node. Maps onto a canonical ``Location`` candidate."""

    poi_id: str = Field(min_length=1, max_length=64)
    name: ProposalName
    location_type: LocationType
    region_ref: str | None = Field(default=None, max_length=64)
    parent_ref: str | None = Field(default=None, max_length=64)
    coordinates: Coordinate | None = None
    source_label: str | None = Field(
        default=None, max_length=200, description="Raw label text read from the image."
    )
    tags: tuple[str, ...] = ()
    confidence: Confidence = 1.0


class Waypoint(_StrictModel):
    """A sub-point in between two POIs (the 'points in between' of a route)."""

    name: str | None = Field(default=None, max_length=120)
    location_type: LocationType = LocationType.ROAD_SEGMENT
    coordinates: Coordinate | None = None
    confidence: Confidence = 1.0


class MapEdge(_StrictModel):
    """A proposed connection between two POIs. Maps onto a canonical ``Route``."""

    edge_id: str = Field(min_length=1, max_length=64)
    origin_poi_id: str = Field(min_length=1, max_length=64)
    destination_poi_id: str = Field(min_length=1, max_length=64)
    directionality: Directionality = Directionality.TWO_WAY
    terrain_tags: tuple[str, ...] = ()
    danger: Confidence = 0.0
    waypoints: tuple[Waypoint, ...] = ()

    @model_validator(mode="after")
    def _no_self_loop(self) -> MapEdge:
        if self.origin_poi_id == self.destination_poi_id:
            raise ValueError(f"edge {self.edge_id!r} connects a POI to itself")
        return self


class Provenance(_StrictModel):
    """Where a proposal came from. Model input is limited to image + config."""

    model_slug: str = Field(min_length=1, max_length=200)
    prompt_version: str = Field(min_length=1, max_length=64)
    image_content_hash: str = Field(min_length=1, max_length=128)
    config_version: str = Field(min_length=1, max_length=64)


def compute_extraction_id(image_content_hash: str, config_version: str) -> str:
    """Deterministic idempotency key for one (image, config) pair."""

    digest = hashlib.sha256(f"{image_content_hash}:{config_version}".encode())
    return digest.hexdigest()


class MapExtraction(_StrictModel):
    """A full proposal-only extraction from one world-map image."""

    extraction_id: str = Field(min_length=1, max_length=128)
    provenance: Provenance
    points_of_interest: tuple[PointOfInterest, ...]
    edges: tuple[MapEdge, ...] = ()
    generated_at: datetime

    @model_validator(mode="after")
    def _validate_graph(self) -> MapExtraction:
        # Idempotency key must match its inputs.
        expected = compute_extraction_id(
            self.provenance.image_content_hash, self.provenance.config_version
        )
        if self.extraction_id != expected:
            raise ValueError("extraction_id does not match provenance (image_hash, config_version)")

        # Timestamps are timezone-aware UTC (AGENTS.md section 10).
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() != UTC.utcoffset(None):
            raise ValueError("generated_at must be timezone-aware UTC")

        # POI ids are unique.
        ids = [p.poi_id for p in self.points_of_interest]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate poi_id in points_of_interest")
        known = set(ids)

        # Every edge endpoint references a known POI.
        for edge in self.edges:
            missing = {edge.origin_poi_id, edge.destination_poi_id} - known
            if missing:
                raise ValueError(
                    f"edge {edge.edge_id!r} references unknown poi ids {sorted(missing)}"
                )
        return self


def parse_map_extraction(raw: str | bytes) -> MapExtraction:
    """Parse a raw model payload into a validated ``MapExtraction``.

    Raises :class:`MapExtractionParseError` for malformed JSON or any contract
    violation. This is the single boundary where untrusted model output becomes
    a typed proposal.
    """

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MapExtractionParseError("payload is not valid JSON", cause=exc) from exc
    try:
        return MapExtraction.model_validate(data)
    except ValidationError as exc:
        raise MapExtractionParseError("payload failed contract validation", cause=exc) from exc
