# Federated Platform Hardening Design

## Goal

Close the remaining platform hardening debt while preserving the federated repository model: service repositories own service code, tests, migrations, and images; the root repository owns platform control-plane artifacts.

## Architecture Decision

The platform uses a federated service-repository model with a root control-plane repository.

Root owns:

- orchestration topology
- staging/production compose overlays
- GitOps workflows and release gates
- SOPS/AGE policy and secrets runbooks
- platform-level Flyway orchestration
- observability stack configuration
- Traefik public routing contracts
- release evidence templates and validators

Service repositories own:

- service source code
- service-local tests and CI
- service-local migrations or bootstrap commands
- service telemetry instrumentation
- release images and commit SHAs

The root repository must not import service code or pretend service source is versioned by root Git. Root workflows consume released service images, service commit SHAs, and evidence files.

## Debt Closure Criteria

A debt row is closed only when all of these are checked in:

1. executable artifact
2. automated validation or CI gate
3. operator runbook
4. release evidence slot
5. root validator enforcement

If an artifact requires external credentials or a staging host, the repo must include the exact command and evidence slot, but local verification may stop at static validation.

## GitOps Deployment

Root adds staging and production deployment artifacts that consume service image tags or digests instead of building ignored service worktrees.

Files:

- `docker-compose.staging.yml`
- `docker-compose.prod.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`
- `docs/superpowers/runbooks/gitops-deployment.md`

Staging deployment is workflow-dispatch or staging branch driven. Production deployment is workflow-dispatch or release tag driven and requires environment approval in GitHub.

Root validation checks the workflows and compose overlays exist and reference service image inputs, migration execution, secrets decryption, deployment, and smoke verification.

## SOPS/AGE Secrets

Root defines the encrypted-secret policy and required secret keys without committing real secrets.

Files:

- `.sops.yaml`
- `config/staging/secrets.example.yaml`
- `config/prod/secrets.example.yaml`
- `docs/superpowers/runbooks/secrets-rotation.md`

Required runtime keys include:

- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DATABASE_URL`
- `INTERNAL_API_KEY`
- service API tokens owned by each service

GitHub workflows must fail closed if `SOPS_AGE_KEY` is absent. The runbook covers key rotation, emergency recovery, and how to re-encrypt environment files.

## Flyway Migration Execution

Root owns platform-level migration orchestration and evidence. Service-owned schema changes remain in the owning service repositories unless explicitly exported into the release artifact.

Files:

- `migrations/sql/V001__platform_bootstrap.sql`
- `docker-compose.migrations.yml`
- `.github/workflows/db-migrate.yml`
- `docs/superpowers/runbooks/database-migrations.md`

The migration workflow decrypts environment secrets, validates migration config, runs Flyway, and records migration evidence before deployment.

## Observability Stack

Root owns the platform observability stack. Services own instrumentation and `/metrics` implementation.

Files:

- `docker-compose.observability.yml`
- `observability/prometheus/prometheus.yml`
- `observability/prometheus/alerts/platform.yml`
- `observability/grafana/provisioning/datasources/prometheus.yml`
- `observability/grafana/provisioning/dashboards/platform.yml`
- `docs/superpowers/runbooks/observability.md`

Root validation checks observability config exists and includes platform targets for Traefik, PostgreSQL, and each public service target or explicitly documented service-owned telemetry requirement.

## Full Service CI Matrix

Root does not run service source tests directly. Instead, root requires release evidence from each service repository.

Files:

- `.github/workflows/release-evidence.yml`
- `docs/superpowers/runbooks/release-promotion-drill.md`
- service-owned CI workflow references in `docs/TESTING.md`

The release evidence table records repository, commit SHA, image tag or digest, test command, CI run URL, timestamp, and result.

Root validation checks every service has an evidence row and that release promotion docs require fresh evidence before staging or production promotion.

## Traefik Public Routing Contract

Root owns static and runtime route verification for the public proxy entrypoint.

Files:

- `docs/superpowers/contracts/traefik-public-routes.md`
- `.github/scripts/validate_traefik_routes.py`
- `.github/scripts/test_validate_traefik_routes.py`
- `scripts/smoke-traefik-routes.ps1`

Static validation parses `traefik/traefik.yml` and verifies routers, path prefixes, middlewares, services, and upstream URLs. Runtime smoke checks hit public proxy paths when the stack is running.

## Testing Strategy

Root verification:

```powershell
python .github/scripts/validate_runtime_truth.py
$env:PYTHONPATH='.github/scripts'; pytest .github/scripts/test_validate_runtime_truth.py .github/scripts/test_validate_traefik_routes.py -q
docker compose -f docker-compose.yml -f docker-compose.staging.yml config
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
docker compose -f docker-compose.yml -f docker-compose.migrations.yml config
docker compose -f docker-compose.yml -f docker-compose.observability.yml config
```

Service verification remains owned by each service repository and is recorded in release evidence.

## Acceptance

The hardening debt register can mark these rows closed only after the implementation adds and validates the artifacts above:

- GitOps deployment
- SOPS/AGE secrets
- Flyway migration execution
- Observability stack
- Full service CI matrix
- Traefik public routing contract
