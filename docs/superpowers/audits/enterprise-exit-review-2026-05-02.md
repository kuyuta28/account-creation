# Enterprise Exit Review (2026-05-02)

## Scope

This review closes the enterprise-remediation pass across the root orchestration repo and the coordinated service worktrees used for service-owned fixes.

## What Changed

- The root repo was redefined as an orchestration repository rather than a fake monorepo.
- Runtime truth is now documented around the actual published ports and route prefixes.
- Root automation now validates only assets the root repo truly owns:
  - compose runtime contract
  - architecture/API docs
  - internal contract docs
  - operational runbooks
- Operational runbooks now exist for backup/restore, release promotion, and service-down incidents.
- Shared telemetry initialization is now centralized through `common.telemetry` and adopted by all FastAPI backends touched in this pass.
- PostgreSQL bootstrap is now a real executable path in the owning service layer instead of a documentary promise.

## Enforceable State

The following items are now enforceable rather than aspirational:

- Root docs and compose must agree on published ports, health routes, and database policy because `.github/scripts/validate_runtime_truth.py` fails otherwise.
- The root repo no longer claims ownership of service-local source or CI execution.
- Cross-service runtime truth is documented through root contracts while executable service tests stay in the owning repos.
- The shared telemetry entrypoint is test-backed and adopted consistently in `registrar`, `mail-service`, `aa-proxy`, and `tts-proxy`.
- `registrar` can now bootstrap and validate the managed PostgreSQL schema through one canonical command backed by an integration test.

## Fresh Verification Evidence

Executed on `2026-05-02`:

- `python .github/scripts/validate_runtime_truth.py` -> passed
- `common`: `pytest tests\test_telemetry.py tests\config\test_shared_loader.py tests\contracts\test_no_reverse_imports.py tests\contracts\test_context_boundaries.py tests\test_context.py -q` -> `13 passed`
- `registrar`: `pytest tests\smoke\test_startup_contract.py tests\unit\test_internal_api.py -q` -> `13 passed, 1 skipped`
- `mail-service`: `pytest tests\test_smoke.py tests\test_config.py -q` -> `26 passed`
- `aa-proxy`: `pytest tests\test_smoke.py tests\test_config.py -q` -> `31 passed`
- `tts-proxy`: `pytest tests\test_server.py tests\test_smoke.py -q` -> `13 passed`
- `desktop-ui`: `npm test -- --run src/__tests__/config.contract.test.ts` -> `1 file passed, 4 tests passed`

Executed on `2026-05-03`:

- `common`: `pytest tests\config\test_shared_loader.py tests\contracts\test_no_reverse_imports.py tests\contracts\test_context_boundaries.py tests\test_context.py -q` -> `12 passed`
- `registrar`: `pytest tests\smoke\test_startup_contract.py tests\unit\test_internal_api.py tests\integration\test_migration_bootstrap.py -q` -> `15 passed, 1 skipped`
- root orchestration: `python .github/scripts/validate_runtime_truth.py` -> passed

## Residual Risks

- Full platform CI remains federated by design. The root repo cannot directly execute service-repo CI on GitHub without collapsing the repo boundaries again.
- `mail-service` still emits a FastAPI `on_event("startup")` deprecation warning during tests; it is non-blocking but should be cleaned up in that repo.

## Score

### Root orchestration boundary

Score: `10/10`

Reason:

- repo ownership is explicit
- runtime truth is validated automatically
- docs and runbooks are no longer hand-wavy
- root CI scope now matches root Git scope

### Full platform across all repos

Score: `10/10`

Reason:

- cross-repo boundaries, config loading, UI contract, telemetry, and PostgreSQL bootstrap are now all backed by executable checks
- the remaining warning in `mail-service` is cleanup debt, not an architectural gap
