# Enterprise Boundary And Operating Model Remediation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `account-creation` into a platform with hard service boundaries, one enforced operating model, measurable deployment/runtime truth, and enough test/ops discipline that the architecture claim is provable rather than aspirational.

**Architecture:** This plan is intentionally opinionated. It removes undecided branches before implementation starts. The platform target is: `common` is service-agnostic, service startup has no path hacks, `any-auto-register` is consumed only over HTTP, PostgreSQL is the canonical runtime database, SQLite is allowed only for legacy read-only migration utilities or isolated tests, service config is loaded through one shared loader, and docs/compose/UI routing/CI must agree on one runtime truth.

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, PostgreSQL, Docker Compose, GitHub Actions, OpenTelemetry, Prometheus, Grafana, Loki, Jaeger, React 18, Tauri 2, pytest, Vitest, Playwright.

---

## Scope Check

This plan fixes the entire architecture gap identified in the audit, but it is not “one implementation task.” It is a master plan split into strict chunks. No chunk may be started unless the previous chunk is green.

## Hard Decisions Locked Before Execution

These are no longer open questions. Workers must not re-decide them mid-flight.

1. **Database truth source**
   Production and staging use PostgreSQL as the canonical runtime database.
   SQLite is not a production datastore.
   SQLite may remain only for:
   - isolated local test fixtures
   - one-time migration/reference tooling
   - explicitly labeled legacy read-only conversion scripts

2. **Migration model**
   Migrations are forward-only.
   No Flyway undo workflow.
   Rollback strategy is:
   - revert application/config changes with git
   - fix schema with compensating `V_next__...` migrations
   - restore from backup for destructive corruption scenarios

3. **AAR integration boundary**
   `any-auto-register` is treated as an external subsystem consumed over HTTP.
   `registrar` and other services must not import or path-inject AAR source code at runtime.

4. **Shared package rule**
   `common` may depend only on:
   - stdlib
   - third-party libraries
   - other `common` modules
   It may not import service code from `registrar`, `mail-service`, `aa-proxy`, `tts-proxy`, or `any-auto-register`.

5. **Runtime packaging rule**
   No production entrypoint may use `sys.path.insert(...)` to resolve first-party code.

6. **Config rule**
   All service config loading must go through one shared loader in `common`.
   Service `settings.py` files are allowed only as thin typed adapters.

7. **UI routing truth**
   Desktop UI base URLs and route grouping must match the backend runtime model exactly.
   UI config is part of architectural truth, not a cosmetic concern.

---

## Success Metrics

The project is considered 10/10 only if all are true:

- `0` production path hacks remain.
- `0` reverse imports from `common` into service code remain.
- `1` canonical config loader exists and all services use it.
- `1` canonical runtime database story exists and is enforced in CI.
- `100%` of services have smoke tests.
- `100%` of public/internal service routes used cross-service are contract-tested.
- `100%` of docs checked by CI match runtime truth on ports, base URLs, and route prefixes.
- `100%` of release-critical flows have runbooks:
  - release/promotion
  - backup/restore
  - service-down incident
- Full platform verification suite passes on fresh checkout.

---

## File Structure Analysis

### Existing files that will be modified

- `registrar/main.py`
- `registrar/run_api.py`
- `registrar/src/api/server.py`
- `registrar/src/api/routers/internal.py`
- `registrar/src/config/settings.py`
- `mail-service/src/mail_service/server.py`
- `mail-service/src/config/settings.py`
- `aa-proxy/src/aa_proxy/server.py`
- `aa-proxy/src/config/settings.py`
- `tts-proxy/src/tts_proxy/server.py`
- `desktop-ui/src/App.tsx`
- `desktop-ui/src/config.ts`
- `desktop-ui/src/api/client.ts`
- `desktop-ui/src/api/aar-client.ts`
- `desktop-ui/src/api/tts.ts`
- `common/src/common/context.py`
- `common/src/common/database/__init__.py`
- `common/src/common/internal_client.py`
- `docker-compose.yml`
- `docs/ARCHITECTURE.md`
- `docs/API-ARCHITECTURE.md`
- `docs/TESTING.md`
- service `pyproject.toml` files

### New files/directories expected

