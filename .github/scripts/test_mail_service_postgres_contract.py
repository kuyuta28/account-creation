from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLIENTS = (
    ROOT / "mail-service" / "src" / "mail_service" / "mailbox_client.py",
    ROOT / "mail-service" / "src" / "mail_service" / "providers_client.py",
    ROOT / "mail-service" / "src" / "mail_service" / "sms_client.py",
)


def test_mail_service_clients_use_async_postgres():
    """mail-service mailbox / provider / SMS clients must all read and write
    through common.database._engine.get_async_session. Any SQLite path here
    would silently bypass the dev Postgres volume and miss records."""
    for path in CLIENTS:
        source = path.read_text(encoding="utf-8")
        assert "get_async_session" in source, (
            f"{path.name} must use the common async Postgres session"
        )
        assert "sqlite3" not in source
        assert "sqlite_master" not in source
        assert "create_engine" not in source, (
            f"{path.name} should not spin up its own sync SQLAlchemy engine"
        )
