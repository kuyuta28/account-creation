# Root Repo Role

## Purpose

The Git repository at the workspace root is not a monorepo for application code.
It is the orchestration repository for the platform as a whole.

It exists to version assets that belong to the platform boundary rather than to any single service.

## What Belongs In Root Git

- `docker-compose.yml`
- top-level deployment and routing assets such as `traefik/`
- platform documentation under `docs/`
- top-level CI/CD or automation under `.github/`
- workspace-level conventions that apply across services

## What Does Not Belong In Root Git

- service application source code
- service-local tests
- service-local configs owned by the service repo
- runtime SQLite files, local backups, or generated logs
- ad-hoc helper scripts tied to only one service's local development flow

## Service Repo Ownership

Each of these lives in its own Git repository and must be changed there, not via root Git:

- `registrar/`
- `mail-service/`
- `aa-proxy/`
- `tts-proxy/`
- `desktop-ui/`
- `common/`

## Working Rule

If a change can be owned clearly by one service, it belongs in that service repo.
If a change defines how multiple services fit together, it belongs in the root orchestration repo.
