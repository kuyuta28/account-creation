#!/usr/bin/env bash
# Wait until every service reports healthy (or no healthcheck is defined).
# Used by `make up` and the GitHub Actions smoke job.
#
# Usage: ./scripts/wait-healthy.sh [timeout_seconds]
set -euo pipefail

TIMEOUT="${1:-120}"
COMPOSE_BASE="-f docker-compose.yml"
PROFILE_FLAG=""

[ -n "${COMPOSE_PROFILES:-}" ] && PROFILE_FLAG="-f docker-compose.${COMPOSE_PROFILES}.yml"

DC=(docker compose $COMPOSE_BASE $PROFILE_FLAG)

mapfile -t services < <("${DC[@]}" config --services)
echo "[wait-healthy] ${#services[@]} service(s); timeout=${TIMEOUT}s"

elapsed=0
interval=2
all_ok=false
while [ "$elapsed" -lt "$TIMEOUT" ]; do
  ok=true
  for svc in "${services[@]}"; do
    status=$(docker ps \
      --filter "label=com.docker.compose.service=$svc" \
      --format '{{.Status}}' | head -1)
    if [ -z "$status" ]; then
      ok=false
      continue
    fi
    # Pass if "(healthy)" appears or no healthcheck is configured (no "unhealthy" / "starting")
    if [[ "$status" == *"(unhealthy)"* ]] || [[ "$status" == *"health: starting"* ]]; then
      ok=false
      break
    fi
  done
  if $ok; then
    echo "[wait-healthy] all services healthy after ${elapsed}s"
    exit 0
  fi
  sleep "$interval"
  elapsed=$((elapsed + interval))
done

echo "[wait-healthy] timeout after ${TIMEOUT}s"
"${DC[@]}" ps
exit 1