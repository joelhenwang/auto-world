"""Daily consolidation and diary pipeline tests (S2-MEM-001)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.application.knowledge.claims import proposition_key_for
from fictional_world.application.memory import consolidate_day, filter_observations_for_owner
from fictional_world.application.memory.daily_consolidation import (
    MEMORY_STATUS_ACTIVE,
    MEMORY_STATUS_COMPACTED,
    SOURCE_KIND_OBSERVATION,
    build_extractive_proposal,
    compact_routine_duplicates,
    contains_unauthorized_secret,
    day_consolidation_idempotency_key,
)
from fictional_world.application.memory.types import (
    CharacterConsolidationInput,
    ConsolidationProposal,
)
from fictional_world.domain.knowledge.persistence import (
    ObservationPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.memory.persistence import RecentMemoryRecord

SECRET_PHRASE = "the Ashfall recorder is hidden under the north beacon"  # noqa: S105
SECRET_KEY = proposition_key_for(SECRET_PHRASE)


def _obs(
    *,
    observer_id: UUID,
    summary: str,
    event_id: UUID | None = None,
    facts: dict[str, object] | None = None,
    confidence: str = "0.80",
) -> ObservationPersistenceRecord:
    eid = event_id or uuid4()
    return ObservationPersistenceRecord(
        id=uuid4(),
        world_event_id=eid,
        observer_id=observer_id,
        observation_type="scene",
        perceived_summary=summary,
        perceived_facts=facts or {"public_sound": "footsteps"},
        omitted_fact_keys=(),
        confidence=Decimal(confidence),
        visibility_reason="direct_witness",
        source_sense_tags=("sight",),
        content_hash=uuid4().hex,
    )


def _memory(
    *,
    world_id: UUID,
    owner: UUID,
    content: str,
    phase: int = 0,
    obs_id: UUID | None = None,
    status: str = MEMORY_STATUS_ACTIVE,
) -> RecentMemoryRecord:
    return RecentMemoryRecord(
        id=uuid4(),
        world_id=world_id,
        owner_character_id=owner,
        memory_type="episodic",
        content=content,
        salience=Decimal("0.40"),
        confidence=Decimal("0.70"),
        emotional_weight=Decimal("0"),
        visibility="private",
        occurred_phase_index=phase,
        created_phase_index=phase,
        decay_score=Decimal("1"),
        status=status,
        content_hash=uuid4().hex,
        source_observation_id=obs_id,
    )


def _secret_row(
    *,
    world_id: UUID,
    owner: UUID,
    holder: UUID,
    secret_key: str = SECRET_KEY,
    access_level: str = "owner",
) -> SecretAccessPersistenceRecord:
    return SecretAccessPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        secret_key=secret_key,
        owner_character_id=owner,
        holder_character_id=holder,
        access_level=access_level,
    )


@pytest.mark.unit
def test_source_completeness_every_cited_id_is_owner_observation() -> None:
    world_id = uuid4()
    mira = uuid4()
    dain = uuid4()
    mira_obs = [
        _obs(observer_id=mira, summary="Mira saw the cup move."),
        _obs(observer_id=mira, summary="Mira heard porcelain scrape."),
    ]
    foreign = _obs(observer_id=dain, summary="Dain saw Mira's private note.")
    result = consolidate_day(
        world_id=world_id,
        day_index=0,
        character_ids=[mira],
        observations=[*mira_obs, foreign],
    )
    assert len(result.characters) == 1
    entry = result.characters[0]
    cited = {s.source_id for s in entry.sources}
    assert cited == {mira_obs[0].id, mira_obs[1].id}
    assert foreign.id not in cited
    assert all(s.source_kind == SOURCE_KIND_OBSERVATION for s in entry.sources)
    assert entry.summary.content_hash == entry.diary.content_hash
    assert "cup move" in entry.summary.content
    assert "porcelain" in entry.diary.content


@pytest.mark.unit
def test_perspective_filter_excludes_other_characters_observations() -> None:
    mira = uuid4()
    dain = uuid4()
    observations = [
        _obs(observer_id=mira, summary="Mira public market chatter."),
        _obs(observer_id=dain, summary="Dain private ledger inspection."),
    ]
    filtered = filter_observations_for_owner(observations, owner_character_id=mira)
    assert len(filtered) == 1
    assert filtered[0].observer_id == mira

    world_id = uuid4()
    result = consolidate_day(
        world_id=world_id,
        day_index=1,
        character_ids=[mira, dain],
        observations=observations,
    )
    by_owner = {c.owner_character_id: c for c in result.characters}
    assert "ledger" not in by_owner[mira].summary.content
    assert "ledger" not in by_owner[mira].diary.content
    assert "market" not in by_owner[dain].summary.content
    assert "ledger" in by_owner[dain].summary.content


@pytest.mark.unit
def test_diary_has_no_absent_secrets() -> None:
    world_id = uuid4()
    mira = uuid4()
    dain = uuid4()
    # Observation text contains Mira's secret; Dain must not retain it in diary.
    leaked = _obs(
        observer_id=dain,
        summary=f"Dain overheard a rumour: {SECRET_PHRASE}",
    )
    mira_obs = _obs(
        observer_id=mira,
        summary=f"Mira reviewed her notes: {SECRET_PHRASE}",
    )
    result = consolidate_day(
        world_id=world_id,
        day_index=2,
        character_ids=[mira, dain],
        observations=[mira_obs, leaked],
        secret_access=[
            _secret_row(world_id=world_id, owner=mira, holder=mira),
        ],
        secret_catalog={SECRET_KEY: SECRET_PHRASE},
    )
    by_owner = {c.owner_character_id: c for c in result.characters}
    assert SECRET_PHRASE in by_owner[mira].diary.content
    assert SECRET_PHRASE not in by_owner[dain].diary.content
    assert SECRET_PHRASE not in by_owner[dain].summary.content
    assert "[redacted]" in by_owner[dain].diary.content
    assert not contains_unauthorized_secret(
        by_owner[dain].diary.content,
        held_secret_keys=frozenset(),
        secret_catalog={SECRET_KEY: SECRET_PHRASE},
    )


@pytest.mark.unit
def test_failed_model_falls_back_to_extractive() -> None:
    world_id = uuid4()
    owner = uuid4()
    obs = _obs(observer_id=owner, summary="Rain on the quay.")

    def boom(_inp: CharacterConsolidationInput) -> ConsolidationProposal:
        raise RuntimeError("model timeout")

    result = consolidate_day(
        world_id=world_id,
        day_index=0,
        character_ids=[owner],
        observations=[obs],
        consolidator=boom,
    )
    entry = result.characters[0]
    assert entry.fell_back_to_extractive is True
    assert entry.used_model is False
    assert "Rain on the quay" in entry.summary.content
    assert entry.sources[0].source_id == obs.id


@pytest.mark.unit
def test_model_unsupported_source_ids_fall_back() -> None:
    world_id = uuid4()
    owner = uuid4()
    obs = _obs(observer_id=owner, summary="A bell rang twice.")
    fake_id = uuid4()

    def invent(_inp: CharacterConsolidationInput) -> ConsolidationProposal:
        return ConsolidationProposal(
            summary_content="Invented omniscient fact.",
            diary_content="I somehow know everything.",
            cited_source_ids=(fake_id,),
        )

    result = consolidate_day(
        world_id=world_id,
        day_index=0,
        character_ids=[owner],
        observations=[obs],
        consolidator=invent,
    )
    entry = result.characters[0]
    assert entry.fell_back_to_extractive is True
    assert fake_id not in {s.source_id for s in entry.sources}
    assert "bell rang" in entry.summary.content


@pytest.mark.unit
def test_successful_fake_consolidator_accepted() -> None:
    world_id = uuid4()
    owner = uuid4()
    obs = _obs(observer_id=owner, summary=" gulls over the harbour.")

    def polish(inp: CharacterConsolidationInput) -> ConsolidationProposal:
        return ConsolidationProposal(
            summary_content="Gulls wheeled over the harbour.",
            diary_content="I watched gulls over the harbour.",
            cited_source_ids=inp.allowed_source_ids,
            structured_extract={"mode": "model"},
        )

    result = consolidate_day(
        world_id=world_id,
        day_index=0,
        character_ids=[owner],
        observations=[obs],
        consolidator=polish,
    )
    entry = result.characters[0]
    assert entry.used_model is True
    assert entry.fell_back_to_extractive is False
    assert entry.summary.content == "Gulls wheeled over the harbour."


@pytest.mark.unit
def test_retry_does_not_duplicate_summaries() -> None:
    world_id = uuid4()
    owner = uuid4()
    obs = _obs(observer_id=owner, summary="The ferry departed on time.")
    first = consolidate_day(
        world_id=world_id,
        day_index=3,
        character_ids=[owner],
        observations=[obs],
    )
    second = consolidate_day(
        world_id=world_id,
        day_index=3,
        character_ids=[owner],
        observations=[obs],
        prior=first,
    )
    assert second.reused_prior is True
    assert second.day_run.id == first.day_run.id
    assert second.day_run.idempotency_key == day_consolidation_idempotency_key(world_id, 3)
    assert second.characters[0].summary.id == first.characters[0].summary.id
    assert second.characters[0].diary.id == first.characters[0].diary.id
    assert second.daily_audit.hard_violation_count == 0


@pytest.mark.unit
def test_routine_observations_compact_without_deleting() -> None:
    world_id = uuid4()
    owner = uuid4()
    phrase = "Ate breakfast at Willow House."
    mems = [
        _memory(world_id=world_id, owner=owner, content=phrase, phase=0),
        _memory(world_id=world_id, owner=owner, content=phrase, phase=1),
        _memory(
            world_id=world_id,
            owner=owner,
            content="  ate breakfast at willow house. ",
            phase=2,
        ),
        _memory(world_id=world_id, owner=owner, content="Spoke with Torren about maps.", phase=3),
    ]
    compacted = compact_routine_duplicates(mems, owner_character_id=owner, world_id=world_id)
    by_id = {m.id: m for m in compacted}
    assert by_id[mems[0].id].status == MEMORY_STATUS_ACTIVE
    assert by_id[mems[1].id].status == MEMORY_STATUS_COMPACTED
    assert by_id[mems[2].id].status == MEMORY_STATUS_COMPACTED
    assert by_id[mems[3].id].status == MEMORY_STATUS_ACTIVE
    # Raw content preserved
    assert by_id[mems[1].id].content == phrase

    obs = _obs(observer_id=owner, summary="Quiet morning.")
    result = consolidate_day(
        world_id=world_id,
        day_index=0,
        character_ids=[owner],
        observations=[obs],
        recent_memories=mems,
    )
    statuses = {m.id: m.status for m in result.compacted_memories}
    assert statuses[mems[1].id] == MEMORY_STATUS_COMPACTED
    assert statuses[mems[0].id] == MEMORY_STATUS_ACTIVE
    assert result.daily_audit.hard_violation_count == 0
    assert result.day_run.status == "completed"


@pytest.mark.unit
def test_extractive_empty_day() -> None:
    proposal = build_extractive_proposal(())
    assert "No observations" in proposal.summary_content
    assert proposal.cited_source_ids == ()
