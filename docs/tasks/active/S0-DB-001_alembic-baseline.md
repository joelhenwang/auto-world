# `S0-DB-001` — Database/Alembic baseline

**Stage:** 0 | **Workstream:** DB | **Status:** IN_PROGRESS | **Priority:** P0  
**Owner:** parent agent | **Branch:** `cursor/s0-db001-sim001-model001-09ce`  
**Upstream:** `04cabec` | **Depends:** S0-DOM-001

## Objective
Async engine/session, naming convention, Alembic env, vector+pgcrypto extension migration, verify script.

## Writable
`backend/alembic.ini`, `backend/migrations/**`, `backend/src/fictional_world/infrastructure/database/**`, `scripts/verify_migrations.py`, `backend/tests/integration/test_migrations*`, `pyproject.toml` (SQLAlchemy/Alembic/psycopg)

## Non-goals
S0-DB-002 domain tables/ORM; repositories/UoW.

## Tests
Empty upgrade; vector extension; single Alembic head; verify script.
