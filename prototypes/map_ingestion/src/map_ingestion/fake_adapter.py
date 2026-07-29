"""A fake, deterministic multimodal map-extraction adapter.

No network, no model, no canon. It returns *recorded synthetic* responses keyed
by image content hash, mirroring the future real adapter's interface
(MAP-INGEST-004) so downstream contract logic can be tested offline. It also
demonstrates two required behaviours from the testing rules (handbook section 12):
transport-error surfacing (timeouts / 429s) and duplicate-delivery idempotency.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import MapExtraction, MapExtractionParseError, parse_map_extraction


@dataclass(frozen=True)
class ExtractionRequest:
    image_content_hash: str
    config_version: str


class TransportError(Exception):
    """Simulated provider transport failure (e.g. timeout or HTTP 429)."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass
class FakeMapExtractionAdapter:
    """Returns scripted synthetic payloads and dedupes duplicate deliveries.

    :param scripts: map of ``image_content_hash`` -> raw JSON response string.
    :param transport_error: if set, ``extract`` raises it instead of responding
        (used to test timeout/429 handling).
    """

    scripts: dict[str, str]
    transport_error: TransportError | None = None
    _delivered: dict[str, MapExtraction] = field(default_factory=dict, init=False)

    def extract(self, request: ExtractionRequest) -> MapExtraction:
        if self.transport_error is not None:
            raise self.transport_error

        raw = self.scripts.get(request.image_content_hash)
        if raw is None:
            raise MapExtractionParseError(
                f"no scripted response for image hash {request.image_content_hash!r}"
            )

        extraction = parse_map_extraction(raw)

        # At-least-once delivery: a repeated call for the same logical extraction
        # returns the first parsed result rather than a fresh duplicate.
        cached = self._delivered.get(extraction.extraction_id)
        if cached is not None:
            return cached
        self._delivered[extraction.extraction_id] = extraction
        return extraction
