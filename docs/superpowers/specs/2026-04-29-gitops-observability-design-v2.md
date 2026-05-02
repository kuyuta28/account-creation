# GitOps + Observability Architecture Design

> **Spec Version:** 2.1
> **Date:** 2026-04-29
> **Status:** Draft (Reviewed - Critical issues fixed)
> **Author:** Claude

## 1. Executive Summary

Thiết kế kiến trúc enterprise-grade cho hệ thống **account-creation** với focus vào:

1. **GitOps Configuration Management** — Config as Code, audit trail đầy đủ, rollback tức thì
2. **Secrets Management** — SOPS + AGE cho secrets versioning an toàn trong git
3. **Database Migration Strategy** — Flyway cho SQL-based, language-agnostic migrations
4. **Multi-Environment Promotion** — Branch-based dev + Tag-based production
5. **Full Observability Stack** — Distributed tracing, metrics, centralized logging, alerting

**Design Principles:**
- Self-hosted (không external dependencies như Vault, Doppler, AWS)
- Production-ready cho team nhỏ-trung bình
- Docker Compose native (không yêu cầu Kubernetes)

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GIT REPOSITORY                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   config/   │  │ migrations/│  │ docker/    │  │  .github/   │            │
│  │   *.yaml    │  │  V*.sql    │  │  compose   │  │  workflows  │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                │                    │
│         └────────────────┼────────────────┼────────────────┘                    │
│                          ▼                                                    │
│               ┌─────────────────────┐                                          │
│               │   CI/CD Pipeline    │                                          │
│               │   (GitHub Actions)  │                                          │
│               └──────────┬──────────┘                                          │
│                          │                                                     │
│         ┌────────────────┼────────────────┐                                   │
│         ▼                ▼                ▼                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │
│  │  Validator  │  │   Builder   │  │  Secrets   │                           │
│  │  - YAML     │  │  - Docker   │  │  - SOPS    │                           │
│  │  - Schema   │  │  - Images   │  │  - AGE     │                           │
│  └─────────────┘  └─────────────┘  └─────────────┘                           │
└───────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────────────────────────────────┐
                              │         DEPLOYMENT ENVIRONMENT                 │
                              │                                               │
                              │  ┌────────────────────────────────────────┐ │
                              │  │        TRAEFIK REVERSE PROXY            │ │
                              │  └───────────────┬────────────────────────┘ │
                              │                  │                          │
                              │  ┌───────────────▼────────────────────────┐ │
                              │  │              SERVICES                  │ │
                              │  │                                       │ │
                              │  │  registrar  mail-service  aa-proxy    │ │
                              │  │  tts-proxy   any-auto-reg              │ │
                              │  │                                       │ │
                              │  └───────────────┬────────────────────────┘ │
                              │                  │                          │
                              │  ┌───────────────▼────────────────────────┐ │
                              │  │      OPEN TELEMETRY COLLECTOR           │ │
                              │  │                                       │ │
                              │  │  traces ──► Jaeger                      │ │
                              │  │  metrics ──► Prometheus                 │ │
                              │  │  logs ──────► Loki                      │ │
                              │  └───────────────────────────────────────┘ │
                              │                                               │
                              └───────────────────────────────────────────┘
```

---

## 3. Repository Structure

```
account-creation/
├── config/                          # ⭐ GitOps CONFIG (TRUTH SOURCE)
│   ├── registrar/
│   │   ├── config.yaml              # Main config (validated)
│   │   ├── logging.yaml
│   │   └── providers.yaml
│   ├── mail-service/
│   │   ├── config.yaml
│   │   └── providers.yaml
│   ├── aa-proxy/
│   │   └── config.yaml
│   ├── tts-proxy/
│   │   └── config.yaml
│   └── common/
│       └── defaults.yaml           # Shared defaults
│
├── migrations/                      # ⭐ DATABASE MIGRATIONS
│   ├── V1__initial_schema.sql
│   ├── V2__add_users.sql
│   └── V3__add_email_index.sql
│
├── .github/
│   └── workflows/
│       ├── gitops-config.yml        # Config validation + secrets decrypt
│       ├── docker-build.yml         # Docker image builds
│       ├── deploy.yml               # Deployment to servers
│       └── db-migrate.yml            # Flyway migrations
│
├── docker-compose.yml               # Main compose
├── docker-compose.override.yml      # Local dev overrides
├── docker-compose.prod.yml          # Production overrides
│
├── .sops.yaml                       # SOPS configuration
├── .age keys/                       # AGE private key (NOT committed)
│   └── key.txt                      # Encrypted with this
│
└── services/                       # Service code
    ├── registrar/
    ├── mail-service/
    ├── aa-proxy/
    ├── tts-proxy/
    └── any-auto-register/
