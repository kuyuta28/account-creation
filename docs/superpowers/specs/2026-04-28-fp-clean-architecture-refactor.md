# Spec: Enterprise-Grade FP + Clean Architecture Refactor

**Date:** 2026-04-28
**Author:** Claude
**Status:** Approved

## Overview

Refactor `mail-service` và `registrar` để đạt **10/10 FP score + Clean Architecture** bằng cách thay thế module-level mutable state bằng structured state managers trong DI container pattern.

## Problem Statement

### Current Issues

| Service | Issue | Impact |
|---------|-------|--------|
| mail-service | `_provider_fail_counts`, `_provider_cooldown_until`, `_round_robin_counter` là module-level mutable state | Không testable, không observable |
| mail-service | `_active_boxes`, `_created_at` là module-level mutable state | Race condition tiềm năng, khó monitoring |
| registrar | `_store`, `_cancel_flags`, `_tasks` là module-level mutable state | Không graceful shutdown, khó test |

## Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AppContext (frozen)                     │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐  │
│  │ Config  │  │ DBEngine │  │  Mail   │  │  Registrar   │  │
│  │(frozen) │  │ (pooled) │  │ State   │  │   State      │  │
│  └─────────┘  └──────────┘  └─────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  State Managers (classes)                   │
│  CircuitBreakerState, MailboxStore, JobManager             │
│  - init() / shutdown() lifecycle                            │
│  - get_stats() for observability                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Service Layer (pure functions)               │
│  create_mailbox(), run_job(), etc.                         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. common/src/common/context.py — NEW

```python
@dataclass(frozen=True)
class AppContext:
    """Immutable container — single source of truth."""
    config: Any
    db_engine: Any
    mail_state: CircuitBreakerState
    job_state: JobManager
```

**Exports:**
- `init_app_context()` — khởi tạo container
- `get_app_context()` — lấy singleton
- `lifespan_context()` — FastAPI lifespan context manager

### 2. mail-service: CircuitBreakerState

**File:** `mail-service/src/mail/circuit_breaker.py`

```python
class CircuitBreakerState:
    async def init(self) -> None: ...
    async def shutdown(self) -> None: ...
    def is_down(self, provider: str) -> bool: ...
    def mark_fail(self, provider: str, log_fn: LogFn | None = None) -> None: ...
    def mark_ok(self, provider: str) -> None: ...
    def get_stats(self) -> dict[str, Any]: ...
```

### 3. mail-service: MailboxStore

**File:** `mail-service/src/mail_service/services/mailbox_store.py`

```python
class MailboxStore:
    async def init(self) -> None: ...
    async def shutdown(self) -> None: ...
    def add(self, box: Mailbox) -> None: ...
    def remove(self, email: str) -> bool: ...
    def get(self, email: str) -> Mailbox | None: ...
    def list_active(self) -> list[dict[str, Any]]: ...
    def count(self) -> int: ...
```

### 4. registrar: JobManager

**File:** `registrar/src/api/services/job_manager.py`

```python
class JobManager:
    async def init(self) -> None: ...
    async def shutdown(self) -> None: ...
    def create_job(self, job: Job) -> Job: ...
    def get_job(self, job_id: str) -> Job | None: ...
    def list_jobs(self) -> list[Job]: ...
    def request_cancel(self, job_id: str) -> bool: ...
    def is_cancelled(self, job_id: str) -> bool: ...
    def clear_cancel(self, job_id: str) -> None: ...
    def track_task(self, job_id: str, task: asyncio.Task) -> None: ...
    def untrack_task(self, job_id: str) -> None: ...
    def get_stats(self) -> dict[str, Any]: ...
```

## Files to Create/Modify

### NEW Files

| File | Purpose |
|------|---------|
| `common/src/common/context.py` | AppContext container + lifecycle |
| `mail-service/src/mail/circuit_breaker.py` | CircuitBreakerState manager |
| `mail-service/src/mail_service/services/mailbox_store.py` | MailboxStore manager |
| `registrar/src/api/services/job_manager.py` | JobManager state manager |

### MODIFY Files

| File | Changes |
|------|---------|
| `common/src/common/__init__.py` | Export AppContext |
| `mail-service/src/mail/client.py` | Inject CircuitBreakerState, remove module-level state |
| `mail-service/src/mail_service/services/mailbox_service.py` | Use MailboxStore, remove module-level state |
| `mail-service/src/mail_service/server.py` | Init state managers, add lifespan |
| `registrar/src/api/services/registration_service.py` | Inject JobManager, remove module-level state |
| `registrar/main.py` | Init state managers at startup |

## Backward Compatibility

- **Public API signatures unchanged** — routers gọi same functions
- Context được init ở app startup (`server.py` lifespan)
- Graceful shutdown khi restart

## Observability

Every state manager exposes `get_stats()`:
- CircuitBreakerState: fail counts, cooldown providers
- MailboxStore: active count
- JobManager: total jobs, active jobs, running tasks

## Testing Strategy

1. **Unit tests** — mock state managers
2. **Integration tests** — real state managers in test container
3. **Observability tests** — verify get_stats() accuracy

## Acceptance Criteria

1. ✅ No module-level mutable state in mail-service
2. ✅ No module-level mutable state in registrar
3. ✅ All state managers have `init()` / `shutdown()` lifecycle
4. ✅ All state managers expose `get_stats()` for monitoring
5. ✅ Graceful shutdown — no job loss on restart
6. ✅ Backward compatible — no breaking API changes
7. ✅ All existing tests pass