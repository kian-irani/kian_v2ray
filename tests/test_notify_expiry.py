"""Test the expiry/quota scan logic of kian-notify-expiry (loaded by path)."""

from __future__ import annotations

import importlib.util
import os

from core import db, migrate

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "kian_notify_expiry", os.path.join(_HERE, "scripts/kian-notify-expiry.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_find_due_expiring_and_over_quota(tmp_path):
    mod = _load()
    path = os.path.join(str(tmp_path), "kian.db")
    migrate.migrate_path(path)
    now = 1_000_000
    with db.session(path) as conn:
        # expiring in 2 days
        conn.execute("INSERT INTO users (name, uuid, expires_at) VALUES (?,?,?)",
                     ("soon", "u1", now + 2 * 86400))
        # not expiring (30 days)
        conn.execute("INSERT INTO users (name, uuid, expires_at) VALUES (?,?,?)",
                     ("later", "u2", now + 30 * 86400))
        # over 90% quota
        conn.execute("INSERT INTO users (name, uuid, quota_bytes, used_bytes) "
                     "VALUES (?,?,?,?)", ("hog", "u3", 100, 95))
        # under quota
        conn.execute("INSERT INTO users (name, uuid, quota_bytes, used_bytes) "
                     "VALUES (?,?,?,?)", ("light", "u4", 100, 10))
        expiring, over = mod.find_due(conn, days=3, quota_pct=90, now=now)
    assert {u["name"] for u in expiring} == {"soon"}
    assert {u["name"] for u in over} == {"hog"}
