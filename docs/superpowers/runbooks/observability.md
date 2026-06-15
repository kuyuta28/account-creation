# Observability Runbook

## Scope

Root owns Prometheus, Grafana provisioning, platform alert rules, and operator runbooks. Service repositories own service telemetry instrumentation and metrics quality.

## Start Local Observability

```powershell
docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d prometheus grafana
```

## Dashboards

- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Dashboard: `Account Creation Platform Overview`

## Alerts

Baseline alert rules live in `observability/prometheus/alerts/platform.yml`:

- `PlatformTargetDown`
- `HighHttp5xxRate`
- `PostgresDown`

## Service Telemetry Ownership

Each service repository owns adding a native `/metrics` endpoint or exporter. Until native metrics exist, root Prometheus records health endpoint reachability as platform evidence.

## Incident Response

1. Check `PlatformTargetDown` alerts.
2. Inspect Traefik route health through `scripts/smoke-traefik-routes.ps1`.
3. Check service-specific dashboards or logs in the owning repository/runtime.
4. Record incident timeline and remediation evidence in the release or incident record.