- Create: `docs/superpowers/audits/enterprise-gap-baseline-2026-05-02.md`
- Create: `docs/superpowers/audits/enterprise-exit-review-2026-05-02.md`
- Create: `docs/superpowers/contracts/internal-api.md`
- Create: `docs/superpowers/runbooks/backup-restore-drill.md`
- Create: `docs/superpowers/runbooks/release-promotion-drill.md`
- Create: `docs/superpowers/runbooks/incident-response.md`
- Create: `common/src/common/config/__init__.py`
- Create: `common/src/common/config/base.py`
- Create: `common/src/common/config/loader.py`
- Create: `common/src/common/contracts/__init__.py`
- Create: `common/src/common/contracts/lifecycle.py`
- Create: `common/src/common/telemetry.py`
- Create: `common/tests/config/test_shared_loader.py`
- Create: `common/tests/contracts/test_context_boundaries.py`
- Create: `common/tests/contracts/test_no_reverse_imports.py`
- Create: `registrar/tests/smoke/test_startup_contract.py`
- Create: `registrar/tests/integration/test_migration_bootstrap.py`
- Create: `mail-service/tests/smoke/test_imports.py`
- Create: `mail-service/tests/unit/test_config.py`
- Create: `aa-proxy/tests/smoke/test_imports.py`
- Create: `aa-proxy/tests/unit/test_config.py`
- Create: `tts-proxy/tests/smoke/test_imports.py`
- Create: `tts-proxy/tests/unit/test_server.py`
- Create: `desktop-ui/src/__tests__/config.contract.test.ts`
- Create: `.github/workflows/docs-consistency.yml`
- Create: `.github/workflows/test-platform.yml`

### Units and responsibility

- `common.config.*`
  Single config loading engine for first-party services.

- `common.contracts.lifecycle`
  Small service-agnostic interfaces for startup/shutdown dependencies.

- `common.telemetry`
  One shared instrumentation entrypoint.

- per-service `settings.py`
  Typed schemas and service-only field mapping, nothing more.

- `docs/superpowers/contracts/internal-api.md`
  Contract truth source for cross-service usage.

- runbooks
  Operational truth source for humans.

---

## Chunk 1: Baseline And Safety Net First

### Task 1: Capture baseline and freeze runtime truth

**Files:**
- Create: `docs/superpowers/audits/enterprise-gap-baseline-2026-05-02.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/API-ARCHITECTURE.md`

- [ ] **Step 1: Read current runtime sources**

Run:
```powershell
Get-Content docker-compose.yml
Get-Content registrar/src/api/server.py
Get-Content mail-service/src/mail_service/server.py
Get-Content aa-proxy/src/aa_proxy/server.py
Get-Content tts-proxy/src/tts_proxy/server.py
Get-Content desktop-ui/src/config.ts
```

Expected: current ports, route prefixes, UI base URLs, and health endpoints are visible.

- [ ] **Step 2: Write the baseline audit doc**

Include exactly:
- current host/container ports
- current route prefixes
- current DB stores in real use
- startup path hacks
- `common` reverse imports
- config duplication
- test coverage gaps
- docs/runtime mismatches
- UI/backend routing mismatches

- [ ] **Step 3: Update architecture docs with a `Runtime Truth` section**

Must list:
- current external URLs
- current internal service URLs
- current health endpoints
- current datastore ownership

- [ ] **Step 4: Search for stale runtime statements**

Run:
```powershell
Get-ChildItem docs -Recurse -File | Select-String -Pattern '8888|8709|8701|8702|8700|accounts.db|mail.db|SQLite|PostgreSQL'
```

