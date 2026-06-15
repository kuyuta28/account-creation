from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SETTINGS_FILES = [
    ROOT / "mail-service" / "src" / "config" / "settings.py",
    ROOT / "aa-proxy" / "src" / "config" / "settings.py",
]


def test_service_settings_do_not_seed_sqlite_mail_providers_at_runtime():
    for path in SETTINGS_FILES:
        source = path.read_text(encoding="utf-8")
        seed_body = source[source.index("def seed_mail_providers") : source.index("def _parse_mail")]

        assert "upsert_mail_provider" not in seed_body
        assert "get_mail_providers" not in seed_body
        assert ".mail.db_path" not in seed_body


def test_service_settings_do_not_expose_sync_mail_provider_loader():
    for path in SETTINGS_FILES:
        source = path.read_text(encoding="utf-8")

        assert "def providers_for(" not in source
        assert "def all_providers(" not in source
        assert "from common.database import get_mail_providers" not in source
