"""Daily consolidation and diary pipeline (S2-MEM-001).

Pure application transforms: callers persist returned records via UoW.
Observations remain immutable; routine recent-memory duplicates are marked
``compacted`` without deletion. Optional model consolidators may improve prose
but cannot introduce unsupported source IDs.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fictional_world.application.knowledge.secrets import SecretAccessPolicy
from fictional_world.application.memory.types import (
    CharacterConsolidationInput,
    CharacterDayConsolidation,
    ConsolidationProposal,
    ConsolidatorCallable,
    DailyConsolidationResult,
)
from fictional_world.domain.continuity.persistence import (
    DailyAuditPersistenceRecord,
    DayRunPersistenceRecord,
    DiaryEntryPersistenceRecord,
    SummaryPersistenceRecord,
    SummarySourcePersistenceRecord,
)
from fictional_world.domain.knowledge.persistence import (
    ObservationPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.memory.persistence import RecentMemoryRecord
from fictional_world.domain.time.calendar import PHASE_ORDER

SUMMARY_TYPE_DAILY = "daily"
SOURCE_KIND_OBSERVATION = "observation"
MEMORY_STATUS_ACTIVE = "active"
MEMORY_STATUS_COMPACTED = "compacted"
DAY_RUN_STATUS_COMPLETED = "completed"
PERSPECTIVE_CHARACTER = "character"
DEFAULT_VERSION_NUMBER = 1

_PHASES_PER_DAY = len(PHASE_ORDER)


def day_consolidation_idempotency_key(world_id: UUID, day_index: int) -> str:
    """Stable idempotency key for one world's end-of-day consolidation."""

    return f"day-consolidation:{world_id}:{day_index}"


def day_phase_bounds(day_index: int) -> tuple[int, int]:
    """Inclusive absolute phase range for a calendar day index."""

    start = day_index * _PHASES_PER_DAY
    return start, start + _PHASES_PER_DAY - 1


def _content_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def _normalize_routine_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().casefold())


def filter_observations_for_owner(
    observations: Sequence[ObservationPersistenceRecord],
    *,
    owner_character_id: UUID,
) -> tuple[ObservationPersistenceRecord, ...]:
    """Perspective filter: only the owner's own observations."""

    return tuple(obs for obs in observations if obs.observer_id == owner_character_id)


def scrub_unauthorized_secrets(
    text: str,
    *,
    held_secret_keys: frozenset[str],
    secret_catalog: Mapping[str, str],
) -> str:
    """Remove phrases for secrets the owner does not hold."""

    scrubbed = text
    for secret_key, phrase in secret_catalog.items():
        if secret_key in held_secret_keys:
            continue
        if not phrase:
            continue
        scrubbed = re.sub(re.escape(phrase), "[redacted]", scrubbed, flags=re.IGNORECASE)
    return scrubbed


def contains_unauthorized_secret(
    text: str,
    *,
    held_secret_keys: frozenset[str],
    secret_catalog: Mapping[str, str],
) -> bool:
    lowered = text.casefold()
    for secret_key, phrase in secret_catalog.items():
        if secret_key in held_secret_keys:
            continue
        if phrase and phrase.casefold() in lowered:
            return True
    return False


def update_observation_salience(
    observations: Sequence[ObservationPersistenceRecord],
) -> tuple[ObservationPersistenceRecord, ...]:
    """Deterministic salience nudge from confidence (observations stay immutable).

    Returns copies with confidence used as a salience proxy in ``perceived_facts``.
    Callers that need numeric salience on recent memories use
    :func:`apply_salience_to_memories`.
    """

    updated: list[ObservationPersistenceRecord] = []
    for obs in observations:
        facts = dict(obs.perceived_facts)
        # Preserve raw confidence; expose derived salience for consolidators.
        salience = min(Decimal("1"), max(Decimal("0"), obs.confidence))
        facts["derived_salience"] = str(salience)
        updated.append(obs.model_copy(update={"perceived_facts": facts}))
    return tuple(updated)


