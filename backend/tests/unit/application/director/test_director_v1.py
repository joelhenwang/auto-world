"""Unit tests for Narrative Director v1 (S2-WORLD-001)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.application.director.config import DirectorTriggerConfig
from fictional_world.application.director.fallback import safe_no_event_fallback
from fictional_world.application.director.persistence import (
    record_narrative_metric,
    upsert_hook,
)
from fictional_world.application.director.triggers import evaluate_director_trigger
from fictional_world.application.director.types import (
    DirectorProposal,
    DirectorWorldSnapshot,
    ProposedHookStub,
    SecretHandlingPlan,
)
from fictional_world.application.director.validate import validate_director_proposal
from fictional_world.domain.continuity.persistence import (
    HookPersistenceRecord,
    NarrativeMetricPersistenceRecord,
)


@pytest.fixture
def world_id() -> UUID:
    return uuid4()


@pytest.fixture
def phase_id() -> UUID:
    return uuid4()


def _healthy_snapshot(world_id: UUID) -> DirectorWorldSnapshot:
    return DirectorWorldSnapshot(
        world_id=world_id,
        current_phase_index=20,
        phases_since_meaningful_choice=1,
        recent_location_keys=("inn", "market", "bridge", "archive", "orchard"),
        recent_participant_keys=("a|b", "a|c", "b|d", "a|b|c", "c|d"),
        recent_action_families=("talk", "travel", "work", "observe", "rest"),
        goal_progress_delta=0.85,
        unresolved_hook_count=0,
        emotional_intensity_history=(0.2, 0.45, 0.7, 0.55),
        last_disruptive_event_phase=None,
        protected_secret_keys=("mira.father.true_name",),
    )


def _stagnation_snapshot(world_id: UUID) -> DirectorWorldSnapshot:
    return DirectorWorldSnapshot(
        world_id=world_id,
        current_phase_index=40,
        phases_since_meaningful_choice=12,
        recent_location_keys=("inn", "inn", "inn", "inn", "inn"),
        recent_participant_keys=("a|b", "a|b", "a|b", "a|b", "a|b"),
        recent_action_families=("talk", "talk", "talk", "talk", "talk"),
        goal_progress_delta=0.0,
        unresolved_hook_count=3,
        emotional_intensity_history=(0.4, 0.41, 0.39, 0.4),
        last_disruptive_event_phase=None,
        protected_secret_keys=("mira.father.true_name",),
    )


def _base_proposal(
    world_id: UUID,
    phase_id: UUID,
    *,
    guarantees_romance: bool = False,
    reveals_secret: bool = False,
    disclosure_path: str | None = None,
    is_disruptive: bool = False,
    public_payload: dict[str, str | int | float | bool | None] | None = None,
    event_facts: tuple[str, ...] = ("A courier posts a notice at the inn.",),
    trope_tags: tuple[str, ...] = (),
) -> DirectorProposal:
    return DirectorProposal(
        proposal_id=uuid4(),
        phase_id=phase_id,
        world_id=world_id,
        trigger_type="STAGNATION_RISK",
        proposal_kind="SOCIAL_OPPORTUNITY",
        title="Courier notice",
        intent="Offer a low-stakes information opportunity at the inn.",
        causal_basis_event_ids=(uuid4(),),
        proposed_hooks=(
            ProposedHookStub(
                hook_key="courier_notice_day3",
                title="Courier notice",
                premise="A travel notice invites optional involvement.",
                status="dormant",
            ),
        ),
        proposed_event_facts=event_facts,
        proposed_effect_types=("observe",),
        secret_handling=SecretHandlingPlan(
            reveals_secret=reveals_secret,
            disclosure_path=disclosure_path,
        ),
        is_disruptive=is_disruptive,
        guarantees_romance=guarantees_romance,
        public_payload=dict(public_payload or {}),
        trope_tags=trope_tags,
    )


def test_healthy_progression_does_not_call_director(world_id: UUID) -> None:
    decision = evaluate_director_trigger(_healthy_snapshot(world_id))
    assert decision.should_call is False
    assert decision.metrics.stagnation_score < DirectorTriggerConfig().stagnation_score_threshold
    assert decision.metrics.phases_since_meaningful_choice == 1
    assert decision.metrics.goal_progress_stagnation < 1.0
    assert decision.metrics.recent_disruptive_event_cooldown == 0


def test_stagnation_fixture_triggers_director_call(world_id: UUID) -> None:
    decision = evaluate_director_trigger(_stagnation_snapshot(world_id))
    assert decision.should_call is True
    assert "stagnation_risk" in decision.reasons
    assert "phases_since_meaningful_choice" in decision.reasons
    assert "goal_progress_stagnation" in decision.reasons
    assert "repeated_location_pattern" in decision.reasons
    assert "repeated_participant_pattern" in decision.reasons
    assert "repeated_action_pattern" in decision.reasons
    assert decision.metrics.unresolved_hook_count == 3
    assert decision.metrics.stagnation_score >= DirectorTriggerConfig().stagnation_score_threshold


def test_proposal_rejects_secret_without_disclosure_path(world_id: UUID, phase_id: UUID) -> None:
    proposal = _base_proposal(
        world_id,
        phase_id,
        reveals_secret=True,
        disclosure_path=None,
    )
    result = validate_director_proposal(proposal, _stagnation_snapshot(world_id))
    assert result.ok is False
    assert any(i.code == "secret_without_disclosure_path" for i in result.issues)


def test_proposal_accepts_secret_with_disclosure_path(world_id: UUID, phase_id: UUID) -> None:
    proposal = _base_proposal(
        world_id,
        phase_id,
        reveals_secret=True,
        disclosure_path="witnessed_event",
    )
    result = validate_director_proposal(proposal, _stagnation_snapshot(world_id))
    assert result.ok is True


def test_proposal_rejects_secret_key_in_public_payload(world_id: UUID, phase_id: UUID) -> None:
    proposal = _base_proposal(
        world_id,
        phase_id,
        public_payload={"secret_key": "mira.father.true_name"},
    )
    result = validate_director_proposal(proposal, _stagnation_snapshot(world_id))
    assert result.ok is False
    assert any(i.code == "secret_key_in_public_payload" for i in result.issues)


def test_proposal_rejects_protected_secret_embedded_in_facts(
    world_id: UUID, phase_id: UUID
) -> None:
    proposal = _base_proposal(
        world_id,
        phase_id,
        event_facts=("Everyone learns mira.father.true_name tonight.",),
    )
    result = validate_director_proposal(proposal, _stagnation_snapshot(world_id))
    assert result.ok is False
    assert any(i.code == "secret_key_in_public_payload" for i in result.issues)


def test_proposal_rejects_mandatory_romance(world_id: UUID, phase_id: UUID) -> None:
    flagged = _base_proposal(world_id, phase_id, guarantees_romance=True)
    result = validate_director_proposal(flagged, _stagnation_snapshot(world_id))
    assert result.ok is False
    assert any(i.code == "mandatory_romance" for i in result.issues)

    textual = _base_proposal(world_id, phase_id)
    textual = textual.model_copy(
        update={"intent": "Force a mandatory romance between the focus pair."}
    )
    result2 = validate_director_proposal(textual, _stagnation_snapshot(world_id))
    assert result2.ok is False
    assert any(i.code == "mandatory_romance" for i in result2.issues)


def test_cooldown_blocks_disruptive_proposal(world_id: UUID, phase_id: UUID) -> None:
    cfg = DirectorTriggerConfig(disruptive_cooldown_phases=10)
    snapshot = DirectorWorldSnapshot(
        world_id=world_id,
        current_phase_index=25,
        phases_since_meaningful_choice=12,
        recent_location_keys=("inn", "inn", "inn"),
        recent_participant_keys=("a|b", "a|b", "a|b"),
        recent_action_families=("talk", "talk", "talk"),
        goal_progress_delta=0.0,
        unresolved_hook_count=2,
        emotional_intensity_history=(0.4, 0.4, 0.4),
        last_disruptive_event_phase=20,
    )
    decision = evaluate_director_trigger(snapshot, config=cfg)
    assert decision.metrics.recent_disruptive_event_cooldown == 5
    assert "recent_disruptive_event_cooldown" in decision.reasons

    proposal = _base_proposal(world_id, phase_id, is_disruptive=True)
    result = validate_director_proposal(proposal, snapshot, config=cfg)
    assert result.ok is False
    assert any(i.code == "disruptive_cooldown_active" for i in result.issues)

    soft = _base_proposal(world_id, phase_id, is_disruptive=False)
    soft_result = validate_director_proposal(soft, snapshot, config=cfg)
    assert soft_result.ok is True


def test_safe_no_event_fallback_on_validation_failure(world_id: UUID, phase_id: UUID) -> None:
    proposal = _base_proposal(world_id, phase_id, guarantees_romance=True)
    validation = validate_director_proposal(proposal, _stagnation_snapshot(world_id))
    assert validation.ok is False
    fallback = safe_no_event_fallback(validation=validation, proposal=proposal)
    assert fallback.proposal_id == proposal.proposal_id
    assert "mandatory_romance" in fallback.validation_issue_codes
    assert "rejected" in fallback.reason


@dataclass
class _FakeHookRepo:
    by_key: dict[tuple[UUID, str], HookPersistenceRecord] = field(default_factory=dict)

    async def get_by_key(self, world_id: UUID, hook_key: str) -> HookPersistenceRecord | None:
        return self.by_key.get((world_id, hook_key))

    async def insert(self, hook: HookPersistenceRecord) -> HookPersistenceRecord:
        self.by_key[(hook.world_id, hook.hook_key)] = hook
        return hook

    async def update(self, hook: HookPersistenceRecord) -> HookPersistenceRecord:
        self.by_key[(hook.world_id, hook.hook_key)] = hook
        return hook


@dataclass
class _FakeMetricRepo:
    rows: list[NarrativeMetricPersistenceRecord] = field(default_factory=list)

    async def insert(
        self, metric: NarrativeMetricPersistenceRecord
    ) -> NarrativeMetricPersistenceRecord:
        self.rows.append(metric)
        return metric


@dataclass
class _FakeUow:
    hooks: _FakeHookRepo = field(default_factory=_FakeHookRepo)
    narrative_metrics: _FakeMetricRepo = field(default_factory=_FakeMetricRepo)


@pytest.mark.asyncio
async def test_upsert_hook_and_record_narrative_metric(world_id: UUID) -> None:
    uow = _FakeUow()
    hook = HookPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        hook_key="courier_notice_day3",
        title="Courier notice",
        status="dormant",
        premise="A travel notice invites optional involvement.",
    )
    inserted = await upsert_hook(uow, hook)
    assert inserted.version == 0

    updated_input = hook.model_copy(update={"status": "active", "title": "Courier notice (active)"})
    updated = await upsert_hook(uow, updated_input)
    assert updated.id == inserted.id
    assert updated.version == 1
    assert updated.status == "active"

    metric = await record_narrative_metric(
        uow,
        world_id=world_id,
        metric_key="stagnation_score",
        metric_value=0.72,
        window_start_phase=30,
        window_end_phase=40,
        payload={"reasons": "stagnation_risk"},
    )
    assert metric.metric_key == "stagnation_score"
    assert metric.metric_value == Decimal("0.72")
    assert len(uow.narrative_metrics.rows) == 1


def test_valid_proposal_remains_proposal_only(world_id: UUID, phase_id: UUID) -> None:
    """Document commit-through-resolver: validation ok ≠ canon mutation."""
    proposal = _base_proposal(world_id, phase_id)
    result = validate_director_proposal(proposal, _stagnation_snapshot(world_id))
    assert result.ok is True
    assert proposal.proposed_effect_types == ("observe",)
