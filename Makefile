# Convenience targets. All the real commands are plain `uv` / `docker compose`
# calls, documented in README.md for anyone without `make`.

.PHONY: install dev test lint fmt migrate revision up down logs

install:
	uv sync

dev:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -q

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

migrate:
	uv run alembic upgrade head

# make revision m="add foo"
revision:
	uv run alembic revision --autogenerate -m "$(m)"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api
