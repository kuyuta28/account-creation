from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMON_INIT = ROOT / "common" / "src" / "common" / "database" / "__init__.py"


def test_common_database_exports_async_account_helpers():
    source = COMMON_INIT.read_text(encoding="utf-8")

    assert "get_accounts_async" in source
    assert "get_account_by_email_async" in source
    assert "update_account_async" in source
    assert "delete_account_async" in source
    assert "get_mail_providers_async" in source
    assert "upsert_mail_provider_async" in source
