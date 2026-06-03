# Federated Platform Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the root control-plane artifacts that close GitOps deployment, SOPS/AGE secrets, Flyway migration execution, observability stack, full service CI matrix, and Traefik public routing contract debt while preserving federated service ownership.

**Architecture:** The root repository is the platform control-plane and does not own service source. Root artifacts consume service image tags, service commit SHAs, and service CI evidence instead of importing ignored service worktrees. Service repositories remain the source of truth for service code, tests, migrations, telemetry instrumentation, and release images.

**Tech Stack:** Docker Compose, GitHub Actions, SOPS/AGE, Flyway, Prometheus, Grafana provisioning, Traefik, Python validators, pytest.

---

## File Structure

- Create `.sops.yaml` — SOPS/AGE creation rules for environment secrets.
- Create `config/staging/secrets.example.yaml` — staging secret key contract with non-secret example values.
- Create `config/prod/secrets.example.yaml` — production secret key contract with non-secret example values.
- Create `docker-compose.staging.yml` — staging overlay that consumes service image tags and environment secrets.
- Create `docker-compose.prod.yml` — production overlay that consumes immutable service images and disables local-only exposure.
- Create `docker-compose.migrations.yml` — Flyway migration runner overlay.
- Create `docker-compose.observability.yml` — Prometheus/Grafana observability overlay.
- Create `migrations/sql/V001__platform_bootstrap.sql` — platform migration bootstrap artifact.
- Create `observability/prometheus/prometheus.yml` — scrape configuration for root-owned platform targets.
- Create `observability/prometheus/alerts/platform.yml` — baseline platform alerts.
- Create `observability/grafana/provisioning/datasources/prometheus.yml` — Grafana datasource provisioning.
- Create `observability/grafana/provisioning/dashboards/platform.yml` — Grafana dashboard provisioning.
- Create `observability/grafana/dashboards/platform-overview.json` — minimal platform dashboard.
- Create `.github/workflows/deploy-staging.yml` — staging GitOps deployment gate.
- Create `.github/workflows/deploy-production.yml` — production GitOps deployment gate.
- Create `.github/workflows/db-migrate.yml` — Flyway migration workflow.
- Create `.github/workflows/release-evidence.yml` — release evidence validator workflow.
- Create `docs/superpowers/runbooks/gitops-deployment.md` — GitOps deployment runbook.
- Create `docs/superpowers/runbooks/secrets-rotation.md` — SOPS/AGE rotation and recovery runbook.
- Create `docs/superpowers/runbooks/database-migrations.md` — migration execution runbook.
- Create `docs/superpowers/runbooks/observability.md` — observability runbook.
- Create `docs/superpowers/contracts/traefik-public-routes.md` — public routing contract.
- Create `.github/scripts/validate_traefik_routes.py` — static Traefik route validator.
- Create `.github/scripts/test_validate_traefik_routes.py` — validator unit tests.
- Create `scripts/smoke-traefik-routes.ps1` — local/staging runtime proxy smoke script.
- Modify `.github/scripts/validate_runtime_truth.py` — enforce all new hardening artifacts and debt closure evidence.
- Modify `.github/scripts/test_validate_runtime_truth.py` — add helper coverage for new artifact enforcement.
- Modify `docs/TESTING.md` — document root and service verification matrix.
- Modify `docs/API-ARCHITECTURE.md` — link Traefik route contract and deployment boundary.
- Modify `docs/ARCHITECTURE.md` — replace debt wording with implemented artifact summary.
- Modify `docs/superpowers/audits/enterprise-exit-review-2026-05-02.md` — update hardening debt register with implemented artifacts.
- Modify `docs/superpowers/runbooks/release-promotion-drill.md` — require service CI evidence, image tags/digests, migration evidence, and routing/observability checks.

---

### Task 1: Traefik Public Route Contract