```

**Key Points:**
- `.age keys/` chứa private key được .gitignore hoàn toàn
- `config/` được SOPS-encrypt trước khi commit
- `migrations/` là SQL thuần, không chứa secrets

---

## 4. Secrets Management (SOPS + AGE)

### 4.1 Why SOPS + AGE

| Criteria | Value |
|----------|-------|
| Self-hosted | ✅ Yes |
| GitOps Native | ✅ Yes (encrypted in git) |
| Audit Trail | ✅ Git history |
| Key Rotation | ✅ Re-encrypt with new key |
| Docker Compose | ✅ Yes |
| No External Service | ✅ Yes |

### 4.2 Workflow

```text
1. Generate key (one-time setup)
   $ age-keygen -o .age-keys/key.txt
   $ age-keygen -y .age-keys/key.txt > .age-keys/key.pub.txt

2. Encrypt secrets (dev machine)
   $ sops --encrypt --age "$(cat .age-keys/key.pub.txt)" \
     config/secrets.yaml > config/secrets.yaml.enc

3. Commit to git (safe)
   $ git add config/secrets.yaml.enc
   $ git commit -m "chore: add encrypted config"

4. CI/CD decrypt (on deploy)
   $ printf '%s' "$AGE_SECRET_KEY" > /tmp/age.key
   $ SOPS_AGE_KEY_FILE=/tmp/age.key \
     sops --decrypt config/secrets.yaml.enc > .env
   $ docker-compose up

5. Rotate key (when needed)
   $ age-keygen -o new-key.txt
   $ age-keygen -y new-key.txt > new-key.pub.txt
   $ sops re-encrypt --age "$(cat new-key.pub.txt)" config/
   $ git commit -m "chore: re-encrypt secrets with new key"
```

### 4.3 SOPS Configuration

```yaml
# .sops.yaml
version: "3.8"

creation_rules:
  # Production: ops team only
  - path_regex: config/prod/.*\.yaml\.enc
    encrypted_regex: ".*(API_KEY|SECRET|PASSWORD|TOKEN|CREDENTIALS)$"
    age: >-
      age1ops...

  # Staging: shared between dev + ops
  - path_regex: config/staging/.*\.yaml\.enc
    encrypted_regex: ".*(API_KEY|SECRET|PASSWORD|TOKEN|CREDENTIALS)$"
    age: >-
      age1dev...
      age1ops...

  # Default: dev/local/shared examples
  - path_regex: config/.*\.yaml\.enc
    encrypted_regex: ".*(API_KEY|SECRET|PASSWORD|TOKEN|CREDENTIALS)$"
    age: >-
      age1abc123...  # Team public key
```

### 4.4 Secrets Structure

```yaml
# config/secrets.yaml (BEFORE encryption)
version: "1.0"

secrets:
  registrar:
    MAILSERP_API_KEY: "mail_abc123..."
    DB_PASSWORD: "super_secret_password"
    REDIS_PASSWORD: "redis_pass"
    
  mail-service:
    SMTP_HOST: "smtp.example.com"
    SMTP_PASSWORD: "smtp_password"
    MAILSERP_API_KEY: "mail_xyz789..."

  tts-proxy:
    TTS_API_KEY: "tts_key_abc"
    
  aa-proxy:
    AA_API_KEY: "aa_key_xyz"
```

### 4.5 GitHub Actions Integration

```yaml
# .github/workflows/gitops-config.yml
name: GitOps Config Pipeline

on:
  push:
    branches: ['**']
    paths: ['config/**', 'migrations/**']
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install tools
        run: pip install pyyaml jsonschema

      - name: Validate YAML syntax
        run: |
          for f in config/**/*.yaml config/**/*.yaml.enc; do
            python -c "import yaml; yaml.safe_load(open('$f'))"
          done

      - name: Validate config schema
        run: python .github/scripts/validate-config.py

      - name: Check for secrets in plaintext
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base64: false

  decrypt-and-validate:
    runs-on: ubuntu-latest
    needs: validate
    if: github.event_name == 'push'
    environment: ${{ matrix.env }}
    strategy:
      matrix:
        env: [dev, staging, prod]
    steps:
      - uses: actions/checkout@v4

      - name: Install SOPS
        uses: mozilla-actions/sops@main

      - name: Get age private key
        run: echo "$AGE_KEY" > .age-keys/key.txt
        env:
          AGE_KEY: ${{ secrets.AGE_KEY }}

      - name: Decrypt secrets
        run: sops --decrypt config/${{ matrix.env }}/secrets.yaml.enc > .env

      - name: Validate secrets
        run: python .github/scripts/validate-secrets.py

      - name: Docker Compose validate
        run: docker-compose -f docker-compose.${{ matrix.env }}.yml config

      - name: Docker Compose build
        run: docker-compose -f docker-compose.${{ matrix.env }}.yml build --dry-run
