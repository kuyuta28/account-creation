from __future__ import annotations

from validate_runtime_truth import _extract_markdown_table, _extract_published_ports, _stale_runtime_ports


def test_extract_markdown_table_strips_backticks_and_stops_after_table():
    text = """
Before

| Layer | Command | Commit SHA | Timestamp | Result |
|-------|---------|------------|-----------|--------|
| root orchestration | `python .github/scripts/validate_runtime_truth.py` |  |  |  |
| `common` | `PYTHONPATH=src pytest tests -q` |  |  |  |
| `registrar` | `PYTHONPATH=src;../common/src pytest tests -q` |  |  |  |

After
| ignored | row |
"""

    rows = _extract_markdown_table(text, "| Layer | Command | Commit SHA | Timestamp | Result |")

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
