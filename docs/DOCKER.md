# Docker Runbook

Operator-facing guide for the container stack defined by the root
`docker-compose.yml` and its overlays. This project is designed for a single
machine (Windows host + Docker Desktop/WSL2); the runbook stays inside that
scope unless you request more.

## Quick reference

| Action | Command |
|---|---|
| Build all images | `pwsh scripts/docker-build.ps1` |
| Build one service | `pwsh scripts/docker-build.ps1 mail-service` |
| Start dev stack | `cp .env.example .env` then `pwsh scripts/docker-up.ps1` |
| Start prod stack | `docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d` |
| Status + healthchecks | `pwsh scripts/docker-status.ps1` |
| Tail logs | `pwsh scripts/docker-logs.ps1 200 mail-service` |
| Stop stack | `pwsh scripts/docker-down.ps1` |
| Stop + drop Postgres volume | `pwsh -Command "$env:PRUNE_VOLUMES='1'; & scripts/docker-down.ps1"` |
| Validate compose file | `docker compose -f docker-compose.yml config` |
| GUI debug registrar (Windows host) | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up registrar` |

Profiles:

- `COMPOSE_PROFILES=prod` adds `docker-compose.prod.yml` (image-based, no host ports).
- `COMPOSE_PROFILES=staging` adds `docker-compose.staging.yml`.
- `docker-compose.observability.yml` is appended automatically if present.

## Architecture

- **Postgres** 16 Alpine, named volume `postgres_data`.
- **Traefik** v3.0 reverse proxy. Dashboard on `127.0.0.1:8080` in dev only.
- **Registrar** `:8709` — account creation / browser automation / API gateway.
- **Mail-service** `:8701` — mail provider/orchestration.
- **aa-proxy** `:8702` — ArtificialAnalysis proxy + image lab.
- **tts-proxy** `:8700` — Gemini TTS proxy, reads 9router DB from host.
- **web-ui** — static SPA served by nginx on internal port `8080`; Traefik routes `/` to it.

All services connect to Postgres via the isolated `postgres-internal` bridge.
Dev DSN defaults to `postgresql+asyncpg://ccs:ccs_dev_only@postgres:5432/account_creator`.

## Central logging

The observability overlay (`docker-compose.observability.yml`) ships a
Grafana Loki + Alloy pipeline alongside the existing Prometheus + Grafana:

- **Alloy** (`grafana/alloy:v1.17.1`) collects every container's stdout over
  the Docker socket (`/var/run/docker.sock`) — NOT a `/var/lib/docker/containers`
  bind mount, which is unreachable on Docker Desktop/WSL2 (the daemon lives in
  the `docker-desktop` VM). Labels emitted: `service`, `container`, `project`
  (low cardinality only).
- **Loki** (`grafana/loki:3.5.1`) stores logs on the `loki_data` volume,
  filesystem backend, 14-day retention.

No Python changes were needed: `common/logging/structured.py` `JSONFormatter`
already emits JSON with `service`, `request_id`, `trace_id`, `span_id` (set per
request via `RequestIDMiddleware` + contextvars).

**`request_id` is a parsed field, never a Loki label** — labeling it would
explode the index (one stream per request). Query it at read time:

```logql
# all logs for one request across all services
{project="account-creation"} |= "abc-123" | json | request_id="abc-123"
# one service, last errors
{service="registrar"} | json | level="ERROR"
```