def apply_salience_to_memories(
    memories: Sequence[RecentMemoryRecord],
    *,
    observation_ids: frozenset[UUID],
) -> tuple[RecentMemoryRecord, ...]:
    """Bump salience for active memories sourced from today's observations."""

    out: list[RecentMemoryRecord] = []
    for mem in memories:
        if (
            mem.status == MEMORY_STATUS_ACTIVE
            and mem.source_observation_id is not None
            and mem.source_observation_id in observation_ids
        ):
            bumped = min(Decimal("1"), mem.salience + Decimal("0.05"))
            out.append(mem.model_copy(update={"salience": bumped}))
        else:
            out.append(mem)
    return tuple(out)


def compact_routine_duplicates(
    memories: Sequence[RecentMemoryRecord],
    *,
    owner_character_id: UUID,
    world_id: UUID,
) -> tuple[RecentMemoryRecord, ...]:
    """Mark near-identical active routine memories as compacted; keep raw rows.

    Keeps the earliest (by occurred_phase_index, then id) as active; later
    duplicates with the same normalized content become ``compacted``.
    """

    owned = [
        m
        for m in memories
        if m.owner_character_id == owner_character_id
        and m.world_id == world_id
        and m.status == MEMORY_STATUS_ACTIVE
    ]
    owned.sort(key=lambda m: (m.occurred_phase_index, str(m.id)))
    seen: dict[str, UUID] = {}
    compacted_ids: set[UUID] = set()
    for mem in owned:
        key = _normalize_routine_text(mem.content)
        if not key:
            continue
        if key in seen:
            compacted_ids.add(mem.id)
        else:
            seen[key] = mem.id

    result: list[RecentMemoryRecord] = []
    for mem in memories:
        if mem.id in compacted_ids:
            result.append(mem.model_copy(update={"status": MEMORY_STATUS_COMPACTED}))
        else:
            result.append(mem)
    return tuple(result)


def build_extractive_proposal(
    observations: Sequence[ObservationPersistenceRecord],
) -> ConsolidationProposal:
    """Deterministic extractive summary/diary — always available as fallback."""

    if not observations:
        content = "No observations recorded for this day."
        return ConsolidationProposal(
            summary_content=content,
            diary_content=content,
            cited_source_ids=(),
            structured_extract={"mode": "extractive", "observation_count": 0},
        )

    lines = [obs.perceived_summary.strip() for obs in observations if obs.perceived_summary.strip()]
    summary = " ".join(lines) if lines else "No observations recorded for this day."
    diary_lines = [f"I noticed: {line}" for line in lines]
    diary = " ".join(diary_lines) if diary_lines else summary
    fact_keys: list[str] = []
    for obs in observations:
        fact_keys.extend(sorted(obs.perceived_facts.keys()))
    return ConsolidationProposal(
        summary_content=summary,
        diary_content=diary,
        cited_source_ids=tuple(obs.id for obs in observations),
        structured_extract={
            "mode": "extractive",
            "observation_count": len(observations),
            "fact_keys": sorted(set(fact_keys)),
            "belief_evidence_hooks": [str(obs.id) for obs in observations],
        },
    )


def validate_consolidator_proposal(
    proposal: ConsolidationProposal,
    *,
    allowed_source_ids: frozenset[UUID],
    held_secret_keys: frozenset[str],
    secret_catalog: Mapping[str, str],
) -> bool:
    """True when cited sources ⊆ allowed and no unauthorized secrets appear."""

    cited = frozenset(proposal.cited_source_ids)
    if not cited.issubset(allowed_source_ids):
        return False
    if contains_unauthorized_secret(
        proposal.summary_content,
        held_secret_keys=held_secret_keys,
        secret_catalog=secret_catalog,
    ):
        return False
    return not contains_unauthorized_secret(
        proposal.diary_content,
        held_secret_keys=held_secret_keys,
        secret_catalog=secret_catalog,
    )