**Files:**
- Create: `docs/superpowers/contracts/traefik-public-routes.md`
- Create: `.github/scripts/validate_traefik_routes.py`
- Create: `.github/scripts/test_validate_traefik_routes.py`
- Create: `scripts/smoke-traefik-routes.ps1`
- Modify: `.github/scripts/validate_runtime_truth.py`
- Modify: `docs/API-ARCHITECTURE.md`
- Modify: `docs/ARCHITECTURE.md`

- [ ] **Step 1: Write failing tests for route parsing**

Create `.github/scripts/test_validate_traefik_routes.py`:

```python
from pathlib import Path

from validate_traefik_routes import EXPECTED_ROUTES, validate_traefik_routes


def test_validate_traefik_routes_accepts_root_contract():
    errors = validate_traefik_routes(Path("traefik/traefik.yml"))
    assert errors == []


def test_expected_routes_cover_public_services():
    assert set(EXPECTED_ROUTES) == {"mail", "tts", "aa", "api"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
$env:PYTHONPATH='.github/scripts'; pytest .github/scripts/test_validate_traefik_routes.py -q
```

Expected: FAIL because `validate_traefik_routes.py` does not exist.

- [ ] **Step 3: Implement route validator**

Create `.github/scripts/validate_traefik_routes.py`:

```python
from __future__ import annotations

from pathlib import Path

import yaml


EXPECTED_ROUTES = {
    "mail": {
        "rule": "PathPrefix(`/mail`)",
        "service": "mail-service",
        "middleware": "strip-mail",
        "prefix": "/mail",
        "url": "http://mail-service:8701",
    },
    "tts": {
        "rule": "PathPrefix(`/tts`)",
        "service": "tts-proxy",
        "middleware": "strip-tts",
        "prefix": "/tts",
        "url": "http://tts-proxy:8700",
    },
    "aa": {
        "rule": "PathPrefix(`/aa`)",
        "service": "aa-proxy",
        "middleware": "strip-aa",
        "prefix": "/aa",
        "url": "http://aa-proxy:8702",
    },
    "api": {
        "rule": "PathPrefix(`/api`)",
        "service": "registrar",
        "middleware": None,
        "prefix": None,
        "url": "http://registrar:8709",
    },
}


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_traefik_routes(path: Path) -> list[str]:
    config = _load_yaml(path)
    http = config.get("http", {})
    routers = http.get("routers", {})
    middlewares = http.get("middlewares", {})
    services = http.get("services", {})
    errors: list[str] = []

    for route_name, expected in EXPECTED_ROUTES.items():
        router = routers.get(route_name)
        if router is None:
            errors.append(f"missing router: {route_name}")
            continue
        if router.get("rule") != expected["rule"]:
            errors.append(f"router {route_name} rule mismatch: {router.get('rule')}")
        if router.get("service") != expected["service"]:
            errors.append(f"router {route_name} service mismatch: {router.get('service')}")
        middleware = expected["middleware"]
        if middleware is None:
            if router.get("middlewares"):
                errors.append(f"router {route_name} should not strip prefixes")
        else:
            if middleware not in router.get("middlewares", []):
                errors.append(f"router {route_name} missing middleware: {middleware}")
            prefixes = middlewares.get(middleware, {}).get("stripPrefix", {}).get("prefixes", [])
            if expected["prefix"] not in prefixes:
                errors.append(f"middleware {middleware} missing prefix: {expected['prefix']}")
        service = services.get(expected["service"], {})
        servers = service.get("loadBalancer", {}).get("servers", [])
        urls = {server.get("url") for server in servers}
        if expected["url"] not in urls:
            errors.append(f"service {expected['service']} missing upstream: {expected['url']}")

    return errors


def main() -> int:
    errors = validate_traefik_routes(Path("traefik/traefik.yml"))
    if errors:
        print("Traefik route validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Traefik route validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Create route contract doc**

Create `docs/superpowers/contracts/traefik-public-routes.md`:

```markdown
# Traefik Public Routes Contract

