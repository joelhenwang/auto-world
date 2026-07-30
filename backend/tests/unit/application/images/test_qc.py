"""Unit tests for image QC (S4-IMG-003)."""

from __future__ import annotations

import pytest

from fictional_world.application.images.qc import technical_qc

_STUB_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)

_STUB_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 200


@pytest.mark.unit
def test_qc_passes_valid_png() -> None:
    # Pad the stub PNG so it passes the byte-size minimum
    padded = _STUB_PNG + b"\x00" * 200
    report = technical_qc(padded, expected_content_type="image/png")
    assert report.passed is True
    assert report.checks["non_empty"] is True
    assert report.checks["valid_format"] is True


@pytest.mark.unit
def test_qc_passes_valid_jpeg() -> None:
    report = technical_qc(_STUB_JPEG, expected_content_type="image/jpeg")
    assert report.passed is True


@pytest.mark.unit
def test_qc_fails_empty_bytes() -> None:
    report = technical_qc(b"", expected_content_type="image/png")
    assert report.passed is False
    assert report.checks["non_empty"] is False


@pytest.mark.unit
def test_qc_fails_invalid_format() -> None:
    report = technical_qc(b"not-an-image" * 20, expected_content_type="image/png")
    assert report.passed is False
    assert report.checks["valid_format"] is False


@pytest.mark.unit
def test_qc_fails_bad_content_type() -> None:
    report = technical_qc(_STUB_PNG, expected_content_type="application/octet-stream")
    assert report.passed is False
    assert report.checks["content_type_plausible"] is False


@pytest.mark.unit
def test_qc_dimension_check() -> None:
    padded = _STUB_PNG + b"\x00" * 200
    report = technical_qc(padded, width_px=100, height_px=100)
    assert report.checks["min_dimensions"] is True


@pytest.mark.unit
def test_qc_dimension_too_small() -> None:
    report = technical_qc(_STUB_PNG, width_px=10, height_px=10, min_width=100, min_height=100)
    assert report.checks["min_dimensions"] is False
    assert report.passed is False


@pytest.mark.unit
def test_qc_no_content_type_passes_format_check() -> None:
    padded = _STUB_PNG + b"\x00" * 200
    report = technical_qc(padded)
    assert report.checks["content_type_plausible"] is True
    assert report.checks["valid_format"] is True
