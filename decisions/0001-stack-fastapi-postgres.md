# 0001 — Stack: FastAPI + PostgreSQL + SQLAlchemy/Alembic + uv

- **Date:** 2026-09-09
- **Status:** Accepted

## Context
A self-hostable URL shortener that also serves as a DevOps portfolio piece. It
needs a small JSON API, server-side redirects, click analytics, link expiry, and
a minimal web UI. It should be production-realistic without being heavy.

## Decision
- **Python 3.12 + FastAPI** for the API and the Jinja2-rendered UI. Async
  end-to-end so the redirect path (the hot path) never blocks the event loop.
- **PostgreSQL 16** for storage — one `db` service in compose, a real relational
  store that the Phase 2 analytics queries can lean on.
- **SQLAlchemy 2.0 (async, asyncpg)** as the ORM, **Alembic** for migrations.
- **uv** for dependency management and locking (`pyproject.toml` + `uv.lock`).
- **ruff** for lint + format. No mypy yet.
- Rate limiting via **slowapi**; see [0005](0005-rate-limiting.md).

## Consequences
- The ORM models are kept backend-agnostic (no PG-only column types) so the test
  suite runs against in-memory SQLite and needs no Docker. PostgreSQL-specific
  behaviour lives only in Alembic migrations, exercised against compose.
- `alembic upgrade head` is a deliberate deploy step (a compose `migrate`
  service, later a k8s Job) — the app never auto-migrates on boot.
- Two Python runtimes to keep in step: local (`uv`) and the container
  (`python:3.12-slim`).

## Alternatives considered
- **Node/Express or Go:** both fine; Python/FastAPI chosen for iteration speed
  and because it pairs with the sibling portfolio project's Phase 2 direction.
- **Redis-only store:** great for `code → URL` with native TTL, but a poor fit
  for the per-click analytics rows we want. Postgres covers both.
- **SQLModel over SQLAlchemy** (as the FastAPI skill suggests): its async +
  Alembic story is less mature; plain SQLAlchemy 2.0 typed models are well
  understood and the dedicated review skill targets them.
- **SQLite for everything:** viable for a demo, but Postgres is the realistic
  target and the thing worth showing in a DevOps portfolio.
