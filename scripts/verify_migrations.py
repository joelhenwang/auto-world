"""Verify Alembic migration graph and extension baseline."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = ROOT / "backend" / "alembic.ini"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("ALEMBIC_DATABASE_URL"),
        help="postgresql+psycopg:// URL (or set ALEMBIC_DATABASE_URL)",
    )
    args = parser.parse_args()
    env = dict(os.environ)
    if args.database_url:
        env["ALEMBIC_DATABASE_URL"] = args.database_url

    def alembic(*parts: str) -> str:
        cmd = ["uv", "run", "alembic", "-c", str(ALEMBIC_INI), *parts]
        print("+", " ".join(cmd))
        completed = subprocess.run(
            cmd, check=True, cwd=ROOT, env=env, text=True, capture_output=True
        )
        if completed.stdout.strip():
            print(completed.stdout.strip())
        return completed.stdout

    heads = [line for line in alembic("heads").splitlines() if line.strip()]
    if len(heads) != 1:
        print(f"expected single alembic head, got: {heads}", file=sys.stderr)
        return 1

    alembic("upgrade", "head")
    alembic("downgrade", "-1")
    alembic("upgrade", "head")
    print("verify_migrations: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
