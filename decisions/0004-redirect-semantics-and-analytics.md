# 0004 — 307 redirects + fire-and-forget click logging

- **Date:** 2026-09-09
- **Status:** Accepted

## Context
`GET /{code}` is the hot path. It must send the visitor onward fast, record a
click for analytics, and respect expiry.

## Decision
- **Status 307 (Temporary Redirect), not 301.** A 301 is cached by browsers and
  intermediaries, so subsequent visits never hit the server — which would break
  click counts and make expiry invisible to anyone who visited once.
- **Click logging runs in a Starlette `BackgroundTask`** attached to the redirect
  response: the visitor gets the `Location` header immediately, and the `clicks`
  row + `links.click_count` bump happen after the response is flushed, in their
  own DB session.
- **Expiry:** `expires_at` is nullable. If set and `now >= expires_at`, return
  `410 Gone` (not 404 — the link existed, it's just done).
- **Stored per click:** timestamp, `Referer`, `User-Agent`, and a salted
  SHA-256 of the client IP (`IP_HASH_SALT`). The raw IP is never persisted.
- `click_count` is denormalised onto `links` so the common "how many hits?"
  answer is one row, not an aggregate over `clicks`.

## Consequences
- A crash between sending the redirect and committing the click loses that one
  click. Acceptable — analytics here are best-effort, not billing.
- `clicks_by_day` is computed in Python from fetched rows (portable across
  SQLite/Postgres, fine at Phase 1 volume). Phase 2 can push it into SQL / a
  rollup table if the `clicks` table grows.
- Behind a proxy, `X-Forwarded-For` is trusted as-is for now — revisited in
  [0002](0002-phased-architecture-and-seams.md) when an ingress is in front.

## Alternatives considered
- **302:** similar effect to 307 but does not guarantee the method is preserved;
  307 is the precise "same request, new location" signal even though these are
  all GETs.
- **Synchronous click write before redirecting:** adds a DB round-trip to every
  redirect for data nobody is waiting on.
- **Queue/beacon to a separate collector:** the Phase 2/3 answer if volume
  warrants it; overkill now.
