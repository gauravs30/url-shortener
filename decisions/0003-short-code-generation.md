# 0003 — Short-code generation and custom-alias rules

- **Date:** 2026-09-09
- **Status:** Accepted

## Context
Every link needs a short, URL-safe code. Users may also supply their own alias.
Codes share the root path namespace with real routes (`/api`, `/healthz`, ...).

## Decision
- **Random codes:** base62 (`[0-9A-Za-z]`), default length 7 (`SHORT_CODE_LENGTH`),
  drawn from `secrets.choice`. Keyspace ≈ 62⁷ ≈ 3.5 × 10¹².
- **Collision handling:** generate → check the unique index → retry up to 5
  times, then return `503`. At Phase 1 scale collisions are astronomically rare;
  the retry is cheap insurance.
- **Custom aliases:** must match `^[A-Za-z0-9_-]{3,32}$` and not be in a reserved
  set (`api`, `healthz`, `static`, `docs`, `redoc`, `openapi.json`, `admin`,
  `favicon.ico`). Invalid → `422`; already taken → `409`.
- `code` column is `String(32)`, unique + indexed — covers both the redirect
  lookup and the "is this code free?" check.

## Consequences
- Random and custom codes live in the same column and namespace; one lookup path.
- Reserved set must be kept in sync with real root-level routes. The path regex
  on `/{code}` also refuses anything outside the alias charset, so `/static/...`
  etc. never reach the redirect handler.
- Codes are case-sensitive (base62). Acceptable for a copy-paste tool.

## Alternatives considered
- **Auto-increment ID → base62 encode:** shorter early codes, but leaks how many
  links exist and makes enumeration trivial.
- **Hashids / sqids:** nice, but an extra dependency for no real gain here.
- **UUID:** far too long for a "short" link.
