"""Stage 2 perspective/leakage corpus (≥100 assertions for S2-QA-001)."""

from __future__ import annotations

import sys
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.application.context import (
    ContextTaskType,
    assemble_character_context,
)
from fictional_world.application.context.fixtures import (
    ALL_PRIVATE_BELIEFS,
    DIRECTOR_ONLY_FACTS,
    private_beliefs_for,
)
from fictional_world.application.knowledge import (
    lookup_perspective_knowledge,
    npc_restricted_package_beliefs,
)
from fictional_world.application.knowledge.claims import proposition_key_for
from fictional_world.application.memory.daily_consolidation import scrub_unauthorized_secrets
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.seed.records import CharacterCardVersionRecord

CAST: tuple[tuple[str, UUID], ...] = (
    ("character/mira-talren", seed_uuid("character/mira-talren")),
    ("character/dain-arcen", seed_uuid("character/dain-arcen")),
    ("character/iri-voss", seed_uuid("character/iri-voss")),
    ("character/torren-kest", seed_uuid("character/torren-kest")),
)

# Synthetic sealed phrases for dense cross-character isolation coverage.
SYNTHETIC_SECRETS: tuple[tuple[str, str], ...] = tuple(
    (
        owner_key,
        f"SEALED-{owner_key.split('/')[-1].upper()}-{index:02d}: "
        f"private ledger note {index} for {owner_key}",
    )
    for owner_key, _ in CAST
    for index in range(1, 7)
)


def _card(character_id: UUID, *, name: str) -> CharacterCardVersionRecord:
    return CharacterCardVersionRecord(
        id=uuid4(),
        character_id=character_id,
        version_number=1,
        identity={"canonical_name": name},
        backstory=f"{name} backstory",
        appearance={"eyes": "grey"},
        personality_traits={"openness": 0.5},
        values={},
        fears={},
        desires={},
        boundaries={},
        voice_profile={"register": "direct"},
        initial_capabilities={"survey": 0.4},
        secret_manifest={},
        change_summary="v1",
        content_hash="abc",
    )


def _state(character_id: UUID) -> CharacterStateRecord:
    return CharacterStateRecord(
        character_id=character_id,
        location_id=seed_uuid("location/veycross/cinder-lantern-inn"),
        life_status="alive",
        stamina=Decimal("50"),
        mana=Decimal("30"),
        energy=Decimal("60"),
        hunger=Decimal("20"),
        pain=Decimal("0"),
        stress=Decimal("10"),
        social_need=Decimal("30"),
        valence=Decimal("0"),
        arousal=Decimal("0.2"),
        dominance=Decimal("0"),
        current_card_version_id=uuid4(),
        version=0,
    )


def _belief(*, character_id: UUID, text: str, world_id: UUID) -> BeliefPersistenceRecord:
    key = proposition_key_for(text)
    return BeliefPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        character_id=character_id,
        proposition_key=key,
        belief_text=text,
        confidence=Decimal("0.4200"),
        status="active",
        evidence_summary={},
        version=0,
    )


def _secret(
    *,
    world_id: UUID,
    owner: UUID,
    holder: UUID,
    secret_key: str,
) -> SecretAccessPersistenceRecord:
    return SecretAccessPersistenceRecord(
        id=uuid4(),
        world_id=world_id,
        secret_key=secret_key,
        owner_character_id=owner,
        holder_character_id=holder,
        access_level="owner",
    )


def _section_blob(package: object, section_id: str) -> str:
    for section in package.sections:  # type: ignore[attr-defined]
        if section.section_id.value == section_id:
            return str(section.content)
    raise AssertionError(f"missing section {section_id}")


@pytest.mark.unit
@pytest.mark.security
def test_stage2_leakage_corpus_meets_gate_threshold() -> None:
    """Cross-cast isolation matrix; prints aggregate count for the stage gate report."""

    world_id = uuid4()
    snapshot = uuid4()
    assertion_count = 0

    seed_beliefs = [
        _belief(
            character_id=seed_uuid(str(item["owner"])),
            text=str(item["proposition"]),
            world_id=world_id,
        )
        for item in ALL_PRIVATE_BELIEFS
    ]
    synthetic_beliefs = [
        _belief(
            character_id=seed_uuid(owner_key),
            text=phrase,
            world_id=world_id,
        )
        for owner_key, phrase in SYNTHETIC_SECRETS
    ]
    all_beliefs = seed_beliefs + synthetic_beliefs
    secrets = [
        _secret(
            world_id=world_id,
            owner=seed_uuid(owner_key),
            holder=seed_uuid(owner_key),
            secret_key=proposition_key_for(phrase),
        )
        for owner_key, phrase in SYNTHETIC_SECRETS
    ]

    for observer_key, observer_id in CAST:
        knowledge = lookup_perspective_knowledge(
            character_id=observer_id,
            beliefs=all_beliefs,
            secret_access=secrets,
            world_id=world_id,
        )
        package = assemble_character_context(
            observer_id=observer_id,
            phase_snapshot_id=snapshot,
            task_type=ContextTaskType.CHARACTER_DECISION,
            card=_card(observer_id, name=observer_key.split("/")[-1]),
            state=_state(observer_id),
            perspective_knowledge=knowledge,
        )
        private_blob = _section_blob(package, "private_beliefs")
        knowledge_blob = str(knowledge.beliefs) + str(knowledge.secret_keys)
        npc_blob = str(npc_restricted_package_beliefs(knowledge))

        for owner_key, phrase in [
            *[(str(item["owner"]), str(item["proposition"])) for item in ALL_PRIVATE_BELIEFS],
            *SYNTHETIC_SECRETS,
        ]:
            if owner_key == observer_key:
                assert phrase in private_blob or phrase in knowledge_blob
                assertion_count += 1
                continue
            assert phrase not in private_blob
            assertion_count += 1
            assert phrase not in knowledge_blob
            assertion_count += 1
            assert phrase not in npc_blob
            assertion_count += 1
            secret_key = proposition_key_for(phrase)
            assert secret_key not in knowledge.secret_keys
            assertion_count += 1

        for director_fact in DIRECTOR_ONLY_FACTS:
            assert director_fact not in private_blob
            assertion_count += 1
            assert director_fact not in knowledge_blob
            assertion_count += 1
            assert director_fact not in npc_blob
            assertion_count += 1

        for other_key, _ in CAST:
            if other_key == observer_key:
                continue
            for belief in private_beliefs_for(other_key):
                assert belief["proposition"] not in private_blob
                assertion_count += 1

        held = frozenset(knowledge.secret_keys)
        catalog = {proposition_key_for(phrase): phrase for _, phrase in SYNTHETIC_SECRETS}
        for _, phrase in SYNTHETIC_SECRETS:
            scrubbed = scrub_unauthorized_secrets(
                f"Witness heard: {phrase}",
                held_secret_keys=held,
                secret_catalog=catalog,
            )
            owner_of_phrase = next(owner for owner, text in SYNTHETIC_SECRETS if text == phrase)
            if owner_of_phrase == observer_key:
                assert phrase in scrubbed
            else:
                assert phrase not in scrubbed
                assert "[redacted]" in scrubbed
            assertion_count += 1

    # Gate script parses this line from `pytest -s` evidence (`leakage.txt`).
    sys.stdout.write(f"LEAKAGE_CORPUS_ASSERTIONS={assertion_count}\n")
    assert assertion_count >= 100, f"expected >=100 leakage assertions, got {assertion_count}"