Expected: every hit is either correct or explicitly transitional.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/audits/enterprise-gap-baseline-2026-05-02.md docs/ARCHITECTURE.md docs/API-ARCHITECTURE.md
git commit -m "docs: capture enterprise remediation baseline"
```

### Task 2: Add architecture drift guardrails before refactor

**Files:**
- Create: `.github/workflows/docs-consistency.yml`
- Create: `registrar/tests/smoke/test_startup_contract.py`
- Create: `common/tests/contracts/test_no_reverse_imports.py`
- Create: `desktop-ui/src/__tests__/config.contract.test.ts`
- Modify: `docs/TESTING.md`

- [ ] **Step 1: Write failing startup contract test**

Test file: `registrar/tests/smoke/test_startup_contract.py`

Assertions:
- startup entrypoints import successfully
- startup modules expose expected app/server objects
- TODO/xfail documents current `sys.path.insert(...)` debt

- [ ] **Step 2: Write failing reverse-import boundary test**

Test file: `common/tests/contracts/test_no_reverse_imports.py`

Assertions:
- no file under `common/src/common` imports service packages

- [ ] **Step 3: Write failing UI config contract test**

Test file: `desktop-ui/src/__tests__/config.contract.test.ts`

Assertions:
- `API_BASE_URL`, `TTS_BASE_URL`, and `AAR_BASE_URL` match the documented runtime contract

- [ ] **Step 4: Run the new safety-net tests**

Run:
```bash
pytest registrar/tests/smoke/test_startup_contract.py -v
pytest common/tests/contracts/test_no_reverse_imports.py -v
cd desktop-ui && npm test -- --run src/__tests__/config.contract.test.ts
```

Expected: at least one failure documents current drift/debt.

- [ ] **Step 5: Add docs-consistency workflow**

Checks must fail if:
- docs ports != compose ports
- docs route prefixes != server prefixes
- UI config base URLs != documented runtime truth

- [ ] **Step 6: Update testing guide**

Add explicit section:
- architecture drift tests
- docs consistency checks
- UI config contract checks

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/docs-consistency.yml registrar/tests/smoke/test_startup_contract.py common/tests/contracts/test_no_reverse_imports.py desktop-ui/src/__tests__/config.contract.test.ts docs/TESTING.md
git commit -m "test: add architecture drift guardrails"
```

---

## Chunk 2: Raise Test Floor Before Deep Refactors

### Task 3: Create minimum smoke coverage for under-tested services

**Files:**
- Create: `mail-service/tests/smoke/test_imports.py`
- Create: `aa-proxy/tests/smoke/test_imports.py`
- Create: `tts-proxy/tests/smoke/test_imports.py`

- [ ] **Step 1: Write failing smoke test for `mail-service`**

Assert:
- server module imports
- app object exists
- health route exists

- [ ] **Step 2: Write failing smoke test for `aa-proxy`**

- [ ] **Step 3: Write failing smoke test for `tts-proxy`**

- [ ] **Step 4: Run the smoke tests**

Run:
```bash
pytest mail-service/tests/smoke/test_imports.py -v
pytest aa-proxy/tests/smoke/test_imports.py -v
pytest tts-proxy/tests/smoke/test_imports.py -v
```

Expected: failures or setup gaps surface immediately.

- [ ] **Step 5: Add the minimal test seams needed**

- [ ] **Step 6: Re-run the smoke tests**

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add mail-service/tests/smoke aa-proxy/tests/smoke tts-proxy/tests/smoke
git commit -m "test: add smoke coverage for all backend services"
```

### Task 4: Create minimum config/unit coverage for under-tested services

**Files:**
- Create: `mail-service/tests/unit/test_config.py`
- Create: `aa-proxy/tests/unit/test_config.py`
- Create: `tts-proxy/tests/unit/test_server.py`

- [ ] **Step 1: Write failing config/unit tests**

Coverage:
- config load behavior
- health endpoint behavior
- router/exception wiring

- [ ] **Step 2: Run the tests**

Run:
```bash
pytest mail-service/tests/unit/test_config.py -v
pytest aa-proxy/tests/unit/test_config.py -v
pytest tts-proxy/tests/unit/test_server.py -v
```

Expected: current gaps become explicit before refactors start.

- [ ] **Step 3: Add minimal implementation/helpers if needed**

- [ ] **Step 4: Re-run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mail-service/tests/unit aa-proxy/tests/unit tts-proxy/tests/unit
git commit -m "test: add minimum unit coverage for backend services"
```

---

## Chunk 3: Remove Illegal Dependency Boundaries

### Task 5: Remove reverse imports from `common`

**Files:**
- Modify: `common/src/common/context.py`
- Create: `common/src/common/contracts/__init__.py`
- Create: `common/src/common/contracts/lifecycle.py`
- Modify: `common/tests/contracts/test_context_boundaries.py`

- [ ] **Step 1: Write failing context boundary test**

Test file: `common/tests/contracts/test_context_boundaries.py`

Assertions:
- `common.context` imports only service-agnostic lifecycle interfaces

- [ ] **Step 2: Run the boundary tests**

Run:
```bash
pytest common/tests/contracts/test_context_boundaries.py -v
pytest common/tests/contracts/test_no_reverse_imports.py -v
```

