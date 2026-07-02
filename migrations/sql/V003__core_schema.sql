-- V003__core_schema.sql
-- Core application schema: accounts + per-service extension tables (CTI),
-- mail providers, provider domain tags, services catalog, mailbox service blocks.
--
-- Single source of truth for the relational schema, owned by Flyway.
-- The legacy SQLAlchemy create_all() path (common/database/_migrations.py init_db)
-- is SQLite-only (test fixtures) and must not run against this Postgres schema.
--
-- Idempotent: every object uses IF NOT EXISTS so re-runs are safe.

-- accounts ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.accounts (
    id            integer       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service       varchar(64)   NOT NULL,
    email         varchar(256)  NOT NULL,
    password      text          NOT NULL DEFAULT '',
    disabled      boolean       NOT NULL DEFAULT false,
    session_state text          NOT NULL DEFAULT '',
    source_email  text          NOT NULL DEFAULT '',
    check_status  varchar(32)   NOT NULL DEFAULT '',
    last_checked  varchar(64)   NOT NULL DEFAULT '',
    last_error    text          NOT NULL DEFAULT '',
    created_at    varchar(64)   NOT NULL DEFAULT '',
    updated_at    varchar(64)   NOT NULL DEFAULT ''
);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_service_email') THEN
        ALTER TABLE public.accounts ADD CONSTRAINT uq_service_email UNIQUE (service, email);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_accounts_service           ON public.accounts (service);
CREATE INDEX IF NOT EXISTS idx_accounts_service_disabled  ON public.accounts (service, disabled);

-- per-service extension tables (FK account_id → accounts.id, CASCADE) ─────────
CREATE TABLE IF NOT EXISTS public.accounts_gmail (
    account_id   integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    totp_secret  text NOT NULL DEFAULT '',
    app_password text NOT NULL DEFAULT '',
    label        text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_artificialanalysis (
    account_id integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key    text NOT NULL DEFAULT '',
    org_slug   text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_openrouter (
    account_id    integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key       text       NOT NULL DEFAULT '',
    credits       integer    NOT NULL DEFAULT 0,
    quota_pct     varchar(16) NOT NULL DEFAULT '',
    refresh_token text       NOT NULL DEFAULT '',
    access_token  text       NOT NULL DEFAULT '',
    id_token      text       NOT NULL DEFAULT '',
    token_type    varchar(32) NOT NULL DEFAULT '',
    expired       varchar(64) NOT NULL DEFAULT '',
    last_refresh  varchar(64) NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_elevenlabs (
    account_id integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key    text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_ollama (
    account_id integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key    text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_testmail (
    account_id integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key    text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_cloudflare (
    account_id          integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key             text NOT NULL DEFAULT '',
    account_id_in_token text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS public.accounts_mailosaur (
    account_id integer PRIMARY KEY REFERENCES public.accounts(id) ON DELETE CASCADE,
    api_key    text NOT NULL DEFAULT '',
    server_id  text NOT NULL DEFAULT ''
);

-- mail providers ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.mail_providers (
    id             integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider_type  varchar(64) NOT NULL,
    api_key        text        NOT NULL DEFAULT '',
    server_id      text        NOT NULL DEFAULT '',
    label          text        NOT NULL DEFAULT '',
    disabled       boolean     NOT NULL DEFAULT false,
    fail_count     integer     NOT NULL DEFAULT 0,
    cooldown_until varchar(64) NOT NULL DEFAULT '',
    last_used      varchar(64) NOT NULL DEFAULT '',
    created_at     varchar(64) NOT NULL DEFAULT '',
    updated_at     varchar(64) NOT NULL DEFAULT ''
);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_mail_provider') THEN
        ALTER TABLE public.mail_providers ADD CONSTRAINT uq_mail_provider UNIQUE (provider_type, api_key, server_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_mail_providers_disabled ON public.mail_providers (disabled);
CREATE INDEX IF NOT EXISTS idx_mail_providers_type     ON public.mail_providers (provider_type);

-- provider domain tags ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.provider_domain_tags (
    id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    provider_type varchar(64)  NOT NULL,
    tag           varchar(128) NOT NULL
);

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_domain_tag') THEN
        ALTER TABLE public.provider_domain_tags ADD CONSTRAINT uq_domain_tag UNIQUE (provider_type, tag);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_domain_tag ON public.provider_domain_tags (tag);

-- services catalog ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.services (
    name          varchar(64) NOT NULL PRIMARY KEY,
    has_registrar boolean     NOT NULL DEFAULT false
);

-- mailbox service blocks (email × service blacklist) ────────────────────────
CREATE TABLE IF NOT EXISTS public.mailbox_service_blocks (
    email      varchar(256) NOT NULL,
    service    varchar(64)  NOT NULL,
    reason     text         NOT NULL DEFAULT '',
    blocked_at varchar(64)  NOT NULL DEFAULT '',
    CONSTRAINT mailbox_service_blocks_pkey PRIMARY KEY (email, service)
);

CREATE INDEX IF NOT EXISTS idx_msb_service ON public.mailbox_service_blocks (service);
