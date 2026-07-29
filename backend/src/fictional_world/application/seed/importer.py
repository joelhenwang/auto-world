"""Atomic Stage 0 seed importer (handbook ``23`` §26)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

from fictional_world.application.ports.repositories import UnitOfWork
from fictional_world.application.seed.loader import SeedPack, load_seed_pack
from fictional_world.application.seed.validate import SeedValidationReport, validate_seed_pack
from fictional_world.application.simulation.commit import (
    CommitOperationCommand,
    EventCommitService,
)
from fictional_world.domain.characters.records import (
    CharacterRecord,
    CharacterStateRecord,
    EntityRecord,
)
from fictional_world.domain.common.errors import DomainError
from fictional_world.domain.seed.ids import seed_uuid
from fictional_world.domain.seed.records import (
    CharacterCardVersionRecord,
    LocationRecord,
    WorldConfigRecord,
)
from fictional_world.domain.world.records import (
    AggregateVersionRecord,
    WorldClockRecord,
    WorldRecord,
)

DEFAULT_SEED_ROOT = Path("seed/worlds/caldris-embervale-v1")
WORLD_SEEDED = "WORLD_SEEDED"


class SeedImportError(DomainError):
    """Seed validation or import failure."""

    def __init__(self, message: str, *, report: SeedValidationReport | None = None) -> None:
        self.report = report
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class SeedImportResult:
    world_id: UUID
    event_id: UUID | None
    already_imported: bool
    seed_id: str
    content_version: int
    manifest_hash: str
    seed_keys: dict[str, str]
    validation: SeedValidationReport


def manifest_hash(pack: SeedPack) -> str:
    digest = hashlib.sha256()
    for relative in sorted(pack.file_bytes):
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(pack.file_bytes[relative])
        digest.update(b"\0")
    return digest.hexdigest()


def _card_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class SeedImporter:
    """Import a validated Stage 0 seed pack into an empty or matching world."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow
        self._commit = EventCommitService()

    async def import_pack(
        self,
        pack: SeedPack,
        *,
        fixture_name: str = "stage0",
    ) -> SeedImportResult:
        report = validate_seed_pack(pack)
        if not report.ok:
            raise SeedImportError("seed validation failed", report=report)

        hash_value = manifest_hash(pack)
        world_key = str(pack.world["key"])
        world_id = seed_uuid(world_key, namespace=pack.manifest.namespace_uuid)
        slug = str(pack.world["slug"])
        idempotency_key = (
            f"seed:{pack.manifest.seed_id}:v{pack.manifest.content_version}:{fixture_name}"
        )

        existing = await self._uow.worlds.get_by_slug(slug)
        if existing is not None:
            prior = await self._uow.events.find_by_idempotency_key(idempotency_key)
            if prior is not None:
                facts = prior.structured_facts
                keys_raw = facts.get("seed_keys_json")
                seed_keys: dict[str, str] = {}
                if isinstance(keys_raw, str) and keys_raw:
                    parsed: object = json.loads(keys_raw)
                    if isinstance(parsed, dict):
                        typed_items = cast(dict[object, object], parsed)
                        seed_keys = {str(key): str(value) for key, value in typed_items.items()}
                return SeedImportResult(
                    world_id=existing.id,
                    event_id=prior.id,
                    already_imported=True,
                    seed_id=pack.manifest.seed_id,
                    content_version=pack.manifest.content_version,
                    manifest_hash=str(facts.get("manifest_hash", hash_value)),
                    seed_keys=seed_keys,
                    validation=report,
                )
            raise SeedImportError(
                f"world slug {slug!r} already exists without matching seed event",
                report=report,
            )

        seed_keys = {world_key: str(world_id)}
        phase_names = tuple(
            str(item["name"]) for item in pack.calendar.get("phases", []) if "name" in item
        )
        if not phase_names:
            phase_names = (
                "dawn",
                "sunrise",
                "morning",
                "noon",
                "afternoon",
                "sunset",
                "dusk",
                "evening",
                "night",
                "midnight",
            )

        world = await self._uow.worlds.insert(
            WorldRecord(
                id=world_id,
                slug=slug,
                name=str(pack.world["name"]),
                status="initializing",
                language=str(pack.world.get("language", pack.manifest.language)),
                content_rating=str(pack.world.get("content_rating", pack.manifest.rating)),
                current_event_sequence=0,
                version=0,
            )
        )

        initial = pack.calendar.get("initial", {})
        await self._uow.worlds.upsert_clock(
            WorldClockRecord(
                world_id=world.id,
                generation_number=int(initial.get("generation_number", 1)),
                year=int(initial.get("year", 412)),
                month=int(initial.get("month", 3)),
                day=int(initial.get("day", 12)),
                phase_name=str(initial.get("phase_name", "dawn")),
                phase_ordinal=int(initial.get("phase_ordinal", 0)),
                absolute_day_index=int(initial.get("absolute_day_index", 0)),
                absolute_phase_index=int(initial.get("absolute_phase_index", 0)),
                resolution_mode=str(initial.get("resolution_mode", "detailed")),
                version=0,
            ),
            expected_version=None,
        )

        config = await self._uow.worlds.insert_config(
            WorldConfigRecord(
                id=uuid4(),
                world_id=world.id,
                config_version=pack.manifest.content_version,
                is_active=True,
                effective_from_phase_index=0,
                detailed_phase_names=phase_names,
                max_days=int(pack.world.get("max_days", 36500)),
                max_generations=int(pack.world.get("max_generations", 3)),
                plot_armour_level=Decimal("0"),
                director_privileges={
                    "hooks": list(pack.beliefs.get("director_only", [])),
                },
                image_budget_per_day=0,
                macro_simulation_policy={
                    "seed_id": pack.manifest.seed_id,
                    "content_version": pack.manifest.content_version,
                    "fixture": fixture_name,
                    "public_knowledge": list(pack.beliefs.get("public_knowledge", [])),
                },
                content_policy_version=f"seed-{pack.manifest.content_version}",
            )
        )

        location_ids: dict[str, UUID] = {}
        for loc in pack.locations:
            key = str(loc["key"])
            if key not in report.resolved_location_keys:
                continue
            entity_id = seed_uuid(key, namespace=pack.manifest.namespace_uuid)
            seed_keys[key] = str(entity_id)
            location_ids[key] = entity_id
            await self._uow.characters.insert_entity(
                EntityRecord(
                    id=entity_id,
                    world_id=world.id,
                    entity_type="location",
                    canonical_name=str(loc["name"]),
                    normalized_name=str(loc["name"]).casefold(),
                    lifecycle_status="active",
                    created_event_id=None,
                )
            )
            raw_tags_obj: object = loc.get("environment_tags") or []
            raw_tags = cast(list[object], raw_tags_obj) if isinstance(raw_tags_obj, list) else []
            tags = tuple(str(tag) for tag in raw_tags)
            capacity = loc.get("capacity")
            await self._uow.characters.insert_location(
                LocationRecord(
                    entity_id=entity_id,
                    parent_location_id=None,
                    location_type=str(loc.get("type", "building")),
                    region_code=str(loc.get("region_code", "embervale-march")),
                    capacity=int(capacity) if capacity is not None else None,
                    environment_tags=tags,
                    canonical_description=str(loc.get("description", loc["name"])),
                )
            )

        private_by_owner: dict[str, list[dict[str, Any]]] = {}
        for belief in pack.beliefs.get("private_beliefs", []):
            owner = str(belief["owner"])
            private_by_owner.setdefault(owner, []).append(dict(belief))

        character_ids: dict[str, UUID] = {}
        for key in report.resolved_character_keys:
            doc = pack.characters[key]
            char = doc["character"]
            entity_id = seed_uuid(key, namespace=pack.manifest.namespace_uuid)
            seed_keys[key] = str(entity_id)
            character_ids[key] = entity_id
            location_key = str(char["current_location"])
            location_id = location_ids[location_key]

            await self._uow.characters.insert_entity(
                EntityRecord(
                    id=entity_id,
                    world_id=world.id,
                    entity_type="character",
                    canonical_name=str(char["canonical_name"]),
                    normalized_name=str(char["canonical_name"]).casefold(),
                    lifecycle_status="active",
                    created_event_id=None,
                )
            )
            await self._uow.characters.insert_character(
                CharacterRecord(
                    entity_id=entity_id,
                    character_kind="focus",
                    species_code=str(char.get("species", "human")),
                    current_card_version_id=None,
                    version=0,
                )
            )

            card_id = seed_uuid(f"{key}/card/v1", namespace=pack.manifest.namespace_uuid)
            secrets = {
                "private_beliefs": private_by_owner.get(key, []),
                "seed_key": key,
            }
            identity_doc = dict(doc.get("identity", {}))
            card_payload = {
                "identity": identity_doc,
                "appearance": doc.get("appearance", {}),
                "psychology": doc.get("psychology", {}),
                "expression": doc.get("expression", {}),
            }
            await self._uow.characters.insert_card(
                CharacterCardVersionRecord(
                    id=card_id,
                    character_id=entity_id,
                    version_number=1,
                    identity={
                        "seed_key": key,
                        "pronouns": char.get("pronouns"),
                        "age": char.get("age"),
                        "culture": char.get("culture"),
                        "occupation": char.get("occupation"),
                        "focus_role": char.get("focus_role"),
                        **identity_doc,
                    },
                    backstory=str(identity_doc.get("formative_history", "")),
                    appearance=dict(doc.get("appearance", {})),
                    personality_traits=dict(doc.get("psychology", {}).get("traits", {})),
                    values={"items": list(doc.get("psychology", {}).get("values", []))},
                    fears={"items": list(doc.get("psychology", {}).get("fears", []))},
                    desires={"items": list(doc.get("psychology", {}).get("desires", []))},
                    boundaries={},
                    voice_profile=dict(doc.get("expression", {})),
                    initial_capabilities={},
                    secret_manifest=secrets,
                    change_summary="seed v1",
                    content_hash=_card_hash(card_payload),
                )
            )
            await self._uow.characters.set_character_card(entity_id, card_version_id=card_id)

            resources = doc.get("resources", {})
            await self._uow.characters.insert_state(
                CharacterStateRecord(
                    character_id=entity_id,
                    location_id=location_id,
                    life_status="alive",
                    stamina=Decimal(str(resources.get("stamina", 50))),
                    mana=Decimal(str(resources.get("mana", 20))),
                    energy=Decimal(str(resources.get("energy", 70))),
                    hunger=Decimal(str(resources.get("hunger", 20))),
                    pain=Decimal(str(resources.get("pain", 0))),
                    stress=Decimal(str(resources.get("stress", 10))),
                    social_need=Decimal(str(resources.get("social_need", 40))),
                    valence=Decimal(str(resources.get("valence", 0))),
                    arousal=Decimal(str(resources.get("arousal", 0.2))),
                    dominance=Decimal(str(resources.get("dominance", 0))),
                    current_card_version_id=card_id,
                    version=0,
                )
            )
            await self._uow.aggregate_versions.upsert(
                AggregateVersionRecord(
                    world_id=world.id,
                    aggregate_type="character_state",
                    aggregate_id=entity_id,
                    version=0,
                ),
                expected_version=None,
            )

        commit = await self._commit.commit(
            self._uow,
            CommitOperationCommand(
                world_id=world.id,
                idempotency_key=idempotency_key,
                event_type=WORLD_SEEDED,
                canonical_summary=(
                    f"Seeded {pack.manifest.seed_id} "
                    f"content_version={pack.manifest.content_version} fixture={fixture_name}"
                ),
                structured_facts={
                    "seed_id": pack.manifest.seed_id,
                    "content_version": pack.manifest.content_version,
                    "fixture": fixture_name,
                    "manifest_hash": hash_value,
                    "world_key": world_key,
                    "seed_keys_json": json.dumps(seed_keys, sort_keys=True),
                },
                source_kind="migration",
                importance=Decimal("1.0"),
                visibility_class="public",
                absolute_phase_index=int(initial.get("absolute_phase_index", 0)),
                effects=(),
                expected_versions={},
                enqueue_outbox=False,
            ),
        )

        for entity_id in [*location_ids.values(), *character_ids.values()]:
            await self._uow.characters.set_entity_created_event(
                entity_id, created_event_id=commit.event_id
            )
        await self._uow.worlds.set_config_created_event(config.id, created_event_id=commit.event_id)
        clock = await self._uow.worlds.get_clock(world.id)
        if clock is not None:
            await self._uow.worlds.upsert_clock(
                clock.model_copy(update={"last_event_id": commit.event_id}),
                expected_version=clock.version,
            )

        await self._uow.worlds.update_status(world.id, status="active", expected_version=1)

        return SeedImportResult(
            world_id=world.id,
            event_id=commit.event_id,
            already_imported=False,
            seed_id=pack.manifest.seed_id,
            content_version=pack.manifest.content_version,
            manifest_hash=hash_value,
            seed_keys=seed_keys,
            validation=report,
        )


async def import_caldris_stage0(
    uow: UnitOfWork,
    *,
    root: Path | None = None,
    fixture_name: str = "stage0",
) -> SeedImportResult:
    pack = load_seed_pack(root or DEFAULT_SEED_ROOT, fixture_name=fixture_name)
    return await SeedImporter(uow).import_pack(pack, fixture_name=fixture_name)


async def import_caldris_stage1(
    uow: UnitOfWork,
    *,
    root: Path | None = None,
) -> SeedImportResult:
    """Import the dual-character Stage 1 fixture."""

    return await import_caldris_stage0(
        uow,
        root=root,
        fixture_name="stage1",
    )
