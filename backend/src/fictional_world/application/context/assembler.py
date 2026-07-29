"""Assemble sealed perspective-safe character context packages (S1-KNOW-001 / S2-KNOW-001)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fictional_world.application.context.budget import (
    estimate_content_tokens,
    trim_sections,
)
from fictional_world.application.context.fixtures import (
    DIRECTOR_ONLY_FACTS,
    STAGE1_LOCAL_MAP,
    goals_for,
    private_beliefs_for,
    relationship_edges_for,
    seed_key_for_character_id,
)
from fictional_world.application.context.hashing import (
    compute_package_hash,
    content_hash,
    section_content_hash,
)
from fictional_world.application.context.sanitize import sanitize_memory_text
from fictional_world.application.context.types import (
    STAGE1_ACTION_FAMILIES,
    ContextSection,
    ContextSectionId,
    ContextTaskType,
    SealedContextPackage,
)
from fictional_world.application.knowledge.types import PerspectiveKnowledge
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.errors import SecretAccessDenied
from fictional_world.domain.seed.records import CharacterCardVersionRecord


def _beliefs_from_perspective(knowledge: PerspectiveKnowledge) -> list[dict[str, Any]]:
    """Map lookup output into the private_beliefs section shape."""

    beliefs: list[dict[str, Any]] = [dict(b) for b in knowledge.beliefs]
    # Secret keys held by the observer may be listed without payloads for others.
    if knowledge.secret_keys:
        beliefs.append(
            {
                "held_secret_keys": list(knowledge.secret_keys),
                "access": "granted",
            }
        )
    return beliefs


def _assert_no_director_leak(text: str) -> None:
    for secret in DIRECTOR_ONLY_FACTS:
        if secret in text:
            raise SecretAccessDenied("director-only fact leaked into context")


def _make_section(
    section_id: ContextSectionId,
    content: dict[str, Any] | str | list[Any],
    *,
    source_record_ids: tuple[str, ...] = (),
    trusted: bool = True,
) -> ContextSection:
    draft = ContextSection(
        section_id=section_id,
        content=content,
        source_record_ids=source_record_ids,
        token_estimate=estimate_content_tokens(content),
        trusted=trusted,
        content_hash="pending",
    )
    return ContextSection(
        section_id=draft.section_id,
        content=draft.content,
        source_record_ids=draft.source_record_ids,
        token_estimate=draft.token_estimate,
        trusted=draft.trusted,
        content_hash=section_content_hash(draft),
    )


def assemble_character_context(
    *,
    observer_id: UUID,
    phase_snapshot_id: UUID,
    task_type: ContextTaskType,
    card: CharacterCardVersionRecord,
    state: CharacterStateRecord,
    recent_memories: Sequence[str] = (),
    perception_facts: Sequence[Mapping[str, Any]] = (),
    co_located_character_ids: Sequence[UUID] = (),
    scene_working: Mapping[str, Any] | None = None,
    package_id: UUID | None = None,
    now: datetime | None = None,
    perspective_knowledge: PerspectiveKnowledge | None = None,
) -> SealedContextPackage:
    """Build a sealed context package for one observer from snapshot-pinned inputs.

    Callers must supply only already-filtered, owner-scoped memories and
    perception facts. This function enforces directional relationship isolation
    and never includes director-only secrets.

    When ``perspective_knowledge`` is provided (S2-KNOW-001 lookup output), it
    replaces fixture private beliefs. The lookup must already be observer-scoped.
    """

    if state.character_id != observer_id:
        raise SecretAccessDenied("character state does not match observer")
    if card.character_id != observer_id:
        raise SecretAccessDenied("character card does not match observer")
    if perspective_knowledge is not None and perspective_knowledge.character_id != observer_id:
        raise SecretAccessDenied("perspective knowledge does not match observer")

    seed_key = seed_key_for_character_id(observer_id)
    if seed_key is None:
        seed_key = f"character/{observer_id}"

    if perspective_knowledge is not None:
        own_beliefs = _beliefs_from_perspective(perspective_knowledge)
    else:
        own_beliefs = private_beliefs_for(seed_key)

    sanitized_memories = [sanitize_memory_text(m) for m in recent_memories if m.strip()]

    sections: list[ContextSection] = [
        _make_section(
            ContextSectionId.STABLE_IDENTITY,
            {
                "identity": card.identity,
                "appearance": card.appearance,
                "personality_traits": card.personality_traits,
                "values": card.values,
                "fears": card.fears,
                "desires": card.desires,
                "voice_profile": card.voice_profile,
                "backstory": card.backstory,
            },
            source_record_ids=(f"card:{card.id}",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.CURRENT_STATE,
            {
                "character_id": str(observer_id),
                "location_id": None if state.location_id is None else str(state.location_id),
                "life_status": state.life_status,
                "stamina": str(state.stamina),
                "mana": str(state.mana),
                "energy": str(state.energy),
                "hunger": str(state.hunger),
                "pain": str(state.pain),
                "stress": str(state.stress),
                "version": state.version,
            },
            source_record_ids=(f"character_state:{observer_id}",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.CURRENT_PERCEPTION,
            [dict(f) for f in perception_facts],
            source_record_ids=tuple(
                str(f.get("source_id", f"perception:{i}")) for i, f in enumerate(perception_facts)
            ),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.GOALS_AND_PLANS,
            goals_for(seed_key),
            source_record_ids=(f"goals:{seed_key}",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.RELATIONSHIPS,
            relationship_edges_for(seed_key),
            source_record_ids=(f"relationships:{seed_key}",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.RECENT_MEMORY,
            sanitized_memories,
            source_record_ids=(f"recent_memory:{observer_id}",),
            trusted=False,
        ),
        _make_section(
            ContextSectionId.PRIVATE_BELIEFS,
            own_beliefs,
            source_record_ids=(f"private_beliefs:{seed_key}",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.CAPABILITIES,
            card.initial_capabilities or {"stage": "1", "notes": "seed capabilities stub"},
            source_record_ids=(f"capabilities:{card.id}",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.KNOWN_LOCAL_MAP,
            list(STAGE1_LOCAL_MAP),
            source_record_ids=("map:stage1-local",),
            trusted=True,
        ),
        _make_section(
            ContextSectionId.ALLOWED_ACTION_FAMILIES,
            list(STAGE1_ACTION_FAMILIES),
            source_record_ids=("actions:stage1",),
            trusted=True,
        ),
    ]

    if task_type == ContextTaskType.CHARACTER_REACTION and scene_working is not None:
        sections.append(
            _make_section(
                ContextSectionId.SCENE_WORKING,
                dict(scene_working),
                source_record_ids=("scene_working",),
                trusted=True,
            )
        )

    # Co-located peers are presence-only; never attach peer secrets here.
    _ = co_located_character_ids

    trimmed, omitted = trim_sections(tuple(sections))
    # Hard invariant: director-only facts never appear in any section content.
    for section in trimmed:
        blob = content_hash(section.content)  # force materialization
        _assert_no_director_leak(str(section.content))
        _ = blob

    created = now or datetime.now(UTC)
    package = SealedContextPackage(
        package_id=package_id or uuid4(),
        observer_id=observer_id,
        phase_snapshot_id=phase_snapshot_id,
        task_type=task_type,
        sections=trimmed,
        source_record_ids=tuple(sid for section in trimmed for sid in section.source_record_ids),
        omitted_sections=omitted,
        token_estimate=sum(s.token_estimate for s in trimmed),
        package_hash="pending",
        created_at=created,
    )
    return SealedContextPackage(
        schema_version=package.schema_version,
        package_id=package.package_id,
        observer_id=package.observer_id,
        phase_snapshot_id=package.phase_snapshot_id,
        task_type=package.task_type,
        sections=package.sections,
        source_record_ids=package.source_record_ids,
        omitted_sections=package.omitted_sections,
        token_estimate=package.token_estimate,
        package_hash=compute_package_hash(package),
        created_at=package.created_at,
    )
