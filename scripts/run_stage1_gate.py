#!/usr/bin/env python3
"""Collect deterministic Stage 1 gate evidence."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "status" / "evidence" / "stage-1"
GATE_DATABASE = "fictional_world_stage1_gate"
GATE_DATABASE_URL = (
    f"postgresql+psycopg://fictional_world:change-me-local@127.0.0.1:5432/{GATE_DATABASE}"
)


def _run(cmd: list[str], *, outfile: Path | None = None, env: dict[str, str] | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    body = (result.stdout or "") + (result.stderr or "")
    if outfile is not None:
        outfile.write_text(body, encoding="utf-8")
    if result.returncode != 0:
        print(body, file=sys.stderr)
        return 1
    return 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _git_rev() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _prepare_gate_database() -> tuple[int, dict[str, str]]:
    migration_log = EVIDENCE / "migrations.txt"
    failures = _run(["docker", "compose", "up", "-d", "postgres"], outfile=migration_log)
    commands = [
        [
            "docker",
            "exec",
            "fictional-world-postgres",
            "psql",
            "-U",
            "fictional_world",
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            f"DROP DATABASE IF EXISTS {GATE_DATABASE} WITH (FORCE);",
            "-c",
            f"CREATE DATABASE {GATE_DATABASE};",
        ],
        [
            "uv",
            "run",
            "python",
            "scripts/verify_migrations.py",
            "--database-url",
            GATE_DATABASE_URL,
        ],
    ]
    environment = {**os.environ, "ALEMBIC_DATABASE_URL": GATE_DATABASE_URL}
    for command in commands:
        temporary = EVIDENCE / ".migration-step.txt"
        failures += _run(command, outfile=temporary, env=environment)
        with migration_log.open("a", encoding="utf-8") as target:
            target.write(temporary.read_text(encoding="utf-8"))
        temporary.unlink(missing_ok=True)
    return failures, environment


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    failures, environment = _prepare_gate_database()

    checks = [
        (
            ["uv", "run", "ruff", "check", "backend", "scripts", "tools"],
            "ruff.txt",
        ),
        (
            ["uv", "run", "ruff", "format", "--check", "backend", "scripts", "tools"],
            "ruff-format.txt",
        ),
        (["uv", "run", "basedpyright"], "basedpyright.txt"),
        (["pnpm", "--dir", "frontend", "generate:api"], "frontend-api-types.txt"),
        (["pnpm", "--dir", "frontend", "test"], "frontend-test.txt"),
        (["pnpm", "--dir", "frontend", "build"], "frontend-build.txt"),
        (
            [
                "uv",
                "run",
                "pytest",
                "backend/tests/scenario/test_stage1_first_day.py",
                "--junitxml",
                str(EVIDENCE / "scenario-junit.xml"),
            ],
            "scenario.txt",
        ),
        (
            [
                "uv",
                "run",
                "pytest",
                "backend/tests/unit/application/context/test_assembler_leakage.py",
                "backend/tests/integration/test_stage1_api.py",
            ],
            "leakage.txt",
        ),
        (
            [
                "uv",
                "run",
                "pytest",
                "backend/tests/unit/agents/test_stage1_graphs.py",
                "backend/tests/integration/test_scene_commit.py",
                "backend/tests/integration/test_stage1_phase_runner.py",
            ],
            "fault-and-retry.txt",
        ),
        (
            [
                "uv",
                "run",
                "pytest",
                "--junitxml",
                str(EVIDENCE / "pytest-junit.xml"),
            ],
            "pytest.txt",
        ),
        (["uv", "run", "python", "scripts/export_openapi.py"], "openapi-export.txt"),
        (
            [
                "git",
                "diff",
                "--exit-code",
                "--",
                "docs/generated/openapi.json",
                "frontend/src/api/generated/schema.d.ts",
            ],
            "generated-contract-diff.txt",
        ),
    ]
    for command, filename in checks:
        failures += _run(command, outfile=EVIDENCE / filename, env=environment)

    scenario = {
        "scenario_id": "stage1-first-day-v1",
        "seed": "caldris-embervale-v1:stage1",
        "model": "fake/stage1-first-day-v1",
        "phases": ["dawn", "morning", "evening"],
        "active_characters": ["Mira Talren", "Dain Arcen"],
        "expected_fake_model_calls": 10,
        "scenario_test_passed": (EVIDENCE / "scenario.txt")
        .read_text(encoding="utf-8")
        .find("1 passed")
        >= 0,
    }
    (EVIDENCE / "scenario-summary.json").write_text(
        json.dumps(scenario, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "collected_at": stamp,
        "git_commit": _git_rev(),
        "alembic_head": "0003_stage1_action_scene_tables",
        "seed_id": "caldris-embervale-v1",
        "seed_fixture": "stage1",
        "scenario_id": "stage1-first-day-v1",
        "model_mode": "fake",
        "hashes": {
            "uv.lock": _sha256(ROOT / "uv.lock"),
            "frontend/pnpm-lock.yaml": _sha256(ROOT / "frontend" / "pnpm-lock.yaml"),
            "openapi.json": _sha256(ROOT / "docs" / "generated" / "openapi.json"),
            "database-schema.sql": _sha256(ROOT / "docs" / "generated" / "database-schema.sql"),
        },
        "gate_script_exit_nonzero_count": failures,
    }
    (EVIDENCE / "version-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
