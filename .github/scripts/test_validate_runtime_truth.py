from __future__ import annotations

from validate_runtime_truth import (
    ROOT,
    _extract_markdown_table,
    _extract_published_ports,
    _require_contains,
    _require_documented_artifact,
    _require_regex,
    _stale_runtime_ports,
)


def test_extract_markdown_table_strips_backticks_and_stops_after_table():
    text = """
Before

| Layer | Repository | Commit SHA | Image tag or digest | Command | CI run URL | Timestamp | Result |
|-------|------------|------------|---------------------|---------|------------|-----------|--------|
| root orchestration | `account-creation` |  | n/a | `python .github/scripts/validate_runtime_truth.py` |  |  |  |
| `common` | `common` |  | n/a | `PYTHONPATH=src pytest tests -q` |  |  |  |
| `registrar` | `registrar` |  |  | `PYTHONPATH=src;../common/src pytest tests -q` |  |  |  |

After
| ignored | row |
"""

    rows = _extract_markdown_table(text, "| Layer | Repository | Commit SHA | Image tag or digest | Command | CI run URL | Timestamp | Result |")

    assert rows == {
        "root orchestration": "python .github/scripts/validate_runtime_truth.py",
        "common": "PYTHONPATH=src pytest tests -q",
        "registrar": "PYTHONPATH=src;../common/src pytest tests -q",
    }


def test_stale_runtime_ports_detects_only_full_local_urls():
    text = "localhost:8799 127.0.0.1:8801 port 8802 http://localhost:8709"

    assert _stale_runtime_ports(text) == ["8799", "8801"]


def test_extract_published_ports_handles_compose_port_formats():
    compose = {
        "services": {
            "registrar": {"ports": ["8709:8000"]},
            "tts-proxy": {"ports": ["127.0.0.1:8700:8000"]},
            "postgres": {"ports": [5432]},
            "common": {},
        }
    }

    assert _extract_published_ports(compose) == {
        "registrar": {"8709"},
        "tts-proxy": {"8700"},
        "postgres": {"5432"},
        "common": set(),
    }


def test_require_contains_appends_error_only_when_missing():
    errors: list[str] = []

    _require_contains(errors, "runtime truth", "truth", "doc.md")
    _require_contains(errors, "runtime truth", "missing", "doc.md")

    assert errors == ["doc.md missing expected text: missing"]


def test_require_regex_appends_error_only_when_missing():
    errors: list[str] = []

    _require_regex(errors, "line one\nline two", r"(?m)^line two$", "doc.md")
    _require_regex(errors, "line one\nline two", r"(?m)^line three$", "doc.md")

    assert errors == ["doc.md missing pattern: (?m)^line three$"]


def test_require_documented_artifact_checks_existing_path_in_docs():
    errors: list[str] = []
    artifact = __import__("pathlib").Path(__file__)
    docs_text = ".github/scripts/test_validate_runtime_truth.py"

    _require_documented_artifact(errors, docs_text, artifact, "docs/TESTING.md")

    assert errors == []


def test_require_documented_artifact_reports_existing_undocumented_path():
    errors: list[str] = []
    artifact = __import__("pathlib").Path(__file__)

    _require_documented_artifact(errors, "", artifact, "docs/TESTING.md")

    assert errors == ["docs/TESTING.md missing expected text: .github/scripts/test_validate_runtime_truth.py"]


def test_require_documented_artifact_does_not_require_service_worktree_path_to_exist():
    errors: list[str] = []
    artifact = ROOT / "missing-service" / "tests" / "test_smoke.py"
    docs_text = "missing-service/tests/test_smoke.py"

    _require_documented_artifact(errors, docs_text, artifact, "docs/TESTING.md")

    assert errors == []

def test_runtime_smoke_artifact_is_documented_by_validator():
    validator = (ROOT / ".github" / "scripts" / "validate_runtime_truth.py").read_text(encoding="utf-8")

    assert "scripts/smoke-runtime-contract.ps1" in validator
    assert "pg_isready -U ccs -d account_creator" in validator
    assert "http://localhost:8709/api/v1/health" in validator
    assert "http://127.0.0.1:1421" in validator
    assert "Assert-ImageFileNotEmpty" in validator