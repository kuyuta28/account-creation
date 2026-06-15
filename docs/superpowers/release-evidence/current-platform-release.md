# Current Platform Release Evidence

This file records the evidence required before staging or production promotion in the federated platform model.

## Service CI Matrix

| Layer | Repository | Commit SHA | Image tag or digest | Command | CI run URL | Timestamp | Result |
|-------|------------|------------|---------------------|---------|------------|-----------|--------|
| root orchestration | `account-creation` | `052e8fe` | n/a | `python .github/scripts/validate_runtime_truth.py` | local | 2026-05-12 23:15 +07:00 | pass |
| `common` | `common` | local worktree | n/a | `PYTHONPATH=common/src pytest common/tests -q` | local | 2026-05-12 23:23 +07:00 | `16 passed` |
| `registrar` | `registrar` | local worktree | required before deploy | `PYTHONPATH=registrar/src;common/src pytest registrar/tests -q` | local | 2026-05-12 23:23 +07:00 | `558 passed, 92 skipped` |
| `mail-service` | `mail-service` | local worktree | required before deploy | `PYTHONPATH=mail-service/src;common/src pytest mail-service/tests -q` | local | 2026-05-12 23:24 +07:00 | `38 passed` |
| `aa-proxy` | `aa-proxy` | local worktree | required before deploy | `PYTHONPATH=aa-proxy/src;common/src pytest aa-proxy/tests -q` | local | 2026-05-12 23:24 +07:00 | `31 passed` |
| `tts-proxy` | `tts-proxy` | local worktree | required before deploy | `PYTHONPATH=tts-proxy/src;common/src pytest tts-proxy/tests -q` | local | 2026-05-12 23:24 +07:00 | `53 passed` |
| `web-ui` (formerly desktop-ui) | `web-ui` | local worktree | required before deploy | `npm --prefix web-ui test -- --run` | local | 2026-05-12 23:23 +07:00 | `89 passed` |

## Platform Gates

| Gate | Evidence | Result |
|------|----------|--------|
| SOPS/AGE decrypt staging | `docker run ... ghcr.io/getsops/sops:v3.9.4 --decrypt config/staging/secrets.yaml` | pass |
| SOPS/AGE decrypt production | `docker run ... ghcr.io/getsops/sops:v3.9.4 --decrypt config/prod/secrets.yaml` | pass |
| Flyway staging migration | workflow URL | pending |
| Flyway production migration | workflow URL | pending |
| Deploy staging | workflow URL | pending |
| Deploy production | workflow URL | pending |
| Traefik route static validation | `python .github/scripts/validate_traefik_routes.py` | pass |
| Traefik runtime smoke | `./scripts/smoke-traefik-routes.ps1 -BaseUrl http://localhost` | pass: registrar/mail-service/tts-proxy/aa-proxy returned 200 |
| Observability stack validation | `docker compose -f docker-compose.yml -f docker-compose.observability.yml config` | pass |
