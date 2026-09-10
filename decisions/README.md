# Decision Records

Lightweight ADRs. One file per decision so we can reload just the relevant
context later instead of re-reading the whole project.

## Naming

`NNNN-short-kebab-title.md` — `NNNN` is a zero-padded running number.

## Template

```markdown
# NNNN — Title

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded by NNNN | Deprecated

## Context
What forces are at play — the problem, constraints, requirements.

## Decision
What we chose to do.

## Consequences
What becomes easier, what becomes harder, follow-ups this creates.

## Alternatives considered
Options we rejected and why.
```

## Index

| # | Title | Status |
|---|-------|--------|
| [0001](0001-stack-fastapi-postgres.md) | Stack: FastAPI + PostgreSQL + SQLAlchemy/Alembic + uv | Accepted |
| [0002](0002-phased-architecture-and-seams.md) | Phased architecture and where the seams are | Accepted |
| [0003](0003-short-code-generation.md) | Short-code generation and custom-alias rules | Accepted |
| [0004](0004-redirect-semantics-and-analytics.md) | 307 redirects + fire-and-forget click logging | Accepted |
| [0005](0005-rate-limiting.md) | In-memory per-IP rate limiting for Phase 1 | Accepted (interim) |
