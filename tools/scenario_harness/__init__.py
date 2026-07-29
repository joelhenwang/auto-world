"""Scenario harness skeleton (expanded by later Stage 0/1 scenario tasks)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ScenarioStep:
    action: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScenarioAssertion:
    path: str | None = None
    equals: Any = None
    invariant: str | None = None


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    scenario_id: str
    seed: str
    model_script: str | None = None
    random_script: str | None = None
    steps: tuple[ScenarioStep, ...] = ()
    assertions: tuple[ScenarioAssertion, ...] = ()


@dataclass
class ScenarioResult:
    scenario_id: str
    event_timeline: list[str] = field(default_factory=list)
    task_trace: list[str] = field(default_factory=list)
    model_calls: list[dict[str, Any]] = field(default_factory=list)
    state_hashes: list[str] = field(default_factory=list)
    invariant_report: list[str] = field(default_factory=list)
    passed: bool = False


def load_scenario(path: Path) -> ScenarioSpec:
    """Load a TOML/YAML-shaped scenario; Stage 0 supports TOML only."""

    if path.suffix not in {".toml", ".tml"}:
        msg = f"Stage 0 scenario harness supports TOML only: {path}"
        raise ValueError(msg)
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    steps = tuple(
        ScenarioStep(action=str(item["action"]), params=dict(item.get("params", {})))
        for item in raw.get("steps", [])
    )
    assertions = tuple(
        ScenarioAssertion(
            path=item.get("path"),
            equals=item.get("equals"),
            invariant=item.get("invariant"),
        )
        for item in raw.get("assertions", [])
    )
    return ScenarioSpec(
        scenario_id=str(raw["scenario_id"]),
        seed=str(raw.get("seed", "")),
        model_script=raw.get("model_script"),
        random_script=raw.get("random_script"),
        steps=steps,
        assertions=assertions,
    )


def run_scenario_skeleton(spec: ScenarioSpec) -> ScenarioResult:
    """Produce an empty structured result; execution arrives with S0-ORCH-002/S0-QA-002."""

    return ScenarioResult(
        scenario_id=spec.scenario_id,
        invariant_report=[a.invariant for a in spec.assertions if a.invariant],
        passed=False,
    )
