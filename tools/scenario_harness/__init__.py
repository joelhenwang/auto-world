"""Scenario harness for Stage 0 foundation gate (S0-QA-002)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.seed import import_caldris_stage0
from fictional_world.domain.phases.states import PhaseRunState
from fictional_world.domain.seed.ids import seed_uuid


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
    world_id: UUID | None = None
    event_timeline: list[str] = field(default_factory=list)
    task_trace: list[str] = field(default_factory=list)
    model_calls: list[dict[str, Any]] = field(default_factory=list)
    state_hashes: list[str] = field(default_factory=list)
    invariant_report: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    passed: bool = False


def load_scenario(path: Path) -> ScenarioSpec:
    """Load a TOML scenario; Stage 0 supports TOML only."""

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
    """Produce an empty structured result (kept for harness self-tests)."""

    return ScenarioResult(
        scenario_id=spec.scenario_id,
        invariant_report=[a.invariant for a in spec.assertions if a.invariant],
        passed=False,
    )


async def run_stage0_foundation(
    uow: UnitOfWork,
    *,
    pack_root: Path,
    spec: ScenarioSpec,
) -> ScenarioResult:
    """Execute the Caldris Stage 0 foundation scenario against a real UoW."""

    result = ScenarioResult(scenario_id=spec.scenario_id)
    runner = DeterministicPhaseRunner(uow)

    for step in spec.steps:
        action = step.action
        if action == "noop":
            result.task_trace.append("noop")
            continue
        if action == "seed_caldris":
            seeded = await import_caldris_stage0(uow, root=pack_root, fixture_name="stage0")
            await uow.commit()
            result.world_id = seeded.world_id
            result.task_trace.append(f"seed:{seeded.seed_id}:{seeded.already_imported}")
            result.event_timeline.append("WORLD_SEEDED")
            continue
        if action == "advance_phase":
            if result.world_id is None:
                result.failures.append("advance_phase before seed")
                result.passed = False
                return result
            advance = await runner.request_phase_advance(result.world_id)
            await uow.commit()
            result.task_trace.append(f"advance:{advance.absolute_phase_index}:{advance.phase_name}")
            result.event_timeline.extend(
                [f"phase:{advance.absolute_phase_index}:{eid}" for eid in advance.event_ids]
            )
            if advance.snapshot_id is not None:
                result.state_hashes.append(str(advance.snapshot_id))
            continue
        if action == "reconcile":
            if result.world_id is None:
                result.failures.append("reconcile before seed")
                result.passed = False
                return result
            report = await runner.reconcile(result.world_id)
            await uow.commit()
            result.task_trace.append(
                f"reconcile:completed={report.phase_completed}:tasks={report.tasks_created}"
            )
            continue
        result.failures.append(f"unknown action: {action}")
        result.passed = False
        return result

    await _evaluate_invariants(uow, spec, result)
    result.passed = not result.failures
    return result


async def _evaluate_invariants(uow: UnitOfWork, spec: ScenarioSpec, result: ScenarioResult) -> None:
    world_id = result.world_id
    if world_id is None:
        result.failures.append("missing world_id after scenario steps")
        return

    for assertion in spec.assertions:
        invariant = assertion.invariant
        if invariant is None:
            continue
        result.invariant_report.append(invariant)
        if invariant == "no_duplicate_events":
            events = await uow.events.list_for_world(world_id, limit=200)
            keys = [event.idempotency_key for event in events]
            if len(keys) != len(set(keys)):
                result.failures.append("duplicate event idempotency keys")
            continue
        if invariant == "phase_completed":
            phase = await uow.phases.find_by_world_and_index(world_id, 0)
            if phase is None or PhaseRunState(phase.state) is not PhaseRunState.COMPLETED:
                result.failures.append("phase 0 not completed")
            continue
        if invariant == "snapshot_sealed":
            phase = await uow.phases.find_by_world_and_index(world_id, 0)
            if phase is None:
                result.failures.append("phase 0 missing for snapshot check")
                continue
            snap = await uow.snapshots.get_for_phase(phase.id)
            if snap is None:
                result.failures.append("phase 0 snapshot missing")
            continue
        if invariant == "mira_memory_written":
            memories = await uow.recent_memories.list_for_owner(
                seed_uuid("character/mira-talren"),
                world_id=world_id,
                limit=20,
            )
            if not memories:
                result.failures.append("mira recent memory missing")
            continue
        if invariant == "world_tick_present":
            events = await uow.events.list_for_world(world_id, limit=200)
            if not any(event.event_type == "WORLD_TICK" for event in events):
                result.failures.append("WORLD_TICK missing")
            continue
        result.failures.append(f"unknown invariant: {invariant}")