```

### 4.6 Key Management

#### Backup AGE Key (CRITICAL!)

**⚠️ Nếu mất AGE key, không thể decrypt secrets = SYSTEM DOWN**

```bash
#!/bin/bash
# scripts/backup-keys.sh - Backup AGE key securely

set -e

BACKUP_DIR="$HOME/.account-creation-key-backups"
KEY_FILE=".age-keys/key.txt"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# 1. Backup to local secure location
cp "$KEY_FILE" "$BACKUP_DIR/key.txt.$TIMESTAMP"

# 2. Encrypt with GPG before storing remotely
gpg --symmetric --yes --output "$BACKUP_DIR/key.txt.$TIMESTAMP.gpg" "$KEY_FILE"

# 3. Copy to USB/drive (offline backup)
# rsync -av "$BACKUP_DIR/" /mnt/usb/key-backups/

# 4. Upload encrypted backup to password manager
# (LastPass, Bitwarden, 1Password support file attachments)

echo "Backup complete: $BACKUP_DIR/key.txt.$TIMESTAMP"
echo "ALSO upload .gpg file to password manager!"
```

**Recovery Procedure:**
```bash
# 1. Get encrypted backup from password manager
# 2. Decrypt
gpg --decrypt key.txt.gpg > key.txt

# 3. Restore to .age-keys/
mkdir -p .age-keys
mv key.txt .age-keys/key.txt

# 4. Verify
SOPS_AGE_KEY_FILE=.age-keys/key.txt sops --decrypt config/prod/secrets.yaml.enc | head -1
```

#### Rotate Keys

```bash
#!/bin/bash
# scripts/rotate-keys.sh

set -e

# 1. Generate new key pair
age-keygen -o .age-keys/new-key.txt
age-keygen -y .age-keys/new-key.txt > .age-keys/new-key.pub.txt

# 2. Backup old key (see backup-keys.sh)
cp .age-keys/key.txt .age-keys/key.txt.backup.$(date +%Y%m%d)

# 3. Re-encrypt all files
for file in config/**/*.yaml.enc; do
  sops re-encrypt --age $(cat .age-keys/new-key.pub.txt) "$file" > "$file.new"
  mv "$file.new" "$file"
done

# 4. Update SOPS config
sed -i 's/age1old.../age1new.../g' .sops.yaml

# 5. Commit
git add .
git commit -m "chore: rotate SOPS keys"

# 6. Update GitHub Secret AGE_KEY
# Manually update in GitHub → Settings → Secrets → AGE_KEY
```

### 4.7 Onboarding New Team Member

```bash
# 1. Receive public key from new member
# new-member.pub.txt contains their AGE public key

# 2. Add to SOPS config
# Edit .sops.yaml to add new public key

# 3. Re-encrypt with all keys
sops re-encrypt --age age1old... --age age1new... config/secrets.yaml.enc > config/secrets.yaml.enc.new
mv config/secrets.yaml.enc.new config/secrets.yaml.enc