def _resolve_proposal(
    *,
    filtered: Sequence[ObservationPersistenceRecord],
    owner_character_id: UUID,
    world_id: UUID,
    day_index: int,
    held_secret_keys: frozenset[str],
    secret_catalog: Mapping[str, str],
    consolidator: ConsolidatorCallable | None,
) -> tuple[ConsolidationProposal, bool, bool]:
    """Return (proposal, used_model, fell_back)."""

    extractive = build_extractive_proposal(filtered)
    allowed = frozenset(obs.id for obs in filtered)
    if consolidator is None:
        return extractive, False, False

    inp = CharacterConsolidationInput(
        world_id=world_id,
        day_index=day_index,
        owner_character_id=owner_character_id,
        observations=tuple(filtered),
        allowed_source_ids=tuple(allowed),
        held_secret_keys=tuple(sorted(held_secret_keys)),
    )
    try:
        proposal = consolidator(inp)
    except Exception:
        # Any consolidator failure (timeout, schema, etc.) uses extractive fallback.
        return extractive, False, True

    if validate_consolidator_proposal(
        proposal,
        allowed_source_ids=allowed,
        held_secret_keys=held_secret_keys,
        secret_catalog=secret_catalog,
    ):
        return proposal, True, False
    return extractive, False, True


def _character_content_fingerprint(
    *,
    owner_character_id: UUID,
    day_index: int,
    version_number: int,
    summary_content: str,
    diary_content: str,
    source_ids: Sequence[UUID],
) -> str:
    return _content_hash(
        {
            "owner": str(owner_character_id),
            "day": day_index,
            "version": version_number,
            "summary": summary_content,
            "diary": diary_content,
            "sources": [str(s) for s in source_ids],
        }
    )


def _prior_character(
    prior: DailyConsolidationResult | None,
    owner_character_id: UUID,
) -> CharacterDayConsolidation | None:
    if prior is None:
        return None
    for entry in prior.characters:
        if entry.owner_character_id == owner_character_id:
            return entry
    return None