Expected: FAIL on current service-specific imports.

- [ ] **Step 3: Implement neutral lifecycle contracts**

Create interfaces like:
- `AsyncInitializable`
- `AsyncShutdownable`
- `AsyncStateManager`

- [ ] **Step 4: Refactor `common.context` to depend only on lifecycle contracts**

- [ ] **Step 5: Re-run boundary tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add common/src/common/context.py common/src/common/contracts common/tests/contracts/test_context_boundaries.py common/tests/contracts/test_no_reverse_imports.py
git commit -m "refactor: make common package service-agnostic"
```

### Task 6: Remove production `sys.path.insert(...)` usage

**Files:**
- Modify: `registrar/main.py`
- Modify: `registrar/run_api.py`
- Modify: `tts-proxy/src/tts_proxy/server.py`
- Modify: relevant `pyproject.toml` files

- [ ] **Step 1: Write failing import-startup tests if missing**

Cover:
- `registrar.main`
- `registrar.run_api`
- `tts_proxy.server`

- [ ] **Step 2: Run startup/import tests**

Run:
```bash
pytest registrar/tests/smoke/test_startup_contract.py -v
pytest mail-service/tests/smoke/test_imports.py -v
pytest aa-proxy/tests/smoke/test_imports.py -v
pytest tts-proxy/tests/smoke/test_imports.py -v
```

Expected: FAIL or xfail documenting path hacks.

- [ ] **Step 3: Wire proper first-party packaging**

Target:
- `common` resolved through declared dependency/import path
- no ad-hoc path mutation in runtime entrypoints

- [ ] **Step 4: Re-run startup/import tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add registrar/main.py registrar/run_api.py tts-proxy/src/tts_proxy/server.py registrar/pyproject.toml tts-proxy/pyproject.toml common/pyproject.toml
git commit -m "refactor: remove production path hacks"
```

---

## Chunk 4: Canonical Config Architecture

### Task 7: Build the shared config loader

**Files:**
- Create: `common/src/common/config/__init__.py`
- Create: `common/src/common/config/base.py`
- Create: `common/src/common/config/loader.py`
- Create: `common/tests/config/test_shared_loader.py`

- [ ] **Step 1: Write failing shared loader tests**

Test cases:
- merge order across multiple yaml files
- strict required sections
- optional defaults
- list-to-tuple coercion
- str-to-Path coercion
- env-aware overrides
- helpful error messages

- [ ] **Step 2: Run the shared loader tests**

Run:
```bash
pytest common/tests/config/test_shared_loader.py -v
```

Expected: FAIL because loader does not exist.

- [ ] **Step 3: Implement `common.config.loader` minimally**

- [ ] **Step 4: Re-run tests**

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add common/src/common/config common/tests/config/test_shared_loader.py
git commit -m "feat: add shared config loader"
```

### Task 8: Move services onto the shared config loader

**Files:**
- Modify: `registrar/src/config/settings.py`
- Modify: `mail-service/src/config/settings.py`
- Modify: `aa-proxy/src/config/settings.py`
- Extend existing tests plus:
  - `registrar/tests/unit/test_config.py`
  - `mail-service/tests/unit/test_config.py`
  - `aa-proxy/tests/unit/test_config.py`

- [ ] **Step 1: Snapshot current config behavior**

Add/confirm tests for:
- `load_config()`
- db path resolution
- env interaction
- provider seeding
- service-specific optional sections

- [ ] **Step 2: Run all config tests before refactor**

Run:
```bash
pytest registrar/tests/unit/test_config.py -v
pytest mail-service/tests/unit/test_config.py -v
pytest aa-proxy/tests/unit/test_config.py -v
pytest common/tests/config/test_shared_loader.py -v
```

Expected: baseline green or known debt documented.

- [ ] **Step 3: Refactor `registrar` settings onto shared loader**

- [ ] **Step 4: Run `registrar` config tests**

- [ ] **Step 5: Refactor `mail-service` settings onto shared loader**

- [ ] **Step 6: Run `mail-service` config tests**

- [ ] **Step 7: Refactor `aa-proxy` settings onto shared loader**

- [ ] **Step 8: Run `aa-proxy` config tests**

- [ ] **Step 9: Re-run the full config test set**

- [ ] **Step 10: Commit**

```bash
git add registrar/src/config/settings.py mail-service/src/config/settings.py aa-proxy/src/config/settings.py registrar/tests/unit/test_config.py mail-service/tests/unit/test_config.py aa-proxy/tests/unit/test_config.py
git commit -m "refactor: unify service config loading"
```

---

## Chunk 5: Database Truth And Migration Discipline

### Task 9: Enforce the database decision in code and docs

**Files:**
- Modify: `common/src/common/database/__init__.py`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/API-ARCHITECTURE.md`
- Modify: `docs/TESTING.md`

