from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GOOGLE_SESSION_SERVICE = ROOT / "registrar" / "src" / "api" / "services" / "google_session_service.py"
ELEVENLABS_REGISTRAR = ROOT / "registrar" / "src" / "services" / "elevenlabs_io" / "registrar.py"
OAUTH_LOOPS = ROOT / "registrar" / "src" / "core" / "google_oauth" / "_loops.py"
OAUTH_HANDLERS = ROOT / "registrar" / "src" / "core" / "google_oauth" / "_handlers.py"


def test_google_session_runtime_does_not_pass_sqlite_db_path():
    for path in [GOOGLE_SESSION_SERVICE, ELEVENLABS_REGISTRAR]:
        source = path.read_text(encoding="utf-8")

        assert "db_path=" not in source
        assert "db_path" not in source


def test_google_oauth_phone_challenge_uses_postgres_not_db_path():
    for path in [OAUTH_LOOPS, OAUTH_HANDLERS]:
        source = path.read_text(encoding="utf-8")

        assert "db_path" not in source
        assert "get_sms_phones_async" in source or path == OAUTH_LOOPS
