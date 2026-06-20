"""core.db — SQLite access layer for kian_v2ray.

A thin, dependency-free wrapper over :mod:`sqlite3` that:

* opens the database with sane pragmas (WAL, foreign keys, busy timeout),
* returns rows as :class:`sqlite3.Row` (dict-like access),
* exposes the canonical schema so the installer, panel and tests agree on it.

The schema is intentionally migration-driven: :mod:`core.migrate` applies the
ordered statements in :data:`MIGRATIONS`. Never edit an existing migration in
place once shipped — append a new one instead.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

DEFAULT_DB_PATH = os.environ.get("KIAN_DB_PATH", "/etc/kian-v2ray/kian.db")

# Ordered, forward-only migrations. The index (0-based) is the schema version
# that the migration *produces*. core.migrate records the highest applied id.
MIGRATIONS: list[str] = [
    # 0001 — users: the heart of multi-user management.
    """
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL UNIQUE,
        uuid          TEXT    NOT NULL,
        quota_bytes   INTEGER NOT NULL DEFAULT 0,   -- 0 = unlimited
        used_bytes    INTEGER NOT NULL DEFAULT 0,
        expires_at    INTEGER,                       -- unix ts, NULL = never
        ip_limit      INTEGER NOT NULL DEFAULT 0,    -- 0 = unlimited concurrent IPs
        speed_kbps    INTEGER NOT NULL DEFAULT 0,    -- 0 = unlimited
        hwid          TEXT,                          -- bound device token, NULL = any
        enabled       INTEGER NOT NULL DEFAULT 1,
        created_at    INTEGER NOT NULL DEFAULT (strftime('%s','now'))
    );
    """,
    # 0002 — audit_log: every admin action, for accountability.
    """
    CREATE TABLE IF NOT EXISTS audit_log (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ts        INTEGER NOT NULL DEFAULT (strftime('%s','now')),
        actor     TEXT    NOT NULL,
        action    TEXT    NOT NULL,
        target    TEXT,
        ip        TEXT,
        detail    TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
    """,
    # 0003 — nodes: phase-5 multi-server registry.
    """
    CREATE TABLE IF NOT EXISTS nodes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL UNIQUE,
        address     TEXT    NOT NULL,
        api_port    INTEGER NOT NULL DEFAULT 8443,
        token       TEXT    NOT NULL,
        geo         TEXT,
        enabled     INTEGER NOT NULL DEFAULT 1,
        last_seen   INTEGER,
        created_at  INTEGER NOT NULL DEFAULT (strftime('%s','now'))
    );
    """,
    # 0004 — settings: simple key/value config (panel secrets, flags).
    """
    CREATE TABLE IF NOT EXISTS settings (
        key    TEXT PRIMARY KEY,
        value  TEXT
    );
    """,
]


def connect(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open (creating parent dirs for) a SQLite db with safe pragmas."""
    if path != ":memory:":
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


@contextmanager
def session(path: str = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    """Context manager that opens, yields and always closes a connection."""
    conn = connect(path)
    try:
        yield conn
    finally:
        conn.close()
