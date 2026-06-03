# Enterprise Standards

Coding standards and conventions for all services.

---

## 1. Error Taxonomy

### Nguyên tắc
- **CẤM** dùng `RuntimeError` trực tiếp — phải dùng error class từ hierarchy.
- **CẤM** match lỗi bằng string (`"some error" in str(exc)`) — phải dùng `isinstance()`.
- **CẤM** nuốt lỗi (`except: pass`, `except Exception: pass`) — phải raise hoặc log + raise.
- Mỗi error class thuộc đúng 1 nhánh, dispatcher tự biết cách xử lý.

### Hierarchy (common/errors.py)

```
AppError (base)
├── RegistrationError       → lỗi trong flow đăng ký account
├── MailError               → lỗi liên quan đến mailbox/email provider
├── GoogleAuthError         → lỗi trong Google OAuth / login flow
├── CaptchaError            → captcha solve thất bại
├── BrowserError            → Playwright browser / page error
├── ConfigError             → config sai / thiếu setting
└── DatabaseError           → lỗi database layer
```

### API Error Hierarchy (src/api/exceptions.py)

```
AppError (base, từ common.errors)
  → FastAPI exception handlers tự convert thành ApiResponse envelope
  → 4 handlers: app_error_handler, validation_error_handler, http_exception_handler, generic_error_handler
```

---

## 2. API Response Envelope

### Chuẩn

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "uuid",
    "ts": "2026-04-03T06:37:09Z"
  }
}
```

Khi lỗi:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Không còn mailbox khả dụng cho service ELEVENLABS"
  },
  "meta": { ... }
}
```

### ErrorCode enum

`NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, `INTERNAL_ERROR`, `UNSUPPORTED_SERVICE`, `ALREADY_RUNNING`, `SESSION_EXPIRED`, `NO_ACCOUNTS`, `JOB_CANCELLED`, `TIMEOUT`

---

## 3. Logging

### Nguyên tắc
- **Log 1 dòng per action** — không log intermediate steps.
- **Truncate URL** — dùng `_short_url()`, bỏ query string.
- **Không print HTML** ra console — chỉ ghi file vào `debug/`.
- **Log level đúng**: DEBUG cho trace, INFO cho action summary, WARNING cho recoverable, ERROR cho failure.
- **Dependency injection** — inject `LogFn` vào function, không dùng global logger trong service layer.

---

## 4. Config

### Nguyên tắc
- **Frozen dataclass** — immutable sau khi tạo.
- **Strict parsing** — `_parse_section_strict()` validate schema.
- **CẤM hardcode** giá trị — mọi thứ phải đọc từ config YAML hoặc env var.
- **Type-safe** — không dùng `Any`, không dùng `dict` khi có thể dùng dataclass.

---

## 5. Functional Programming

### Nguyên tắc
- **FP only** — pure functions, không OOP, không global state.
- **Async & concurrent** — tận dùng `asyncio`, cấm blocking IO.
- **Dependency injection** — inject cfg, log_fn, save_fn. Không import global.
- **SRP** — mỗi file ≤ 200 dòng, mỗi function làm đúng 1 việc.
- **CẤM fallback** — flow sai = raise exception, không try hướng khác.

---

## 6. Database

### Nguyên tắc
- **PostgreSQL là runtime truth** cho production và staging.
- **SQLite chỉ còn dành cho** isolated tests hoặc migration utilities được gắn nhãn legacy.
- **Runtime services dùng PostgreSQL qua `DATABASE_URL`; không fallback SQLite.**
- **NullPool** — không connection pooling.
- **Idempotent migrations** — ALTER TABLE IF NOT EXISTS.
- **Index đúng** — (service, disabled), (service, email unique).
- **PRAGMA** — chỉ áp dụng cho legacy SQLite paths.
- **Retry** — `_retry_db_op()` cho legacy conversion flows.

### Environment Isolation

| Env | DB Path | Purpose |
|-----|---------|---------|
| `prod` | `DATABASE_URL` (PostgreSQL) | Canonical production runtime |
| `staging` | `DATABASE_URL` (PostgreSQL) | Canonical staging runtime |
| `dev` | `DATABASE_URL` (PostgreSQL) | Local runtime + migration work |
| `test` | disposable SQLite fixture or ephemeral PostgreSQL | CI/CD and isolated tests |

**Config:** `APP_ENV=dev|prod|test` via `.env` hoặc environment variable.

**Usage:**
```python
import os

DATABASE_URL = os.environ["DATABASE_URL"]
```

---

## 7. Browser Automation

### Quy trình BẮT BUỘC khi viết service mới

1. **Dùng Playwright lấy HTML rendered** — KHÔNG dùng `requests.get()`.
2. **Dump & phân tích DOM** — liệt kê buttons, inputs, tabs, dialogs.
3. **Xác định thứ tự tương tác** — skip OAuth buttons, check tab UI.
4. **Code dựa trên DOM thực tế** — không đoán.
5. **Dump HTML sau mỗi action** khi debug.

### Nguyên tắc
- Dùng **Playwright locator** (`.click()`, `.fill()`).
- **CẤM hardcode selector** — phải flexible.
- Log **1 dòng per action**, URL truncated.

---

## 8. Testing

### Structure

```
tests/
├── unit/          # Không network, không browser. Mock everything.
├── integration/   # Có DB, có config. Không browser.
├── e2e/           # Full flow với browser.
└── conftest.py    # Shared fixtures
```

### Nguyên tắc
- Mọi module mới phải có unit test.
- Mock external dependencies (`@patch`).
- Test cả happy path lẫn error path.

### Test Environment Isolation

**conftest.py** phải set `APP_ENV=test`:
```python
import os
os.environ["APP_ENV"] = "test"
```

**Fixtures cung cấp:**
- `tmp_db` — fresh SQLite trong tmpdir (function scope)
- `real_cfg` — load config từ config/ thật (session scope)

---

## 9. Code Quality

### Enforced
- **Ruff** — BLE001 (no blind except), E722 (no bare except), UP (pyupgrade).
- **Pre-commit** — ruff check on `src/`.
- **Frozen dataclass** — immutable config & records.

### Nguyên tắc chung
- Nói tiếng Việt trong comments/docs.
- FP style — tránh OOP.
- Mỗi file ≤ 200 dòng.
- Không dùng `Any`.
- Không tự viết lại lib có sẵn.
