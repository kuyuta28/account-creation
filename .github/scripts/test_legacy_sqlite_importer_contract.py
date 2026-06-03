from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMPORTER = ROOT / "scripts" / "import_legacy_sqlite_to_postgres.py"


def test_legacy_importer_has_safe_dry_run_contract():
    source = IMPORTER.read_text(encoding="utf-8")

    assert "--dry-run" in source
    assert "--apply" in source
    assert "DATABASE_URL" in source
    assert "postgresql+asyncpg" in source
    assert "DELETE FROM" not in source.upper()
    assert "DROP TABLE" not in source.upper()
    assert "ON CONFLICT" in source


def test_legacy_importer_covers_main_legacy_sqlite_scopes():
    source = IMPORTER.read_text(encoding="utf-8")

    assert "registrar/data/accounts.db" in source
    assert "mail-service/data/mail.db" in source
    assert "aa-proxy/data/accounts.db" in source
    assert "tts-proxy/data/accounts.db" in source
    assert "accounts_gmail" in source
    assert "mail_providers" in source
    assert "provider_domain_tags" in source
    assert "tts.gemini_key_rpd" in source
