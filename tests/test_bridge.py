"""Tests for panel.bridge — installer users.json -> panel db (no server)."""

from __future__ import annotations

import json
import os

from core import db, migrate
from panel import bridge


def _write_users(path: str, users: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"users": users}, fh)


def test_read_installer_users_normalizes(tmp_path):
    p = os.path.join(str(tmp_path), "users.json")
    _write_users(p, [
        {"id": "uuid-1", "email": "ali", "active": True, "expiry": 99},
        {"id": "uuid-2", "email": "off", "active": False},
        {"email": "", "id": "x"},  # no name -> skipped
    ])
    rows = bridge.read_installer_users(p)
    assert len(rows) == 2
    assert rows[0]["name"] == "ali" and rows[0]["uuid"] == "uuid-1"
    assert rows[0]["expires_at"] == 99
    assert rows[1]["enabled"] == 0


def test_import_users_upserts(tmp_path):
    p = os.path.join(str(tmp_path), "users.json")
    dbp = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(dbp)
    _write_users(p, [{"id": "u1", "email": "ali", "active": True}])
    with db.session(dbp) as conn:
        r1 = bridge.import_users(conn, p)
        assert r1 == {"added": 1, "updated": 0, "total": 1}
        # second import updates, doesn't duplicate
        _write_users(p, [{"id": "u1", "email": "ali", "active": False}])
        r2 = bridge.import_users(conn, p)
        assert r2["added"] == 0 and r2["updated"] == 1
        row = conn.execute("SELECT enabled FROM users WHERE name='ali'").fetchone()
        assert row["enabled"] == 0


def test_missing_file_is_empty(tmp_path):
    assert bridge.read_installer_users(os.path.join(str(tmp_path), "nope.json")) == []
