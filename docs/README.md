# Documentation Index

## Shared Documentation (common to all services)

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, service topology, Traefik routing |
| [API-ARCHITECTURE.md](API-ARCHITECTURE.md) | API conventions, endpoints, response envelope |
| [ENTERPRISE-STANDARDS.md](ENTERPRISE-STANDARDS.md) | Coding standards, error handling, testing |

## Service-Specific Documentation

| Service | Port | Docs |
|---------|------|------|
| [registrar](../registrar/docs/README.md) | 8709 | [API Reference](../registrar/docs/api-reference.md), [Architecture](../registrar/docs/architecture.md) |
| [tts-proxy](../tts-proxy/docs/README.md) | 8700 | [TTS API](../tts-proxy/docs/README.md) |
| [aa-proxy](../aa-proxy/docs/README.md) | 8702 | [Image Lab](../aa-proxy/docs/aa-image-lab.md) |
| [mail-service](../mail-service/docs/README.md) | 8701 | [Mail API](../mail-service/docs/mail.md) |
| [any-auto-register](../any-auto-register/README.md) | 8708 | Browser automation |

## Infrastructure

| Document | Description |
|----------|-------------|
| [Traefik](../traefik/traefik.yml) | Reverse proxy configuration |
| [Docker Compose](../docker-compose.yml) | Service orchestration |
| [Frontend](../desktop-ui/README.md) | Desktop UI (Tauri/React) |
