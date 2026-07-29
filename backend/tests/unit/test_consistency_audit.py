"""Consistency audit helper tests."""

from __future__ import annotations

from fictional_world.testing.consistency import (
    audit_stage0_consistency,
    stage0_hard_invariant_checklist,
)


def test_stage0_consistency_audit_clean() -> None:
    assert stage0_hard_invariant_checklist()
    assert audit_stage0_consistency() == []


def test_stage0_consistency_audit_reports_failures() -> None:
    findings = audit_stage0_consistency(failing_codes=frozenset({"atomic_event_commit"}))
    assert len(findings) == 1
    assert findings[0].severity == "hard"
