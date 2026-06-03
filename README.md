# account-creation workspace

This root repository is the platform orchestration repo for the `account-creation` workspace.
It is not the application-code monorepo.

## Root repo responsibility

The root Git repo owns only cross-service assets:

- `docker-compose.yml`
- platform docs in [`docs/`](docs/)
- top-level automation in [`.github/`](.github/)
- shared routing/deployment assets such as [`traefik/`](traefik/)

## Service repos

These directories are independent Git repositories and should be changed in their own repos:

| Repo | Runtime port | Role |
|------|--------------|------|
| `registrar/` | `8709` | Account orchestration API |
| `mail-service/` | `8701` | Mailbox/provider API |
| `aa-proxy/` | `8702` | Artificial Analysis proxy |
| `tts-proxy/` | `8700` | TTS proxy |
| `desktop-ui/` | `1421` | Tauri/React desktop UI |
| `common/` | n/a | Shared Python package |

## Runtime orchestration

The root workspace currently defines local multi-service runtime composition through [`docker-compose.yml`](docker-compose.yml). Its published ports and sample credentials are local orchestration truth, not a staging or production security posture.

Canonical local exposed service ports:

- `registrar`: `8709`
- `mail-service`: `8701`
- `aa-proxy`: `8702`
- `tts-proxy`: `8700`
- `postgres`: `5432`
- `traefik`: `80`, dashboard `8080`

## Rule of thumb

- If a change affects one service only, make it in that service repo.
- If a change defines how services fit together, document it and version it in the root repo.
