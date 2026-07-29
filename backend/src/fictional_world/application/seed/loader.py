"""Load Caldris seed YAML packs into typed dictionaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID

import yaml
from pydantic import Field

from fictional_world.domain.common.base import StrictContract
from fictional_world.domain.seed.ids import DEFAULT_SEED_NAMESPACE


class SeedManifest(StrictContract):
    seed_id: str
    seed_version: int = Field(ge=1)
    schema_version: int = Field(ge=1)
    content_version: int = Field(ge=1)
    world_name: str
    language: str = "en"
    rating: str
    namespace_uuid: UUID
    required_files: tuple[str, ...]


class SeedPack(StrictContract):
    root: Path
    manifest: SeedManifest
    world: dict[str, Any]
    calendar: dict[str, Any]
    locations: tuple[dict[str, Any], ...]
    characters: dict[str, dict[str, Any]]
    beliefs: dict[str, Any]
    fixture: dict[str, Any]
    file_bytes: dict[str, bytes]


def _read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_seed_pack(root: Path, *, fixture_name: str = "stage0") -> SeedPack:
    """Load a seed world directory and Stage fixture overlay."""
    manifest_raw = cast(dict[str, Any], _read_yaml(root / "manifest.yaml"))
    namespace = UUID(str(manifest_raw["namespace_uuid"]))
    if namespace != DEFAULT_SEED_NAMESPACE:
        # Allow override but keep Stage 0 Caldris stable by default.
        pass
    manifest = SeedManifest(
        seed_id=str(manifest_raw["seed_id"]),
        seed_version=int(manifest_raw["seed_version"]),
        schema_version=int(manifest_raw["schema_version"]),
        content_version=int(manifest_raw["content_version"]),
        world_name=str(manifest_raw["world_name"]),
        language=str(manifest_raw.get("language", "en")),
        rating=str(manifest_raw["rating"]),
        namespace_uuid=namespace,
        required_files=tuple(str(item) for item in manifest_raw.get("required_files", ())),
    )

    file_bytes: dict[str, bytes] = {}
    for relative in manifest.required_files:
        path = root / relative
        file_bytes[relative] = path.read_bytes()

    world_doc = cast(dict[str, Any], _read_yaml(root / "world.yaml"))
    calendar_doc = cast(dict[str, Any], _read_yaml(root / "calendar.yaml"))
    locations_doc = cast(dict[str, Any], _read_yaml(root / "locations.yaml"))
    beliefs_doc = cast(dict[str, Any], _read_yaml(root / "initial-beliefs.yaml"))
    fixture_doc = cast(dict[str, Any], _read_yaml(root / "fixtures" / f"{fixture_name}.yaml"))

    characters: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "characters").glob("*.yaml")):
        doc = cast(dict[str, Any], _read_yaml(path))
        key = str(doc["character"]["key"])
        characters[key] = doc
        file_bytes[f"characters/{path.name}"] = path.read_bytes()

    locations = tuple(cast(dict[str, Any], item) for item in locations_doc.get("locations", []))
    return SeedPack(
        root=root,
        manifest=manifest,
        world=cast(dict[str, Any], world_doc.get("world", world_doc)),
        calendar=cast(dict[str, Any], calendar_doc.get("calendar", calendar_doc)),
        locations=locations,
        characters=characters,
        beliefs=beliefs_doc,
        fixture=fixture_doc,
        file_bytes=file_bytes,
    )
