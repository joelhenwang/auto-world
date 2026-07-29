"""Secret access + perspective leakage tests (S2-KNOW-001)."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from fictional_world.application.context import (
    ContextTaskType,
    assemble_character_context,
)
from fictional_world.application.context.fixtures import (
    DIRECTOR_ONLY_FACTS,
    private_beliefs_for,
)
from fictional_world.application.knowledge import (
    SecretAccessPolicy,
    lookup_perspective_knowledge,
    npc_restricted_package_beliefs,
)
from fictional_world.domain.characters.records import CharacterStateRecord
from fictional_world.domain.common.errors import SecretAccessDenied
from fictional_world.domain.knowledge.persistence import (
    BeliefPersistenceRecord,
    SecretAccessPersistenceRecord,
)
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.seed.records import CharacterCardVersionRecord

MIRA = seed_uuid("character/mira-talren")
DAIN = seed_uuid("character/dain-arcen")
IRI = seed_uuid("character/iri-voss")
TORREN = seed_uuid("character/torren-kest")

MIRA_PROP = "Her father's disappearance may be connected to a falsified north-route report."


def _mira_secret_key() -> str:
    # Match importer-style key from the real proposition text.
    from fictional_world.application.knowledge.claims import proposition_key_for

    return proposition_key_for(MIRA_PROP)


def _belief(
    *,
    character_id: UUID,
    text: str,
    world_id: UUID,
    prop_key: str | None = None,
) -> BeliefPersistenceRecord:
    from fictional_world.application.knowledge.claims import proposition_key_for

    key = prop_key or proposition_key_for(text)
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


def _section_content(package: object, section_id: str) -> object:
    for section in package.sections:  # type: ignore[attr-defined]
        if section.section_id.value == section_id:
            return section.content
    raise AssertionError(f"missing section {section_id}")


@pytest.mark.unit
def test_mira_secret_not_in_other_character_lookups() -> None:
    world_id = uuid4()
    secret_key = _mira_secret_key()
    beliefs = [
        _belief(character_id=MIRA, text=MIRA_PROP, world_id=world_id, prop_key=secret_key),
        _belief(
            character_id=DAIN,
            text="His probationary captain cares more about clean reports than uncertain warnings.",
            world_id=world_id,
        ),
        _belief(
            character_id=IRI,
            text=(
                "The current marker anomalies resemble deliberate interference "
                "more than natural drift."
            ),
            world_id=world_id,
        ),
        _belief(
            character_id=TORREN,
            text="The cracked route compass contains a nonstandard internal pattern.",
            world_id=world_id,
        ),
    ]
    secrets = [_secret(world_id=world_id, owner=MIRA, holder=MIRA, secret_key=secret_key)]

    mira = lookup_perspective_knowledge(
        character_id=MIRA, beliefs=beliefs, secret_access=secrets, world_id=world_id
    )
    assert secret_key in mira.secret_keys
    assert any(MIRA_PROP in str(b.get("proposition", "")) for b in mira.beliefs)

    for other in (DAIN, IRI, TORREN):
        pkg = lookup_perspective_knowledge(
            character_id=other, beliefs=beliefs, secret_access=secrets, world_id=world_id
        )
        assert secret_key not in pkg.secret_keys
        blob = str(pkg.beliefs) + str(pkg.secret_keys)
        assert MIRA_PROP not in blob
        assert secret_key not in blob


@pytest.mark.unit
def test_mira_secret_absent_from_assembled_peer_packages() -> None:
    world_id = uuid4()
    secret_key = _mira_secret_key()
    beliefs = [
        _belief(character_id=MIRA, text=MIRA_PROP, world_id=world_id, prop_key=secret_key),
        _belief(
            character_id=DAIN,
            text="His probationary captain cares more about clean reports than uncertain warnings.",
            world_id=world_id,
        ),
    ]
    secrets = [_secret(world_id=world_id, owner=MIRA, holder=MIRA, secret_key=secret_key)]
    snapshot = uuid4()

    for character_id, name in (
        (DAIN, "Dain"),
        (IRI, "Iri"),
        (TORREN, "Torren"),
    ):
        knowledge = lookup_perspective_knowledge(
            character_id=character_id,
            beliefs=beliefs,
            secret_access=secrets,
            world_id=world_id,
        )
        package = assemble_character_context(
            observer_id=character_id,
            phase_snapshot_id=snapshot,
            task_type=ContextTaskType.CHARACTER_DECISION,
            card=_card(character_id, name=name),
            state=_state(character_id),
            perspective_knowledge=knowledge,
        )
        blob = str(_section_content(package, "private_beliefs"))
        assert MIRA_PROP not in blob
        assert secret_key not in blob
        for director_fact in DIRECTOR_ONLY_FACTS:
            assert director_fact not in blob


@pytest.mark.unit
def test_npc_restricted_package_excludes_director_only() -> None:
    world_id = uuid4()
    director_text = DIRECTOR_ONLY_FACTS[0]
    beliefs = [
        _belief(character_id=DAIN, text="Wardens are short on patrols.", world_id=world_id),
        _belief(character_id=DAIN, text=director_text, world_id=world_id),
    ]
    knowledge = lookup_perspective_knowledge(
        character_id=DAIN,
        beliefs=beliefs,
        secret_access=(),
        world_id=world_id,
    )
    # Director-only belief text is stripped at lookup.
    assert all(director_text not in str(b.get("proposition", "")) for b in knowledge.beliefs)
    npc_beliefs = npc_restricted_package_beliefs(knowledge)
    assert all(director_text not in str(b) for b in npc_beliefs)


@pytest.mark.unit
def test_secret_policy_denies_without_grant() -> None:
    world_id = uuid4()
    secret_key = _mira_secret_key()
    policy = SecretAccessPolicy(
        [_secret(world_id=world_id, owner=MIRA, holder=MIRA, secret_key=secret_key)]
    )
    assert policy.may_access(holder_character_id=MIRA, secret_key=secret_key, world_id=world_id)
    assert not policy.may_access(holder_character_id=DAIN, secret_key=secret_key, world_id=world_id)
    with pytest.raises(SecretAccessDenied):
        policy.require_access(holder_character_id=DAIN, secret_key=secret_key, world_id=world_id)


@pytest.mark.unit
def test_fixture_private_beliefs_still_isolated() -> None:
    mira_belief = private_beliefs_for("character/mira-talren")[0]["proposition"]
    for other in (
        "character/dain-arcen",
        "character/iri-voss",
        "character/torren-kest",
    ):
        props = [b["proposition"] for b in private_beliefs_for(other)]
        assert mira_belief not in props