- [ ] **Step 1: Write the canonical DB policy into docs**

Must state explicitly:
- PostgreSQL is canonical in prod/staging
- SQLite is test/legacy-only
- schema authority lives in migrations

- [ ] **Step 2: Remove misleading `accounts.db`-centric wording**

- [ ] **Step 3: Add DB decision matrix**

Matrix rows:
- prod
- staging
- local dev
- unit tests
- integration tests

- [ ] **Step 4: Add code comments that match the new truth**

- [ ] **Step 5: Commit**

```bash
git add common/src/common/database/__init__.py docs/ARCHITECTURE.md docs/API-ARCHITECTURE.md docs/TESTING.md
git commit -m "docs: codify canonical database model"
```

### Task 10: Make migration bootstrap real, not documentary

**Files:**
- Create: `registrar/tests/integration/test_migration_bootstrap.py`
- Create/modify: migration tooling files once canonical path is chosen
- Modify: `.github/workflows/test-platform.yml`

- [ ] **Step 1: Write failing migration bootstrap test**

Test file: `registrar/tests/integration/test_migration_bootstrap.py`

Assertions:
- fresh PostgreSQL instance boots from migrations
- app starts against migrated schema
- schema drift is surfaced

- [ ] **Step 2: Run the migration bootstrap test**

Expected: FAIL until tooling is real.

- [ ] **Step 3: Implement one canonical migration command**

The command must work in:
- local dev
- CI
- staging/prod automation

- [ ] **Step 4: Wire CI to boot fresh DB and run migration bootstrap**

- [ ] **Step 5: Re-run migration bootstrap plus smoke tests**

- [ ] **Step 6: Commit**

```bash
git add registrar/tests/integration/test_migration_bootstrap.py .github/workflows/test-platform.yml
git commit -m "test: enforce fresh-db migration bootstrap"
```

---

## Chunk 6: AAR Boundary And Internal Contract

### Task 11: Standardize the internal service contract

**Files:**
- Create: `docs/superpowers/contracts/internal-api.md`
- Modify: `common/src/common/internal_client.py`
- Modify: `registrar/src/api/routers/internal.py`
- Modify: `registrar/tests/unit/test_internal_api.py`

- [ ] **Step 1: Write failing contract tests**

Cover:
- auth header requirements
- envelope shape
- 404 behavior
- idempotent upsert/update semantics
- timeout expectations where client wraps server

- [ ] **Step 2: Run contract tests**

Run:
```bash
pytest registrar/tests/unit/test_internal_api.py -v
```

- [ ] **Step 3: Write the contract document**

Document:
- path
- method
- request body
- success body
- failure body
- retry semantics
- timeout semantics

- [ ] **Step 4: Align client and router implementation**

