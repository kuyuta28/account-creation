from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_ASYNC = ROOT / "tts-proxy" / "src" / "tts_proxy" / "db_async.py"
CONFIG = ROOT / "tts-proxy" / "src" / "tts_proxy" / "config.py"
MIGRATION = ROOT / "migrations" / "sql" / "V002__tts_rpd.sql"


def test_tts_rpd_requires_explicit_database_url_without_local_fallback():
    source = DB_ASYNC.read_text(encoding="utf-8")

    assert "os.environ[\"DATABASE_URL\"]" in source
    assert "localhost:5432" not in source
    assert "run_until_complete" not in source
    assert "def load_rpd_state(" not in source
    assert "def save_rpd_state(" not in source
    assert "def update_key_remaining(" not in source


def test_tts_config_no_longer_resolves_sqlite_db_path():
    source = CONFIG.read_text(encoding="utf-8")

    assert "def load_db_path" not in source
    assert "common.env" not in source
    assert "gemini.db_path" not in source


def test_tts_rpd_table_has_flyway_migration():
    source = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE SCHEMA IF NOT EXISTS tts" in source
    assert "CREATE TABLE IF NOT EXISTS tts.gemini_key_rpd" in source
    assert "PRIMARY KEY" in source
