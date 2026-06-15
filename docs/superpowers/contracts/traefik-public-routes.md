# Traefik Public Routes Contract

The root repository owns the public proxy routing contract for local, staging, and production orchestration.

| Public path | Router | Middleware | Upstream service | Upstream URL | Health path |
|-------------|--------|------------|------------------|--------------|-------------|
| `/api` | `api` | none | `registrar` | `http://registrar:8709` | `/api/v1/health` |
| `/mail` | `mail` | `strip-mail` | `mail-service` | `http://mail-service:8701` | `/api/health` |
| `/tts` | `tts` | `strip-tts` | `tts-proxy` | `http://tts-proxy:8700` | `/api/health` |
| `/aa` | `aa` | `strip-aa` | `aa-proxy` | `http://aa-proxy:8702` | `/api/health` |

Static validation:

```powershell
python .github/scripts/validate_traefik_routes.py
```

Runtime smoke validation when the stack is running:

```powershell
./scripts/smoke-traefik-routes.ps1 -BaseUrl http://localhost
```
