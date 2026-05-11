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

## Residual Risks

- Full platform CI remains federated by design. The root repo cannot directly execute service-repo CI on GitHub without collapsing the repo boundaries again.
- SOPS/AGE secrets management is still design/spec work unless implemented in the deployment environment.
- Flyway-managed migration execution is still future hardening where service-owned migration artifacts do not exist.
- Full observability stack wiring, alerting, and dashboards remain future hardening beyond root runtime-truth validation.
- Full service CI matrix status must be checked in the owning repos before release decisions.
- `common.context` reverse type references and the `mail-service` FastAPI `on_event("startup")` warning were cleaned up after this review; keep checking service-owned tests before release decisions.

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