The root repository owns the public proxy routing contract for local, staging, and production orchestration.

| Public path | Router | Middleware | Upstream service | Upstream URL | Health path |
|-------------|--------|------------|------------------|--------------|-------------|
| `/api` | `api` | none | `registrar` | `http://registrar:8709` | `/api/v1/health` |
| `/mail` | `mail` | `strip-mail` | `mail-service` | `http://mail-service:8701` | `/api/health` |
| `/tts` | `tts` | `strip-tts` | `tts-proxy` | `http://tts-proxy:8700` | `/api/health` |
| `/aa` | `aa` | `strip-aa` | `aa-proxy` | `http://aa-proxy:8702` | `/api/health` |

Static validation:

```powershell
python .github/scripts/validate_traefik_routes.py
```

Runtime smoke validation when the stack is running:

```powershell
./scripts/smoke-traefik-routes.ps1 -BaseUrl http://localhost
```
```

- [ ] **Step 5: Create runtime smoke script**

Create `scripts/smoke-traefik-routes.ps1`:

```powershell
param(
    [string]$BaseUrl = "http://localhost"
)

$routes = @(
    @{ Name = "registrar"; Url = "$BaseUrl/api/v1/health" },
    @{ Name = "mail-service"; Url = "$BaseUrl/mail/api/health" },
    @{ Name = "tts-proxy"; Url = "$BaseUrl/tts/api/health" },
    @{ Name = "aa-proxy"; Url = "$BaseUrl/aa/api/health" }
)

foreach ($route in $routes) {
    $response = Invoke-WebRequest -Uri $route.Url -UseBasicParsing -TimeoutSec 10
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "$($route.Name) returned HTTP $($response.StatusCode) at $($route.Url)"
    }
    Write-Host "$($route.Name) OK $($response.StatusCode) $($route.Url)"
}
```

- [ ] **Step 6: Run validation**

Run:

```powershell
python .github/scripts/validate_traefik_routes.py
$env:PYTHONPATH='.github/scripts'; pytest .github/scripts/test_validate_traefik_routes.py -q
```

Expected: validator prints `Traefik route validation passed.` and pytest passes.

---

### Task 2: SOPS/AGE Secrets Contract

**Files:**
- Create: `.sops.yaml`
- Create: `config/staging/secrets.example.yaml`
- Create: `config/prod/secrets.example.yaml`
- Create: `docs/superpowers/runbooks/secrets-rotation.md`
- Modify: `.github/scripts/validate_runtime_truth.py`

- [ ] **Step 1: Create SOPS policy**

Create `.sops.yaml`:

```yaml
creation_rules:
  - path_regex: config/staging/secrets\.yaml$
    age: age1exampleexampleexampleexampleexampleexampleexampleexample0xy2
  - path_regex: config/prod/secrets\.yaml$
    age: age1exampleexampleexampleexampleexampleexampleexampleexample0xy2
