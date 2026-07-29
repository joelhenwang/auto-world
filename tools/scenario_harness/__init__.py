"""Scenario harness for Stage 0 foundation gate (S0-QA-002)."""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from fictional_world.application.orchestration.phase_runner import DeterministicPhaseRunner
from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.seed import import_caldris_stage0, import_caldris_stage1
from fictional_world.domain.phases.states import PhaseRunState
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.testing import Stage1FakeModelGateway


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


UowFactory = Callable[[], UnitOfWork]


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


async def run_stage1_first_day(
    uow_factory: UowFactory,
    *,
    pack_root: Path,
    spec: ScenarioSpec,
) -> ScenarioResult:
    """Run the fake-model Stage 1 day with a fresh UoW at every step."""

    result = ScenarioResult(scenario_id=spec.scenario_id)
    for step in spec.steps:
        async with uow_factory() as uow:
            if step.action == "seed_caldris_stage1":
                seeded = await import_caldris_stage1(uow, root=pack_root)
                await uow.commit()
                result.world_id = seeded.world_id
                result.task_trace.append(f"seed:{seeded.seed_id}:stage1:{seeded.already_imported}")
                result.event_timeline.append("WORLD_SEEDED")
                continue
            if step.action == "advance_stage1_phase":
                if result.world_id is None:
                    result.failures.append("advance_stage1_phase before seed")
                    break
                gateway = Stage1FakeModelGateway()
                advance = await DeterministicPhaseRunner(
                    uow,
                    model_gateway=gateway,
                    stage1=True,
                ).request_phase_advance(result.world_id)
                await uow.commit()
                result.task_trace.append(
                    f"advance:{advance.absolute_phase_index}:{advance.phase_name}"
                )
                result.event_timeline.extend(
                    f"phase:{advance.absolute_phase_index}:{event_id}"
                    for event_id in advance.event_ids
                )
                result.model_calls.extend(gateway.calls)
                if advance.snapshot_id is not None:
                    result.state_hashes.append(str(advance.snapshot_id))
                continue
            result.failures.append(f"unknown Stage 1 action: {step.action}")
            break

    if result.world_id is not None:
        async with uow_factory() as uow:
            await _evaluate_stage1_invariants(uow, spec, result)
    result.passed = not result.failures
    return result


async def _evaluate_stage1_invariants(
    uow: UnitOfWork,
    spec: ScenarioSpec,
    result: ScenarioResult,
) -> None:
    world_id = result.world_id
    if world_id is None:
        result.failures.append("missing world_id after Stage 1 steps")
        return

    phases = [await uow.phases.find_by_world_and_index(world_id, index) for index in (0, 2, 7)]
    mira_id = seed_uuid("character/mira-talren")
    dain_id = seed_uuid("character/dain-arcen")
    for assertion in spec.assertions:
        invariant = assertion.invariant
        if invariant is None:
            continue
        result.invariant_report.append(invariant)
        if invariant == "three_phase_day":
            if any(phase is None for phase in phases):
                result.failures.append("one or more Stage 1 phases are missing")
            elif any(
                PhaseRunState(phase.state) is not PhaseRunState.COMPLETED
                for phase in phases
                if phase is not None
            ):
                result.failures.append("one or more Stage 1 phases are incomplete")
            continue
        if invariant == "two_intents_one_snapshot":
            for phase in phases:
                if phase is None:
                    continue
                snapshot = await uow.snapshots.get_for_phase(phase.id)
                proposals = await uow.action_proposals.list_for_phase(phase.id)
                if snapshot is None or len(proposals) != 2:
                    result.failures.append(f"phase {phase.id} missing snapshot or two intents")
                    continue
                if {proposal.snapshot_id for proposal in proposals} != {snapshot.id}:
                    result.failures.append(f"phase {phase.id} intents use different snapshots")
            continue
        if invariant == "isolated_perspective_records":
            for phase in phases:
                if phase is None:
                    continue
                scenes = await uow.scenes.list_for_phase(phase.id)
                if len(scenes) != 1:
                    result.failures.append(f"phase {phase.id} does not have one scene")
                    continue
                scope_hashes = {
                    participant.knowledge_scope_hash for participant in scenes[0].participants
                }
                if None in scope_hashes or len(scope_hashes) != 2:
                    result.failures.append(f"phase {phase.id} perspective scopes are not isolated")
            for character_id in (mira_id, dain_id):
                observations = await uow.observations.list_for_observer(character_id)
                memories = await uow.recent_memories.list_for_owner(
                    character_id,
                    world_id=world_id,
                )
                if not observations or not memories:
                    result.failures.append(
                        f"character {character_id} missing observations or recent memories"
                    )
            continue
        if invariant == "no_duplicate_events":
            events = await uow.events.list_for_world(world_id, limit=200)
            keys = [event.idempotency_key for event in events]
            if len(keys) != len(set(keys)):
                result.failures.append("duplicate Stage 1 event idempotency keys")
            continue
        if invariant == "bounded_fake_model_calls":
            if len(result.model_calls) != 10:
                result.failures.append(
                    f"expected 10 fake model calls, got {len(result.model_calls)}"
                )
            continue
        result.failures.append(f"unknown Stage 1 invariant: {invariant}")


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
