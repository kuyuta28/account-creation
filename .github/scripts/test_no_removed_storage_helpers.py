from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKERS = ROOT / "registrar" / "src" / "checkers"
# Sync storage helpers that the checkers used to call directly. The async
# rewrite moved checkers to *_async variants in src.core.account_record, so
# these bare names must not appear in checker call sites. (They still exist
# in account_record.py as the sync wrappers kept for backward compat with
# other call sites — that is intentional and out of scope here.)
FORBIDDEN = (
    "repo_update(",
    "repo_delete_many(",
    "repo_all(",
    "init_repo(",
)


def test_checkers_do_not_reference_removed_storage_helpers():
    offenders: list[str] = []
    for path in CHECKERS.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            if token in source:
                offenders.append(f"{path.relative_to(ROOT)}:{token}")

    assert offenders == []
