# System Architecture

## Runtime Truth

This document describes the actual runtime contract of the root workspace as of `2026-05-02`.
If runtime ports, route prefixes, or datastore ownership change, this file must be updated in the same change.

## Overview

`account-creation` is a multi-service workspace orchestrated from the root with Docker Compose.
The runtime is composed of:

- `postgres`
- `traefik`
- `registrar`
- `mail-service`
- `aa-proxy`
- `tts-proxy`

## Repository Topology

Important: this workspace is not one unified Git repository in practice.

- The root repository tracks orchestration/docs-level assets.
- Several service directories are separate Git repositories with their own `.git` directories:
  - `registrar/`
  - `aa-proxy/`
  - `desktop-ui/`
  - `common/`
  - `mail-service/`

Any architecture remediation spanning those services must be executed as coordinated multi-repo work, not as a single root-only branch.

## Services

| Service | Runtime Port | Purpose | Tech Stack |
|---------|--------------|---------|------------|
| `registrar` | `8709` | Account management API and registration orchestration | FastAPI + Python |
| `mail-service` | `8701` | Mailbox and provider management | FastAPI + Python |
| `aa-proxy` | `8702` | Artificial Analysis proxy and image lab APIs | FastAPI + Python |
| `tts-proxy` | `8700` | TTS proxy APIs | FastAPI + Python |
| `traefik` | `80` | Reverse proxy | Docker |
| `postgres` | `5432` | Canonical relational database runtime in Compose | PostgreSQL |

## Internal Service URLs

Services communicate over Docker DNS names:

- `http://registrar:8709`
- `http://mail-service:8701`
- `http://aa-proxy:8702`
- `http://tts-proxy:8700`
- `postgres:5432`

## External Runtime URLs

Current root Compose is a local orchestration artifact. Its published ports, Traefik dashboard exposure, and sample PostgreSQL credentials are not a staging or production security posture.

Current root Compose publishes:

- Traefik web: `http://localhost/`
- Traefik dashboard: `http://localhost:8080/`
- registrar: `http://localhost:8709/`
- mail-service: `http://localhost:8701/`
- aa-proxy: `http://localhost:8702/`
- tts-proxy: `http://localhost:8700/`
- PostgreSQL: `localhost:5432`

## Current API Prefixes

These are the prefixes enforced by service code today:

- `registrar`: `/api/v1/*`
- `mail-service`: `/api/v1/*`
- `aa-proxy`: `/api/v1/*`
- `tts-proxy`: `/api/*`

## Current Storage Story

### Canonical runtime in root Compose

- PostgreSQL is the database actually provisioned by the root `docker-compose.yml`.
- PostgreSQL is the canonical database for production and staging.
- SQLite is allowed only for isolated tests, local transitional tooling, or legacy conversion flows.

### Legacy SQLite references

- References to SQLite files such as `accounts.db` and `mail.db` are legacy/test/migration references only.
- They must not be described as primary production or staging stores.

## Frontend Runtime Surface

`desktop-ui` is a separate repository/workspace and must be validated against backend routing truth independently.
Its generated config now points at the root runtime ports for registrar, TTS, and AA service origins.

## Development Access

Direct service access currently works through published ports:

```bash
curl http://localhost:8709/api/v1/health
curl http://localhost:8701/api/health
curl http://localhost:8702/api/health
curl http://localhost:8700/api/health
```

## Verification Ownership

- Runtime truth in the root repo is validated by `.github/scripts/validate_runtime_truth.py`.
- Executable service tests live in the owning service repositories, not in root Git.
- The root repo is responsible for orchestration/docs consistency, not for impersonating service-local CI.

## Docker Network

All root-compose services share the `account-net` bridge network.

## Architecture Debt Summary

The primary gaps to close are:

1. Traefik public routing contract is checked in at `docs/superpowers/contracts/traefik-public-routes.md` and statically verified by `.github/scripts/validate_traefik_routes.py`
2. service-local config duplication
3. full service CI execution across repository boundaries
4. multi-repo boundary ambiguity
5. GitOps/secrets/migration/observability hardening