# 4. Share encrypted file
# New member can now decrypt with their private key
```

---

## 5. GitOps Multi-Environment Workflow

### 5.1 Branch Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   GIT BRANCH STRATEGY                                      │
│                                                                          │
│  dev/* ───────────────────────────────────────────────────────────┐       │
│     │                                                           │       │
│     │  Auto-deploy on push                                      │       │
│     │  Feature testing, integration tests                        │       │
│     │                                                           │       │
│     ▼                                                           │       │
│  staging/* ─────────────────────────────────────────────────┐    │       │
│     │                                                     │    │       │
│     │  Manual promotion from dev                           │    │       │
│     │  Pre-production validation                           │    │       │
│     │                                                     │    │       │
│     ▼                                                     │    │       │
│  main ──────────────────────────────────────────────► TAG vX.Y.Z ──► PROD│
│     │                                                     │    │       │
│     │  Protected branch                                    │    │       │
│     │  Requires PR approval                                │    │       │
│     │  Manual tag triggers production deploy               │    │       │
│                                                                          │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.2 GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: GitOps Deploy

on:
  push:
    branches:
      - 'dev/**'      # Auto deploy dev
      - 'staging/**'  # Auto deploy staging
      - 'main'        # Requires tag for production
  release:
    tags:
      - 'v*.*.*'     # Tag triggers production

env:
  REGISTRY: ghcr.io/${{ github.repository_owner }}

jobs:
  # ============================================================
  # DEV DEPLOYMENT (auto on dev/* push)
  # ============================================================
  deploy-dev:
    if: startsWith(github.ref, 'refs/heads/dev/')
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4

      - name: Decrypt secrets
        run: |
          printf '%s' "$AGE_KEY" > /tmp/age.key
          SOPS_AGE_KEY_FILE=/tmp/age.key sops --decrypt config/dev/secrets.yaml.enc > .env
        env:
          AGE_KEY: ${{ secrets.AGE_KEY }}

      - name: Deploy to Dev Server
        run: |
          ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no $DEV_HOST "cd /opt/account-creation && \
            git pull && \
            docker-compose -f docker-compose.dev.yml pull && \
            docker-compose -f docker-compose.dev.yml up -d" || {
            echo "SSH deployment failed, retrying..."
            sleep 10
            ssh -o ConnectTimeout=60 $DEV_HOST "cd /opt/account-creation && \
              git pull && \
              docker-compose -f docker-compose.dev.yml up -d"
          }

  # ============================================================
  # STAGING DEPLOYMENT (auto on staging/* push)
  # ============================================================
  deploy-staging:
    if: startsWith(github.ref, 'refs/heads/staging/')
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Decrypt secrets
        run: |
          printf '%s' "$AGE_KEY" > /tmp/age.key
          SOPS_AGE_KEY_FILE=/tmp/age.key sops --decrypt config/staging/secrets.yaml.enc > .env
        env:
          AGE_KEY: ${{ secrets.AGE_KEY }}

      - name: Deploy to Staging Server
        run: |
          ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no $STAGING_HOST "cd /opt/account-creation && \
            git pull && \
            docker-compose -f docker-compose.staging.yml pull && \
            docker-compose -f docker-compose.staging.yml up -d" || {
            echo "SSH deployment failed, retrying..."
            sleep 10
            ssh -o ConnectTimeout=60 $STAGING_HOST "cd /opt/account-creation && \
              git pull && \
              docker-compose -f docker-compose.staging.yml up -d"
          }

  # ============================================================
  # PRODUCTION DEPLOYMENT (manual via tag only)
  # ============================================================
  deploy-prod:
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.ref_name }}

      - name: Decrypt production secrets
        run: |
          printf '%s' "$AGE_KEY" > /tmp/age.key
          SOPS_AGE_KEY_FILE=/tmp/age.key sops --decrypt config/prod/secrets.yaml.enc > .env
        env:
          AGE_KEY: ${{ secrets.AGE_KEY }}

      - name: Run database migrations
        run: docker-compose -f docker-compose.prod.yml run --rm flyway migrate

      - name: Deploy to Production Server
        run: |
          ssh -o ConnectTimeout=30 -o StrictHostKeyChecking=no $PROD_HOST "cd /opt/account-creation && \
            git fetch --tags && \
            git checkout ${{ github.ref_name }} && \
            docker-compose -f docker-compose.prod.yml pull && \
            docker-compose -f docker-compose.prod.yml up -d" || {
            echo "SSH deployment failed, retrying..."
            sleep 10
            ssh -o ConnectTimeout=60 $PROD_HOST "cd /opt/account-creation && \
              git fetch --tags && \
              git checkout ${{ github.ref_name }} && \
              docker-compose -f docker-compose.prod.yml up -d"
          }

      - name: Health check
        run: |
          for i in {1..10}; do
            curl -f http://$PROD_HOST/health && break
            sleep 10
          done

      - name: Notify Slack
        if: always()
        run: |
          curl -X POST $SLACK_WEBHOOK -d "{
            \"text\": \"Production deployed: ${{ github.ref_name }}\"
          }"
```

### 5.3 Promotion Process

```bash
#!/bin/bash
# scripts/promote.sh - Promote from dev to staging to production
# Usage: ./promote.sh <dev-branch> <tag>

set -e

BRANCH=$1
TAG=$2

if [ -z "$BRANCH" ] || [ -z "$TAG" ]; then
  echo "Usage: $0 <dev-branch> <tag>"
  echo "Example: $0 dev/feature-login v1.2.3"
  exit 1
fi

# 1. Merge dev branch to staging
git checkout staging
git merge $BRANCH
git push origin staging

# 2. Wait for staging deployment
echo "Waiting for staging deployment..."
sleep 60

# 3. Manual validation required (check Grafana/Slack)
echo "=========================================="
echo "PLEASE VALIDATE STAGING BEFORE PRODUCTION"
echo "URL: https://staging.example.com"
echo "=========================================="
echo ""
echo "To continue production release, run:"
echo "  git checkout main"
echo "  git merge $BRANCH"
echo "  git tag $TAG"
echo "  git push origin main --tags"
echo ""
read -p "Press Enter after validation complete, or Ctrl+C to abort..."

# 4. Create tag and merge to main
git checkout main
git merge $BRANCH
git tag $TAG
git push origin main --tags

echo "Production release $TAG triggered"
```

---

## 6. Database Migration Strategy (Flyway)

### 6.1 Why Flyway

