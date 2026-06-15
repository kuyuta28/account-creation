from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
README_DOC = ROOT / "README.md"
COMPOSE_FILE = ROOT / "docker-compose.yml"
PYTEST_INI = ROOT / "pytest.ini"
DOCS_CONSISTENCY_WORKFLOW = ROOT / ".github" / "workflows" / "docs-consistency.yml"
ROOT_CONTRACT_WORKFLOW = ROOT / ".github" / "workflows" / "test-platform.yml"
ARCH_DOC = ROOT / "docs" / "ARCHITECTURE.md"
API_DOC = ROOT / "docs" / "API-ARCHITECTURE.md"
ENTERPRISE_STANDARDS_DOC = ROOT / "docs" / "ENTERPRISE-STANDARDS.md"
TESTING_DOC = ROOT / "docs" / "TESTING.md"
RELEASE_RUNBOOK = ROOT / "docs" / "superpowers" / "runbooks" / "release-promotion-drill.md"
EXIT_REVIEW = ROOT / "docs" / "superpowers" / "audits" / "enterprise-exit-review-2026-05-02.md"
INTERNAL_API_CONTRACT = ROOT / "docs" / "superpowers" / "contracts" / "internal-api.md"
TRAEFIK_ROUTE_CONTRACT = ROOT / "docs" / "superpowers" / "contracts" / "traefik-public-routes.md"
TRAEFIK_ROUTE_VALIDATOR = ROOT / ".github" / "scripts" / "validate_traefik_routes.py"
TRAEFIK_ROUTE_VALIDATOR_TEST = ROOT / ".github" / "scripts" / "test_validate_traefik_routes.py"
TRAEFIK_ROUTE_SMOKE = ROOT / "scripts" / "smoke-traefik-routes.ps1"
SOPS_CONFIG = ROOT / ".sops.yaml"
STAGING_SECRETS = ROOT / "config" / "staging" / "secrets.yaml"
PROD_SECRETS = ROOT / "config" / "prod" / "secrets.yaml"
STAGING_SECRETS_EXAMPLE = ROOT / "config" / "staging" / "secrets.example.yaml"
PROD_SECRETS_EXAMPLE = ROOT / "config" / "prod" / "secrets.example.yaml"
SECRETS_RUNBOOK = ROOT / "docs" / "superpowers" / "runbooks" / "secrets-rotation.md"
STAGING_COMPOSE = ROOT / "docker-compose.staging.yml"
PROD_COMPOSE = ROOT / "docker-compose.prod.yml"
MIGRATIONS_COMPOSE = ROOT / "docker-compose.migrations.yml"
OBSERVABILITY_COMPOSE = ROOT / "docker-compose.observability.yml"
DEPLOY_STAGING_WORKFLOW = ROOT / ".github" / "workflows" / "deploy-staging.yml"
DEPLOY_PRODUCTION_WORKFLOW = ROOT / ".github" / "workflows" / "deploy-production.yml"
DB_MIGRATE_WORKFLOW = ROOT / ".github" / "workflows" / "db-migrate.yml"
RELEASE_EVIDENCE_WORKFLOW = ROOT / ".github" / "workflows" / "release-evidence.yml"
GITOPS_RUNBOOK = ROOT / "docs" / "superpowers" / "runbooks" / "gitops-deployment.md"
MIGRATION_RUNBOOK = ROOT / "docs" / "superpowers" / "runbooks" / "database-migrations.md"
OBSERVABILITY_RUNBOOK = ROOT / "docs" / "superpowers" / "runbooks" / "observability.md"
PLATFORM_MIGRATION = ROOT / "migrations" / "sql" / "V001__platform_bootstrap.sql"
PROMETHEUS_CONFIG = ROOT / "observability" / "prometheus" / "prometheus.yml"
PROMETHEUS_ALERTS = ROOT / "observability" / "prometheus" / "alerts" / "platform.yml"
GRAFANA_DATASOURCE = ROOT / "observability" / "grafana" / "provisioning" / "datasources" / "prometheus.yml"
GRAFANA_DASHBOARD_PROVIDER = ROOT / "observability" / "grafana" / "provisioning" / "dashboards" / "platform.yml"
GRAFANA_DASHBOARD = ROOT / "observability" / "grafana" / "dashboards" / "platform-overview.json"
CURRENT_RELEASE_EVIDENCE = ROOT / "docs" / "superpowers" / "release-evidence" / "current-platform-release.md"