def consolidate_day(
    *,
    world_id: UUID,
    day_index: int,
    character_ids: Sequence[UUID],
    observations: Sequence[ObservationPersistenceRecord],
    recent_memories: Sequence[RecentMemoryRecord] = (),
    secret_access: Sequence[SecretAccessPersistenceRecord] = (),
    secret_catalog: Mapping[str, str] | None = None,
    consolidator: ConsolidatorCallable | None = None,
    prior: DailyConsolidationResult | None = None,
    version_number: int = DEFAULT_VERSION_NUMBER,
    now: datetime | None = None,
) -> DailyConsolidationResult:
    """Consolidate one day's observations into perspective summaries and diaries.

    Idempotency: when ``prior`` shares the same ``day_run.idempotency_key`` and
    each character's (world, owner, day, content_hash/version) matches the new
    computation, the prior records are reused without inventing new IDs.
    """

    catalog = dict(secret_catalog or {})
    policy = SecretAccessPolicy(secret_access)
    idem_key = day_consolidation_idempotency_key(world_id, day_index)
    start_phase, end_phase = day_phase_bounds(day_index)
    stamp = now or datetime.now(UTC)

    prior_reusable = (
        prior is not None
        and prior.world_id == world_id
        and prior.day_index == day_index
        and prior.day_run.idempotency_key == idem_key
        and prior.day_run.status == DAY_RUN_STATUS_COMPLETED
        and _prior_matches(
            prior=prior,
            world_id=world_id,
            day_index=day_index,
            character_ids=character_ids,
            observations=observations,
            secret_access=secret_access,
            secret_catalog=catalog,
            consolidator=consolidator,
            version_number=version_number,
        )
    )
    if prior_reusable and prior is not None:
        return prior.model_copy(update={"reused_prior": True})

    day_run_id = uuid4()
    if prior is not None and prior.day_run.idempotency_key == idem_key:
        day_run_id = prior.day_run.id

    character_results: list[CharacterDayConsolidation] = []
    all_compacted: list[RecentMemoryRecord] = list(recent_memories)

    for character_id in character_ids:
        held = policy.held_secret_keys(character_id, world_id=world_id)
        owned = filter_observations_for_owner(observations, owner_character_id=character_id)
        # Scrub unauthorized secret phrases from observation text before summary.
        scrubbed: list[ObservationPersistenceRecord] = []
        for obs in owned:
            summary = scrub_unauthorized_secrets(
                obs.perceived_summary,
                held_secret_keys=held,
                secret_catalog=catalog,
            )
            facts = {
                k: (
                    scrub_unauthorized_secrets(
                        str(v), held_secret_keys=held, secret_catalog=catalog
                    )
                    if isinstance(v, str)
                    else v
                )
                for k, v in obs.perceived_facts.items()
            }
            scrubbed.append(
                obs.model_copy(update={"perceived_summary": summary, "perceived_facts": facts})
            )
        with_salience = update_observation_salience(scrubbed)

        proposal, used_model, fell_back = _resolve_proposal(
            filtered=with_salience,
            owner_character_id=character_id,
            world_id=world_id,
            day_index=day_index,
            held_secret_keys=held,
            secret_catalog=catalog,
            consolidator=consolidator,
        )

        # Final scrub (belt-and-suspenders for extractive path).
        summary_text = scrub_unauthorized_secrets(
            proposal.summary_content, held_secret_keys=held, secret_catalog=catalog
        )
        diary_text = scrub_unauthorized_secrets(
            proposal.diary_content, held_secret_keys=held, secret_catalog=catalog
        )
        allowed_ids = {o.id for o in with_salience}
        cited = tuple(sid for sid in proposal.cited_source_ids if sid in allowed_ids)
        if not cited and with_salience:
            cited = tuple(o.id for o in with_salience)

        fingerprint = _character_content_fingerprint(
            owner_character_id=character_id,
            day_index=day_index,
            version_number=version_number,
            summary_content=summary_text,
            diary_content=diary_text,
            source_ids=cited,
        )

        prior_char = _prior_character(prior, character_id)
        if (
            prior_char is not None
            and prior_char.summary.content_hash == fingerprint
            and prior_char.summary.version_number == version_number
            and prior_char.diary.day_index == day_index
        ):
            character_results.append(prior_char)
        else:
            summary_id = uuid4()
            summary = SummaryPersistenceRecord(
                id=summary_id,
                world_id=world_id,
                owner_character_id=character_id,
                summary_type=SUMMARY_TYPE_DAILY,
                start_phase_index=start_phase,
                end_phase_index=end_phase,
                content=summary_text,
                structured_extract=dict(proposal.structured_extract),
                perspective=PERSPECTIVE_CHARACTER,
                version_number=version_number,
                content_hash=fingerprint,
            )
            sources = tuple(
                SummarySourcePersistenceRecord(
                    summary_id=summary_id,
                    ordinal=i,
                    source_kind=SOURCE_KIND_OBSERVATION,
                    source_id=source_id,
                )
                for i, source_id in enumerate(cited)
            )
            diary = DiaryEntryPersistenceRecord(
                id=uuid4(),
                world_id=world_id,
                owner_character_id=character_id,
                day_index=day_index,
                content=diary_text,
                summary_id=summary_id,
                content_hash=fingerprint,
                version=0,
            )
            character_results.append(
                CharacterDayConsolidation(
                    owner_character_id=character_id,
                    summary=summary,
                    sources=sources,
                    diary=diary,
                    used_model=used_model,
                    fell_back_to_extractive=fell_back,
                )
            )

        obs_ids = frozenset(o.id for o in with_salience)
        all_compacted = list(
            apply_salience_to_memories(tuple(all_compacted), observation_ids=obs_ids)
        )
        all_compacted = list(
            compact_routine_duplicates(
                tuple(all_compacted),
                owner_character_id=character_id,
                world_id=world_id,
            )
        )

    day_run = DayRunPersistenceRecord(
        id=day_run_id,
        world_id=world_id,
        day_index=day_index,
        status=DAY_RUN_STATUS_COMPLETED,
        started_at=stamp,
        completed_at=stamp,
        idempotency_key=idem_key,
        version=0,
    )
    audit = DailyAuditPersistenceRecord(
        id=uuid4(),
        day_run_id=day_run_id,
        world_id=world_id,
        hard_violation_count=0,
        soft_violation_count=0,
        findings=[],
        created_at=stamp,
    )
    if prior is not None and prior.day_run.idempotency_key == idem_key:
        audit = prior.daily_audit.model_copy(update={"day_run_id": day_run_id})

    # Return full memory list with status updates (active + compacted).
    return DailyConsolidationResult(
        world_id=world_id,
        day_index=day_index,
        day_run=day_run,
        daily_audit=audit,
        characters=tuple(character_results),
        compacted_memories=tuple(all_compacted),
        reused_prior=False,
    )


