# Test Strategy

## Overview

Multi-layered testing approach đảm bảo code quality và regression prevention.

## Test Pyramid

```
         ┌─────────┐
         │   E2E   │  ← Browser automation, full user flows
         ├─────────┤
         │Integrate│  ← DB + Config, no browser
         ├─────────┤
         │  Unit   │  ← Pure functions, mocks
         ├─────────┤
         │  Smoke  │  ← Import checks, basic sanity
         └─────────┘
```

## Test Types

### 1. Smoke Tests (`tests/test_smoke.py`)

**Purpose:** Fast sanity checks — verify imports work, routes exist.

**Characteristics:**
- No network calls
- No database
- No mocks
- Execution: <1s per file

**Example:**
```python
def test_import_server_module():
    from src.server import app
    assert app is not None

def test_app_has_health_route():
    from src.server import app
    assert any(r.path == "/health" for r in app.routes)
```

### 2. Unit Tests (`tests/unit/`)

**Purpose:** Test individual functions/modules in isolation.

**Characteristics:**
- No network calls
- Real SQLite in tmpdir for isolated local fixtures only
- Mocks external dependencies (`@patch`)
- Test happy path + error path

**Example:**
```python
def test_insert_and_get_by_email(tmp_db):
    insert_account(tmp_db, _rec(api_key="sk_test"))
    row = get_account_by_email(tmp_db, "ELEVENLABS", "a@b.com")
    assert row["api_key"] == "sk_test"
```

### 3. Integration Tests (`tests/integration/`)

**Purpose:** Test component interactions — DB + config + business logic.

**Characteristics:**
- Prefer PostgreSQL-backed integration coverage for runtime-critical flows
- SQLite remains acceptable only for isolated fixture-style integration tests
- Real config loading from YAML
- No browser
- Test full pipelines

**Example:**
```python
def test_mail_config_providers_query(tmp_db):
    upsert_mail_provider(tmp_db, "mailslurp.com", api_key="sk")
    mail = MailConfig(db_path=tmp_db)
    assert "mailslurp.com:sk" in mail.providers_for()
```

### 4. E2E Tests (`tests/e2e/`)

**Purpose:** Full user flows with real browser automation.

**Characteristics:**
- Playwright browser
- Real external services (or mocks)
- Slowest to run

**Example:**
```python
async def test_google_oauth_flow(browser_context):
    page = await browser_context.new_page()
    await page.goto("https://accounts.google.com")
    # Full OAuth flow simulation
```

### 5. Fuzz Tests (`tests/fuzz/`)

**Purpose:** Discover edge cases and malformed inputs.

**Characteristics:**
- Random input generation
- Property-based testing (hypothesis)
- Invalid inputs

**Example:**
```python
@given(text(min_length=0, max_length=10000))
def test_text_split_handles_extreme_lengths(text):
    result = split_text(text, max_chars=5000)
    assert all(len(p) <= 5000 for p in result)
```

### 6. Static Analysis

**Tool:** Ruff + Pyright

**Purpose:** Catch type errors, style violations, security issues before runtime.

**Commands:**
```bash
# Type checking
cd <service> && pyright src/

# Linting
cd <service> && ruff check src/

# All checks
cd <service> && ruff check src/ && pyright src/
```

## Environment Isolation

### APP_ENV Configuration

| Env | DB Path | Use Case |
|-----|---------|----------|
| `prod` | `DATABASE_URL` → PostgreSQL | Canonical production runtime |
| `staging` | `DATABASE_URL` → PostgreSQL | Canonical staging runtime |
| `dev` | `DATABASE_URL` or local SQLite fixture | Local development and migration work |
| `test` | fresh tmpdir SQLite or ephemeral PostgreSQL | CI/CD and isolated tests |

### Test Configuration

Every `conftest.py` MUST set:
```python
import os
os.environ["APP_ENV"] = "test"
```

This ensures:
- test data stays isolated from dev/prod data
- SQLite fixtures stay disposable
- runtime-critical DB behavior can still be exercised through PostgreSQL-specific tests

## Running Tests

### Local Development

```bash
# All services
cd D:\business\account-creation

# Run by type
python -m pytest common/tests/ -v          # Smoke + Unit
python -m pytest registrar/tests/unit/ -v
python -m pytest registrar/tests/integration/ -v
python -m pytest tts-proxy/tests/ -v
python -m pytest mail-service/tests/ -v
python -m pytest aa-proxy/tests/ -v

# Quick smoke only
python -m pytest */tests/test_smoke.py -v

# Full suite (slow)
python -m pytest */tests/ -v
```

### CI/CD (GitHub Actions)

```yaml
- name: Run tests
  run: |
    python -m pytest common/tests/ -v
    python -m pytest tts-proxy/tests/ -v
    python -m pytest mail-service/tests/ -v
    python -m pytest aa-proxy/tests/ -v
    python -m pytest registrar/tests/unit/ -v
```

## Test Fixtures

### Required Fixtures

| Fixture | Scope | Purpose |
|----------|-------|---------|
| `tmp_db` | function | Fresh disposable SQLite DB in tmpdir |
| `tmp_path` | function | Temporary directory |
| `project_root` | session | Project root Path |
| `real_cfg` | session | Load real config YAML |

### Custom Fixtures

```python
@pytest.fixture
def make_account():
    """Factory tạo AccountRecord với overrides."""
    def _factory(**kwargs):
        defaults = dict(service="ELEVENLABS", email="test@example.com", password="P@ssw0rd!")
        defaults.update(kwargs)
        return AccountRecord(**defaults)
    return _factory
```

## Coverage Targets

| Test Type | Coverage Target |
|-----------|-----------------|
| Smoke | 100% (all modules importable) |
| Unit | 80% (critical paths) |
| Integration | 60% (DB interactions) |

## Troubleshooting

### ImportError: No module named 'common'

**Fix:** Add to `conftest.py`:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common" / "src"))
```

### Database locked errors

**Fix:** Always use `tmp_db` fixture which disposes engine after test.

### Test isolation failures

**Fix:** Ensure each test uses fresh `tmp_db` — don't share state.
