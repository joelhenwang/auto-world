"""Unit tests for deterministic seed IDs and Stage 0 pack validation."""

from __future__ import annotations

from pathlib import Path

from fictional_world.application.seed.loader import load_seed_pack
from fictional_world.application.seed.validate import validate_seed_pack
from fictional_world.domain.seed.ids import DEFAULT_SEED_NAMESPACE, seed_uuid

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "seed" / "worlds" / "caldris-embervale-v1"


def test_seed_uuid_stable() -> None:
    first = seed_uuid("character/mira-talren")
    second = seed_uuid("character/mira-talren", namespace=DEFAULT_SEED_NAMESPACE)
    assert first == second
    assert first != seed_uuid("character/dain-arcen")
    assert seed_uuid("world/caldris") == seed_uuid("world/caldris")


def test_load_and_validate_stage0_pack() -> None:
    pack = load_seed_pack(PACK, fixture_name="stage0")
    report = validate_seed_pack(pack)
    assert report.ok, report.result.issues
    assert report.resolved_character_keys == ("character/mira-talren",)
    assert report.resolved_location_keys == ("location/veycross/cinder-lantern-inn",)


def test_broken_location_reference_fails_validation() -> None:
    pack = load_seed_pack(PACK, fixture_name="stage0")
    broken = pack.model_copy(
        update={
            "characters": {
                "character/mira-talren": {
                    **pack.characters["character/mira-talren"],
                    "character": {
                        **pack.characters["character/mira-talren"]["character"],
                        "current_location": "location/missing",
                    },
                }
            }
        }
    )
    report = validate_seed_pack(broken)
    assert not report.ok
    codes = {issue.code for issue in report.result.issues}
    assert "broken_location_ref" in codes
