# Test Strategy

## Scope

This workspace uses a federated testing model.

- Each service repository owns its executable test suite.
- The root orchestration repository owns runtime-truth validation, docs consistency, and operator runbooks.
- Cross-service contracts are enforced through a mix of service-local tests and root-level contract documentation.

## Repository Ownership

### Root orchestration repo

The root repo validates only assets it actually versions:

- [`docker-compose.yml`](/D:/business/account-creation/docker-compose.yml)
- [`docs/ARCHITECTURE.md`](/D:/business/account-creation/docs/ARCHITECTURE.md)
- [`docs/API-ARCHITECTURE.md`](/D:/business/account-creation/docs/API-ARCHITECTURE.md)
- [`docs/superpowers/contracts/internal-api.md`](/D:/business/account-creation/docs/superpowers/contracts/internal-api.md)
- runbooks under [`docs/superpowers/runbooks/`](/D:/business/account-creation/docs/superpowers/runbooks)

Root automation:

- `.github/workflows/docs-consistency.yml`
- `.github/workflows/test-platform.yml`
- `.github/scripts/validate_runtime_truth.py`

These root workflows validate docs/runtime truth and root-owned contract artifacts only; they do not run service CI, migration runners, or service-local release gates.

### Service repos

These repositories own their own runnable test suites:

- `common`
- `registrar`
- `mail-service`
- `aa-proxy`
- `tts-proxy`
- `desktop-ui`

The root repo must not pretend to execute service-repo CI on GitHub because those repos are not versioned inside root Git.

## Required Service Test Floor

Every backend service must maintain:

- smoke tests for import/startup and health route sanity
- unit tests for config and service-local logic
- integration tests where runtime-critical persistence or contract behavior is involved

Current service test floor artifacts:

- `common/tests/test_smoke.py`
- `registrar/tests/unit/test_api_services.py`
- `mail-service/tests/test_smoke.py`
- `mail-service/tests/test_config.py`
- `aa-proxy/tests/test_smoke.py`
- `aa-proxy/tests/test_config.py`
- `tts-proxy/tests/test_smoke.py`
- `tts-proxy/tests/test_config.py`

Current critical contract tests already introduced during remediation:

- `.github/scripts/test_validate_runtime_truth.py`
- `common/tests/contracts/test_no_reverse_imports.py`
- `common/tests/test_context.py`
- `registrar/tests/unit/test_internal_client.py`
- `registrar/tests/smoke/test_startup_contract.py`
- `registrar/tests/smoke/test_postgres_bootstrap_contract.py`
- `desktop-ui/src/__tests__/config.contract.test.ts`
- `desktop-ui/src/__tests__/api.client.test.ts`
- `desktop-ui/src/__tests__/App.test.tsx`

## Local Verification Commands

Run these from the owning repo or worktree.

### Root orchestration repo

```bash
python .github/scripts/validate_runtime_truth.py
PYTHONPATH=.github/scripts pytest .github/scripts/test_validate_runtime_truth.py -q
```

The root repo deliberately ignores service worktrees in `pytest.ini`; a plain root-level `pytest` must not be used as the platform test gate.

| Repo | Required local command | Owner |
|------|------------------------|-------|
| `common` | `PYTHONPATH=src pytest tests -q` | common repo |
| `registrar` | `PYTHONPATH=src;../common/src pytest tests -q` | registrar repo |
| `mail-service` | `PYTHONPATH=src;../common/src pytest tests -q` | mail-service repo |
| `aa-proxy` | `PYTHONPATH=src;../common/src pytest tests -q` | aa-proxy repo |
| `tts-proxy` | `PYTHONPATH=src;../common/src pytest tests -q` | tts-proxy repo |
| `desktop-ui` | `npm test -- --run` | desktop-ui repo |

Run service commands from the owning repo or worktree. On PowerShell, set `$env:PYTHONPATH` before `pytest` if inline environment assignment is not available.

`registrar` additionally owns PostgreSQL bootstrap verification. This checkout includes `registrar/tests/smoke/test_postgres_bootstrap_contract.py` as a local-only `DATABASE_URL` smoke artifact, but it still does not include a checked-in `bootstrap-postgres` command artifact.

## Runtime-Truth Checks

The root validator is the minimum acceptance gate for orchestration changes.

It checks:

- compose published ports
- architecture docs URLs
- API prefix declarations
- health endpoint declarations
- database policy language

If a change touches routes, ports, or datastore ownership, the root validator must pass in the same change.

## Database Policy

- PostgreSQL is the canonical runtime database for production and staging.
- SQLite is allowed only for isolated tests, transitional tooling, or legacy conversion flows.
- Migration/bootstrap verification belongs with the service repo that owns the runtime behavior, not the root orchestration repo.
- `registrar` owns a local-only PostgreSQL bootstrap smoke artifact; a canonical executable bootstrap command remains migration hardening debt until checked in.

## Release Evidence

No release is considered valid without fresh evidence from both layers:

- service-repo test evidence
- root orchestration runtime-truth evidence

Both are required because the platform is multi-repo by design. Record the command, commit SHA, timestamp, and result for each row. The root validator enforces the release evidence template shape in `docs/superpowers/runbooks/release-promotion-drill.md`.

| Layer | Evidence command | Required result |
|-------|------------------|-----------------|
| Root orchestration | `python .github/scripts/validate_runtime_truth.py` | `Runtime truth validation passed.` |
| `common` | `PYTHONPATH=src pytest tests -q` | pass |
| `registrar` | `PYTHONPATH=src;../common/src pytest tests -q` | pass |
| `mail-service` | `PYTHONPATH=src;../common/src pytest tests -q` | pass |
| `aa-proxy` | `PYTHONPATH=src;../common/src pytest tests -q` | pass |
| `tts-proxy` | `PYTHONPATH=src;../common/src pytest tests -q` | pass |
| `desktop-ui` | `npm test -- --run` | pass |