EXPECTED_PORTS = {
    "registrar": "8709",
    "mail-service": "8701",
    "aa-proxy": "8702",
    "tts-proxy": "8700",
    "postgres": "5432",
    "traefik": "80",
    "traefik-dashboard": "8080",
}

EXPECTED_PREFIXES = {
    "registrar": "/api/v1",
    "mail-service": "/api/v1",
    "aa-proxy": "/api/v1",
    "tts-proxy": "/api",
}

EXPECTED_HEALTH = {
    "registrar": "/api/v1/health",
    "mail-service": "/api/health",
    "aa-proxy": "/api/health",
    "tts-proxy": "/api/health",
}

EXPECTED_SERVICE_TEST_COMMANDS = {
    "common": "PYTHONPATH=src pytest tests -q",
    "registrar": "PYTHONPATH=src;../common/src pytest tests -q",
    "mail-service": "PYTHONPATH=src;../common/src pytest tests -q",
    "aa-proxy": "PYTHONPATH=src;../common/src pytest tests -q",
    "tts-proxy": "PYTHONPATH=src;../common/src pytest tests -q",
    "web-ui": "npm test -- --run",
}

# Web-ui config uses relative paths (proxied via Traefik in dev stack).
EXPECTED_WEBUI_CONFIG = {
    "API_BASE_URL": "/api/v1",
    "TTS_BASE_URL": "/tts",
}

EXPECTED_CONTRACT_ARTIFACTS = (
    ROOT / ".github" / "scripts" / "test_validate_runtime_truth.py",
    TRAEFIK_ROUTE_VALIDATOR_TEST,
    ROOT / "common" / "tests" / "contracts" / "test_no_reverse_imports.py",
    ROOT / "common" / "tests" / "test_context.py",
    ROOT / "registrar" / "tests" / "unit" / "test_internal_client.py",
    ROOT / "registrar" / "tests" / "smoke" / "test_startup_contract.py",
    ROOT / "registrar" / "tests" / "smoke" / "test_postgres_bootstrap_contract.py",
    ROOT / "web-ui" / "src" / "__tests__" / "config.contract.test.ts",
    ROOT / "web-ui" / "src" / "__tests__" / "api.client.test.ts",
    ROOT / "web-ui" / "src" / "__tests__" / "App.test.tsx",
    ROOT / "web-ui" / "src" / "__tests__" / "ConfigPage.test.tsx",
    ROOT / "web-ui" / "src" / "__tests__" / "AccountsPage.test.tsx",
    ROOT / "web-ui" / "src" / "__tests__" / "CreatePage.test.tsx",
)

EXPECTED_SERVICE_CI_ARTIFACTS = (
    ROOT / "common" / ".github" / "workflows" / "ci.yml",
    ROOT / "registrar" / ".github" / "workflows" / "ci.yml",
    ROOT / "mail-service" / ".github" / "workflows" / "ci.yml",
    ROOT / "aa-proxy" / ".github" / "workflows" / "ci.yml",
    ROOT / "tts-proxy" / ".github" / "workflows" / "ci.yml",
    ROOT / "web-ui" / ".github" / "workflows" / "ci.yml",
)

