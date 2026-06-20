"""Unit tests for the core package (db, migrate, logging, audit).

Run from the repo root:  pytest -q
Stdlib + pytest only — no network, no server.
"""

from __future__ import annotations

import io
import json
import logging
import os

from core import audit, db, migrate
from core.logging import get_logger


def _tmp_db(tmp_path) -> str:
    return os.path.join(str(tmp_path), "kian.db")


# ---------- migrate ----------

def test_migrate_creates_schema_and_sets_version(tmp_path):
    path = _tmp_db(tmp_path)
    applied = migrate.migrate_path(path)
    assert applied == len(db.MIGRATIONS)
    with db.session(path) as conn:
        assert migrate.current_version(conn) == len(db.MIGRATIONS)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    for expected in {"users", "audit_log", "nodes", "settings"}:
        assert expected in tables


def test_migrate_is_idempotent(tmp_path):
    path = _tmp_db(tmp_path)
    migrate.migrate_path(path)
    assert migrate.migrate_path(path) == 0  # nothing left to apply


# ---------- db / users ----------

def test_user_insert_and_unique_constraint(tmp_path):
    path = _tmp_db(tmp_path)
    migrate.migrate_path(path)
    with db.session(path) as conn:
        conn.execute("INSERT INTO users (name, uuid) VALUES (?, ?)",
                     ("ali", "uuid-1"))
        row = conn.execute("SELECT * FROM users WHERE name='ali'").fetchone()
        assert row["quota_bytes"] == 0      # default unlimited
        assert row["enabled"] == 1
        assert row["ip_limit"] == 0
        # name is UNIQUE
        import sqlite3
        try:
            conn.execute("INSERT INTO users (name, uuid) VALUES (?, ?)",
                         ("ali", "uuid-2"))
            raised = False
        except sqlite3.IntegrityError:
            raised = True
        assert raised


# ---------- audit ----------

def test_audit_record_and_tail(tmp_path):
    path = _tmp_db(tmp_path)
    migrate.migrate_path(path)
    with db.session(path) as conn:
        rid = audit.record(conn, actor="root", action="user.add",
                           target="ali", ip="1.2.3.4", detail="quota=100GB")
        assert rid >= 1
        audit.record(conn, actor="root", action="user.remove", target="ali")
        entries = audit.tail(conn, limit=10)
    assert len(entries) == 2
    assert entries[0]["action"] == "user.remove"   # newest first
    assert entries[1]["target"] == "ali"


# ---------- logging ----------

def test_structured_logging_emits_json():
    buf = io.StringIO()
    log = get_logger("test-json", level=logging.INFO, stream=buf)
    log.info("user_added", name="ali", quota_gb=100)
    line = buf.getvalue().strip().splitlines()[-1]
    obj = json.loads(line)
    assert obj["msg"] == "user_added"
    assert obj["name"] == "ali"
    assert obj["quota_gb"] == 100
    assert obj["level"] == "INFO"
    assert obj["logger"] == "test-json"
