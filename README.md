# url-shortener

A small, self-hostable URL shortener — random or custom short codes, click
analytics, link expiry, and a minimal web UI. Built with FastAPI + PostgreSQL,
async end to end, and shipped as a Docker Compose stack.

Built in phases (see [`decisions/0002`](decisions/0002-phased-architecture-and-seams.md)):

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | API + Postgres + redirect + analytics + web UI, in Docker Compose | **current** |
| 2 | Kubernetes manifests, Terraform IaC, GitHub Actions CI | planned |
| 3 | API keys, Redis rate limiting, metrics, backups, management UI | planned |

## Quickstart (Docker)

```bash
cp .env.example .env          # then edit IP_HASH_SALT (and BASE_URL if not localhost)
docker compose up --build     # db → migrate → api
```

- Web UI: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- DB browser (optional): `docker compose --profile tools up adminer` → <http://localhost:8080>

```bash
# create a link
curl -s -X POST localhost:8000/api/links \
  -H 'content-type: application/json' \
  -d '{"url":"https://example.com","alias":"demo","ttl_days":7}'

# follow it (307 → example.com)
curl -i localhost:8000/demo

# stats
curl -s localhost:8000/api/links/demo/stats
```

## Quickstart (local, no Docker)

Needs a reachable PostgreSQL and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/shortener
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The **test suite needs neither Docker nor Postgres** — it runs against in-memory
SQLite:

```bash
uv run pytest -q
uv run ruff check .
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/links` | Body `{url, alias?, ttl_days? \| expires_at?}` → `201` with `{code, short_url, target_url, created_at, expires_at}`. Rate-limited per IP. |
| `GET` | `/api/links/{code}` | Link metadata. |
| `GET` | `/api/links/{code}/stats` | `{total_clicks, clicks_by_day[], recent_clicks[], ...}`. |
| `GET` | `/{code}` | `307` redirect to the target. `404` if unknown, `410` if expired. |
| `GET` | `/healthz` | `200` when the DB is reachable, else `503`. |

Errors: `422` invalid URL or alias, `409` alias already taken, `429` rate limited.

## How it fits together

```
GET /{code}  ──►  look up code  ──►  307 Location: <target>
                       │                     └─ BackgroundTask: insert click row,
                       │                        bump links.click_count
                       └─ expired? ─► 410 Gone
```

- **307, not 301**, so redirects aren't cached and analytics/expiry keep working
  ([`decisions/0004`](decisions/0004-redirect-semantics-and-analytics.md)).
- Short codes are base62, length 7, with a retry-on-collision loop; custom
  aliases are validated and checked against a reserved set
  ([`decisions/0003`](decisions/0003-short-code-generation.md)).
- Visitor IPs are stored only as a salted SHA-256 hash.
- Migrations are a deploy step (`migrate` service), never run on app boot.

## Layout

See [`CLAUDE.md`](CLAUDE.md) for the full file-by-file tour and
[`tasks.md`](tasks.md) for the phased task tracker.

## License

MIT — see [`LICENSE`](LICENSE).
