# Docker Runbook

Operator-facing guide for the platform container stack defined by the root
`docker-compose.yml` and its overlays. Keep this file in sync with
`docker-compose.yml` whenever a service, port, or volume changes.

## Quick reference

| Action | Command |
|---|---|
| Build all images | `pwsh scripts/docker-build.ps1` |
| Build one service | `pwsh scripts/docker-build.ps1 mail-service` |
| Start stack | `pwsh scripts/docker-up.ps1` |
| Status + healthchecks | `pwsh scripts/docker-status.ps1` |
| Tail logs | `pwsh scripts/docker-logs.ps1 200 mail-service` |
| Stop stack | `pwsh scripts/docker-down.ps1` |
| Stop + drop Postgres volume | `pwsh -Command "$env:PRUNE_VOLUMES='1'; & scripts/docker-down.ps1"` |
| Validate compose file | `docker compose -f docker-compose.yml config` |

Profiles:

- `COMPOSE_PROFILES=prod` adds `docker-compose.prod.yml` (image-based, no host ports).
- `COMPOSE_PROFILES=staging` adds `docker-compose.staging.yml`.
- `docker-compose.observability.yml` is appended automatically if present.

## Architecture

- **Postgres** (`ccs-postgres`, image `postgres:16-alpine`, volume `account-creation_postgres_data`).
- **Traefik** v3.0 reverse proxy. Dashboard on `127.0.0.1:8080` (dev) / closed in prod.
- **Registrar** `:8709` — account creation, browser automation. Mounts `registrar/{data,logs,debug,screenshots,config}` as bind mounts.
- **Mail-service** `:8701` — mail provider/orchestration. Mounts `mail-service/{logs,data,config}`.
- **aa-proxy** `:8702` — ArtificalAnalysis proxy + Image Lab. Mounts `aa-proxy/{logs,config}`.
- **tts-proxy** `:8700` — TTS proxy. Mounts `tts-proxy/{logs,config}`.

All services connect to Postgres via the shared `account-net` bridge network
using `DATABASE_URL=postgresql+asyncpg://ccs:ccs_dev_only@postgres:5432/account_creator`.

## Dockerfile design

Each service uses a 2-stage build (`builder` + `runtime`):

1. **Builder** stage (`python:3.12-slim`): installs `build-essential`, copies
   `pyproject.toml` + `common/src`, resolves dependencies into a deterministic
   layer, then copies service source. Build deps are discarded after this stage.
2. **Runtime** stage: bare `python:3.12-slim` with a non-root `app` user
   (uid/gid 1001), browser system deps inlined for services that need Playwright
   (registrar, mail-service, aa-proxy), `/app/{data,logs,debug,screenshots}`
   writable, `/tmp` on tmpfs, and `HEALTHCHECK` against `/api/health`.

Image size targets observed on 2026-06-03:

| Service | Old | New | Why |
|---|---:|---:|---|
| registrar | 2.4 GB | 1.85 GB | builder stage discarded, `playwright install --with-deps` replaced by pre-baked system deps |
| aa-proxy | 2.16 GB | 1.7 GB | same |
| mail-service | 2.01 GB | 1.67 GB | same |

tts-proxy has no browser, image ≈ 1.1 GB.

## Compose hardening

| Concern | Mitigation |
|---|---|
| Container escape | `security_opt: [no-new-privileges:true]`, `cap_drop: [ALL]` (only the caps each service needs are added back) |
| Disk exhaustion | `mem_limit`, `pids_limit` per service |
| Log rotation | json-file driver, 20 MB × 5 files per service |
| Writable /tmp | `tmpfs: [/tmp:size=…m,mode=1777]` on every service that runs code |
| Orphan containers | `docker compose up --remove-orphans` |
| Health-gated startup | `depends_on: { postgres: { condition: service_healthy } }`; per-service `healthcheck:` |
| Host exposure | All app ports bound to `127.0.0.1`. Traefik dashboard bound to `127.0.0.1:8080` in dev, closed in prod via overlay |
| Postgres data | Docker named volume `account-creation_postgres_data`. Never bind-mount the data dir on Windows (WAL+filesystem performance) |

## Service env

All env in compose uses the `${VAR:?VAR required}` mandatory form for prod/staging
overlays to fail loudly on missing config. The dev compose hardcodes
`ccs:ccs_dev_only` to match the local Postgres init. The dev password is intentionally different from any production credential so a leaked compose file never matches a real password.

Required env for prod/staging:

```
DB_USER, DB_PASSWORD, DB_NAME
DATABASE_URL
INTERNAL_API_KEY
REGISTRAR_IMAGE, MAIL_SERVICE_IMAGE, AA_PROXY_IMAGE, TTS_PROXY_IMAGE
```

## Bring-up procedure

```bash
# 1. Validate compose
docker compose -f docker-compose.yml config

# 2. Build
pwsh scripts/docker-build.ps1

# 3. Up + wait for healthchecks
pwsh scripts/docker-up.ps1

# 4. Smoke
pwsh scripts/smoke-runtime-contract.ps1
pwsh scripts/smoke-traefik-routes.ps1
```

If a service does not become healthy within 120 s, inspect with
`pwsh scripts/docker-logs.ps1 500 <service>` and `docker compose ps`.

## Teardown

```bash
pwsh scripts/docker-down.ps1                 # keep volumes
$env:PRUNE_VOLUMES=1; pwsh scripts/docker-down.ps1   # also drop Postgres
```

