"""Prototype: world-map image -> proposal-only MapExtraction contract."""

from .contracts import (
    Coordinate,
    Directionality,
    LocationType,
    MapEdge,
    MapExtraction,
    MapExtractionParseError,
    PointOfInterest,
    Provenance,
    Waypoint,
    compute_extraction_id,
    parse_map_extraction,
)
from .fake_adapter import ExtractionRequest, FakeMapExtractionAdapter, TransportError

__all__ = [
    "Coordinate",
    "Directionality",
    "ExtractionRequest",
    "FakeMapExtractionAdapter",
    "LocationType",
    "MapEdge",
    "MapExtraction",
    "MapExtractionParseError",
    "PointOfInterest",
    "Provenance",
    "TransportError",
    "Waypoint",
    "compute_extraction_id",
    "parse_map_extraction",
]