| Criteria | Value |
|----------|-------|
| Language-agnostic | ✅ SQL-based, works with any language |
| Self-hosted | ✅ No external service required |
| Docker Compose | ✅ Official Docker image available |
| Production-ready | ✅ Battle-tested since 2010 |
| Rollback | ✅ Versioned migrations with forward-fix + restore workflow |

### 6.2 Migration File Structure

```
migrations/
├── V1__initial_schema.sql          # Version 1: Create initial tables
├── V2__add_users_table.sql          # Version 2: Add users table
├── V3__add_email_indexes.sql        # Version 3: Add indexes
├── V4__add_account_status.sql       # Version 4: Add status column
├── V5__drop_legacy_users_table.sql  # Forward fix migration
└── V6__recreate_email_index.sql     # Compensating migration if needed
```

**Rollback policy:** dùng forward-only migrations. Khi migration đã được apply:
- rollback application/config bằng `git revert` nếu cần
- sửa schema bằng migration bù `V_next__...`
- restore từ backup nếu có destructive/data-corruption change

### 6.3 Migration File Example

```sql
-- V2__add_users_table.sql
-- Description: Add users table for account management

-- +-----------------------------------------------------------------------+
-- | WARNING: This migration MUST be compatible with previous version      |
-- +-----------------------------------------------------------------------+

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    account_id UUID REFERENCES accounts(id),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for email lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Rollback
-- DROP INDEX IF EXISTS idx_users_status;
-- DROP INDEX IF EXISTS idx_users_email;
-- DROP TABLE IF EXISTS users;
```

### 6.4 Existing Database Schema Reference

Tham khảo schema hiện tại từ project (để tạo migration baseline):

```sql
-- Current tables in account-creation.db (SQLite)
-- Reference only - actual migrations use PostgreSQL syntax

-- accounts table
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    kling_session_file TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP
);

-- image_lab_jobs table
CREATE TABLE image_lab_jobs (
    id TEXT PRIMARY KEY,
    account_id TEXT,
    status TEXT,
    result TEXT,
    created_at TIMESTAMP
);
```

**Lưu ý:** Chuyển từ SQLite sang PostgreSQL cần migration plan riêng.

### 6.4 Docker Compose Integration

```yaml
# docker-compose.prod.yml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=account_creation
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  flyway:
    image: flyway/flyway:10-alpine
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./migrations:/flyway/sql
      - ./config/prod:/config
    command: migrate -validateOnMigrate true
    environment:
      - FLYWAY_URL=jdbc:postgresql://db:5432/${DB_NAME}
      - FLYWAY_USER=${DB_USER}
      - FLYWAY_PASSWORD=${DB_PASSWORD}
    env_file:
      - .env

  registrar:
    image: ghcr.io/$ORG/account-creation/registrar:latest
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
    env_file:
      - .env

volumes:
  postgres_data:
```

### 6.5 GitOps Integration

```yaml
# .github/workflows/db-migrate.yml
name: Database Migration

on:
  push:
    branches: ['main', 'staging/**']
    paths: ['migrations/**']

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Determine environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "name=production" >> $GITHUB_OUTPUT
          else
            echo "name=staging" >> $GITHUB_OUTPUT
          fi

      - name: Decrypt secrets
        run: |
          printf '%s' "$AGE_KEY" > /tmp/age.key
          SOPS_AGE_KEY_FILE=/tmp/age.key \
            sops --decrypt config/${{ steps.env.outputs.name }}/secrets.yaml.enc > .env
        env:
          AGE_KEY: ${{ secrets.AGE_KEY }}

      - name: Run Flyway migration
        run: docker-compose -f docker-compose.${{ steps.env.outputs.name }}.yml run --rm flyway migrate

      - name: Verify migration
        run: docker-compose -f docker-compose.${{ steps.env.outputs.name }}.yml exec -T db psql -U $DB_USER -d $DB_NAME -c "SELECT version, description FROM flyway_schema_history ORDER BY installed_rank;"
        env:
          DB_USER: ${{ secrets.DB_USER }}
          DB_NAME: ${{ secrets.DB_NAME }}
```

### 6.6 Migration Best Practices

1. **Never modify committed migrations** — Always create new migration
2. **Document compensation path** — Note how to roll forward or restore from backup
3. **Test on staging first** — Migrations run automatically on staging before prod
4. **Backward compatible** — New code must work with old schema
5. **Large table migrations** — Use separate non-transactional migrations for `CONCURRENTLY`, batch inserts

---

## 7. Rollback Strategy

