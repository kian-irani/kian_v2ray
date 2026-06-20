#!/usr/bin/env python3
"""migrate-import — import users from Marzban / 3X-UI into kian_v2ray (phase 5.5).

Reads an export and normalizes it into kian's user model, then inserts via
core.db + panel.repo. Supports:

  * Marzban  — a JSON export ({"users":[{"username","data_limit",
                "expire","status",...}]})
  * 3X-UI    — the x-ui SQLite db (table `client_traffics` / inbound settings)

    migrate-import.py --marzban export.json --db /etc/kian-v2ray/kian.db
    migrate-import.py --xui   /etc/x-ui/x-ui.db
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time

from core import db as core_db
from core import migrate as core_migrate
from panel import repo


def normalize_marzban(data: dict) -> list[dict]:
    """Marzban export -> list of {name, quota_bytes, expires_at, enabled}."""
    out = []
    for u in data.get("users", []):
        name = u.get("username")
        if not name:
            continue
        out.append({
            "name": name,
            "quota_bytes": int(u.get("data_limit") or 0),
            "expires_at": int(u["expire"]) if u.get("expire") else None,
            "enabled": 0 if u.get("status") in ("disabled", "expired") else 1,
        })
    return out


def normalize_xui(path: str) -> list[dict]:
    """3X-UI sqlite -> list of normalized users (best-effort across schemas)."""
    out: list[dict] = []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT email, total, expiry_time, enable FROM client_traffics"
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    for r in rows:
        name = (r["email"] or "").strip()
        if not name:
            continue
        out.append({
            "name": name,
            "quota_bytes": int(r["total"] or 0),
            "expires_at": int(r["expiry_time"] // 1000) if r["expiry_time"] else None,
            "enabled": 1 if (r["enable"] in (1, "1", True)) else 0,
        })
    conn.close()
    return out


def import_users(users: list[dict], db_path: str) -> dict:
    core_migrate.migrate_path(db_path)
    added, skipped = 0, 0
    with core_db.session(db_path) as conn:
        for u in users:
            if repo.get_user(conn, u["name"]):
                skipped += 1
                continue
            created = repo.create_user(
                conn, actor="migrate", name=u["name"],
                quota_bytes=u["quota_bytes"], expires_at=u["expires_at"])
            if not u.get("enabled", 1):
                repo.set_enabled(conn, actor="migrate", name=u["name"],
                                 enabled=False)
            added += 1 if created else 0
    return {"added": added, "skipped": skipped, "total": len(users)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="import users into kian_v2ray")
    ap.add_argument("--marzban", help="Marzban JSON export")
    ap.add_argument("--xui", help="3X-UI sqlite db path")
    ap.add_argument("--db", default=core_db.DEFAULT_DB_PATH)
    args = ap.parse_args(argv)

    if args.marzban:
        with open(args.marzban) as fh:
            users = normalize_marzban(json.load(fh))
    elif args.xui:
        users = normalize_xui(args.xui)
    else:
        print("provide --marzban or --xui", file=sys.stderr); return 2

    result = import_users(users, args.db)
    print(f"migrate-import: added {result['added']}, "
          f"skipped {result['skipped']} of {result['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
