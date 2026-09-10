# URL Shortener — Task Tracker

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[-]` dropped
**Current phase: Phase 1 — Working service (Docker + compose)**

Related: [`decisions/`](decisions/) for the *why* behind each choice.

---

## Phase 1 — Working service

### Scaffold
- [x] U1-1  Repo layout, `pyproject.toml` + `uv.lock` (uv, ruff config, pytest config)
- [x] U1-2  `CLAUDE.md`, `README.md`, `tasks.md`, `decisions/` (README + ADRs 0001–0005)
- [x] U1-3  `.gitignore`, `.dockerignore`, `.env.example`, `Makefile`

### Application
- [x] U1-4  `config.py` — pydantic-settings `Settings`
- [x] U1-5  `database.py` — lazy async engine + `SessionDep`
- [x] U1-6  `models.py` — `Link`, `Click` (backend-agnostic)
- [x] U1-7  `shortcode.py` — base62 generation + alias validation
- [x] U1-8  `crud.py` — create/lookup/record-click/stats
- [x] U1-9  `routes/health.py` — `GET /healthz` (SELECT 1)
- [x] U1-10 `routes/links.py` — `POST /api/links`, `GET /api/links/{code}`, `.../stats`
- [x] U1-11 `routes/redirect.py` — `GET /{code}` → 307 + background click log, 404/410
- [x] U1-12 `limiter.py` + wire slowapi into `main.py` (429 handler)
- [x] U1-13 `main.py` — app, lifespan, router order, `/` UI route, `/static` mount

### Web UI
- [x] U1-14 `templates/index.html` — create form + result + copy button
- [x] U1-15 `static/style.css` — responsive, light/dark, focus-visible
- [x] U1-15a fix: `<output id="result">` defaults to `display:inline` (ignores
        `margin-top`), so the result box overlapped the Shorten button —
        forced `display:block` on `.result, .error`.

### Migrations
- [x] U1-16 Alembic scaffold (`alembic.ini`, async `env.py`, `script.py.mako`)
- [x] U1-17 `versions/0001_initial.py` — `links` + `clicks` + indexes
- [ ] U1-18 Run `alembic upgrade head` against real Postgres (needs Docker) and confirm schema

### Tests
- [x] U1-19 `tests/conftest.py` — SQLite engine + `AsyncClient` fixtures, limiter reset
- [x] U1-20 `test_shortcode.py` — length, alphabet, alias regex, reserved words
- [x] U1-21 `test_links_api.py` — create (random/custom), 409, 422, TTL, rate limit
- [x] U1-22 `test_redirect.py` — 307, 404, 410, click recorded, stats endpoint
- All 31 tests passing; `ruff check` clean.

### Docker
- [x] U1-23 `docker/Dockerfile` — multi-stage uv build, non-root, HEALTHCHECK
- [x] U1-24 `docker-compose.yml` — `db` + `migrate` + `api` (+ `adminer` profile)
- [ ] U1-25 `docker compose up --build` — **Docker not installed on this machine.**
        Verify once Docker Desktop is available: create a link, follow it (307),
        check `/api/links/{code}/stats`, open the UI, confirm a past `expires_at` → 410.

### Wrap-up
- [ ] U1-26 `git init` + first commit
- [ ] U1-27 (optional) Reuse the portfolio's PostToolUse code-review hook in `.claude/`
- [ ] U1-28 (optional) Update workspace `ClaudeCode/CLAUDE.md` to name this project too

---

## Phase 2 — Kubernetes + IaC + CI  *(not started)*

- [ ] U2-1  `k8s/`: Deployment + Service + HPA for `api`
- [ ] U2-2  `k8s/`: Postgres StatefulSet + PVC + Secret
- [ ] U2-3  `k8s/`: migration `Job` (replaces the compose `migrate` service)
- [ ] U2-4  `k8s/`: Ingress; set `BASE_URL` to the ingress host
- [ ] U2-5  ConfigMap + Secret from the `.env` keys
- [ ] U2-6  `redis` service + point slowapi storage at it (fixes multi-replica limits)
- [ ] U2-7  Trust only the ingress hop for `X-Forwarded-For`
- [ ] U2-8  `infra/` — Terraform (cluster / namespace / DB, target TBD)
- [ ] U2-9  `.github/workflows/ci.yml` — ruff + pytest + docker build
- [ ] U2-10 CI pushes a tagged image; k8s pulls it

---

## Phase 3 — Hardening  *(not started)*

- [ ] U3-1  API keys for `POST`/`DELETE` link operations
- [ ] U3-2  `DELETE /api/links/{code}`
- [ ] U3-3  Redis-backed rate limiting confirmed across replicas
- [ ] U3-4  Structured logging + `/metrics` (Prometheus)
- [ ] U3-5  `pg_dump` backup CronJob
- [ ] U3-6  Link-management UI (list, edit expiry, delete)
- [ ] U3-7  `clicks_by_day` pushed into SQL / a rollup table