### 7.1 Git Revert Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ROLLBACK WORKFLOW                                     │
│                                                                          │
│  1. DETECT ISSUE                                                          │
│     ┌────────────────────────────────────┐                               │
│     │ Alert fires → Slack notification   │                               │
│     │ Dashboard shows high error rate    │                               │
│     └────────────────────────────────────┘                               │
│                        │                                                  │
│                        ▼                                                  │
│  2. ROLLBACK (Developer)                                                  │
│     ┌────────────────────────────────────┐                               │
│     │ $ git revert HEAD                  │                               │
│     │ $ git push origin main             │                               │
│     └────────────────────────────────────┘                               │
│                        │                                                  │
│                        ▼                                                  │
│  3. AUTO DEPLOY                                                          │
│     ┌────────────────────────────────────┐                               │
│     │ GitHub Actions detects push        │                               │
│     │ → Build previous version           │                               │
│     │ → Deploy to production            │                               │
│     └────────────────────────────────────┘                               │
│                        │                                                  │
│                        ▼                                                  │
│  4. VERIFY                                                               │
│     ┌────────────────────────────────────┐                               │
│     │ Health checks pass                 │                               │
│     │ Rollback complete (5-10 min)       │                               │
│     └────────────────────────────────────┘                               │
│                                                                          │
└───────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Rollback Script

```bash
#!/bin/bash
# scripts/rollback.sh - Rollback to previous version
# Usage: ./rollback.sh [production|staging] [reason]

set -e

ENV=${1:-production}
REASON=${2:-"Manual rollback"}

echo "Rolling back $ENV environment"
echo "Reason: $REASON"

# Get current commit
CURRENT=$(git rev-parse HEAD)

# Revert HEAD
git revert --no-edit HEAD

# Push revert commit
git push origin main

# Monitor via GitHub API
echo "Deployment in progress..."
echo "Monitor at: https://github.com/$GITHUB_REPOSITORY/actions"

# Wait for workflow to complete
for i in {1..30}; do
  STATUS=$(gh run list --limit 1 --json status --jq '.[0].status')
  if [ "$STATUS" == "completed" ]; then
    break
  fi
  sleep 20
done

echo "Rollback complete!"
echo "Previous: $CURRENT"
echo "Current: $(git rev-parse HEAD)"
```

### 7.3 Rollback Decision Matrix

| Scenario | Action | Time |
|----------|--------|------|
| Config change broke something | `git revert HEAD` | 5-10 min |
| Database migration failed | Manual intervention | 30+ min |
| Docker image issue | Re-tag previous image | 5-10 min |
| Complete system failure | Restore from backup | 1-2 hours |

### 7.4 GitHub Actions Rollback Job

```yaml
# Partial - add to deploy.yml
  rollback:
    if: failure() && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Revert last commit
        run: |
          git revert --no-edit HEAD
          git push origin main

      - name: Notify rollback initiated
        run: |
          curl -X POST $SLACK_WEBHOOK -d "{
            \"text\": \"⚠️ Rollback initiated for production\",
            \"attachments\": [{
              \"color\": \"warning\",
              \"fields\": [
                {\"title\": \"Initiated by\", \"value\": \"${{ github.actor }}\"},
                {\"title\": \"Reason\", \"value\": \"${{ github.run_url }}\"}
              ]
            }]
          }"
```

---

## 8. Observability Stack

### 8.1 The Three Pillars

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OBSERVABILITY STACK                               │
│                                                                          │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│    │   TRACES     │     │   METRICS    │     │    LOGS      │              │
│    │              │     │              │     │              │              │
│    │  OpenTelemetry│     │ Prometheus  │     │    Loki      │              │
│    │  + Jaeger    │     │  + Grafana   │     │  + Grafana   │              │
│    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘              │
│           │                    │                    │                      │
│           └────────────────────┼────────────────────┘                      │
│                                ▼                                           │
│                    ┌───────────────────────┐                               │
│                    │   GRAFANA UNIFIED    │                               │
│                    │      DASHBOARD       │                               │
│                    └───────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 OpenTelemetry Integration

```python
# common/src/common/telemetry.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging

class TelemetryManager:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._tracer = None

    def init_telemetry(self, otlp_endpoint: str):
        """Initialize OpenTelemetry with OTLP exporter."""
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("APP_ENV", "dev"),
        })

        trace_provider = TracerProvider(resource=resource)
        trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        trace_provider.add_span_processor(
            BatchSpanProcessor(trace_exporter)
        )
        trace.set_tracer_provider(trace_provider)
        self._tracer = trace.get_tracer(self.service_name)

    def create_span(self, name: str, attributes: dict = None):
        """Create a traced span."""
        return self._tracer.start_as_current_span(name, attributes=attributes)
```

### 8.3 Prometheus Metrics

```yaml
# prometheus/config.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'account-creation'
    static_configs:
      - targets:
          - 'registrar:8709'
          - 'mail-service:8701'
          - 'aa-proxy:8702'
          - 'tts-proxy:8700'
        labels:
          group: 'services'

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### 8.4 Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: account_creation_alerts
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.service }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency on {{ $labels.service }}"
```

---

## 9. SLO/SLA Definition

### 9.1 Service Level Objectives

