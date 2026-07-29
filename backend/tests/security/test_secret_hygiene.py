"""Security / secret hygiene checks for Stage 0 gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from fictional_world.observability.logging import redact_secrets

ROOT = Path(__file__).resolve().parents[3]
GENERATED = ROOT / "docs" / "generated"


@pytest.mark.security
def test_generated_docs_have_no_live_api_keys() -> None:
    needles = ("sk-live-", "OPENROUTER_API_KEY=", "Bearer sk-")
    offenders: list[str] = []
    for path in GENERATED.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".json", ".sql", ".md", ".yaml", ".yml", ".toml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle in text:
                offenders.append(f"{path.relative_to(ROOT)} contains {needle}")
    assert offenders == []


@pytest.mark.security
def test_redaction_blocks_openrouter_style_keys() -> None:
    raw = "calling openrouter with api_key=sk-or-v1-abcdefghijklmnopqrstuvwxyz012345"
    cleaned = redact_secrets(raw)
    assert "sk-or-v1-abcdefghijklmnopqrstuvwxyz012345" not in cleaned
    assert "***REDACTED***" in cleaned
