"""Contract tests for the proposal-only MapExtraction pipeline (MAP-INGEST-001).

These follow handbook section 12: a happy-path parse is not enough. We exercise
malformed JSON, missing fields, unknown enum values, out-of-range values,
transport failures (timeout/429), and duplicate delivery.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from map_ingestion import (
    ExtractionRequest,
    FakeMapExtractionAdapter,
    MapExtraction,
    MapExtractionParseError,
    TransportError,
    compute_extraction_id,
    parse_map_extraction,
)

FIXTURES = Path(__file__).parent / "fixtures"
VALID_RAW = (FIXTURES / "world_map_extraction_valid.json").read_text()


def _valid_data() -> dict:
    return json.loads(VALID_RAW)


# --- happy path -----------------------------------------------------------


def test_valid_payload_parses_and_maps_to_location_route_shapes() -> None:
    extraction = parse_map_extraction(VALID_RAW)
    assert isinstance(extraction, MapExtraction)
    assert len(extraction.points_of_interest) == 6
    # POI -> Location candidate.
    valerion = next(p for p in extraction.points_of_interest if p.poi_id == "valerion")
    assert valerion.location_type.value == "settlement"
    assert valerion.region_ref == "valerian_empire"
    # Edge -> Route candidate, with the "sub-points in between" as waypoints.
    edge = extraction.edges[0]
    assert edge.origin_poi_id == "valerion"
    assert edge.destination_poi_id == "dawnspire_citadel"
    assert len(edge.waypoints) == 2


def test_extraction_id_is_deterministic_over_image_and_config() -> None:
    data = _valid_data()
    expected = compute_extraction_id(
        data["provenance"]["image_content_hash"], data["provenance"]["config_version"]
    )
    assert parse_map_extraction(VALID_RAW).extraction_id == expected


# --- parser robustness ----------------------------------------------------


def test_malformed_json_raises_typed_error() -> None:
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction('{"extraction_id": "abc", ')  # truncated


def test_missing_required_field_is_rejected() -> None:
    data = _valid_data()
    del data["points_of_interest"][0]["name"]
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_unknown_location_type_is_rejected() -> None:
    data = _valid_data()
    data["points_of_interest"][0]["location_type"] = "megacity"  # not in the enum
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_unknown_extra_field_is_forbidden() -> None:
    data = _valid_data()
    data["points_of_interest"][0]["smuggled"] = "value"
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_coordinate_out_of_range_is_rejected() -> None:
    data = _valid_data()
    data["points_of_interest"][0]["coordinates"] = {"x": 1.7, "y": 0.2}
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_empty_name_is_rejected() -> None:
    data = _valid_data()
    data["points_of_interest"][0]["name"] = ""
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


# --- graph integrity ------------------------------------------------------


def test_edge_referencing_unknown_poi_is_rejected() -> None:
    data = _valid_data()
    data["edges"][0]["destination_poi_id"] = "atlantis"
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_duplicate_poi_id_is_rejected() -> None:
    data = _valid_data()
    dup = dict(data["points_of_interest"][0])
    data["points_of_interest"].append(dup)
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_self_loop_edge_is_rejected() -> None:
    data = _valid_data()
    data["edges"][0]["destination_poi_id"] = data["edges"][0]["origin_poi_id"]
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_naive_timestamp_is_rejected() -> None:
    data = _valid_data()
    data["generated_at"] = "2026-07-29T11:20:00"  # no tz
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


def test_tampered_extraction_id_is_rejected() -> None:
    data = _valid_data()
    data["extraction_id"] = "0" * 64
    with pytest.raises(MapExtractionParseError):
        parse_map_extraction(json.dumps(data))


# --- fake adapter: transport + idempotency --------------------------------


def _hash_from_valid() -> str:
    return _valid_data()["provenance"]["image_content_hash"]


def test_adapter_returns_parsed_extraction() -> None:
    adapter = FakeMapExtractionAdapter(scripts={_hash_from_valid(): VALID_RAW})
    result = adapter.extract(ExtractionRequest(_hash_from_valid(), "map-extract-config-v1"))
    assert result.extraction_id == compute_extraction_id(
        _hash_from_valid(), "map-extract-config-v1"
    )


def test_adapter_surfaces_retryable_transport_error() -> None:
    adapter = FakeMapExtractionAdapter(
        scripts={_hash_from_valid(): VALID_RAW},
        transport_error=TransportError("429 Too Many Requests", retryable=True),
    )
    with pytest.raises(TransportError) as exc:
        adapter.extract(ExtractionRequest(_hash_from_valid(), "map-extract-config-v1"))
    assert exc.value.retryable is True


def test_duplicate_delivery_is_idempotent() -> None:
    adapter = FakeMapExtractionAdapter(scripts={_hash_from_valid(): VALID_RAW})
    req = ExtractionRequest(_hash_from_valid(), "map-extract-config-v1")
    first = adapter.extract(req)
    second = adapter.extract(req)  # at-least-once redelivery
    assert first is second  # same object, not a duplicate proposal


def test_unknown_image_hash_raises() -> None:
    adapter = FakeMapExtractionAdapter(scripts={})
    with pytest.raises(MapExtractionParseError):
        adapter.extract(ExtractionRequest("deadbeef", "map-extract-config-v1"))


def test_contract_is_proposal_only_no_persistence_surface() -> None:
    # Guard against accidental canon coupling: the contract module must not
    # import database / ORM / session machinery.
    from map_ingestion import contracts

    source = Path(contracts.__file__).read_text().lower()
    for forbidden in ("sqlalchemy", "psycopg", "session", "engine", "commit("):
        assert forbidden not in source, f"proposal contract must not reference {forbidden!r}"
