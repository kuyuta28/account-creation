# Service-Down Incident Runbook

## Scope

Use this runbook when any public service in the platform is unavailable, flapping, or returning unexpected contract errors.

## Priority Order

1. Protect production traffic.
2. Identify whether the issue is service-local, database, or orchestration-wide.
3. Restore the declared runtime contract.
4. Capture evidence for follow-up.

## Triage Sequence

### 1. Confirm the failing surface

```bash
curl -i http://localhost:8709/api/v1/health
curl -i http://localhost:8701/api/health
curl -i http://localhost:8702/api/health
curl -i http://localhost:8700/api/health
docker compose ps
```

### 2. Check logs first

Inspect the failing service logs before changing config.

```bash
docker compose logs --tail=200 registrar
docker compose logs --tail=200 mail-service
docker compose logs --tail=200 aa-proxy
docker compose logs --tail=200 tts-proxy
docker compose logs --tail=200 postgres
```

### 3. Check metrics and traces second

Use metrics and tracing to determine whether the failure is local or systemic.

- Metrics order:
  - service health and restart count
  - request error rate
  - latency spikes
  - database connection saturation
- Trace order:
  - failing request path
  - downstream dependency span
  - request correlation ID

### 4. Isolate the blast radius

- If only one service is down: treat it as a service-repo incident first.
- If multiple services are down and share DB errors: treat PostgreSQL or orchestration as primary.
- If routes fail but containers are healthy: inspect Traefik or published port drift.

## Escalation Path

- First responder: current platform on-call engineer
- Secondary: owner of the affected service repository
- Escalate immediately when:
  - PostgreSQL data integrity is at risk
  - more than one public service is unavailable
  - rollback is required but the release owner is unavailable

## Recovery Actions

- Restart only the failed service when the issue is isolated and understood.
- Restart PostgreSQL only after confirming the incident is database-led.
- Revert the last deploy when a release introduced the regression.
- Restore from backup only for confirmed data corruption or unrecoverable schema failure.

## Recovery Verification

A service is not considered recovered until:

- its health endpoint returns HTTP `200`
- dependent services stop surfacing downstream failures
- logs no longer show repeating startup or DB connection errors
- the restored runtime still matches the documented port/prefix contract

## Follow-Up

Record:

- incident start and end times
- affected services
- root cause class: service, database, orchestration, or external dependency
- rollback/restart/restore actions taken
- docs or contract gaps found during the incident
