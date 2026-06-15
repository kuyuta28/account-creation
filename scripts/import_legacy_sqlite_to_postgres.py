from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEGACY_DATABASES = (
    "registrar/data/accounts.db",
    "mail-service/data/mail.db",
    "aa-proxy/data/accounts.db",
    "tts-proxy/data/accounts.db",
)

BASE_COLUMNS = {
    "service", "email", "password", "disabled", "session_state", "source_email",
    "check_status", "last_checked", "last_error", "created_at", "updated_at",
}
EXTENSION_TABLES = {
    "GMAIL": ("accounts_gmail", ("totp_secret", "app_password", "label")),
    "ARTIFICIALANALYSIS": ("accounts_artificialanalysis", ("api_key", "org_slug")),
    "OPENROUTER": ("accounts_openrouter", ("api_key", "credits", "quota_pct", "refresh_token", "access_token", "id_token", "token_type", "expired", "last_refresh")),
    "ELEVENLABS": ("accounts_elevenlabs", ("api_key",)),
    "OLLAMA": ("accounts_ollama", ("api_key",)),
    "TESTMAIL": ("accounts_testmail", ("api_key",)),
    "MAILOSAUR": ("accounts_mailosaur", ("api_key", "server_id")),
}


@dataclass
class ImportStats:
    path: str
    accounts: int = 0
    providers: int = 0
    tags: int = 0
    tts_rpd: int = 0


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _value(row: sqlite3.Row, columns: set[str], name: str, default: Any = "") -> Any:
    return row[name] if name in columns and row[name] is not None else default


def _extension_data(row: sqlite3.Row, columns: set[str], service: str) -> dict[str, Any]:
    if service == "ARTIFICIALANALYSIS":
        return {"api_key": _value(row, columns, "api_key"), "org_slug": _value(row, columns, "org_slug", _value(row, columns, "account_id"))}
    if service == "MAILOSAUR":
        return {"api_key": _value(row, columns, "api_key"), "server_id": _value(row, columns, "server_id", _value(row, columns, "account_id"))}
    table_info = EXTENSION_TABLES.get(service)
    if not table_info:
        return {}
    return {field: _value(row, columns, field, 0 if field == "credits" else "") for field in table_info[1]}


def _read_accounts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if "accounts" not in _tables(conn):
        return []
    columns = _columns(conn, "accounts")
    if not {"service", "email"}.issubset(columns):
        return []
    rows = conn.execute("SELECT * FROM accounts").fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        service = str(_value(row, columns, "service")).upper()
        email = str(_value(row, columns, "email")).strip()
        if not service or not email:
            continue
        result.append({
            "source_id": int(row["id"]) if "id" in columns and row["id"] is not None else None,
            "service": service,
            "email": email,
            "password": _value(row, columns, "password"),
            "disabled": bool(_value(row, columns, "disabled", False)),
            "session_state": _value(row, columns, "session_state"),
            "source_email": _value(row, columns, "source_email"),
            "check_status": _value(row, columns, "check_status"),
            "last_checked": _value(row, columns, "last_checked"),
            "last_error": _value(row, columns, "last_error"),
            "created_at": _value(row, columns, "created_at", "1970-01-01 00:00:00 UTC"),
            "updated_at": _value(row, columns, "updated_at", "1970-01-01 00:00:00 UTC"),
            "ext": _extension_data(row, columns, service),
        })
    return result


def _read_mailboxes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if "mailboxes" not in _tables(conn):
        return []
    columns = _columns(conn, "mailboxes")
    if "email" not in columns:
        return []
    rows = conn.execute("SELECT * FROM mailboxes").fetchall()
    result = []
    for row in rows:
        email = str(_value(row, columns, "email")).strip().lower()
        if not email:
            continue
        result.append({
            "service": "GMAIL",
            "email": email,
            "password": _value(row, columns, "password"),
            "disabled": bool(_value(row, columns, "disabled", False)),
            "session_state": _value(row, columns, "session_state", _value(row, columns, "google_auth_state")),
            "source_email": _value(row, columns, "source_email"),
            "check_status": "",
            "last_checked": "",
            "last_error": "",
            "created_at": _value(row, columns, "created_at", "1970-01-01 00:00:00 UTC"),
            "updated_at": _value(row, columns, "updated_at", "1970-01-01 00:00:00 UTC"),
            "ext": {
                "totp_secret": _value(row, columns, "totp_secret"),
                "app_password": _value(row, columns, "app_password"),
                "label": _value(row, columns, "label"),
            },
        })
    return result


