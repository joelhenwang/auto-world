"""Stage 3 evaluator graph — diagnostics only; cannot mutate canon."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from fictional_world.domain.stage3.persistence import (
    EvaluatorRunPersistenceRecord,
    QualityFindingPersistenceRecord,
)


@dataclass(frozen=True, slots=True)
class EvaluatorGraphInput:
    world_id: UUID
    scope: str
    target_ref: str | None = None
    narration_text: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class EvaluatorGraphResult:
    run: EvaluatorRunPersistenceRecord
    findings: tuple[QualityFindingPersistenceRecord, ...]
    may_request_narration_regen: bool


def run_evaluator_graph(inp: EvaluatorGraphInput) -> EvaluatorGraphResult:
    """Produce quality findings that never set can_mutate_canon=True."""

    run_id = uuid4()
    key = inp.idempotency_key or f"evaluator:{inp.world_id}:{inp.scope}:{run_id}"
    findings: list[QualityFindingPersistenceRecord] = []
    if inp.narration_text and len(inp.narration_text) > 8_000:
        findings.append(
            QualityFindingPersistenceRecord(
                id=uuid4(),
                evaluator_run_id=run_id,
                world_id=inp.world_id,
                finding_code="narration_too_long",
                severity="warn",
                message="Narration exceeds soft length budget",
                can_mutate_canon=False,
            )
        )
    run = EvaluatorRunPersistenceRecord(
        id=run_id,
        world_id=inp.world_id,
        scope=inp.scope,
        target_ref=inp.target_ref,
        status="completed",
        idempotency_key=key,
        findings_summary={"count": len(findings)},
        requested_narration_regen=False,
    )
    return EvaluatorGraphResult(
        run=run,
        findings=tuple(findings),
        may_request_narration_regen=len(findings) > 0,
    )
