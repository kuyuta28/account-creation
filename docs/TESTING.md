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

Current critical contract tests already introduced during remediation:

- `common/tests/contracts/test_no_reverse_imports.py`
- `common/tests/contracts/test_context_boundaries.py`
- `registrar/tests/smoke/test_startup_contract.py`
- `registrar/tests/integration/test_migration_bootstrap.py`
- `desktop-ui/src/__tests__/config.contract.test.ts`

## Local Verification Commands

Run these from the owning repo or worktree.

### Root orchestration repo

```bash
python .github/scripts/validate_runtime_truth.py
```

### `common`

```bash
pytest tests -v
```

### `registrar`

```bash
pytest tests -v
bootstrap-postgres --database-url "$DATABASE_URL"
```

### `mail-service`

```bash
pytest tests -v
```

### `aa-proxy`

```bash
pytest tests -v
```

### `tts-proxy`

```bash
pytest tests -v
```

### `desktop-ui`

```bash
npm test -- --run
```

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
- `registrar` now owns the canonical PostgreSQL bootstrap command and integration test for the shared account schema.

## Release Evidence

No release is considered valid without fresh evidence from both layers:

- service-repo test evidence
- root orchestration runtime-truth evidence

Both are required because the platform is multi-repo by design.
