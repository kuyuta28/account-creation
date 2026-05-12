from __future__ import annotations

from validate_runtime_truth import _extract_markdown_table


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
