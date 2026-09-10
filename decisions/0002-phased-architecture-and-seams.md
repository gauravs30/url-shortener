# 0002 — Phased architecture and where the seams are

- **Date:** 2026-09-09
- **Status:** Accepted

## Context
Phase 1 is a working service in Docker. Phase 2 adds a Kubernetes deployment,
Terraform IaC, and CI. Phase 3 is hardening. Phase 1 code should absorb that
without a rewrite, so the seams are placed now.

## Decision
Three phases, with explicit seams so later phases are additive:

| Seam | Phase 1 state | Phase 2 change |
|------|---------------|----------------|
| `GET /healthz` (`app/routes/health.py`) | compose `healthcheck` | k8s liveness + readiness probes |
| `migrate` compose service | one-shot `alembic upgrade head` container | k8s `Job` / init container |
| Rate limiter (`app/limiter.py`) | in-memory, per-process | swap slowapi storage for Redis; add `redis` service |
| Config (`app/config.py`) | `.env` → `env_file` in compose | `ConfigMap` + `Secret` with the same keys |
| `BASE_URL` | `http://localhost:8000` | the Ingress host |
| `X-Forwarded-For` handling (`app/routes/redirect.py`) | trusted as-is (single hop) | trust only the ingress/proxy hop |
| Image build | `docker compose build` | CI builds + pushes a tagged image; k8s pulls it |
| Alembic index creation | non-concurrent (empty tables) | any index on a populated table uses `postgresql_concurrently=True` in an autocommit block (see the sqlalchemy-alembic skill's `only-concurrent-indexes`) |

**Phase 2** — `k8s/` (Deployment, Service, Ingress, HPA for `api`; StatefulSet +
PVC + Secret for Postgres; migration Job), `infra/` (Terraform), and
`.github/workflows/ci.yml` (ruff + pytest + build).

**Phase 3** — API keys for create/delete, Redis-backed limits, structured
logging + a `/metrics` endpoint, `pg_dump` backups, a link-management UI.

## Consequences
- The redirect handler and the JSON API share one `get_link_by_code` path.
- nginx/ingress terminates in front of the API on one origin → no CORS.
- Phase boundaries tracked in `tasks.md` (U1-/U2-/U3-).

## Alternatives considered
- **Build k8s/CI now, unused:** premature; more surface with no current payoff.
- **Skip compose, go straight to k8s:** loses the fast local loop and makes the
  "runs anywhere with Docker" story worse.