- [ ] **Step 5: Re-run tests**

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/contracts/internal-api.md common/src/common/internal_client.py registrar/src/api/routers/internal.py registrar/tests/unit/test_internal_api.py
git commit -m "refactor: formalize internal service contract"
```

### Task 12: Remove source-tree AAR embedding and force HTTP boundary

**Files:**
- Modify: `registrar/main.py`
- Modify: `registrar/run_api.py`
- Modify: `desktop-ui/src/App.tsx`
- Modify: `desktop-ui/src/config.ts`
- Modify: `desktop-ui/src/api/aar-client.ts`

- [ ] **Step 1: Write failing AAR boundary tests**

Back-end assertions:
- no startup path injection for AAR
- AAR access happens through configured URL/client only

Front-end assertions:
- AAR base URL is explicit and environment-driven

- [ ] **Step 2: Run AAR-related tests**

- [ ] **Step 3: Remove raw AAR source-path coupling**

- [ ] **Step 4: Re-run AAR backend and UI tests**

- [ ] **Step 5: Commit**

```bash
git add registrar/main.py registrar/run_api.py desktop-ui/src/App.tsx desktop-ui/src/config.ts desktop-ui/src/api/aar-client.ts
git commit -m "refactor: isolate any-auto-register behind HTTP boundary"
```

---

## Chunk 7: Observability And Runtime Consistency

### Task 13: Introduce one shared telemetry entrypoint

**Files:**
- Create: `common/src/common/telemetry.py`
- Modify: `registrar/src/api/server.py`
- Modify: `mail-service/src/mail_service/server.py`
- Modify: `aa-proxy/src/aa_proxy/server.py`
- Modify: `tts-proxy/src/tts_proxy/server.py`

- [ ] **Step 1: Write failing telemetry tests**

Verify:
- service name tagging
- request correlation
- health endpoint instrumentation
- shared initialization path

- [ ] **Step 2: Run telemetry tests**

- [ ] **Step 3: Implement shared telemetry module**

- [ ] **Step 4: Move all services onto shared telemetry initialization**

- [ ] **Step 5: Re-run telemetry and smoke tests**

- [ ] **Step 6: Commit**

```bash
git add common/src/common/telemetry.py registrar/src/api/server.py mail-service/src/mail_service/server.py aa-proxy/src/aa_proxy/server.py tts-proxy/src/tts_proxy/server.py
git commit -m "feat: unify telemetry initialization"
```

### Task 14: Make UI runtime config and backend truth agree

**Files:**
- Modify: `desktop-ui/src/config.ts`
- Modify: `desktop-ui/src/api/client.ts`
- Modify: `desktop-ui/src/api/tts.ts`
- Modify: `desktop-ui/src/api/aar-client.ts`
- Modify: `desktop-ui/src/__tests__/config.contract.test.ts`

- [ ] **Step 1: Write failing assertions for current UI base URLs**

Check:
- `API_BASE_URL`
- `TTS_BASE_URL`
- `AAR_BASE_URL`
- path concatenation rules in API clients

- [ ] **Step 2: Run UI config contract tests**

Run:
```bash
cd desktop-ui && npm test -- --run src/__tests__/config.contract.test.ts
```

- [ ] **Step 3: Fix UI config values and API client assumptions**

- [ ] **Step 4: Re-run UI config tests**

- [ ] **Step 5: Commit**

```bash
git add desktop-ui/src/config.ts desktop-ui/src/api/client.ts desktop-ui/src/api/tts.ts desktop-ui/src/api/aar-client.ts desktop-ui/src/__tests__/config.contract.test.ts
git commit -m "fix: align desktop UI runtime config with backend contract"
```

---

## Chunk 8: Deployment, Docs, And CI Truth Alignment

### Task 15: Build the full platform CI matrix

**Files:**
- Create or modify: `.github/workflows/test-platform.yml`
- Modify: `docs/TESTING.md`

- [ ] **Step 1: Add CI jobs for all required suites**

Matrix must run:
- `common` tests
- `registrar` smoke/unit/integration
- `mail-service` smoke/unit
- `aa-proxy` smoke/unit
- `tts-proxy` smoke/unit
- `desktop-ui` tests

- [ ] **Step 2: Add fresh-db migration bootstrap into the matrix**

- [ ] **Step 3: Document CI ownership and expected runtimes**

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test-platform.yml docs/TESTING.md
git commit -m "ci: add full platform matrix"
```

### Task 16: Align compose, docs, monitoring, and UI on one runtime story

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/API-ARCHITECTURE.md`
- Modify: any deployment doc/spec still describing stale routes or ports

- [ ] **Step 1: Write failing consistency assertions if any gap remains**

Checks:
- compose ports == docs ports
- docs routes == server routes
- UI base URLs == docs routes
- monitoring endpoints == actual health routes

- [ ] **Step 2: Run docs-consistency workflow locally**

- [ ] **Step 3: Fix every remaining mismatch**

- [ ] **Step 4: Re-run consistency checks**

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml docs/ARCHITECTURE.md docs/API-ARCHITECTURE.md desktop-ui/src/config.ts
git commit -m "ops: align runtime truth across compose docs and UI"
```

---

## Chunk 9: Runbooks And Human Operability

### Task 17: Write real runbooks, not placeholders

