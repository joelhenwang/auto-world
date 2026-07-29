"""Lightweight consistency audit checklist used by the Stage 0 gate report."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConsistencyFinding:
    code: str
    severity: str
    message: str


def stage0_hard_invariant_checklist() -> tuple[str, ...]:
    """Named hard invariants that Stage 0 tests must cover."""

    return (
        "atomic_event_commit",
        "duplicate_delivery_safe",
        "task_lease_exclusive",
        "phase_snapshot_immutable",
        "seed_import_idempotent",
        "no_network_in_default_tests",
        "secret_redaction",
        "loopback_bind_default",
    )


def audit_stage0_consistency(
    *, failing_codes: frozenset[str] = frozenset()
) -> list[ConsistencyFinding]:
    """Return findings; empty list means zero hard violations."""

    findings: list[ConsistencyFinding] = []
    for code in stage0_hard_invariant_checklist():
        if code in failing_codes:
            findings.append(
                ConsistencyFinding(
                    code=code,
                    severity="hard",
                    message=f"invariant {code} reported failing",
                )
            )
    return findings
