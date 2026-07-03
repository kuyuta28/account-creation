from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.yml"
ENV = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

POSTGRES_BACKED = ("registrar", "mail-service", "aa-proxy", "tts-proxy")
ALL_APP_SERVICES = POSTGRES_BACKED

DEV_PASSWORD = "ccs_dev_only"
DEV_DSN = f"postgresql+asyncpg://ccs:{DEV_PASSWORD}@postgres:5432/account_creator"


def _service_block(source: str, service: str) -> str:
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"  {service}:")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("  ") and not lines[i].startswith("    ")), len(lines))
    return "\n".join(lines[start:end])


def test_postgres_backed_services_reference_env_database_url():
    """DATABASE_URL is interpolated from .env into every Postgres-backed service.
    Compose must NOT hardcode the DSN (DRY: single source of truth in .env)."""
    source = COMPOSE.read_text(encoding="utf-8")
    for service in POSTGRES_BACKED:
        block = _service_block(source, service)
        assert "DATABASE_URL: ${DATABASE_URL}" in block, (
            f"{service} must reference ${{DATABASE_URL}}, not hardcode the DSN"
        )


def test_env_files_carry_dev_dsn():
    """The dev DSN lives in .env and .env.example, with the dev-only password."""
    for path in (ENV, ENV_EXAMPLE):
        text = path.read_text(encoding="utf-8")
        assert DEV_DSN in text, f"{path.name} must contain the dev DSN with {DEV_PASSWORD}"


def test_dev_password_is_distinct_from_prod():
    """A leaked compose file must never match a real production password."""
    source = COMPOSE.read_text(encoding="utf-8")
    assert "ccs_secret" not in source, "dev compose contains prod-like 'ccs_secret'"
    assert DEV_PASSWORD in source


def test_app_services_declare_required_env():
    """All app services must expose APP_ENV, INTERNAL_API_KEY, SENTRY_DSN and
    the service-specific port variables used by their Dockerfiles."""
    source = COMPOSE.read_text(encoding="utf-8")
    required = [
        "APP_ENV",
        "INTERNAL_API_KEY",
        "SENTRY_DSN",
    ]
    per_service = {
        "aa-proxy": ["AA_PORT"],
        "mail-service": ["MAIL_PORT"],
        "tts-proxy": ["TTS_PORT", "NINE_ROUTER_DB"],
        "registrar": ["REGISTRAR_HOST", "REGISTRAR_PORT", "CAMOUFOX_HEADLESS"],
    }
    for service in ALL_APP_SERVICES:
        block = _service_block(source, service)
        for key in required + per_service[service]:
            assert f"{key}:" in block, f"{service} missing env key {key}"


def test_postgres_backed_services_wait_for_postgres_health():
    """No app service should start before Postgres is ready."""
    source = COMPOSE.read_text(encoding="utf-8")
    for service in ALL_APP_SERVICES:
        block = _service_block(source, service)
        assert "postgres:" in block
        assert "condition: service_healthy" in block


def test_postgres_single_shared_network():
    """Local=prod: one flat account-net, no internal isolation network.
    Host is trusted and must reach Postgres (host-browser-agent). An
    internal:true network would block the 127.0.0.1:5432 port-publish."""
    source = COMPOSE.read_text(encoding="utf-8")
    assert "postgres-internal" not in source, "postgres-internal network removed (local=prod)"
    assert "internal: true" not in source, "no internal:true network (host must reach DB)"


def test_all_ports_bound_to_loopback():
    """No port should bind 0.0.0.0 — single-user local box, no LAN exposure."""
    import re
    source = COMPOSE.read_text(encoding="utf-8")
    # match port mappings like  - "127.0.0.1:NN:NN"  or  - "NN:NN"
    bad = re.findall(r'-\s*"(\d+:\d+)"', source)
    assert not bad, f"ports bound to all interfaces (should be 127.0.0.1): {bad}"


def test_web_ui_healthcheck_uses_internal_port_80():
    source = COMPOSE.read_text(encoding="utf-8")
    block = _service_block(source, "web-ui")
    assert "127.0.0.1:80" in block, "web-ui healthcheck must target nginx internal port 80"