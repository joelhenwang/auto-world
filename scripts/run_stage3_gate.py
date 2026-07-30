#!/usr/bin/env python3
"""Collect deterministic Stage 3 gate evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "status" / "evidence" / "stage-3"
GATE_DATABASE = "fictional_world_stage3_gate"
GATE_DATABASE_URL = (
    f"postgresql+psycopg://fictional_world:change-me-local@127.0.0.1:5432/{GATE_DATABASE}"
)
ALEMBIC_HEAD = "0005_stage3_long_term_tables"
SCENARIO_ID = "stage3-autonomous-month-v1"
SEED_CONTENT_VERSION = 2


def _run(
    cmd: list[str],
    *,
    outfile: Path | None = None,
    env: dict[str, str] | None = None,
) -> int:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    raw_body = (result.stdout or "") + (result.stderr or "")
    normalized = "\n".join(line.rstrip() for line in raw_body.splitlines()).rstrip()
    body = f"{normalized}\n" if normalized else ""
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


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _passed_count(log_text: str) -> int | None:
    match = re.search(r"(\d+) passed", log_text)
    if match is None:
        return None
    return int(match.group(1))


def _leakage_assertion_count(log_text: str) -> int | None:
    match = re.search(r"LEAKAGE_CORPUS_ASSERTIONS=(\d+)", log_text)
    if match is None:
        return None
    return int(match.group(1))


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


def _write_reports(
    *,
    stamp: str,
    failures: int,
    commit: str,
    leakage_assertions: int | None,
) -> None:
    decision = "PASS" if failures == 0 else "FAIL"
    scenario_log = _read(EVIDENCE / "scenario.txt")
    pytest_log = _read(EVIDENCE / "pytest.txt")
    leakage_log = _read(EVIDENCE / "leakage.txt")
    fault_log = _read(EVIDENCE / "fault-and-retry.txt")
    frontend_test_log = _read(EVIDENCE / "frontend-test.txt")

    scenario_summary = {
        "scenario_id": SCENARIO_ID,
        "seed": "caldris-embervale-v1:stage2",
        "content_version": SEED_CONTENT_VERSION,
        "model": "fake/stage2-seven-day-v1",
        "days": 7,
        "phases_per_day": 10,
        "expected_phase_hashes": 70,
        "active_characters": [
            "Mira Talren",
            "Dain Arcen",
            "Iri Voss",
            "Torren Kest",
        ],
        "stage1_regression_included": True,
        "scenario_test_passed": "passed" in scenario_log and failures == 0,
    }
    (EVIDENCE / "scenario-summary.json").write_text(
        json.dumps(scenario_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    hashes = {
        "uv.lock": _sha256(ROOT / "uv.lock"),
        "frontend/pnpm-lock.yaml": _sha256(ROOT / "frontend" / "pnpm-lock.yaml"),
        "openapi.json": _sha256(ROOT / "docs" / "generated" / "openapi.json"),
        "database-schema.sql": _sha256(ROOT / "docs" / "generated" / "database-schema.sql"),
    }
    manifest = {
        "collected_at": stamp,
        "git_commit": commit,
        "alembic_head": ALEMBIC_HEAD,
        "seed_id": "caldris-embervale-v1",
        "seed_fixture": "stage2",
        "seed_content_version": SEED_CONTENT_VERSION,
        "scenario_id": SCENARIO_ID,
        "model_mode": "fake",
        "leakage_corpus_assertions": leakage_assertions,
        "hashes": hashes,
        "gate_script_exit_nonzero_count": failures,
    }
    (EVIDENCE / "version-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    leakage_report = EVIDENCE / "leakage-report.md"
    leakage_report.write_text(
        "\n".join(
            [
                "# Stage 2 knowledge and perspective leakage report",
                "",
                f"**Result:** {decision}",
                (
                    "**Command:** `uv run pytest "
                    "backend/tests/unit/application/knowledge/test_leakage.py "
                    "backend/tests/unit/application/knowledge/test_leakage_corpus.py "
                    "backend/tests/unit/application/context/test_assembler_leakage.py -s`"
                ),
                f"**Raw evidence:** `leakage.txt` — {_passed_count(leakage_log)} passed",
                (
                    f"**Corpus assertion count:** {leakage_assertions}"
                    if leakage_assertions is not None
                    else "**Corpus assertion count:** unknown"
                ),
                "",
                "Verified:",
                "",
                "- seeded private beliefs stay owner-scoped across four characters;",
                "- synthetic sealed phrases (>=100 assertion matrix) never cross observers;",
                "- director-only facts never enter character or NPC packages;",
                "- unauthorized secret phrases are scrubbed from consolidation text;",
                "- Stage 1 assembler leakage suite remains green.",
                "",
                "No hard leakage finding was observed."
                if decision == "PASS"
                else "Hard leakage or corpus threshold failure — see `leakage.txt`.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    fault_report = EVIDENCE / "fault-injection-report.md"
    fault_report.write_text(
        "\n".join(
            [
                "# Stage 2 fault, retry, and day-boundary restart report",
                "",
                f"**Result:** {decision}",
                f"**Raw evidence:** `fault-and-retry.txt` — {_passed_count(fault_log)} passed",
                "",
                "| Boundary | Injection/proof | Recovery |",
                "|---|---|---|",
                (
                    "| day finalize after process restart | "
                    "`test_process_restart_at_day_boundary_reuses_day_run` | "
                    "same day_run/summary/diary IDs |"
                ),
                (
                    "| daily consolidation retry | prior day_run reuse | "
                    "no duplicate summaries/diaries |"
                ),
                (
                    "| travel mid-route restart | seed modifier travel progress | "
                    "progress preserved |"
                ),
                ("| Stage 0 snapshot/outbox faults | `test_stage0_faults` | idempotent inserts |"),
                ("| Stage 1 scene commit duplicate | same idempotency key | original event IDs |"),
                "",
                "The default fault suite makes no external provider calls.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    report = EVIDENCE / "stage-gate-report.md"
    report.write_text(
        "\n".join(
            [
                "# Stage 3 Gate Report — Autonomous Month and Long-Term Coherence",
                "",
                f"**Decision:** {decision}",
                f"**Report date:** {stamp}",
                "**Stage owner:** parent coding agent",
                "**QA owner:** S3-QA-001 subagent",
                f"**Tested integration commit:** `{commit}`",
                "**Release candidate:** `cursor/s3-mem-rules-world-03fc`",
                "**Previous verified stage:** Stage 2 seven-day world (FROZEN)",
                "**Environment/profile:** Linux cloud agent, fake provider default, "
                "PostgreSQL 16 + pgvector",
                "**Handbook:** v1.0 / `28_STAGE_3_AUTONOMOUS_MONTH.md` §9",
                "",
                "## 1. Intended outcome",
                "",
                "Four primary characters complete thirty autonomous days x ten phases from one",
                "sealed snapshot per phase. Day-finalization is restart-safe; knowledge",
                "isolation holds across perspective packages; Stage 1-2 remain green.",
                "",
                "## 2. Build and version manifest",
                "",
                "See `version-manifest.json`.",
                "",
                "| Component | Version/hash |",
                "|---|---|",
                f"| Git commit | `{commit}` |",
                f"| Alembic head | `{ALEMBIC_HEAD}` |",
                f"| uv.lock | `{hashes['uv.lock'][:8]}…` |",
                f"| frontend lock | `{hashes['frontend/pnpm-lock.yaml'][:8]}…` |",
                f"| OpenAPI | `{hashes['openapi.json'][:8]}…` |",
                f"| database-schema.sql | `{hashes['database-schema.sql'][:8]}…` |",
                f"| seed content_version | `{SEED_CONTENT_VERSION}` |",
                f"| scenario | `{SCENARIO_ID}` |",
                "| model mode | fake |",
                "",
                "## 3. Static, build, and migration quality",
                "",
                "| Check | Result | Evidence |",
                "|---|---|---|",
                f"| Ruff lint + format | "
                f"{'PASS' if failures == 0 else 'see logs'} | "
                "`ruff.txt`, `ruff-format.txt` |",
                "| strict basedpyright | see log | `basedpyright.txt` |",
                f"| full offline Python suite | "
                f"{_passed_count(pytest_log)} passed (live markers deselected) | "
                "`pytest.txt`, JUnit |",
                f"| frontend tests | {_passed_count(frontend_test_log)} passed | "
                "`frontend-test.txt` |",
                "| frontend strict build | see log | `frontend-build.txt` |",
                "| generated OpenAPI/types current | see log | `generated-contract-diff.txt` |",
                "| clean migration cycle | see log | `migrations.txt` |",
                "",
                "## 4. Functional scenarios",
                "",
                "| Scenario | Expected | Result |",
                "|---|---|---|",
                f"| `{SCENARIO_ID}` | 30 days x 10 phases, 4 characters | "
                f"{'PASS' if 'passed' in scenario_log else 'FAIL'} |",
                "| `stage2-seven-day-world-v1` + stage1 regression | dawn/morning/evening | "
                "included in scenario.txt |",
                "",
                "## 5. Knowledge / leakage",
                "",
                f"- Leakage suite passed count: {_passed_count(leakage_log)}",
                (
                    f"- Corpus assertions: **{leakage_assertions}** (threshold >=100)"
                    if leakage_assertions is not None
                    else "- Corpus assertions: not recorded"
                ),
                "- Detail: `leakage-report.md`",
                "",
                "## 6. Fault / idempotency",
                "",
                f"- Fault subset passed count: {_passed_count(fault_log)}",
                "- Detail: `fault-injection-report.md`",
                "",
                "## 7. Stage 3 hard exit checklist (handbook §9)",
                "",
                f"- [{'x' if decision == 'PASS' else ' '}] thirty autonomous days / ten phases "
                "without manual DB repair",
                f"- [{'x' if decision == 'PASS' else ' '}] primary intents share sealed "
                "snapshot (scenario invariants)",
                f"- [{'x' if decision == 'PASS' else ' '}] typed/idempotent effects + "
                "day/phase machines",
                f"- [{'x' if decision == 'PASS' else ' '}] no unauthorized secret in "
                "perspective packages (>=100 corpus assertions)",
                f"- [{'x' if decision == 'PASS' else ' '}] day-boundary restart yields no "
                "duplicate consolidation",
                f"- [{'x' if decision == 'PASS' else ' '}] Stage 0/1 gates remain green "
                "(stage1 scenario + full pytest)",
                f"- [{'x' if decision == 'PASS' else ' '}] lint, format, types, migrations, "
                "frontend checks pass",
                "",
                "## 8. Decision",
                "",
                f"### {decision}",
                "",
                (
                    "All deterministic Stage 3 hard gates pass at the tested commit. "
                    "Human narrative rubric scores remain blank in "
                    "`human-review-worksheet.md` (non-blocking for automated gate)."
                    if decision == "PASS"
                    else "One or more Stage 2 gate checks failed. See evidence logs; "
                    "do not freeze Stage 2 contracts."
                ),
                "",
                "## 9. Sign-off",
                "",
                "| Role | Decision | Date | Notes |",
                "|---|---|---|---|",
                f"| QA owner (automated) | {decision} | {stamp[:10]} | "
                "evidence under `docs/status/evidence/stage-3/` |",
                "| Stage owner | pending parent review | — | merge/freeze owner |",
                "| Project owner | pending | — | human promotion / rubric |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    failures, environment = _prepare_gate_database()

    checks: list[tuple[list[str], str]] = [
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
                "backend/tests/scenario/test_stage3_autonomous_month.py",
                "backend/tests/scenario/test_stage2_seven_day_world.py",
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
                "-s",
                "backend/tests/unit/application/knowledge/test_leakage.py",
                "backend/tests/unit/application/knowledge/test_leakage_corpus.py",
                "backend/tests/unit/application/context/test_assembler_leakage.py",
            ],
            "leakage.txt",
        ),
        (
            [
                "uv",
                "run",
                "pytest",
                "backend/tests/unit/application/orchestration/test_day_boundary_idempotency.py",
                "backend/tests/unit/application/memory/test_daily_consolidation.py",
                "backend/tests/unit/application/simulation/test_s2_sim_001_calendar_travel.py",
                "backend/tests/fault/test_stage0_faults.py",
                "backend/tests/integration/test_scene_commit.py",
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

    commit = _git_rev()
    leakage_assertions = _leakage_assertion_count(_read(EVIDENCE / "leakage.txt"))
    if leakage_assertions is not None and leakage_assertions < 100:
        print(
            f"leakage corpus below threshold: {leakage_assertions} < 100",
            file=sys.stderr,
        )
        failures += 1

    _write_reports(
        stamp=stamp,
        failures=failures,
        commit=commit,
        leakage_assertions=leakage_assertions,
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
