from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER = ROOT / "aa-proxy" / "src" / "aa_proxy" / "server.py"
AA_REGISTRAR = ROOT / "aa-proxy" / "src" / "services" / "artificialanalysis_ai" / "registrar.py"


def test_aa_proxy_server_does_not_initialize_sqlite():
    source = SERVER.read_text(encoding="utf-8")

    assert "from common.database import init_db" not in source
    assert "init_db(" not in source
    assert ".mail.db_path" not in source


def test_aa_proxy_registrar_uses_async_postgres_session():
    """aa-proxy persists account state through the common async Postgres
    session. A regression that reintroduces sqlite3 / sync create_engine
    would silently bypass the dev Postgres volume and miss new accounts
    from mail-service."""
    source = AA_REGISTRAR.read_text(encoding="utf-8")
    assert "get_async_session" in source, (
        "aa-proxy registrar must use the common async Postgres session"
    )
    assert "sqlite3" not in source
    assert "sqlite_master" not in source
    assert "create_engine" not in source, (
        "aa-proxy should not spin up its own sync SQLAlchemy engine"
    )