**Files:**
- Create: `docs/superpowers/runbooks/backup-restore-drill.md`
- Create: `docs/superpowers/runbooks/release-promotion-drill.md`
- Create: `docs/superpowers/runbooks/incident-response.md`

- [ ] **Step 1: Write backup/restore drill**

Must include:
- trigger
- prerequisites
- command sequence
- verification query/check
- failure branches

- [ ] **Step 2: Write release/promotion drill**

Must include:
- dev to staging
- staging verification
- prod release gate
- rollback trigger points

- [ ] **Step 3: Write incident-response runbook**

Must include:
- service-down triage
- log/trace/metrics order
- escalation path
- recovery verification

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/runbooks
git commit -m "docs: add operational runbooks"
```

---

## Chunk 10: Final Exit Gate

### Task 18: Execute the final enterprise audit

**Files:**
- Modify: `docs/superpowers/audits/enterprise-gap-baseline-2026-05-02.md`
- Create: `docs/superpowers/audits/enterprise-exit-review-2026-05-02.md`

- [ ] **Step 1: Re-run the full verification suite**

Run:
```bash
pytest common/tests -v
pytest registrar/tests -v
pytest mail-service/tests -v
pytest aa-proxy/tests -v
pytest tts-proxy/tests -v
cd desktop-ui && npm test -- --run
```

Expected: all green.

- [ ] **Step 2: Verify measurable acceptance criteria**

Required evidence:
- `0` production `sys.path.insert(...)`
- `0` reverse imports from `common` into services
- `1` shared config loader in use by all backend services
- `1` canonical migration bootstrap path passing in CI
- `100%` services with smoke tests
- `100%` cross-service HTTP contract documented and tested
- docs-consistency workflow passing
- UI config contract test passing
- runbooks present and reviewed

- [ ] **Step 3: Re-score platform**

Use this rubric:
- Service decomposition: 10/10 only if no service boundary is bypassed by source import hacks
- Dependency boundaries: 10/10 only if `common` is service-agnostic
- Config/secrets/deploy discipline: 10/10 only if docs/UI/compose/CI agree
- DB/migration clarity: 10/10 only if PostgreSQL path is canonical and enforced
- Observability/ops maturity: 10/10 only if telemetry is shared and runbooks exist
- Cross-service consistency: 10/10 only if all services meet minimum smoke/unit floor

- [ ] **Step 4: Write the exit review**

Include:
- what changed
- what is now enforceable
- residual risks if any
- explicit statement whether 10/10 was actually achieved

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/audits/enterprise-gap-baseline-2026-05-02.md docs/superpowers/audits/enterprise-exit-review-2026-05-02.md
git commit -m "docs: record enterprise remediation exit review"
```

---

## Order Of Execution

1. Chunk 1: baseline and guardrails
2. Chunk 2: raise minimum test floor
3. Chunk 3: remove illegal dependency boundaries
4. Chunk 4: canonical config architecture
5. Chunk 5: database truth and migration discipline
6. Chunk 6: AAR boundary and internal contract
7. Chunk 7: observability and runtime consistency
8. Chunk 8: deployment, docs, and CI truth alignment
9. Chunk 9: runbooks and human operability
10. Chunk 10: final exit gate

## Non-Negotiable Rules During Execution

- No chunk closes on docs alone if the chunk claims runtime behavior change.
- No worker may reopen the hard decisions section unless the human explicitly approves a redesign.
- Every refactor chunk must end with tests proving the new boundary.
- If a step cannot be verified automatically, add the missing automated check before claiming success.
- `common` stays service-agnostic.
- UI runtime config is treated as part of platform architecture.

## Definition Of Done

The platform is only “10/10 enterprise-ready” when all of these are simultaneously true:

- All first-party runtime dependencies resolve without path hacks.
- `common` does not import any service implementation module.
- `any-auto-register` is consumed only through HTTP boundary code.
- PostgreSQL is the documented and tested runtime truth in prod/staging.
- SQLite is not described or used as production truth anywhere.
- Service config loading is centralized in `common.config`.
- Desktop UI runtime config matches backend routing truth.
- Docs, compose, CI, and tests describe the same runtime model.
- Every backend service has smoke coverage and minimum unit coverage.
- Full platform verification passes on fresh checkout.

Plan complete and saved to `docs/superpowers/plans/2026-05-02-enterprise-remediation-plan.md`. Ready to execute?
