from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "docker-compose.yml"
PYTEST_INI = ROOT / "pytest.ini"
ARCH_DOC = ROOT / "docs" / "ARCHITECTURE.md"
API_DOC = ROOT / "docs" / "API-ARCHITECTURE.md"
TESTING_DOC = ROOT / "docs" / "TESTING.md"
INTERNAL_API_CONTRACT = ROOT / "docs" / "superpowers" / "contracts" / "internal-api.md"
DESKTOP_CONFIG = ROOT / "desktop-ui" / "src" / "config.ts"


EXPECTED_PORTS = {
    "registrar": "8709",
    "mail-service": "8701",
    "aa-proxy": "8702",
    "tts-proxy": "8700",
    "any-auto-register": "8708",
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
    "desktop-ui": "npm test -- --run",
}

EXPECTED_DESKTOP_CONFIG = {
    "API_BASE_URL": "http://localhost:8709/api/v1",
    "TTS_BASE_URL": "http://localhost:8700",
    "AAR_BASE_URL": "http://localhost:8708",
}

EXPECTED_CONTRACT_ARTIFACTS = (
    ROOT / "common" / "tests" / "contracts" / "test_no_reverse_imports.py",
    ROOT / "common" / "tests" / "test_context.py",
    ROOT / "registrar" / "tests" / "smoke" / "test_startup_contract.py",
    ROOT / "desktop-ui" / "src" / "__tests__" / "config.contract.test.ts",
)

EXPECTED_SERVICE_TEST_FLOOR_ARTIFACTS = (
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


def main() -> int:
    compose = _load_compose()
    arch_text = _read_text(ARCH_DOC)
    api_text = _read_text(API_DOC)
    testing_text = _read_text(TESTING_DOC)
    internal_api_contract_text = _read_text(INTERNAL_API_CONTRACT)
    desktop_config_text = _read_text(DESKTOP_CONFIG)
    pytest_ini_text = _read_text(PYTEST_INI)
    errors: list[str] = []

    published_ports = _extract_published_ports(compose)

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
        elif service_name == "postgres":
            _require_contains(errors, arch_text, "localhost:5432", "docs/ARCHITECTURE.md")
        else:
            url = f"http://localhost:{expected_port}"
            _require_contains(errors, arch_text, url, "docs/ARCHITECTURE.md")
            _require_contains(errors, api_text, url, "docs/API-ARCHITECTURE.md")

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
        r"(?m)^- `desktop-ui` and backend services are validated in their own repositories\.$",
        "docs/API-ARCHITECTURE.md",
    )

    for service_name, command in EXPECTED_SERVICE_TEST_COMMANDS.items():
        _require_contains(errors, testing_text, f"| `{service_name}` |", "docs/TESTING.md")
        _require_contains(errors, testing_text, f"`{command}`", "docs/TESTING.md")
        if service_name != "desktop-ui":
            _require_contains(errors, pytest_ini_text, f"--ignore={service_name}", "pytest.ini")
            _require_contains(errors, pytest_ini_text, service_name, "pytest.ini")

    _require_contains(errors, pytest_ini_text, "--ignore=desktop-ui", "pytest.ini")
    _require_contains(errors, pytest_ini_text, "--ignore=any-auto-register", "pytest.ini")

    for artifact in EXPECTED_CONTRACT_ARTIFACTS:
        if not artifact.exists():
            errors.append(f"Missing expected contract artifact: {artifact.relative_to(ROOT)}")
        else:
            _require_contains(errors, testing_text, str(artifact.relative_to(ROOT)).replace("\\", "/"), "docs/TESTING.md")

    for artifact in EXPECTED_SERVICE_TEST_FLOOR_ARTIFACTS:
        if not artifact.exists():
            errors.append(f"Missing expected service test floor artifact: {artifact.relative_to(ROOT)}")
        else:
            _require_contains(errors, testing_text, str(artifact.relative_to(ROOT)).replace("\\", "/"), "docs/TESTING.md")

    for name, value in EXPECTED_DESKTOP_CONFIG.items():
        _require_contains(errors, api_text, f"export const {name} = \"{value}\";", "docs/API-ARCHITECTURE.md")
        _require_contains(errors, desktop_config_text, f"export const {name} = \"{value}\";", "desktop-ui/src/config.ts")

    _require_contains(errors, api_text, "`AAR_BASE_URL` means `any-auto-register`", "docs/API-ARCHITECTURE.md")
    _require_contains(errors, api_text, "aa-proxy` at `http://localhost:8702`", "docs/API-ARCHITECTURE.md")
    _require_contains(errors, api_text, "docs/superpowers/contracts/internal-api.md", "docs/API-ARCHITECTURE.md")
    _require_contains(errors, internal_api_contract_text, "Required header: `X-Internal-Key`", "docs/superpowers/contracts/internal-api.md")
    _require_contains(errors, internal_api_contract_text, "GET /api/v1/internal/accounts", "docs/superpowers/contracts/internal-api.md")

    if "must be formalized in a dedicated contract document" in api_text:
        errors.append("docs/API-ARCHITECTURE.md still describes internal API contract as unformalized")
    if "bootstrap-postgres --database-url" in testing_text:
        errors.append("docs/TESTING.md references bootstrap-postgres command without a checked-in artifact")

    for label, text in {
        "docs/ARCHITECTURE.md": arch_text,
        "docs/API-ARCHITECTURE.md": api_text,
        "docs/TESTING.md": testing_text,
    }.items():
        for stale_port in ("8799", "8800", "8801", "8802", "8888"):
            if f"localhost:{stale_port}" in text or f"127.0.0.1:{stale_port}" in text:
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
