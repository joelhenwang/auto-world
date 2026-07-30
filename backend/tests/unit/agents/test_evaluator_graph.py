"""Unit tests for Stage 3 evaluator (cannot mutate canon)."""

from __future__ import annotations

from uuid import uuid4

from fictional_world.agents.evaluator import EvaluatorGraphInput, run_evaluator_graph


def test_evaluator_findings_never_mutate_canon() -> None:
    result = run_evaluator_graph(
        EvaluatorGraphInput(
            world_id=uuid4(),
            scope="narration",
            narration_text="x" * 9000,
        )
    )
    assert result.findings
    assert all(f.can_mutate_canon is False for f in result.findings)
    assert result.run.requested_narration_regen is False