| Service | SLO | Window | Error Budget |
|---------|-----|--------|--------------|
| registrar | 99.9% availability | 30 days | 43.8 min/month |
| mail-service | 99.5% availability | 30 days | 3.65 hours/month |
| API latency | p95 < 500ms | 7 days | 10% of requests |
| Account creation | 99.9% success | 30 days | 0.1% failure |

### 9.2 Alert Severity Levels

| Severity | Response Time | Example |
|----------|---------------|---------|
| P1 Critical | 15 minutes | Service down, data loss |
| P2 High | 1 hour | High error rate, degraded performance |
| P3 Medium | 4 hours | Non-critical feature broken |
| P4 Low | Next business day | Minor UI issue, cosmetic |

### 9.3 Runbook Template

```markdown
# Runbook: [Alert Name]

## Symptoms
- What user experiences
- How to detect

## Impact
- Users affected
- Duration

## Investigation
1. Check Grafana dashboard
2. Check Jaeger traces
3. Check recent deployments

## Resolution
1. [Step 1]
2. [Step 2]

## Post-mortem
- [Link to post-mortem document]
```

---

## 10. Implementation Phases

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Set up observability stack (Prometheus, Grafana, Loki, Jaeger)
- [ ] Configure Docker metrics export
- [ ] Set up GitHub Actions runners
- [ ] Create config validation pipeline

### Phase 2: Secrets Management (Week 1-2)
- [ ] Generate AGE key pair
- [ ] Configure SOPS with `.sops.yaml`
- [ ] Encrypt existing secrets
- [ ] Set up CI/CD secret decryption
- [ ] Document key rotation process

### Phase 3: Database Migration (Week 2)
- [ ] Set up Flyway Docker container
- [ ] Create initial migration
- [ ] Configure CI/CD migration pipeline
- [ ] Test rollback scenario

### Phase 4: Service Instrumentation (Week 2-3)
- [ ] Add OpenTelemetry to common library
- [ ] Instrument all services with tracing
- [ ] Add standard metrics to all endpoints
- [ ] Implement health check endpoints

### Phase 5: GitOps Pipeline (Week 3)
- [ ] Restructure repository for GitOps
- [ ] Implement multi-environment workflow
- [ ] Configure branch-based deployment
- [ ] Set up tag-based production release

### Phase 6: Alerting & Dashboards (Week 4)
- [ ] Create Grafana dashboards
- [ ] Configure alert rules
- [ ] Set up alert routing
- [ ] Document runbooks

---

## 11. Migration Strategy

### 11.1 Incremental Migration (Zero Downtime)

```
Week 1: Observability
┌────────────────────────────────────────────────────────────────────┐
│ Add metrics exporter sidecar to all services (no code changes)     │
│ Deploy and verify metrics are collecting                          │
└────────────────────────────────────────────────────────────────────┘

Week 2: Secrets
┌────────────────────────────────────────────────────────────────────┐
│ Generate keys, configure SOPS                                      │
│ Encrypt first service (registrar), test decrypt in CI/CD          │
│ Roll out to other services                                       │
└────────────────────────────────────────────────────────────────────┘

Week 3: Migrations
┌────────────────────────────────────────────────────────────────────┐
│ Set up Flyway alongside existing manual migrations                 │
│ Verify both produce same result                                   │
│ Switch to Flyway-only                                             │
└────────────────────────────────────────────────────────────────────┘

Week 4: GitOps
┌────────────────────────────────────────────────────────────────────┐
│ Create branch strategy                                            │
│ Configure GitHub Actions workflows                                 │
│ Test promotion flow (dev → staging → prod)                        │
└────────────────────────────────────────────────────────────────────┘
```

### 11.2 Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Secrets loss | Backup keys in 2 locations (password manager + USB) |
| Migration failure | Test on staging first, have rollback plan |
| Deployment broken | Keep previous Docker image tagged |
| Data loss | Daily backups before major changes |

---

## 12. Technology Stack Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Secrets | SOPS + AGE | Encrypted secrets in git |
| Migrations | Flyway | Database schema management |
| CI/CD | GitHub Actions | Automation |
| Container Registry | GHCR | Docker image storage |
| Tracing | Jaeger + OpenTelemetry | Distributed request tracing |
| Metrics | Prometheus + Grafana | Time-series metrics & visualization |
| Logs | Loki + Grafana | Log aggregation |
| Reverse Proxy | Traefik | Routing & load balancing |

---

## 13. Appendix

### A. Docker Network Configuration

```yaml
# docker-compose.prod.yml
services:
  # ... other services ...

networks:
  default:
    name: account-creation-network
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
  internal:
    name: account-creation-internal
    driver: bridge
    internal: true  # No external internet access
  web:
    name: account-creation-web
    driver: bridge
```

### B. PostgreSQL Backup Strategy

