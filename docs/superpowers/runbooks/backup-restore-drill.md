# Backup And Restore Drill

## Purpose

This runbook verifies that the platform can back up and restore the canonical PostgreSQL runtime used by the root orchestration workspace.

## Trigger

Run this drill:

- before any destructive schema change
- before a production release that changes persistence behavior
- after PostgreSQL major-version upgrades
- at least once per quarter

## Ownership

- Driver: platform operator on call
- Reviewer: second engineer who validates recovery evidence

## Preconditions

- Root orchestration repo checked out
- Docker Engine running
- `docker compose` available
- Root stack uses the canonical `postgres` service from [`docker-compose.yml`](/D:/business/account-creation/docker-compose.yml)
- A recent application quiesce window is agreed if this is not a synthetic drill

## Backup Procedure

1. Confirm the database container is healthy.
2. Capture a logical dump from the live `postgres` container.
3. Record the dump artifact name and timestamp.
4. Verify the dump is non-empty and readable.

```bash
docker compose ps postgres
mkdir -p data/backups
docker compose exec -T postgres pg_dump -U ccs -d account_creator > data/backups/account_creator-$(date +%Y%m%d-%H%M%S).sql
ls -lh data/backups
head -n 5 data/backups/account_creator-*.sql
```

## Restore Procedure

1. Stop writers to avoid replaying inconsistent state during restore.
2. Create a fresh disposable PostgreSQL instance or recreate the root `postgres` container.
3. Apply the dump into an empty target database.
4. Start the dependent services only after the restore verification passes.

```bash
docker compose stop registrar mail-service aa-proxy tts-proxy any-auto-register
docker compose down postgres
docker compose up -d postgres
docker compose exec -T postgres psql -U ccs -d postgres -c "DROP DATABASE IF EXISTS account_creator_restore;"
docker compose exec -T postgres psql -U ccs -d postgres -c "CREATE DATABASE account_creator_restore;"
Get-ChildItem data/backups/account_creator-*.sql | Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object {
  Get-Content $_.FullName | docker compose exec -T postgres psql -U ccs -d account_creator_restore
}
```

## Verification

Run both structural and application-level checks.

```bash
docker compose exec -T postgres psql -U ccs -d account_creator_restore -c "\dt"
docker compose exec -T postgres psql -U ccs -d account_creator_restore -c "SELECT COUNT(*) FROM accounts;"
docker compose up -d registrar
curl http://localhost:8709/api/v1/health
```

Expected evidence:

- core tables such as `accounts`, `mail_providers`, `services` exist
- row counts are non-zero when restoring a non-empty environment
- registrar health returns HTTP `200`

## Failure Branches

- If `pg_dump` fails: stop and fix container health, credentials, or disk pressure before retrying.
- If restore fails on SQL errors: do not continue startup; capture the failing statement and compare schema version against the backup source.
- If tables restore but the app fails health checks: keep writers stopped, inspect registrar logs first, then validate config and internal service dependencies.
- If the latest dump is corrupt: fall back to the previous known-good dump and record the corruption incident.

## Exit Criteria

The drill is complete only when:

- a dump artifact was produced
- the dump restored into a clean target database
- the restored schema was queried successfully
- at least one application health endpoint passed against the restored environment