EXPECTED_SERVICE_TEST_FLOOR_ARTIFACTS = (
    ROOT / "common" / "tests" / "test_smoke.py",
    ROOT / "registrar" / "tests" / "unit" / "test_api_services.py",
    ROOT / "mail-service" / "tests" / "test_smoke.py",
    ROOT / "mail-service" / "tests" / "test_config.py",
    ROOT / "aa-proxy" / "tests" / "test_smoke.py",
    ROOT / "aa-proxy" / "tests" / "test_config.py",
    ROOT / "tts-proxy" / "tests" / "test_smoke.py",
    ROOT / "tts-proxy" / "tests" / "test_config.py",
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_compose() -> dict:
    return yaml.safe_load(_read_text(COMPOSE_FILE))


def _extract_published_ports(compose: dict) -> dict[str, set[str]]:
    ports: dict[str, set[str]] = {}
    for service_name, service in compose.get("services", {}).items():
        published: set[str] = set()
        for raw in service.get("ports", []):
            if isinstance(raw, int):
                published.add(str(raw))
                continue
            parts = str(raw).split(":")
            if len(parts) >= 2:
                published.add(parts[-2] if len(parts) == 3 else parts[0])
        ports[service_name] = published
    return ports


def _require_contains(errors: list[str], text: str, needle: str, label: str) -> None:
    if needle not in text:
        errors.append(f"{label} missing expected text: {needle}")


def _require_regex(errors: list[str], text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text, flags=re.MULTILINE) is None:
        errors.append(f"{label} missing pattern: {pattern}")


def _extract_markdown_table(text: str, header: str, value_column: str = "Command") -> dict[str, str]:
    lines = text.splitlines()
    headers = [cell.strip() for cell in header.strip("|").split("|")]
    try:
        value_index = headers.index(value_column)
    except ValueError:
        value_index = 1
    for index, line in enumerate(lines):
        if line.strip() != header:
            continue
        rows: dict[str, str] = {}
        for row in lines[index + 2:]:
            if not row.startswith("|"):
                break
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) > value_index:
                rows[cells[0].strip("`")] = cells[value_index].strip("`")
        return rows
    return {}


def _stale_runtime_ports(text: str) -> list[str]:
    return [
        port
        for port in ("8799", "8800", "8801", "8802", "8888")
        if f"localhost:{port}" in text or f"127.0.0.1:{port}" in text
    ]


ROOT_OWNED_ARTIFACT_PREFIXES = (".github/", "docs/", "README.md", "docker-compose.yml", "pytest.ini")


def _require_documented_artifact(errors: list[str], docs_text: str, artifact: Path, label: str) -> None:
    artifact_path = str(artifact.relative_to(ROOT)).replace("\\", "/")
    if artifact_path.startswith(ROOT_OWNED_ARTIFACT_PREFIXES) and not artifact.exists():
        errors.append(f"Missing expected artifact: {artifact.relative_to(ROOT)}")
        return
    _require_contains(errors, docs_text, artifact_path, label)


