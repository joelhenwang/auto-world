#!/usr/bin/env python3
"""Collect Stage 0 gate evidence into docs/status/evidence/stage-0/."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "status" / "evidence" / "stage-0"


def _run(cmd: list[str], *, outfile: Path | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT, check=False, text=True, capture_output=True)
    body = (result.stdout or "") + (result.stderr or "")
    if outfile is not None:
        outfile.write_text(body, encoding="utf-8")
    if result.returncode != 0:
        print(body, file=sys.stderr)
    return result.returncode


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


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    failures = 0

    if not os.environ.get("ALEMBIC_DATABASE_URL"):
        os.environ["ALEMBIC_DATABASE_URL"] = (
            "postgresql+psycopg://fictional_world:change-me-local@127.0.0.1:5432/fictional_world"
        )

    failures += _run(
        ["uv", "run", "ruff", "check", "backend", "scripts", "tools"],
        outfile=EVIDENCE / "ruff.txt",
    )
    failures += _run(
        ["uv", "run", "ruff", "format", "--check", "backend", "scripts", "tools"],
        outfile=EVIDENCE / "ruff-format.txt",
    )
    failures += _run(
        ["uv", "run", "basedpyright"],
        outfile=EVIDENCE / "basedpyright.txt",
    )
    failures += _run(
        [
            "uv",
            "run",
            "pytest",
            "--junitxml",
            str(EVIDENCE / "pytest-junit.xml"),
        ],
        outfile=EVIDENCE / "pytest.txt",
    )
    failures += _run(
        ["uv", "run", "python", "scripts/verify_migrations.py"],
        outfile=EVIDENCE / "migrations.txt",
    )
    failures += _run(
        ["uv", "run", "python", "scripts/export_openapi.py"],
        outfile=EVIDENCE / "openapi-export.txt",
    )

    manifest = {
        "collected_at": stamp,
        "git_commit": _git_rev(),
        "alembic_head": "0002_core_stage0_tables",
        "seed_id": "caldris-embervale-v1",
        "hashes": {
            "uv.lock": _sha256(ROOT / "uv.lock"),
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
