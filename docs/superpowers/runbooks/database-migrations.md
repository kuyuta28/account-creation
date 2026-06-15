# Database Migrations Runbook

## Ownership

Root owns platform migration orchestration. Service repositories own service-specific schema migrations unless they export migrations into the root release artifact.

## Local Rehearsal

```powershell
docker compose --env-file config/staging/secrets.example.yaml -f docker-compose.yml -f docker-compose.migrations.yml config
```

For execution, use an encrypted environment file decrypted to `.env`:

```powershell
sops --decrypt config/staging/secrets.yaml > .env
docker compose --env-file .env -f docker-compose.yml -f docker-compose.migrations.yml run --rm flyway
```

## Staging Migration

Run the `Database Migration` workflow with `environment=staging`. Record the workflow URL, commit SHA, migration version, timestamp, and result in release evidence.

## Production Migration

Run production migrations only after staging evidence exists for the same migration revision. Use `environment=prod` and require GitHub environment approval.

## Failure Handling

Do not edit committed migration files. Add a new forward-fix migration or restore from backup according to `docs/superpowers/runbooks/backup-restore-drill.md`.

## Evidence

Each release must include:

- migration workflow URL
- root commit SHA
- migration version
- environment
- timestamp
- result
