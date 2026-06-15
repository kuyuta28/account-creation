from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEGACY_RUNTIME_PATHS = [
    ROOT / "registrar" / "src" / "core" / "database",
    ROOT / "registrar" / "src" / "core" / "storage.py",
    ROOT / "aa-proxy" / "src" / "core" / "database",
    ROOT / "aa-proxy" / "src" / "core" / "storage.py",
    ROOT / "mail-service" / "src" / "core" / "database",
    ROOT / "mail-service" / "src" / "core" / "storage.py",
    ROOT / "tts-proxy" / "src" / "tts_proxy" / "db.py",
]


def test_legacy_sqlite_runtime_modules_are_removed_outside_importer_boundary():
    existing = [str(path.relative_to(ROOT)) for path in LEGACY_RUNTIME_PATHS if path.exists()]

    assert existing == []