def _prior_matches(
    *,
    prior: DailyConsolidationResult,
    world_id: UUID,
    day_index: int,
    character_ids: Sequence[UUID],
    observations: Sequence[ObservationPersistenceRecord],
    secret_access: Sequence[SecretAccessPersistenceRecord],
    secret_catalog: Mapping[str, str],
    consolidator: ConsolidatorCallable | None,
    version_number: int,
) -> bool:
    """Whether recomputing would yield the same content hashes as ``prior``."""

    policy = SecretAccessPolicy(secret_access)
    if {c.owner_character_id for c in prior.characters} != set(character_ids):
        return False
    for character_id in character_ids:
        held = policy.held_secret_keys(character_id, world_id=world_id)
        owned = filter_observations_for_owner(observations, owner_character_id=character_id)
        scrubbed: list[ObservationPersistenceRecord] = []
        for obs in owned:
            summary = scrub_unauthorized_secrets(
                obs.perceived_summary, held_secret_keys=held, secret_catalog=secret_catalog
            )
            scrubbed.append(obs.model_copy(update={"perceived_summary": summary}))
        proposal, _, _ = _resolve_proposal(
            filtered=scrubbed,
            owner_character_id=character_id,
            world_id=world_id,
            day_index=day_index,
            held_secret_keys=held,
            secret_catalog=secret_catalog,
            consolidator=consolidator,
        )
        summary_text = scrub_unauthorized_secrets(
            proposal.summary_content, held_secret_keys=held, secret_catalog=secret_catalog
        )
        diary_text = scrub_unauthorized_secrets(
            proposal.diary_content, held_secret_keys=held, secret_catalog=secret_catalog
        )
        allowed_ids = {o.id for o in scrubbed}
        cited = tuple(sid for sid in proposal.cited_source_ids if sid in allowed_ids)
        if not cited and scrubbed:
            cited = tuple(o.id for o in scrubbed)
        fingerprint = _character_content_fingerprint(
            owner_character_id=character_id,
            day_index=day_index,
            version_number=version_number,
            summary_content=summary_text,
            diary_content=diary_text,
            source_ids=cited,
        )
        prior_char = _prior_character(prior, character_id)
        if prior_char is None or prior_char.summary.content_hash != fingerprint:
            return False
    return True


__all__ = [
    "DAY_RUN_STATUS_COMPLETED",
    "MEMORY_STATUS_ACTIVE",
    "MEMORY_STATUS_COMPACTED",
    "SOURCE_KIND_OBSERVATION",
    "SUMMARY_TYPE_DAILY",
    "apply_salience_to_memories",
    "build_extractive_proposal",
    "compact_routine_duplicates",
    "consolidate_day",
    "contains_unauthorized_secret",
    "day_consolidation_idempotency_key",
    "day_phase_bounds",
    "filter_observations_for_owner",
    "scrub_unauthorized_secrets",
    "update_observation_salience",
    "validate_consolidator_proposal",
]
