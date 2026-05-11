# API Architecture Documentation

## Runtime Truth

This document records the backend/API routing contract that currently exists in code and root Compose.
It must be kept in sync with:

- `docker-compose.yml`
- service `server.py` files
- `desktop-ui/src/config.ts`

## 1. Current Service Route Prefixes

### registrar

- Base runtime URL: `http://localhost:8709`
- Application prefix: `/api/v1`
- Example endpoints:
  - `/api/v1/accounts`
  - `/api/v1/registration/*`
  - `/api/v1/internal/*`

### mail-service

- Base runtime URL: `http://localhost:8701`
- Application prefix: `/api/v1`
- Health endpoint: `/api/health`
- Example endpoints:
  - `/api/v1/mailbox`
  - `/api/v1/providers`
  - `/api/v1/sms`

### aa-proxy

- Base runtime URL: `http://localhost:8702`
- Application prefix: `/api/v1`
- Health endpoint: `/api/health`
- Example endpoints:
  - `/api/v1/session`
  - `/api/v1/generate`
  - `/api/v1/image-lab/*`

### tts-proxy

- Base runtime URL: `http://localhost:8700`
- Application prefix: `/api`
- Example endpoints:
  - `/api/health`
  - `/api/voices`
  - `/api/tts`

## 2. Reverse Proxy Reality

Traefik is published from the root Compose on:

- web: `http://localhost/`
- dashboard: `http://localhost:8080/`

This document does not assert final Traefik path routing until those routes are verified and normalized during remediation.

## 3. Cross-Service Contract Reality

Current cross-service helper code points at:

- `REGISTRAR_URL=http://registrar:8709`

That internal contract is used by shared client code and must be formalized in a dedicated contract document during remediation.

## 4. Desktop UI Runtime Contract

Current desktop runtime config resolves to:

```typescript
export const API_BASE_URL = "http://localhost:8709/api/v1";
export const TTS_BASE_URL = "http://localhost:8700";
export const AAR_BASE_URL = "http://localhost:8702";
```

The TTS and AAR clients must talk to their own service origins directly.
They must not be routed through `registrar`.
`any-auto-register` remains available separately at `http://localhost:8708`.

## 5. Validation Ownership

- `desktop-ui` and backend services are validated in their own repositories.
- The root orchestration repo validates only the documented runtime contract and root Compose truth.
- Cross-repo consistency is enforced through shared contract docs plus service-local tests.

## 6. Known Drift Areas

The following are currently not stable enough to be treated as final architecture:

- Traefik public routing contract
- storage ownership language in older docs
- AAR integration boundary

## 7. Verification Checklist

Any API/routing change is incomplete unless all of these are updated together:

1. `docker-compose.yml`
2. affected service `server.py`
3. `desktop-ui/src/config.ts`
4. `docs/ARCHITECTURE.md`
5. this file
