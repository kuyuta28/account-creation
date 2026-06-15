from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROVIDERS_INIT = ROOT / "registrar" / "src" / "mail" / "providers" / "__init__.py"
SHADOWED_MODULE = ROOT / "registrar" / "src" / "mail" / "providers.py"


def test_mail_provider_loader_is_exported_from_package_import_target():
    source = PROVIDERS_INIT.read_text(encoding="utf-8")

    assert "def load_provider_connections" in source
    assert "get_mail_providers_async" in source
    assert "get_async_session" in source
    assert "load_provider_connections" in source[source.index("__all__") :]


def test_shadowed_mail_providers_module_fails_loudly():
    source = SHADOWED_MODULE.read_text(encoding="utf-8")

    assert "Use src.mail.providers package" in source
    assert "def load_provider_connections" not in source
