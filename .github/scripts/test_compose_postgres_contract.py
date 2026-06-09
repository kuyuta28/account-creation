from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.yml"


def _service_block(source: str, service: str) -> str:
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"  {service}:")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("  ") and not lines[i].startswith("    ")), len(lines))
    return "\n".join(lines[start:end])


def test_runtime_services_receive_postgres_database_url():
    """Each Postgres-backed service must inherit DATABASE_URL via the x-app-env
    anchor. We verify the anchor itself carries the dev DSN."""
    source = COMPOSE.read_text(encoding="utf-8")
    assert "DATABASE_URL: postgresql+asyncpg://ccs:ccs_dev_only@postgres:5432/account_creator" in source
    # Anchor must reach every Postgres-backed service via <<: *app-env.
    for service in ("registrar", "mail-service", "aa-proxy", "tts-proxy"):
        block = _service_block(source, service)
        assert "<<: *app-env" in block, f"{service} does not inherit x-app-env"


def test_postgres_backed_services_wait_for_postgres_health():
    source = COMPOSE.read_text(encoding="utf-8")

    for service in ("registrar", "mail-service", "aa-proxy", "tts-proxy"):
        block = _service_block(source, service)
        assert "postgres:" in block
        assert "condition: service_healthy" in block