```

- [ ] **Step 2: Create example secret contracts**

Create `config/staging/secrets.example.yaml` and `config/prod/secrets.example.yaml` with:

```yaml
DB_USER: ccs
DB_PASSWORD: replace-with-encrypted-secret
DB_NAME: account_creator
DATABASE_URL: postgresql+asyncpg://ccs:replace-with-encrypted-secret@postgres:5432/account_creator
INTERNAL_API_KEY: replace-with-encrypted-secret
REGISTRAR_IMAGE: ghcr.io/example/account-creation-registrar:sha-0000000
MAIL_SERVICE_IMAGE: ghcr.io/example/account-creation-mail-service:sha-0000000
AA_PROXY_IMAGE: ghcr.io/example/account-creation-aa-proxy:sha-0000000
TTS_PROXY_IMAGE: ghcr.io/example/account-creation-tts-proxy:sha-0000000
DESKTOP_UI_IMAGE: ghcr.io/example/account-creation-desktop-ui:sha-0000000
```

- [ ] **Step 3: Create secrets runbook**

Create `docs/superpowers/runbooks/secrets-rotation.md` with commands for generating AGE keys, encrypting `config/<env>/secrets.yaml`, rotating keys, and recovering from a lost deployment key.

- [ ] **Step 4: Enforce artifacts in validator**

Add checks in `.github/scripts/validate_runtime_truth.py` for `.sops.yaml`, both example files, and the runbook.

- [ ] **Step 5: Run validation**

Run:

```powershell
python .github/scripts/validate_runtime_truth.py
```

Expected: `Runtime truth validation passed.`

---

### Task 3: GitOps Deployment Artifacts

**Files:**
- Create: `docker-compose.staging.yml`
- Create: `docker-compose.prod.yml`
- Create: `.github/workflows/deploy-staging.yml`
- Create: `.github/workflows/deploy-production.yml`
- Create: `docs/superpowers/runbooks/gitops-deployment.md`
- Modify: `.github/scripts/validate_runtime_truth.py`

- [ ] **Step 1: Create compose overlays**

`docker-compose.staging.yml` and `docker-compose.prod.yml` must override service `image:` values using environment variables from decrypted secrets and avoid building ignored service worktrees.

- [ ] **Step 2: Create staging deployment workflow**

Create `.github/workflows/deploy-staging.yml` with workflow dispatch inputs for service image tags, SOPS decrypt step, compose config validation, migration workflow dependency note, deploy step, and smoke command.

- [ ] **Step 3: Create production deployment workflow**

Create `.github/workflows/deploy-production.yml` with GitHub environment `production`, release tag input, SOPS decrypt step, compose config validation, migration step, deploy step, and post-deploy smoke evidence.

- [ ] **Step 4: Create GitOps runbook**

Create `docs/superpowers/runbooks/gitops-deployment.md` documenting staging promotion, production promotion, rollback, and required evidence.

- [ ] **Step 5: Validate compose overlays**

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.staging.yml config
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

Expected: both commands render valid config.

---

### Task 4: Flyway Migration Execution

**Files:**
- Create: `migrations/sql/V001__platform_bootstrap.sql`
- Create: `docker-compose.migrations.yml`
- Create: `.github/workflows/db-migrate.yml`
- Create: `docs/superpowers/runbooks/database-migrations.md`
- Modify: `.github/scripts/validate_runtime_truth.py`

- [ ] **Step 1: Create bootstrap migration**

Create `migrations/sql/V001__platform_bootstrap.sql`:

```sql
CREATE SCHEMA IF NOT EXISTS platform;

