# Backup & Restore Policy

This document is the source of truth for **what gets backed up, how often, how
long, and how to restore**. It is enforced by:

- `scripts/postgres-backup.ps1` (Windows / dev) and `scripts/postgres-backup.sh` (Linux / CI)
- `scripts/postgres-restore.ps1`
- `.github/workflows/docker-build.yml` (smoke test only — not a scheduled backup)
- A scheduled job the operator must wire up (see "Scheduling" below)

## What gets backed up

| Asset | Backing mechanism | Backup path | Frequency | Retention |
|---|---|---|---|---|
| Postgres data (clusters, accounts, sessions, TOTP) | `pg_dump` custom format | `backups/postgres/pgdump-<db>-<ts>.dump` | daily (recommended) | 14 days default, override via `BACKUP_RETAIN_DAYS` |
| Service SQLite mirrors (`data/accounts.db`, `mail-service/data/*.db`) | Bind-mount; operator responsibility | Same dir | weekly | n/a |
| Registrar `data/`, `debug/`, `screenshots/`, `logs/` | Bind-mount / named volume | Same dir | weekly | 30 days recommended |
| Traefik config | `traefik/traefik.yml` is in git | n/a | git history | n/a |
| Compose / Dockerfile / scripts | git | n/a | git history | n/a |

**The Docker named volumes `account-creation_postgres_data`,
`account-creation_registrar-data`, `account-creation_mail-service-data` are
the source of truth for live state.** Off-host `pg_dump` is the recommended
backup; volume snapshots are a stop-gap, see "Volume snapshot" below.

## Naming convention

```
pgdump-<DB_NAME>-YYYYMMDD-HHMMSS.dump
```

Example: `pgdump-account_creator-20260609-235648.dump`

## Where backups go

Default: `<repo>/backups/postgres/` (gitignored). Override with `BACKUP_DIR`.

For prod, **do not keep backups on the same host as the database**. Use any of:

1. A second Docker volume mounted on a different host.
2. `aws s3 sync` / `gsutil rsync` / `azcopy sync` from the local dir.
3. A sidecar that `rclone`s each new file off-host.

The script does not implement off-host sync — wire it up at the operator
layer.

## Scheduling

The script is one-shot. To run on a schedule:

- **Windows Task Scheduler**:
  ```powershell
  $action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File D:\business\account-creation\scripts\postgres-backup.ps1"
  $trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
  Register-ScheduledTask -TaskName "postgres-backup" -Action $action -Trigger $trigger
  ```
- **Linux cron** (entry in `/etc/cron.d/account-creation`):
  ```
  0 2 * * *  root  /opt/account-creation/scripts/postgres-backup.sh
  ```
- **GitHub Actions schedule** (`.github/workflows/backup.yml`):
  ```yaml
  on:
    schedule:
      - cron: "0 2 * * *"   # 02:00 UTC daily
  jobs:
    backup:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: backup
          run: |
            docker compose up -d postgres
            bash scripts/postgres-backup.sh
        - uses: actions/upload-artifact@v4
          with:
            name: pgdump-${{ github.run_id }}
            path: backups/postgres/
  ```

## Restore procedure

1. Stop the dependent services to prevent write races during restore:
   ```powershell
   pwsh scripts/docker-up.ps1   # brings the stack up first (idempotent)
   docker compose stop registrar mail-service aa-proxy tts-proxy
   ```
2. Run the restore. The script will drop and recreate the database.
   ```powershell
   pwsh scripts/postgres-restore.ps1 ./backups/postgres/pgdump-account_creator-20260609.dump
   ```
   Pass `--yes` to skip the confirmation prompt (only do this in CI).
3. Restart services:
   ```powershell
   docker compose start registrar mail-service aa-proxy tts-proxy
   pwsh scripts/docker-up.ps1   # optional: re-run healthcheck gate
   ```
4. Verify a sanity row count and the most recent account's `updated_at`:
   ```bash
   docker exec account-creation-postgres-1 psql -U ccs -d account_creator \
     -tAc "SELECT count(*) FROM accounts; SELECT max(updated_at) FROM accounts;"
   ```

## Verifying a backup

The script calls `pg_restore -l` on the file before reporting success. A
failing verification aborts the backup job.

For deeper validation, restore the dump into a throwaway database and
diff against production:

```bash
docker exec account-creation-postgres-1 createdb -U ccs verify
docker cp ./backups/pgdump.dump account-creation-postgres-1:/tmp/
docker exec account-creation-postgres-1 pg_restore -U ccs -d verify --no-owner /tmp/pgdump.dump
docker exec account-creation-postgres-1 pg_dump -U ccs -d verify --schema-only > /tmp/verify-schema.sql
docker exec account-creation-postgres-1 pg_dump -U ccs -d account_creator --schema-only > /tmp/prod-schema.sql
diff /tmp/verify-schema.sql /tmp/prod-schema.sql
```

Schedule a weekly verify against a randomly-chosen backup to catch silent
corruption.

## Volume snapshot (offline, last resort)

Only use this when the cluster is **stopped**.

```bash
docker compose down
docker run --rm \
  -v account-creation_postgres_data:/from:ro \
  -v $PWD:/to \
  alpine tar czf /to/postgres-data.tgz -C /from .
```

Restore:
```bash
docker run --rm \
  -v account-creation_postgres_data:/to \
  -v $PWD:/from \
  alpine tar xzf /from/postgres-data.tgz -C /to
docker compose up -d postgres
```

## What this policy does NOT cover

- **TOTP secrets in the database.** Once a Gmail mailbox is enrolled, the
  `accounts_gmail.totp_secret` lives only in Postgres. If the backup is taken
  after a code path that upserts `''` over the secret, the secret is gone
  from the backup too. See `docs/TOTP-LOSS.md` (not yet written) for the
  upstream issue.
- **Browser session cookies** (`session_state` in `accounts.session_state`).
  These expire on Google's side anyway; they are not part of the durable
  contract.
- **Bind-mount SQLite mirrors under `*/data/`.** They are convenient for the
  desktop UI but should not be relied on as the source of truth. Postgres is.

## Audit trail

| Date | Change | Author |
|---|---|---|
| 2026-06-10 | Initial policy. pg_dump custom format. 14-day retention. | Claude (auto) |
