# 0005 — In-memory per-IP rate limiting for Phase 1

- **Date:** 2026-09-09
- **Status:** Accepted (interim)

## Context
Link creation (`POST /api/links`) is open — no auth. Without a limit, one client
can fill the table. Redirects and reads stay unlimited.

## Decision
Use **slowapi** with the default in-memory storage, keyed by client IP
(`get_remote_address`). The limit is a config string, `RATE_LIMIT`, default
`20/minute`. Only `POST /api/links` is decorated.

## Consequences
- In-memory state is **per process**: with more than one `api` replica the
  effective limit is `N × RATE_LIMIT`, and it resets on restart.
- Fine for Phase 1 (single container). Phase 2 runs one replica until this is
  fixed; Phase 3 swaps slowapi's storage for Redis so the limit is global — see
  [0002](0002-phased-architecture-and-seams.md).
- The limiter instance lives in `app/limiter.py` so both the route and the tests
  import the same object (tests reset it between cases).

## Alternatives considered
- **Redis-backed now:** correct, but adds a service and a dependency before it
  earns its keep.
- **Nginx/ingress `limit_req`:** a good complementary layer, added with the
  ingress in Phase 2; doesn't remove the need for an app-level limit in dev.
- **No limit until auth exists:** leaves the open endpoint trivially abusable.
