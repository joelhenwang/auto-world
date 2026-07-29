# Thin aliases — underlying commands remain the source of truth (handbook 20 §7).

.PHONY: help bootstrap sync test lint format typecheck check compose-config compose-up compose-down migrate seed export-schemas export-db-schema export-openapi api world-cli stage0-gate pre-commit verify-migrations

help:
	@echo "Stage 0 aliases:"
	@echo "  make sync / test / lint / format / typecheck / check"
	@echo "  make export-schemas / export-db-schema / export-openapi / verify-migrations / migrate"
	@echo "  make api / world-cli / seed / stage0-gate / compose-up / compose-down / bootstrap"

sync:
	uv sync

bootstrap: sync compose-up
	@echo "Run: make migrate (seed arrives with S0-CONTENT-001)"

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

typecheck:
	uv run basedpyright

check: format lint typecheck

export-schemas:
	uv run python scripts/generate_json_schemas.py

export-db-schema:
	uv run python scripts/export_database_schema.py

verify-migrations:
	uv run python scripts/verify_migrations.py

pre-commit:
	uv run pre-commit run --all-files

compose-config:
	docker compose config

compose-up:
	docker compose up -d postgres

compose-down:
	docker compose down

migrate:
	uv run alembic -c backend/alembic.ini upgrade head

seed:
	uv run python scripts/seed_world.py

export-openapi:
	uv run python scripts/export_openapi.py

api:
	uv run uvicorn fictional_world.interfaces.http.app:app --host 127.0.0.1 --port 8000

world-cli:
	uv run python scripts/world_cli.py $(ARGS)

stage0-gate:
	uv run python scripts/run_stage0_gate.py