Query in Grafana (`http://localhost:3000` → Explore → Loki). Start only the
logging stack: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d loki alloy grafana`.

## Scope & decisions (local = prod)

This stack is **single-machine, single-user, private-repo**. The local Windows
host IS the production environment; there is no separate deploy target, no
multi-node clustering, no cross-machine secret distribution. Therefore:

- `.env` is intentionally tracked — it holds dev/local placeholder values and
  serves as the single source of runtime truth for the owner. No SOPS/age flow
  is wired for runtime env (the SOPS key is for `config/*/secrets.yaml` only).
- No TLS/HTTPS terminator, no ACME, no dashboard auth — Traefik serves plain
  HTTP on `:80` reachable only from the host. Do not add network-isolation
  overhead that only matters for multi-tenant or multi-node setups.
- Rate limits exist to protect expensive registration endpoints, not for
  multi-tenant fairness; tune them to local single-user load, not prod scale.

### Schema ownership

Flyway owns the relational schema. Migrations live in `migrations/sql/` and run
as a one-shot container before app services start (`scripts/docker-up.ps1`
phase 2 / `docker-compose.migrations.yml`):

- `V001__platform_bootstrap.sql` — `platform` helper schema (baseline).
- `V002__tts_rpd.sql` — `tts.gemini_key_rpd` for the TTS key-rotation RPD tracker.
- `V003__core_schema.sql` — `accounts`, per-service extension tables (CTI:
  gmail, artificialanalysis, openrouter, elevenlabs, ollama, testmail,
  cloudflare, mailosaur), `mail_providers`, `provider_domain_tags`, `services`,
  `mailbox_service_blocks`, with PK/FK/UNIQUE/indexes. All `IF NOT EXISTS` so
  re-runs and existing-DB upgrades are safe.

The legacy `init_db()` / `create_all()` path in `common/database/_migrations.py`
is **SQLite-only** (test fixtures + debug scripts). Runtime services call
`init_async_db()`, which creates only the async engine/session factory — it does
not create schema. A fresh Postgres must run Flyway first; `docker-up.ps1` does
this automatically. Do not re-introduce `create_all()` against Postgres.

## Dockerfile design

Every Python service uses a 2-stage build:

1. **Builder** stage installs `build-essential` and `gcc`, installs the shared
   `common/` package, then installs the service package from its own
   `pyproject.toml`. This makes the Dockerfiles single-source-of-truth
   (PyPI dependencies are no longer duplicated by hand).
2. **Runtime** stage is a bare `python:3.12-slim` with a non-root `app`
   user (uid/gid 1001, home `/app`). Browser OS deps are installed with
   `playwright install-deps chromium`; `/tmp` is on tmpfs; healthchecks hit
   `/api/health` (or `/api/v1/health` for registrar).

The `web-ui` image uses a separate Node builder + `nginx:alpine` runtime.
Nginx master and worker run as the unprivileged `nginx` user and listen on
port 8080; Traefik forwards public port 80 to `web-ui:8080`.

## Playwright / Camoufox browser cache

- Playwright Chromium is pre-downloaded in the `builder` stage and copied to
  `/app/.cache/ms-playwright` in the runtime image.
- Camoufox/Firefox binaries are **not** bundled by default (they are large and
  distributed via GitHub releases, which can be rate-limited). In dev, the
  host Camoufox cache is bind-mounted read-only into the container:
  `${LOCALAPPDATA_POSIX}/camoufox:/app/.cache/camoufox:ro`.
  The container reads the same cache the host Python installation uses.
- For CI / prod builds, pass the `CAMOUFOX_CACHE_PATH` build argument pointing
  to a host directory containing a pre-populated Camoufox cache.

## GUI debug for registrar (dev only)

The base compose forces `CAMOUFOX_HEADLESS=1`. The dev overlay overrides it to
`0`, mounts the host X11 socket, and sets `DISPLAY=host.docker.internal:0`.
To see the browser window:

1. Install/start an X server on the Windows host (VcXsrv, MobaXterm, GWSL).
2. Allow connections from `host.docker.internal`/WSL2 subnet.
3. Run:
   ```powershell
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up registrar
   ```

## Compose hardening

| Concern | Mitigation |
|---|---|
| Container escape | `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]` |
| Disk exhaustion | `mem_limit`, `pids_limit` per service |
| Log rotation | json-file driver, 20 MB x 5 files per service |
| Writable /tmp | `tmpfs` on every service that runs code |
| DB isolation | `postgres-internal` network has `internal: true` |
| Health-gated startup | `depends_on: { postgres: { condition: service_healthy } }` |
| Host exposure | All app ports bound to `127.0.0.1`; Traefik dashboard bound to `127.0.0.1:8080` in dev only |
| Postgres data | Docker named volume; never bind-mount the data dir on Windows |

## Migrations

`docker-compose.migrations.yml` runs Flyway as a one-shot job before app
services start. The app services still call SQLAlchemy `create_all()` on boot
for application tables.

```powershell
pwsh scripts/docker-up.ps1   # migrations run automatically
```

## Secrets

- `INTERNAL_API_KEY`, `DB_PASSWORD`, and real credentials live in `.env` or
  `.env.{prod,staging}` and are never committed. See `.env.example`.
- `config/sops-age-key.txt` is git-ignored and never copied into any image.
- Rotate secrets by recreating affected services:
  `docker compose up -d --force-recreate <service>`.

## Troubleshooting

| Symptom | First check |
|---|---|
| `postgres` not healthy | `docker logs postgres --tail 200` — usually wrong creds or volume perms |
| Service restart loop | mismatched `DATABASE_URL`; `docker compose exec <svc> env \| grep DATABASE_URL` |
| Browser automation fails | Camoufox cache missing or wrong `CAMOUFOX_HEADLESS` value |
| Registrar stuck at `health: starting` | healthcheck path is `/api/v1/health` |
| Traefik 404 on `/api/*` | router file not reloaded; check `docker compose logs traefik` |
| Web UI blank routes | nginx SPA fallback serves `index.html`; check browser dev tools |
| Stale build cache | `NO_CACHE=1 pwsh scripts/docker-build.ps1 <service>` |