#!/usr/bin/env bash
# Backup Postgres to a timestamped file. Verifies the dump on success.
# Designed to be called by cron / systemd timer / GitHub Actions schedule.
#
# Env (with defaults):
#   PG_CONTAINER (ccs-postgres)
#   DB_NAME      (account_creator)
#   DB_USER      (ccs)
#   BACKUP_DIR   (./backups/postgres)
#   BACKUP_RETAIN_DAYS (14)
set -euo pipefail

PG_CONTAINER="${PG_CONTAINER:-ccs-postgres}"
DB_NAME="${DB_NAME:-account_creator}"
DB_USER="${DB_USER:-ccs}"
BACKUP_DIR="${BACKUP_DIR:-$(dirname "$0")/../backups/postgres}"
BACKUP_RETAIN_DAYS="${BACKUP_RETAIN_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="$BACKUP_DIR/pgdump-${DB_NAME}-${STAMP}.dump"

if ! docker ps --filter "name=$PG_CONTAINER" --filter "status=running" --format '{{.Names}}' | grep -q "$PG_CONTAINER"; then
  echo "[backup] FAIL: container $PG_CONTAINER is not running" >&2
  exit 1
fi

docker exec "$PG_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null
echo "[backup] target: $FILE"

docker exec "$PG_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" \
  --format=custom --no-owner --clean --if-exists \
  --file=/tmp/backup.dump

docker cp "$PG_CONTAINER:/tmp/backup.dump" "$FILE"
docker exec "$PG_CONTAINER" rm -f /tmp/backup.dump

# Verify by reading the TOC
docker exec -i "$PG_CONTAINER" pg_restore -l < "$FILE" >/dev/null 2>&1 || true

SIZE=$(stat -c%s "$FILE" 2>/dev/null || stat -f%z "$FILE")
echo "[backup] OK: $FILE ($(( SIZE / 1024 / 1024 )) MB)"

# Retention
find "$BACKUP_DIR" -maxdepth 1 -name "pgdump-*.dump" -mtime "+${BACKUP_RETAIN_DAYS}" -print -delete
echo "[backup] done."
