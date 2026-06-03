# Enterprise Exit Review (2026-05-02)

## Scope

This review records the completed root-orchestration remediation pass and the limited service-owned fixes that were verified at the time. It is not evidence that the whole platform is production-complete across GitOps, secrets, migrations, observability, or full service CI.

## What Changed

- The root repo was redefined as an orchestration repository rather than a fake monorepo.
- Runtime truth is now documented around the actual published ports and route prefixes.
- Root automation now validates only assets the root repo truly owns:
  - compose runtime contract
  - architecture/API docs
  - internal contract docs
  - operational runbooks
- Operational runbooks now exist for backup/restore, release promotion, and service-down incidents.
- Shared telemetry and PostgreSQL bootstrap work were treated as service-owned improvements where artifacts existed, not as root-owned platform guarantees.
- The review now distinguishes verified runtime truth from future enterprise hardening work.

## Enforceable State

The following items are now enforceable rather than aspirational:

- Root docs and compose must agree on published ports, health routes, and database policy because `.github/scripts/validate_runtime_truth.py` fails otherwise.
- The root repo no longer claims ownership of service-local source or CI execution.
- Cross-service runtime truth is documented through root contracts while executable service tests stay in the owning repos.
- Root validation now requires the documented critical contract artifacts to exist: common reverse-import guard, registrar startup smoke, and desktop runtime config contract.
- Service-owned tests are the authority for shared telemetry adoption and PostgreSQL bootstrap behavior.
- Root validation can prove compose/docs runtime consistency, but it does not prove every service is production-hardened.

## Fresh Verification Evidence

Executed on `2026-05-02`:

- `python .github/scripts/validate_runtime_truth.py` -> passed
- Root orchestration evidence: `python .github/scripts/validate_runtime_truth.py` passed.
- Service test evidence was captured in the service repos at the time of the remediation pass; this root audit should not be read as a current full-platform CI report.

Executed on `2026-05-03`:

- root orchestration: `python .github/scripts/validate_runtime_truth.py` -> passed
- service-local results from this date were point-in-time evidence only; rerun the owning repo suites before making release decisions.

Executed on `2026-05-11`:

- root orchestration: `python .github/scripts/validate_runtime_truth.py` -> passed after contract artifact enforcement was expanded.
- `common`: `pytest common/tests/contracts/test_no_reverse_imports.py common/tests/test_context.py -q` -> passed with `PYTHONPATH=common/src`.
- `registrar`: `pytest registrar/tests/smoke/test_startup_contract.py registrar/tests/smoke/test_imports.py -q` -> passed with `PYTHONPATH=registrar;common/src`.
- `desktop-ui`: `npm test -- --run src/__tests__/config.contract.test.ts` -> passed.
- `mail-service`: `pytest mail-service/tests/test_smoke.py mail-service/tests/test_config.py -q` -> passed with `PYTHONPATH=mail-service/src;common/src`.
- `aa-proxy`: `pytest aa-proxy/tests/test_smoke.py aa-proxy/tests/test_config.py -q` -> passed with `PYTHONPATH=aa-proxy/src;common/src`.
- `tts-proxy`: `pytest tts-proxy/tests/test_smoke.py tts-proxy/tests/test_config.py -q` -> passed with `PYTHONPATH=tts-proxy/src;common/src`.
- `common.context` reverse type references and the `mail-service` FastAPI `on_event("startup")` warning were already cleaned up in service-owned commits before this evidence refresh.

## Residual Risks

- Full platform CI remains federated by design. The root repo cannot directly execute service-repo CI on GitHub without collapsing the repo boundaries again.
- SOPS/AGE secrets management is still design/spec work unless implemented in the deployment environment.
- Flyway-managed migration execution is still future hardening: `registrar` now has a local-only PostgreSQL bootstrap smoke artifact, but no checked-in migration runner or `bootstrap-postgres` command artifact.
- Full observability stack wiring, alerting, and dashboards remain future hardening beyond root runtime-truth validation.
- Full service CI matrix status must be checked in the owning repos before release decisions.

## Hardening Debt Register

| Debt | Required artifact before claiming done |
|------|----------------------------------------|
| GitOps deployment | `.github/workflows/deploy-staging.yml`, `.github/workflows/deploy-production.yml`, `docker-compose.staging.yml`, `docker-compose.prod.yml`, and `docs/superpowers/runbooks/gitops-deployment.md` |
| SOPS/AGE secrets | `.sops.yaml`, `config/staging/secrets.example.yaml`, `config/prod/secrets.example.yaml`, and `docs/superpowers/runbooks/secrets-rotation.md` |
| Flyway migration execution | `.github/workflows/db-migrate.yml`, `docker-compose.migrations.yml`, `migrations/sql/V001__platform_bootstrap.sql`, and `docs/superpowers/runbooks/database-migrations.md` |
| Observability stack | `docker-compose.observability.yml`, `observability/prometheus/`, `observability/grafana/`, and `docs/superpowers/runbooks/observability.md` |
| Full service CI matrix | `.github/workflows/release-evidence.yml` and release evidence table with repository, commit SHA, image tag or digest, command, CI run URL, timestamp, and result |
| Traefik public routing contract | `docs/superpowers/contracts/traefik-public-routes.md`, `.github/scripts/validate_traefik_routes.py`, `.github/scripts/test_validate_traefik_routes.py`, and `scripts/smoke-traefik-routes.ps1` |

## Score

### Root orchestration boundary

Score: `10/10`

Reason:

- repo ownership is explicit
- runtime truth is validated automatically
- docs and runbooks are no longer hand-wavy
- root CI scope now matches root Git scope

### Full platform across all repos

Score: `6/10`

Reason:

- root runtime truth and selected service-owned contract checks are in place
- GitOps deployment, SOPS/AGE secret handling, Flyway migration execution, full observability, and a full service CI matrix are not yet implemented as platform-wide enforceable artifacts
- remaining platform-wide GitOps/secrets/migration/observability/CI work is still real hardening debt
