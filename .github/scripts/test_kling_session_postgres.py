from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KLING_REGISTRAR = ROOT / "registrar" / "src" / "services" / "klingai_com" / "registrar.py"


def test_kling_session_uses_internal_postgres_client_not_sqlite_storage():
    source = KLING_REGISTRAR.read_text(encoding="utf-8")

    assert "InternalClient" in source
    assert "from common.database import init_db" not in source
    assert "db_path" not in source
    assert "repo_save" not in source
    assert "await save_session(_db" not in source
