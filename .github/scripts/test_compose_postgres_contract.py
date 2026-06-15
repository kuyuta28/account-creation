from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.yml"

POSTGRES_BACKED = ("registrar", "mail-service", "aa-proxy", "tts-proxy")
ALL_APP_SERVICES = POSTGRES_BACKED

DEV_PASSWORD = "ccs_dev_only"


def _service_block(source: str, service: str) -> str:
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"  {service}:")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("  ") and not lines[i].startswith("    ")), len(lines))
    return "\n".join(lines[start:end])


def test_postgres_backed_services_get_dev_database_url():
    """mail-service, aa-proxy, tts-proxy all use the async Postgres layer and
    need DATABASE_URL in dev. The DSN must point at the dev postgres with
    the dev-only password (NOT the historical ccs_secret)."""
    source = COMPOSE.read_text(encoding="utf-8")
    for service in POSTGRES_BACKED:
        block = _service_block(source, service)
        assert f"DATABASE_URL: postgresql+asyncpg://ccs:{DEV_PASSWORD}@postgres:5432/account_creator" in block, (
            f"{service} missing dev DATABASE_URL with {DEV_PASSWORD}"
        )


def test_dev_password_is_distinct_from_prod():
    """A leaked compose file must never match a real production password."""
    source = COMPOSE.read_text(encoding="utf-8")
    assert "ccs_secret" not in source, "dev compose contains prod-like 'ccs_secret'"
    assert DEV_PASSWORD in source


def test_app_services_inherit_x_app_env_anchor():
    source = COMPOSE.read_text(encoding="utf-8")
    for service in ALL_APP_SERVICES:
        block = _service_block(source, service)
        assert "<<: *app-env" in block, f"{service} does not inherit x-app-env"


def test_postgres_backed_services_wait_for_postgres_health():
    source = COMPOSE.read_text(encoding="utf-8")
    for service in ALL_APP_SERVICES:
        block = _service_block(source, service)
        assert "postgres:" in block
        assert "condition: service_healthy" in block