CREATE TABLE IF NOT EXISTS platform.schema_revision_notes (
    id BIGSERIAL PRIMARY KEY,
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- [ ] **Step 2: Create Flyway compose overlay**

Create `docker-compose.migrations.yml` with a `flyway` service using `flyway/flyway:10-alpine`, mounting `./migrations/sql:/flyway/sql:ro`, depending on `postgres`, and running `migrate -validateOnMigrate=true`.

- [ ] **Step 3: Create migration workflow**

Create `.github/workflows/db-migrate.yml` with SOPS decrypt, compose config validation, Flyway migrate, and evidence output steps.

- [ ] **Step 4: Create migration runbook**

Create `docs/superpowers/runbooks/database-migrations.md` covering local rehearsal, staging migration, production migration, failure handling, and rollback-by-forward-fix.

- [ ] **Step 5: Validate migration compose**

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.migrations.yml config
```

Expected: rendered config includes `flyway` service.

---

### Task 5: Observability Stack

**Files:**
- Create: `docker-compose.observability.yml`
- Create: `observability/prometheus/prometheus.yml`
- Create: `observability/prometheus/alerts/platform.yml`
- Create: `observability/grafana/provisioning/datasources/prometheus.yml`
- Create: `observability/grafana/provisioning/dashboards/platform.yml`
- Create: `observability/grafana/dashboards/platform-overview.json`
- Create: `docs/superpowers/runbooks/observability.md`
- Modify: `.github/scripts/validate_runtime_truth.py`

- [ ] **Step 1: Create observability compose overlay**

Create Prometheus and Grafana services with persistent volumes and config mounts.

- [ ] **Step 2: Create Prometheus config**

Scrape Prometheus itself, Traefik metrics, Postgres exporter, and each public service target listed in the root runtime contract.

- [ ] **Step 3: Create alert rules**

Create `PlatformTargetDown`, `HighHttp5xxRate`, and `PostgresDown` alert skeletons using available metrics.

- [ ] **Step 4: Create Grafana provisioning**

Create datasource, dashboard provider, and minimal dashboard JSON.

- [ ] **Step 5: Create observability runbook**

Document dashboards, alerts, service telemetry ownership, and incident response.

- [ ] **Step 6: Validate observability compose**

Run:

```powershell
docker compose -f docker-compose.yml -f docker-compose.observability.yml config
```

Expected: rendered config includes `prometheus` and `grafana` services.

---

### Task 6: Full Service CI Matrix Evidence

**Files:**
- Create: `.github/workflows/release-evidence.yml`
- Modify: `docs/TESTING.md`
- Modify: `docs/superpowers/runbooks/release-promotion-drill.md`
- Modify: `.github/scripts/validate_runtime_truth.py`

- [ ] **Step 1: Extend release evidence table**

Update release evidence to include: layer, repo, commit SHA, image tag/digest, command, CI run URL, timestamp, result.

- [ ] **Step 2: Create release evidence workflow**

Create `.github/workflows/release-evidence.yml` that runs `python .github/scripts/validate_runtime_truth.py` and fails if evidence table shape drifts.

- [ ] **Step 3: Update service CI matrix docs**

`docs/TESTING.md` must list each service repo, required local command, required CI artifact, and image evidence field.

- [ ] **Step 4: Enforce evidence shape**

Update `validate_runtime_truth.py` table parsing expectations to require all evidence columns and rows.

- [ ] **Step 5: Run validation**

Run:

```powershell
python .github/scripts/validate_runtime_truth.py
$env:PYTHONPATH='.github/scripts'; pytest .github/scripts/test_validate_runtime_truth.py -q
```

Expected: validator passes and tests pass.

---

### Task 7: Close Hardening Debt Register

**Files:**
- Modify: `docs/superpowers/audits/enterprise-exit-review-2026-05-02.md`
- Modify: `.github/scripts/validate_runtime_truth.py`
- Modify: `.github/workflows/docs-consistency.yml`
- Modify: `.github/workflows/test-platform.yml`

- [ ] **Step 1: Update debt register rows**

Change each debt row to point to the checked-in artifact and validation command instead of saying future debt.

- [ ] **Step 2: Update root workflows**

Make root workflows run:

```bash
python .github/scripts/validate_runtime_truth.py
python .github/scripts/validate_traefik_routes.py
PYTHONPATH=.github/scripts pytest .github/scripts/test_validate_runtime_truth.py .github/scripts/test_validate_traefik_routes.py -q
```

- [ ] **Step 3: Run final root verification**

Run:

```powershell
python .github/scripts/validate_runtime_truth.py
python .github/scripts/validate_traefik_routes.py
$env:PYTHONPATH='.github/scripts'; pytest .github/scripts/test_validate_runtime_truth.py .github/scripts/test_validate_traefik_routes.py -q
docker compose -f docker-compose.yml -f docker-compose.staging.yml config
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
docker compose -f docker-compose.yml -f docker-compose.migrations.yml config
docker compose -f docker-compose.yml -f docker-compose.observability.yml config
```

Expected: every command exits 0.
