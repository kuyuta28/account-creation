from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "mail-service" / "Dockerfile"
PYPROJECT = ROOT / "mail-service" / "pyproject.toml"


def test_mail_service_declares_asyncpg_for_postgres_runtime():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")
    pyproject = PYPROJECT.read_text(encoding="utf-8")

    assert "asyncpg" in dockerfile
    assert "asyncpg" in pyproject
