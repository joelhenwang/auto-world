"""Seed pack validation and report (handbook ``23`` §25)."""

from __future__ import annotations

from dataclasses import dataclass, field

from fictional_world.application.seed.loader import SeedPack
from fictional_world.domain.common.result import ValidationIssue, ValidationResult


@dataclass(slots=True)
class SeedValidationReport:
    result: ValidationResult
    resolved_location_keys: tuple[str, ...] = ()
    resolved_character_keys: tuple[str, ...] = ()
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.result.ok


def validate_seed_pack(pack: SeedPack) -> SeedValidationReport:
    issues: list[ValidationIssue] = []
    warnings: list[str] = []

    for relative in pack.manifest.required_files:
        path = pack.root / relative
        if not path.is_file():
            issues.append(
                ValidationIssue(
                    code="missing_required_file",
                    message=f"missing required seed file: {relative}",
                    path=relative,
                )
            )

    location_keys = {str(item["key"]) for item in pack.locations if "key" in item}
    character_keys = set(pack.characters)

    active_locations = [str(item) for item in pack.fixture.get("active_locations", [])]
    active_characters = [str(item) for item in pack.fixture.get("active_characters", [])]

    if not active_locations:
        issues.append(
            ValidationIssue(
                code="empty_fixture_locations",
                message="fixture must list at least one active location",
                path="fixtures",
            )
        )
    if not active_characters:
        issues.append(
            ValidationIssue(
                code="empty_fixture_characters",
                message="fixture must list at least one active character",
                path="fixtures",
            )
        )

    for key in active_locations:
        if key not in location_keys:
            issues.append(
                ValidationIssue(
                    code="unknown_location",
                    message=f"active location not defined: {key}",
                    path=key,
                )
            )

    for key in active_characters:
        if key not in character_keys:
            issues.append(
                ValidationIssue(
                    code="unknown_character",
                    message=f"active character not defined: {key}",
                    path=key,
                )
            )
            continue
        loc = str(pack.characters[key]["character"].get("current_location", ""))
        if loc and loc not in location_keys:
            issues.append(
                ValidationIssue(
                    code="broken_location_ref",
                    message=f"{key} references missing location {loc}",
                    path=f"{key}.current_location",
                )
            )
        if loc and loc not in active_locations:
            issues.append(
                ValidationIssue(
                    code="inactive_location_ref",
                    message=f"{key} starts in inactive location {loc}",
                    path=f"{key}.current_location",
                )
            )

    for belief in pack.beliefs.get("private_beliefs", []):
        owner = str(belief.get("owner", ""))
        if owner and owner not in character_keys:
            issues.append(
                ValidationIssue(
                    code="broken_belief_owner",
                    message=f"private belief owner missing: {owner}",
                    path=owner,
                )
            )

    # Secret / public / director separation sanity.
    public = {str(item) for item in pack.beliefs.get("public_knowledge", [])}
    for belief in pack.beliefs.get("private_beliefs", []):
        proposition = str(belief.get("proposition", ""))
        if proposition and proposition in public:
            issues.append(
                ValidationIssue(
                    code="secret_public_overlap",
                    message="private belief duplicated in public knowledge",
                    path=str(belief.get("owner", "")),
                )
            )

    director = {str(item) for item in pack.beliefs.get("director_only", [])}
    for belief in pack.beliefs.get("private_beliefs", []):
        proposition = str(belief.get("proposition", ""))
        if proposition and proposition in director:
            warnings.append("private belief also listed as director_only")

    if "key" not in pack.world or "slug" not in pack.world:
        issues.append(
            ValidationIssue(
                code="invalid_world",
                message="world.yaml must include key and slug",
                path="world",
            )
        )

    return SeedValidationReport(
        result=ValidationResult(issues=tuple(issues)),
        resolved_location_keys=tuple(active_locations),
        resolved_character_keys=tuple(active_characters),
        warnings=warnings,
    )