```bash
#!/bin/bash
# scripts/backup-db.sh

set -e

BACKUP_DIR="/opt/account-creation/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER="account-creation-db-1"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full backup (pg_dumpall)
docker exec "$CONTAINER" pg_dumpall -U postgres > "$BACKUP_DIR/full_backup_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/full_backup_$DATE.sql"

# Keep only last 30 days
find "$BACKUP_DIR" -name "full_backup_*.sql.gz" -mtime +30 -delete

# Upload to remote storage (example: local NAS)
# rsync -av "$BACKUP_DIR/" nas:/backups/account-creation/

echo "Backup complete: $BACKUP_DIR/full_backup_$DATE.sql.gz"
```

**Crontab (run daily at 3 AM):**
```bash
0 3 * * * /opt/account-creation/scripts/backup-db.sh >> /var/log/backup.log 2>&1
```

**Restore Procedure:**
```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml stop registrar

# 2. Restore
docker exec -i account-creation-db-1 psql -U postgres < full_backup_20260101_030000.sql

# 3. Start services
docker-compose -f docker-compose.prod.yml start registrar
```

### C. SOPS Quick Reference

```bash
# Generate key
age-keygen -o key.txt

# Derive recipient from private key
age-keygen -y key.txt > key.txt.pub

# Encrypt file
sops --encrypt --age $(cat key.txt.pub) secrets.yaml > secrets.yaml.enc

# Decrypt file
SOPS_AGE_KEY_FILE=key.txt sops --decrypt secrets.yaml.enc > secrets.yaml

# Update existing file
sops update-keys secrets.yaml.enc

# Re-encrypt with new key
age-keygen -y new-key.txt > new-key.txt.pub
sops re-encrypt --age $(cat new-key.txt.pub) secrets.yaml.enc > secrets.yaml.enc.new
mv secrets.yaml.enc.new secrets.yaml.enc
```

### D. Flyway Quick Reference

```bash
# Run migrations
docker-compose run --rm flyway migrate

# Clean database (dangerous!)
docker-compose run --rm flyway clean

# Info about migrations
docker-compose run --rm flyway info

# Validate pending migrations
docker-compose run --rm flyway validate

# Apply latest compensating migration
docker-compose run --rm flyway migrate
```

### E. Environment Variables Reference

| Variable | Description | Source |
|----------|-------------|--------|
| `AGE_KEY` | AGE private key for SOPS | GitHub Secret |
| `DB_USER` | PostgreSQL username | SOPS encrypted |
| `DB_PASSWORD` | PostgreSQL password | SOPS encrypted |
| `OTLP_ENDPOINT` | OpenTelemetry collector | Config file |
| `DEV_HOST` | Dev server SSH host | GitHub Secret |
| `STAGING_HOST` | Staging server SSH host | GitHub Secret |
| `PROD_HOST` | Production server SSH host | GitHub Secret |
| `SLACK_WEBHOOK` | Slack webhook for alerts | GitHub Secret |

---

## 14. Spec Review Checklist

### Issues Found & Fixed:

| # | Issue | Status |
|---|-------|--------|
| 1 | k8s/ vs Docker Compose contradiction | ✅ Fixed |
| 2 | Flyway rollback naming (R → U prefix) | ✅ Fixed |
| 3 | `service_completed_successfully` | ✅ Fixed |
| 4 | ENV variable not set in workflow | ✅ Fixed |
| 5 | .sops.yaml location (moved to root) | ✅ Fixed |
| 6 | promote.sh interactive command | ✅ Fixed |
| 7 | SSH no timeout/retry | ✅ Fixed |
| 8 | AGE key backup unclear | ✅ Fixed |
| 9 | No DB schema reference | ✅ Fixed |
| 10 | No network isolation config | ✅ Fixed |
| 11 | SLO error budget calculation | ✅ Fixed |
| 12 | Backup strategy missing | ✅ Fixed |

### Spec Self-Review Checklist:

- [x] No placeholder "TBD" sections
- [x] Architecture consistent with feature descriptions
- [x] Focused scope (single implementation plan)
- [x] No ambiguous requirements
- [x] All critical gaps addressed:
  - [x] Secrets Management (SOPS + AGE)
  - [x] Multi-Environment (Branch + Tag)
  - [x] DB Migration (Flyway)
  - [x] Rollback Strategy (Git Revert)
- [x] All major gaps addressed:
  - [x] Key backup/recovery documented
  - [x] SSH error handling with timeout/retry
  - [x] Interactive script usage noted
  - [x] Network configuration added
- [x] All minor gaps addressed:
  - [x] DB schema reference added
  - [x] Backup strategy documented
- [x] Production-ready for team nhỏ-trung bình
- [x] Self-hosted requirements met
- [x] Reviewed: Critical issues fixed in v2.1
