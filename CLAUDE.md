# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Overview

Self-hostable URL shortener, built in phases:

- **Phase 1 (current):** FastAPI + PostgreSQL, async end-to-end, in Docker
  Compose. Random or custom short codes, click analytics, link expiry, a minimal
  Jinja2 web UI. Link creation is open (no auth) with a per-IP rate limit.
- **Phase 2 (planned):** Kubernetes manifests, Terraform IaC, GitHub Actions CI.
- **Phase 3 (planned):** API keys, Redis-backed rate limiting, structured
  logging + `/metrics`, DB backups, link-management UI.

Phase 1 has deliberate seams so later phases are additive — see `decisions/0002`.

## Layout

- `app/` — the FastAPI application.
  - `main.py` — app object, lifespan, router wiring. The `/{code}` catch-all is
    registered **last** so it never shadows `/api`, `/healthz`, `/static`, `/`.
  - `config.py` — `Settings` (pydantic-settings). **The Phase 2 config seam.**
  - `database.py` — lazy async engine + `SessionDep`.
  - `models.py` — `Link`, `Click`. **Kept backend-agnostic** (no PG-only types)
    so tests run on SQLite.
  - `shortcode.py` — base62 generation + alias validation (`decisions/0003`).
  - `crud.py` — all DB operations; routes stay thin.
  - `limiter.py` — shared slowapi limiter (`decisions/0005`).
  - `routes/` — `health.py`, `links.py`, `redirect.py`.
  - `templates/index.html`, `static/style.css` — the web UI, no build step.
- `alembic/` — migrations. `versions/0001_initial.py` creates `links` + `clicks`.
  The app never auto-migrates; `alembic upgrade head` is a deploy step.
- `tests/` — pytest, runs against in-memory SQLite (no Docker needed).
- `docker/Dockerfile` — multi-stage (uv → `python:3.12-slim`, non-root).
- `docker-compose.yml` — `db` + one-shot `migrate` + `api` (+ `adminer` under the
  `tools` profile).
- `decisions/` — ADR-lite records; `README.md` there has the index + template.
- `tasks.md` — phased task tracker (U1-/U2-/U3- IDs). Keep it updated.
- `.env` — git-ignored. Template: `.env.example`.

## Common commands

```bash
uv sync                       # install deps
uv run pytest -q              # tests (SQLite, no Docker)
uv run ruff check . && uv run ruff format .
uv run uvicorn app.main:app --reload   # local dev (needs a reachable Postgres)
uv run alembic upgrade head   # apply migrations
uv run alembic revision --autogenerate -m "msg"
docker compose up --build     # full stack: API at :8000
```

`make <target>` wraps these (see `Makefile`) for anyone with `make`.

## Conventions

- Ask for permission before creating new folders.
- Record non-obvious decisions as a new file in `decisions/` (next number,
  ADR-lite template) and add it to that folder's `README.md` index.
- Update `tasks.md` when task status changes.
- Keep `app/models.py` backend-agnostic. PostgreSQL-specific concerns
  (concurrent index creation, etc.) belong in Alembic migrations only — see the
  `sqlalchemy-alembic-expert-best-practices-code-review` skill.
- New root-level routes must be added to the reserved-alias set in
  `app/shortcode.py`.
- Every schema change gets an Alembic migration; never edit an applied one.

## Environment notes

- Docker is **not currently installed** on this machine. Tests and lint run
  without it (`uv run pytest`). `docker compose up --build` is the intended path
  once Docker Desktop is available — that is the only way to exercise the Alembic
  migrations and the Postgres-backed integration path end to end.
