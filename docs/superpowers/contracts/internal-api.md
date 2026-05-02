# Internal API Contract

## Purpose

This document defines the service-to-service contract exposed by `registrar` on `/api/v1/internal/*`.
It is the only supported write/read boundary for other first-party services such as `mail-service` and `aa-proxy`.

## Authentication

- Required header: `X-Internal-Key`
- Missing or incorrect key: HTTP `403`
- The caller must not rely on anonymous access for any internal endpoint, including health.

## Envelope

Successful responses use the standard envelope:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "request_id": "uuid",
    "ts": "2026-05-02T00:00:00Z"
  }
}
```

Router-level auth and not-found failures currently return FastAPI `detail` bodies with HTTP status codes.
Consumers must treat HTTP status as authoritative and not assume an envelope on `403` or `404`.

## Endpoints

### `GET /api/v1/internal/health`

- Auth required: yes
- Success: `200`
- Body:

```json
{
  "success": true,
  "data": {
    "status": "healthy"
  }
}
```

### `GET /api/v1/internal/accounts/{service}/{email}`

- Auth required: yes
- Success: `200`
- Not found: `404`
- Success body `data`: account object

### `GET /api/v1/internal/accounts`

- Auth required: yes
- Query params:
  - `service` optional
  - `page` optional, default `1`
  - `limit` optional, default `100`
- Success: `200`
- Success body `data`:

```json
{
  "accounts": [],
  "total": 0,
  "page": 1,
  "limit": 100,
  "pages": 0
}
```

- Consumer rule:
  - `common.internal_client.InternalClient.list_accounts()` unwraps `data.accounts` and returns a list only.

### `POST /api/v1/internal/accounts/upsert`

- Auth required: yes
- Required JSON fields:
  - `service`
  - `email`
- Optional JSON fields:
  - `api_key`
  - `password`
- Success: `200`
- Success body `data`:

```json
{
  "created": true
}
```

- Semantics:
  - Idempotent at the account identity level
  - Safe to retry after transport failure if caller can tolerate duplicate no-op upserts

### `PATCH /api/v1/internal/accounts/{service}/{email}`

- Auth required: yes
- Success: `200`
- Not found: `404`
- Success body `data`:

```json
{
  "updated": true
}
```

### `DELETE /api/v1/internal/accounts/{service}/{email}`

- Auth required: yes
- Success: `200`
- Not found: `404`
- Success body `data`:

```json
{
  "deleted": true
}
```

### `PUT /api/v1/internal/accounts/{service}/{email}/session`

- Auth required: yes
- Required JSON fields:
  - `session_state`
- Success: `200`
- Not found: `404`
- Success body `data`:

```json
{
  "updated": true
}
```

## Timeout And Retry Expectations

- `common.internal_client` default timeout: `30s`
- Callers may retry:
  - `GET` requests after network failure or timeout
  - idempotent `POST /upsert` if caller accepts create-or-update semantics
  - `PATCH`, `PUT`, `DELETE` only when caller knows the previous attempt did not commit or can safely replay

## Boundary Rules

- Other services must not import registrar storage/database modules directly.
- Other services must not read or mutate registrar account state except through this HTTP contract.
- `any-auto-register` is outside this contract and must remain behind its own HTTP boundary.