def main() -> int:
    compose = _load_compose()
    docs_consistency_workflow_text = _read_text(DOCS_CONSISTENCY_WORKFLOW)
    root_contract_workflow_text = _read_text(ROOT_CONTRACT_WORKFLOW)
    readme_text = _read_text(README_DOC)
    arch_text = _read_text(ARCH_DOC)
    api_text = _read_text(API_DOC)
    enterprise_standards_text = _read_text(ENTERPRISE_STANDARDS_DOC)
    testing_text = _read_text(TESTING_DOC)
    release_runbook_text = _read_text(RELEASE_RUNBOOK)
    exit_review_text = _read_text(EXIT_REVIEW)
    internal_api_contract_text = _read_text(INTERNAL_API_CONTRACT)
    pytest_ini_text = _read_text(PYTEST_INI)
    errors: list[str] = []

    _require_contains(errors, docs_consistency_workflow_text, "name: Docs Consistency", ".github/workflows/docs-consistency.yml")
    _require_contains(errors, docs_consistency_workflow_text, "python .github/scripts/validate_runtime_truth.py", ".github/workflows/docs-consistency.yml")
    _require_contains(errors, docs_consistency_workflow_text, "python .github/scripts/validate_traefik_routes.py", ".github/workflows/docs-consistency.yml")
    _require_contains(errors, docs_consistency_workflow_text, "pytest .github/scripts/test_validate_runtime_truth.py .github/scripts/test_validate_traefik_routes.py -q", ".github/workflows/docs-consistency.yml")
    _require_contains(errors, root_contract_workflow_text, "name: Root Orchestration Contract Checks", ".github/workflows/test-platform.yml")
    _require_contains(errors, root_contract_workflow_text, "root-orchestration-contract", ".github/workflows/test-platform.yml")
    _require_contains(errors, root_contract_workflow_text, "python .github/scripts/validate_runtime_truth.py", ".github/workflows/test-platform.yml")
    _require_contains(errors, root_contract_workflow_text, "python .github/scripts/validate_traefik_routes.py", ".github/workflows/test-platform.yml")
    _require_contains(errors, root_contract_workflow_text, "pytest .github/scripts/test_validate_runtime_truth.py .github/scripts/test_validate_traefik_routes.py -q", ".github/workflows/test-platform.yml")
    for forbidden_workflow_claim in ("service CI", "migration runner", "bootstrap-postgres"):
        if forbidden_workflow_claim in docs_consistency_workflow_text or forbidden_workflow_claim in root_contract_workflow_text:
            errors.append(f"Root workflows overclaim unsupported responsibility: {forbidden_workflow_claim}")

    published_ports = _extract_published_ports(compose)


    postgres_healthcheck = compose.get("services", {}).get("postgres", {}).get("healthcheck", {}).get("test", [])
    postgres_healthcheck_text = " ".join(str(part) for part in postgres_healthcheck)
    if "pg_isready -U ccs -d account_creator" not in postgres_healthcheck_text:
        errors.append("docker-compose.yml postgres healthcheck must check account_creator database, not implicit ccs database")

    registrar_dockerfile = ROOT / "registrar" / "Dockerfile"
    registrar_dockerfile_text = _read_text(registrar_dockerfile) if registrar_dockerfile.exists() else ""
    if "http://localhost:8709/api/v1/health" not in registrar_dockerfile_text:
        errors.append("registrar/Dockerfile healthcheck must hit /api/v1/health")

    registrar_config = ROOT / "registrar" / "config" / "config.yaml"
    registrar_config_text = _read_text(registrar_config) if registrar_config.exists() else ""
    if "http://127.0.0.1:1421" not in registrar_config_text:
        errors.append("registrar/config/config.yaml CORS origins must include http://127.0.0.1:1421 for Vite dev server")

    runtime_smoke = ROOT / "scripts" / "smoke-runtime-contract.ps1"
    if not runtime_smoke.exists():
        errors.append("Missing expected artifact: scripts/smoke-runtime-contract.ps1")
    else:
        runtime_smoke_text = _read_text(runtime_smoke)
        for expected_text in (
            "build --no-cache registrar aa-proxy mail-service tts-proxy",
            "Assert-ImageFileNotEmpty",
            "http://localhost:8709/api/v1/health",
            "Access-Control-Allow-Origin",
            "http://127.0.0.1:1421",
        ):
            _require_contains(errors, runtime_smoke_text, expected_text, "scripts/smoke-runtime-contract.ps1")
    for service_name, expected_port in EXPECTED_PORTS.items():
        if service_name == "traefik-dashboard":
            actual = published_ports.get("traefik", set())
        else:
            actual = published_ports.get(service_name, set())
        if expected_port not in actual:
            errors.append(
                f"docker-compose.yml port mismatch for {service_name}: "
                f"expected published port {expected_port}, found {sorted(actual)}"
            )

    for service_name, expected_port in EXPECTED_PORTS.items():
        if service_name == "traefik":
            _require_contains(errors, arch_text, "http://localhost/", "docs/ARCHITECTURE.md")
        elif service_name == "traefik-dashboard":
            _require_contains(
                errors,
                arch_text,
                "http://localhost:8080/",
                "docs/ARCHITECTURE.md",
            )
            _require_contains(
                errors,
                api_text,
                "http://localhost:8080/",
                "docs/API-ARCHITECTURE.md",
            )
            _require_contains(errors, readme_text, "dashboard `8080`", "README.md")
        elif service_name == "postgres":
            _require_contains(errors, arch_text, "localhost:5432", "docs/ARCHITECTURE.md")
            _require_contains(errors, readme_text, "`postgres`", "README.md")
            _require_contains(errors, readme_text, "`5432`", "README.md")
        else:
            url = f"http://localhost:{expected_port}"
            _require_contains(errors, arch_text, url, "docs/ARCHITECTURE.md")
            _require_contains(errors, api_text, url, "docs/API-ARCHITECTURE.md")
            _require_contains(errors, readme_text, f"`{service_name}`", "README.md")
            _require_contains(errors, readme_text, f"`{expected_port}`", "README.md")

    for service_name, expected_prefix in EXPECTED_PREFIXES.items():
        _require_contains(
            errors,
            api_text,
            f"Application prefix: `{expected_prefix}`",
            "docs/API-ARCHITECTURE.md",
        )

    for service_name, expected_health in EXPECTED_HEALTH.items():
        if service_name == "registrar":
            _require_contains(errors, arch_text, expected_health, "docs/ARCHITECTURE.md")
        else:
            _require_contains(errors, arch_text, expected_health, "docs/ARCHITECTURE.md")
            _require_contains(errors, api_text, f"Health endpoint: `{expected_health}`", "docs/API-ARCHITECTURE.md")

    _require_contains(
        errors,
        readme_text,
        "local orchestration truth, not a staging or production security posture",
        "README.md",
    )
    _require_contains(
        errors,
        arch_text,
        "not a staging or production security posture",
        "docs/ARCHITECTURE.md",
    )
    _require_regex(
        errors,
        arch_text,
        r"(?m)^- PostgreSQL is the canonical database for production and staging\.$",
        "docs/ARCHITECTURE.md",
    )
    _require_regex(
        errors,
        arch_text,
        r"(?m)^- SQLite is allowed only for isolated tests, local transitional tooling, or legacy conversion flows\.$",
        "docs/ARCHITECTURE.md",
    )
    _require_regex(
        errors,
        api_text,
        r"(?m)^- `web-ui` and backend services are validated in their own repositories\.$",
        "docs/API-ARCHITECTURE.md",
    )
    _require_contains(errors, enterprise_standards_text, "PostgreSQL là runtime truth", "docs/ENTERPRISE-STANDARDS.md")
    _require_contains(errors, enterprise_standards_text, "SQLite chỉ còn dành cho", "docs/ENTERPRISE-STANDARDS.md")
    _require_contains(errors, enterprise_standards_text, "SQLite chỉ còn dành cho", "docs/ENTERPRISE-STANDARDS.md")
    for envelope_field in ('"success"', '"data"', '"error"', '"meta"', '"request_id"'):
        _require_contains(errors, enterprise_standards_text, envelope_field, "docs/ENTERPRISE-STANDARDS.md")
        _require_contains(errors, api_text, envelope_field, "docs/API-ARCHITECTURE.md")

    release_evidence_header = "| Layer | Repository | Commit SHA | Image tag or digest | Command | CI run URL | Timestamp | Result |"
    release_evidence_rows = _extract_markdown_table(release_runbook_text, release_evidence_header)
    expected_release_evidence = {
        "root orchestration": "python .github/scripts/validate_runtime_truth.py",
        **EXPECTED_SERVICE_TEST_COMMANDS,
    }
    for layer, command in expected_release_evidence.items():
        if release_evidence_rows.get(layer) != command:
            errors.append(
                "docs/superpowers/runbooks/release-promotion-drill.md "
                f"release evidence row mismatch for {layer}: expected `{command}`, "
                f"found `{release_evidence_rows.get(layer)}`"
            )

    _require_contains(
        errors,
        testing_text,
        "Root validation treats these service artifact paths as a documented cross-repo contract; it does not require ignored service worktrees to exist in root CI. Web runtime config values are enforced in root API docs and executable validation remains owned by `web-ui`.",
        "docs/TESTING.md",
    )
    for service_name, command in EXPECTED_SERVICE_TEST_COMMANDS.items():
        _require_contains(errors, testing_text, f"| `{service_name}` |", "docs/TESTING.md")
        _require_contains(errors, testing_text, f"`{command}`", "docs/TESTING.md")
        if service_name != "web-ui":
            _require_contains(errors, pytest_ini_text, f"--ignore={service_name}", "pytest.ini")
            _require_contains(errors, pytest_ini_text, service_name, "pytest.ini")

    _require_contains(errors, release_runbook_text, release_evidence_header, "docs/superpowers/runbooks/release-promotion-drill.md")
    _require_contains(errors, release_runbook_text, "|-------|------------|------------|---------------------|---------|------------|-----------|--------|", "docs/superpowers/runbooks/release-promotion-drill.md")
    _require_contains(errors, release_runbook_text, "PostgreSQL migrations or bootstrap changes were exercised on a local fresh database for release rehearsal and on a fresh staging database before real promotion", "docs/superpowers/runbooks/release-promotion-drill.md")
    _require_contains(errors, release_runbook_text, "migration/bootstrap failure on PostgreSQL", "docs/superpowers/runbooks/release-promotion-drill.md")
    for artifact in (
        SOPS_CONFIG,
        STAGING_SECRETS,
        PROD_SECRETS,
        STAGING_SECRETS_EXAMPLE,
        PROD_SECRETS_EXAMPLE,
        SECRETS_RUNBOOK,
        STAGING_COMPOSE,
        PROD_COMPOSE,
        MIGRATIONS_COMPOSE,
        OBSERVABILITY_COMPOSE,
        DEPLOY_STAGING_WORKFLOW,
        DEPLOY_PRODUCTION_WORKFLOW,
        DB_MIGRATE_WORKFLOW,
        RELEASE_EVIDENCE_WORKFLOW,
        GITOPS_RUNBOOK,
        MIGRATION_RUNBOOK,
        OBSERVABILITY_RUNBOOK,
        PLATFORM_MIGRATION,
        PROMETHEUS_CONFIG,
        PROMETHEUS_ALERTS,
        GRAFANA_DATASOURCE,
        GRAFANA_DASHBOARD_PROVIDER,
        GRAFANA_DASHBOARD,
        CURRENT_RELEASE_EVIDENCE,
    ):
        if not artifact.exists():
            errors.append(f"Missing expected artifact: {artifact.relative_to(ROOT)}")
    secrets_runbook_text = _read_text(SECRETS_RUNBOOK) if SECRETS_RUNBOOK.exists() else ""
    for secret_key in ("DB_USER", "DB_PASSWORD", "DB_NAME", "DATABASE_URL", "INTERNAL_API_KEY", "SOPS_AGE_KEY"):
        _require_contains(errors, secrets_runbook_text + _read_text(STAGING_SECRETS_EXAMPLE) + _read_text(PROD_SECRETS_EXAMPLE), secret_key, "SOPS/AGE secrets artifacts")
    for debt in ("GitOps deployment", "SOPS/AGE secrets", "Flyway migration execution", "Observability stack", "Full service CI matrix", "Traefik public routing contract"):
        _require_contains(errors, exit_review_text, f"| {debt} |", "docs/superpowers/audits/enterprise-exit-review-2026-05-02.md")
    artifact_text = "\n".join(_read_text(path) for path in (GITOPS_RUNBOOK, MIGRATION_RUNBOOK, OBSERVABILITY_RUNBOOK, DEPLOY_STAGING_WORKFLOW, DEPLOY_PRODUCTION_WORKFLOW, DB_MIGRATE_WORKFLOW, RELEASE_EVIDENCE_WORKFLOW))
    for required_text in ("Deploy Staging", "Deploy Production", "Database Migration", "Release Evidence", "SOPS_AGE_KEY", "flyway", "prometheus", "grafana", "image tag or digest"):
        _require_contains(errors, artifact_text, required_text, "platform hardening artifacts")
    _require_documented_artifact(errors, api_text, TRAEFIK_ROUTE_CONTRACT, "docs/API-ARCHITECTURE.md")
    _require_documented_artifact(errors, arch_text, TRAEFIK_ROUTE_CONTRACT, "docs/ARCHITECTURE.md")
    _require_documented_artifact(errors, api_text, TRAEFIK_ROUTE_VALIDATOR, "docs/API-ARCHITECTURE.md")
    _require_documented_artifact(errors, arch_text, TRAEFIK_ROUTE_VALIDATOR, "docs/ARCHITECTURE.md")
    _require_documented_artifact(errors, api_text, TRAEFIK_ROUTE_SMOKE, "docs/API-ARCHITECTURE.md")
    _require_contains(errors, exit_review_text, "| Traefik public routing contract | `docs/superpowers/contracts/traefik-public-routes.md`, `.github/scripts/validate_traefik_routes.py`, `.github/scripts/test_validate_traefik_routes.py`, and `scripts/smoke-traefik-routes.ps1` |", "docs/superpowers/audits/enterprise-exit-review-2026-05-02.md")
    _require_contains(errors, pytest_ini_text, "--ignore=web-ui", "pytest.ini")

    for artifact in EXPECTED_CONTRACT_ARTIFACTS:
        _require_documented_artifact(errors, testing_text, artifact, "docs/TESTING.md")

    for artifact in EXPECTED_SERVICE_TEST_FLOOR_ARTIFACTS:
        _require_documented_artifact(errors, testing_text, artifact, "docs/TESTING.md")

    for artifact in EXPECTED_SERVICE_CI_ARTIFACTS:
        _require_documented_artifact(errors, testing_text, artifact, "docs/TESTING.md")

    for name, value in EXPECTED_WEBUI_CONFIG.items():
        _require_contains(errors, api_text, f"export const {name} = \"{value}\";", "docs/API-ARCHITECTURE.md")

    _require_contains(errors, api_text, "aa-proxy` at `http://localhost:8702`", "docs/API-ARCHITECTURE.md")
    _require_contains(errors, api_text, "docs/superpowers/contracts/internal-api.md", "docs/API-ARCHITECTURE.md")
    _require_contains(errors, internal_api_contract_text, "Required header: `X-Internal-Key`", "docs/superpowers/contracts/internal-api.md")
    _require_contains(errors, internal_api_contract_text, "GET /api/v1/internal/accounts", "docs/superpowers/contracts/internal-api.md")
    _require_contains(errors, internal_api_contract_text, "default timeout: `30s`", "docs/superpowers/contracts/internal-api.md")
    _require_contains(errors, internal_api_contract_text, "`GET` requests after network failure or timeout", "docs/superpowers/contracts/internal-api.md")
    _require_contains(errors, internal_api_contract_text, "idempotent `POST /upsert`", "docs/superpowers/contracts/internal-api.md")
    _require_contains(errors, internal_api_contract_text, "`PATCH`, `PUT`, `DELETE` only when caller knows", "docs/superpowers/contracts/internal-api.md")

    if "must be formalized in a dedicated contract document" in api_text:
        errors.append("docs/API-ARCHITECTURE.md still describes internal API contract as unformalized")
    if "bootstrap-postgres --database-url" in testing_text:
        errors.append("docs/TESTING.md references bootstrap-postgres command without a checked-in artifact")
    if "now owns the canonical PostgreSQL bootstrap command" in testing_text:
        errors.append("docs/TESTING.md overclaims registrar PostgreSQL bootstrap artifact ownership")

    for label, text in {
        "README.md": readme_text,
        "docs/ARCHITECTURE.md": arch_text,
        "docs/API-ARCHITECTURE.md": api_text,
        "docs/TESTING.md": testing_text,
    }.items():
        for stale_port in _stale_runtime_ports(text):
            errors.append(f"{label} contains stale runtime URL port: {stale_port}")
        for stale_storage_phrase in (
            "accounts.db as primary",
            "mail.db as primary",
            "accounts.db and mail.db as primary",
            "SQLite is the canonical database",
        ):
            if stale_storage_phrase in text:
                errors.append(f"{label} contains stale storage wording: {stale_storage_phrase}")

    if errors:
        print("Runtime truth validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Runtime truth validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