`down` is preferred over `kill`: it sends `SIGTERM` and waits the configured
grace period (default 10 s) before `SIGKILL`. Healthchecks go `unhealthy` →
service is restarted by `restart: unless-stopped` policy unless explicitly stopped.

## Performance (Windows host)

Bind-mounts on Windows host (Docker Desktop + WSL2) are **dramatically slower**
than Linux native volumes, because every file operation crosses the 9P
filesystem boundary.

Mitigations already in `docker-compose.yml`:

| Path | Mount | Why |
|---|---|---|
| `postgres_data` (Postgres) | named volume | Hot WAL writes; bind-mount would kill throughput |
| `registrar-data` (`/app/data` in registrar) | named volume | Screenshots / browser cache write a lot |
| `mail-service-data` (`/app/data` in mail-service) | named volume | Same reason |
| `*/logs`, `*/config`, `*/debug`, `*/screenshots` | bind-mount | Read-mostly or low-volume; easier to inspect from host |
| `traefik/traefik.yml` | bind-mount :ro | Operator must be able to edit on host |

If you ever see a container stalling on disk I/O, suspect a bind-mount first.
Convert it to a named volume and you will almost certainly see a 5-20×
improvement on Windows.

For real production on Windows, run the stack on a Linux VM or remote host.
Windows Desktop is fine for dev but never deploy from it.

## Backup & restore

Postgres data lives in the `account-creation_postgres_data` named volume. Two
backup paths:

1. **Logical backup (preferred)**: `pg_dump` from inside the running container.
   ```bash
   docker exec ccs-postgres pg_dump -U ccs -d account_creator \
     --format=custom --file=/tmp/backup-$(date +%F).dump
   docker cp ccs-postgres:/tmp/backup-YYYY-MM-DD.dump ./backups/
   ```
   Restore:
   ```bash
   docker cp ./backups/backup-YYYY-MM-DD.dump ccs-postgres:/tmp/
   docker exec ccs-postgres pg_restore -U ccs -d account_creator \
     --clean --if-exists /tmp/backup-YYYY-MM-DD.dump
   ```

2. **Volume snapshot** (offline): stop the stack, then
   `docker run --rm -v account-creation_postgres_data:/from -v $PWD:/to alpine \
   tar czf /to/postgres-data.tgz -C /from .`. Only use when the cluster is
   stopped.

Service-level bind mounts (`registrar/data`, `mail-service/data`, …) contain
the SQLite mirrors used by the desktop UI. They are excluded from
`.dockerignore` and are the operator's responsibility to back up. The
`scripts/import_legacy_sqlite_to_postgres.py` script goes the other direction
(Postgres → SQLite mirror) for offline use.

## Scaling

- Vertical: bump `mem_limit` / `pids_limit` in the matching service block.
  `registrar` is the only service that benefits from a memory bump (browser
  tabs); `tts-proxy` is the cheapest.
- Horizontal: not supported by `docker-compose` v2 — service images are
  stateful (Postgres, bind mounts). Use Docker Swarm / Kubernetes for horizontal
  scale, or split registrar into a worker pool behind an internal queue.

## Rollback

1. `pwsh scripts/docker-down.ps1`
2. Restore previous image tag in `docker-compose.{prod,staging}.yml` (e.g.
   `${MAIL_SERVICE_IMAGE}:<previous-sha>`).
3. `pwsh scripts/docker-up.ps1`

Image SHA pinning is enforced for prod by the overlay — never `:latest` in
prod.

## Secrets

- The root repo does not contain `INTERNAL_API_KEY` or `DB_PASSWORD`. They are
  injected via the host environment when starting the stack, and rotated by
  recreating the affected services (`docker compose up -d --force-recreate`).
- `config/sops-age-key.txt` is git-ignored and never copied into any image.
- `.env` is git-ignored. `.env.example` (not committed today — create one for
  each service if you need onboarding) is the only env file that should appear
  in the repo.

## Troubleshooting

| Symptom | First check |
|---|---|
| `ccs-postgres` not healthy | `docker logs ccs-postgres --tail 200` — usually wrong creds or volume perm on Linux host |
| `mail-service` restart loop on asyncpg | DB URL mismatch; `docker exec mail-service env \| grep DATABASE_URL` |
| Browser automation fails (registrar) | Playwright cache corrupted; `docker compose exec registrar rm -rf /root/.cache/ms-playwright` then recreate |
| Registrar stuck at `health: starting` | Healthcheck path is `/api/v1/health`, not `/api/health`. The internal router is mounted under `/api/v1` |
| Traefik 404 on `/api/*` | router file not reloaded; `docker exec traefik traefik healthcheck` |
| `python:3.12-slim` pulled but `apt-get update` 404 | stale build cache; rebuild with `NO_CACHE=1 pwsh scripts/docker-build.ps1 <service>` |
| Container exits immediately | check `docker compose logs <service> --tail 200` for traceback; `read_only` would also surface as permission errors in `/app/data` or `/app/logs` |

## Audit trail

| Date | Change | Author |
|---|---|---|
| 2026-06-09 | Fix registrar healthcheck path: `/api/health` → `/api/v1/health`. Verified full stack up with all services healthy (5/6 — traefik has no healthcheck, expected) | Claude (auto) |
| 2026-06-03 | Multi-stage Dockerfiles + non-root user + pinned deps for 4 services; compose hardening (no-new-privileges, drop caps, tmpfs, pids/mem limits, log driver); 5 PowerShell scripts; expanded `.dockerignore` | Claude (auto) |
