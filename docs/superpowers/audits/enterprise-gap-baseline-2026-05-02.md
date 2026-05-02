# Enterprise Gap Baseline Audit (2026-05-02)

## Scope

This audit captures the actual runtime and repository state before enterprise remediation begins.

## Runtime Truth

- Root `docker-compose.yml` publishes:
  - PostgreSQL on `5432`
  - Traefik web on `80`
  - Traefik dashboard on `8080`
  - registrar on `8709`
  - mail-service on `8701`
  - aa-proxy on `8702`
  - tts-proxy on `8700`
  - any-auto-register on `8708`
- Service route prefixes currently in code:
  - registrar: `/api/v1/*`
  - mail-service: `/api/v1/*`
  - aa-proxy: `/api/v1/*`
  - tts-proxy: `/api/*`

## Repository Topology

- This is not a single Git monorepo in practice.
- The root repo tracks:
  - `docker-compose.yml`
  - `docs/`
  - `mail-service` as a gitlink/sub-repo entry
  - a few root helper files
- The following directories are separate Git repositories with their own `.git` directories:
  - `registrar/`
  - `aa-proxy/`
  - `desktop-ui/`
  - `common/`
  - `mail-service/`

## Current Architecture Gaps

### 1. Runtime/documentation drift

- Root architecture docs still describe Traefik on `localhost:8888`.
- Root API docs still describe UI and proxy URLs through `8888`.
- `desktop-ui/src/config.ts` currently points to:
  - `API_BASE_URL=http://localhost:8709/api/v1`
  - `TTS_BASE_URL=http://localhost:8709/tts`
  - `AAR_BASE_URL=http://localhost:8709/aa`
- Those UI values do not match the documented reverse-proxy contract.

### 2. Dependency boundary drift

- `registrar/main.py`, `registrar/run_api.py`, and `tts-proxy/src/tts_proxy/server.py` use `sys.path.insert(...)`.
- `registrar` startup also injects `any-auto-register` source directly into runtime import resolution.
- `common/src/common/context.py` imports service-specific types from `registrar` and `mail-service`.

### 3. Persistence ambiguity

- Codebase currently mixes:
  - PostgreSQL in root compose and registrar runtime config
  - SQLite-oriented comments/utilities/config values
- Architecture docs still describe `accounts.db` and `mail.db` as primary stores.
- The runtime truth is therefore not singular.

### 4. Config duplication

- `registrar/src/config/settings.py`
- `mail-service/src/config/settings.py`
- `aa-proxy/src/config/settings.py`

These files duplicate a large amount of config loading/parsing logic and are already drifting.

### 5. Uneven test floor

- `registrar` has meaningful smoke/unit/integration coverage.
- `desktop-ui` has a moderate test surface.
- `mail-service`, `aa-proxy`, and `tts-proxy` have significantly lighter baseline coverage.

## Immediate Remediation Priorities

1. Freeze and document runtime truth.
2. Add drift-detection tests for docs, startup, and UI config.
3. Raise minimum smoke/config test floor for the weaker services.
4. Remove path hacks and reverse imports.
5. Consolidate config loading and database truth model.
