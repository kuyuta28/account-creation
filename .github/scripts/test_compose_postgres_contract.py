from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.yml"


def _service_block(source: str, service: str) -> str:
    lines = source.splitlines()
    start = next(i for i, line in enumerate(lines) if line == f"  {service}:")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("  ") and not lines[i].startswith("    ")), len(lines))
    return "\n".join(lines[start:end])


def test_runtime_services_receive_postgres_database_url():
    """Dev compose must NOT set DATABASE_URL on app services (they stay on
    SQLite). The prod overlay sets DATABASE_URL from the host env. We assert
    the absence in dev so a future refactor that accidentally re-adds it
    gets caught here."""
    source = COMPOSE.read_text(encoding="utf-8")
    # `DATABASE_URL` may appear in the postgres block (its bootstrap env) or
    # in the migrations overlay (Flyway). It must NOT appear in any app
    # service env block in the base dev compose.
    app_services = ("registrar", "mail-service", "aa-proxy", "tts-proxy")
    for service in app_services:
        block = _service_block(source, service)
        assert "DATABASE_URL" not in block, (
            f"{service} sets DATABASE_URL in dev compose. The dev stack "
            f"stays on the local SQLite mirror; only the prod/staging "
            f"overlay should set DATABASE_URL."
        )
    for service in app_services:
        block = _service_block(source, service)
        assert "<<: *app-env" in block, f"{service} does not inherit x-app-env"


def test_postgres_backed_services_wait_for_postgres_health():
    source = COMPOSE.read_text(encoding="utf-8")

    for service in ("registrar", "mail-service", "aa-proxy", "tts-proxy"):
        block = _service_block(source, service)
        assert "postgres:" in block
        assert "condition: service_healthy" in block