def _read_extension_table(conn: sqlite3.Connection, table: str) -> dict[str, dict[str, Any]]:
    """Read a SQLite extension table keyed by account_id → row dict.

    The legacy SQLite schema stores service-specific fields (Gmail
    TOTP/app_password, AA api_key, …) in dedicated extension tables
    joined to the main `accounts` table by `account_id`. The original
    importer inlined these into the `accounts` row and silently dropped
    them when the schema did not match — which meant every Gmail TOTP
    secret that ever lived in SQLite was lost on import.

    This helper returns a `{account_id: {field: value, …}}` map. The
    upsert step consults the map after writing the main row so the
    extension data lands in the matching extension Postgres table.
    """
    if table not in _tables(conn):
        return {}
    columns = _columns(conn, table)
    if "account_id" not in columns:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for row in conn.execute(f"SELECT * FROM {table}").fetchall():
        result[str(row["account_id"])] = {col: row[col] for col in columns}
    return result


def _read_providers(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if "mail_providers" not in _tables(conn):
        return []
    columns = _columns(conn, "mail_providers")
    if "provider_type" not in columns:
        return []
    rows = conn.execute("SELECT * FROM mail_providers").fetchall()
    result = []
    for row in rows:
        provider_type = str(_value(row, columns, "provider_type")).strip()
        if not provider_type:
            continue
        result.append({
            "provider_type": provider_type,
            "api_key": _value(row, columns, "api_key"),
            "server_id": _value(row, columns, "server_id"),
            "label": _value(row, columns, "label"),
            "disabled": bool(_value(row, columns, "disabled", False)),
            "fail_count": int(_value(row, columns, "fail_count", 0) or 0),
            "cooldown_until": _value(row, columns, "cooldown_until"),
            "last_used": _value(row, columns, "last_used"),
            "created_at": _value(row, columns, "created_at", "1970-01-01 00:00:00 UTC"),
            "updated_at": _value(row, columns, "updated_at", "1970-01-01 00:00:00 UTC"),
        })
    return result


def _read_tags(conn: sqlite3.Connection) -> list[dict[str, str]]:
    if "provider_domain_tags" not in _tables(conn):
        return []
    columns = _columns(conn, "provider_domain_tags")
    if not {"provider_type", "tag"}.issubset(columns):
        return []
    return [
        {"provider_type": str(row["provider_type"]), "tag": str(row["tag"])}
        for row in conn.execute("SELECT provider_type, tag FROM provider_domain_tags").fetchall()
        if row["provider_type"] and row["tag"]
    ]


def _read_tts_rpd(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if "gemini_key_rpd" not in _tables(conn):
        return []
    columns = _columns(conn, "gemini_key_rpd")
    if not {"key_tail", "date", "remaining"}.issubset(columns):
        return []
    return [dict(row) for row in conn.execute("SELECT key_tail, date, remaining FROM gemini_key_rpd").fetchall()]


async def _upsert_account(session, account: dict[str, Any]) -> None:
    result = await session.execute(text("""
        INSERT INTO public.accounts
            (service, email, password, disabled, session_state, source_email,
             check_status, last_checked, last_error, created_at, updated_at)
        VALUES
            (:service, :email, :password, :disabled, :session_state, :source_email,
             :check_status, :last_checked, :last_error, :created_at, :updated_at)
        ON CONFLICT (service, email) DO UPDATE SET
            password = EXCLUDED.password,
            disabled = EXCLUDED.disabled,
            session_state = EXCLUDED.session_state,
            source_email = EXCLUDED.source_email,
            check_status = EXCLUDED.check_status,
            last_checked = EXCLUDED.last_checked,
            last_error = EXCLUDED.last_error,
            updated_at = EXCLUDED.updated_at
        RETURNING id
    """), {k: account[k] for k in BASE_COLUMNS})
    account_id = result.scalar_one()
    table_info = EXTENSION_TABLES.get(account["service"])
    if not table_info or not account["ext"]:
        return
    table_name, fields = table_info
    values = {field: account["ext"].get(field, 0 if field == "credits" else "") for field in fields}
    columns = ", ".join(("account_id", *fields))
    params = ", ".join((":account_id", *(f":{field}" for field in fields)))
    updates = ", ".join(f"{field} = EXCLUDED.{field}" for field in fields)
    await session.execute(
        text(f"""
            INSERT INTO public.{table_name} ({columns})
            VALUES ({params})
            ON CONFLICT (account_id) DO UPDATE SET {updates}
        """),
        {"account_id": account_id, **values},
    )


async def _upsert_provider(session, provider: dict[str, Any]) -> None:
    await session.execute(text("""
        INSERT INTO public.mail_providers
            (provider_type, api_key, server_id, label, disabled, fail_count,
             cooldown_until, last_used, created_at, updated_at)
        VALUES
            (:provider_type, :api_key, :server_id, :label, :disabled, :fail_count,
             :cooldown_until, :last_used, :created_at, :updated_at)
        ON CONFLICT (provider_type, api_key, server_id) DO UPDATE SET
            label = EXCLUDED.label,
            disabled = EXCLUDED.disabled,
            fail_count = EXCLUDED.fail_count,
            cooldown_until = EXCLUDED.cooldown_until,
            last_used = EXCLUDED.last_used,
            updated_at = EXCLUDED.updated_at
    """), provider)


async def _upsert_tag(session, tag: dict[str, str]) -> None:
    await session.execute(text("""
        INSERT INTO public.provider_domain_tags (provider_type, tag)
        VALUES (:provider_type, :tag)
        ON CONFLICT (provider_type, tag) DO NOTHING
    """), tag)


async def _upsert_tts_rpd(session, row: dict[str, Any]) -> None:
    await session.execute(text("""
        INSERT INTO tts.gemini_key_rpd (key_tail, date, remaining)
        VALUES (:key_tail, :date, :remaining)
        ON CONFLICT (key_tail) DO UPDATE SET
            date = EXCLUDED.date,
            remaining = EXCLUDED.remaining
    """), row)


async def import_database(session, path: Path, apply: bool) -> ImportStats:
    stats = ImportStats(str(path.relative_to(ROOT)))
    if not path.exists():
        return stats
    with _connect(path) as conn:
        accounts = _read_accounts(conn) + _read_mailboxes(conn)
        providers = _read_providers(conn)
        tags = _read_tags(conn)
        tts_rows = _read_tts_rpd(conn)
        # Read the per-service extension tables (accounts_gmail, …) so the
        # TOTP secret / app_password / api_key / etc. fields actually land
        # in the matching extension Postgres table. Without this, the
        # upsert path inlined `ext={}` and every Gmail TOTP ever stored
        # in SQLite was silently dropped on import.
        extension_data_by_table: dict[str, dict[str, dict[str, Any]]] = {}
        for table in {info[0] for info in EXTENSION_TABLES.values()}:
            extension_data_by_table[table] = _read_extension_table(conn, table)
    stats.accounts = len(accounts)
    stats.providers = len(providers)
    stats.tags = len(tags)
    stats.tts_rpd = len(tts_rows)
    if not apply:
        return stats
    for account in accounts:
        # Stitch extension data onto the account dict when the row's
        # source_id matches an entry in the extension table for this
        # service. The checkers read from this on import and use it to
        # push fresh tokens back into the DB; without it the import
        # leaves the Gmail TOTP column empty even though the row was
        # upserted.
        if account.get("source_id") is not None:
            table_info = EXTENSION_TABLES.get(account["service"])
            if table_info is not None:
                ext_table, ext_fields = table_info
                ext_row = extension_data_by_table[ext_table].get(str(account["source_id"]))
                if ext_row is not None:
                    account["ext"] = {field: ext_row.get(field, "") for field in ext_fields}
        await _upsert_account(session, account)
    for provider in providers:
        await _upsert_provider(session, provider)
    for tag in tags:
        await _upsert_tag(session, tag)
    for row in tts_rows:
        await _upsert_tts_rpd(session, row)
    return stats


async def run(apply: bool, database_url: str) -> list[ImportStats]:
    if not apply:
        return [await import_database(None, ROOT / rel, False) for rel in LEGACY_DATABASES]
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    globals()["text"] = text
    engine = create_async_engine(database_url, echo=False)
    try:
        async with engine.begin() as session:
            await session.execute(text("CREATE SCHEMA IF NOT EXISTS tts"))
            results = []
            for rel in LEGACY_DATABASES:
                results.append(await import_database(session, ROOT / rel, apply))
            return results
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Import legacy SQLite data into PostgreSQL with idempotent upserts.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Read legacy SQLite and print counts only.")
    group.add_argument("--apply", action="store_true", help="Write rows into PostgreSQL using upserts.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"), help="PostgreSQL URL. Defaults to DATABASE_URL.")
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL is required")
    if "postgresql+asyncpg" not in args.database_url:
        raise SystemExit("database URL must use postgresql+asyncpg")
    stats = asyncio.run(run(args.apply, args.database_url))
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"legacy SQLite import {mode}")
    for item in stats:
        print(f"{item.path}: accounts={item.accounts} providers={item.providers} provider_domain_tags={item.tags} tts.gemini_key_rpd={item.tts_rpd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
