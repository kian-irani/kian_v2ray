"""panel.bridge — connect the web panel to the REAL installed Xray.

The installer keeps users in ``/etc/kian-v2ray/users.json`` (and the live Xray
config in ``config.json``). The panel keeps its own SQLite (``core.db``). Without
a bridge those two drift — "add user in the panel" wouldn't touch the real
server. This module:

* :func:`import_users` — pull the installer's users.json into the panel db so
  the dashboard shows the *real* users.
* :func:`cli` — run the installer CLI (``kian-v2ray add/remove/...``) so panel
  mutations actually change the running server.

The panel runs on the same box as the installer, so shelling out to the CLI is
the safe, single-source way to mutate (the installer rebuilds Xray + restarts).
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
from typing import Any

USERS_JSON = os.environ.get("KIAN_USERS_JSON", "/etc/kian-v2ray/users.json")
CLI = os.environ.get("KIAN_CLI", "kian-v2ray")


def read_installer_users(path: str = USERS_JSON) -> list[dict[str, Any]]:
    """Parse the installer's users.json into normalized dicts."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    out: list[dict[str, Any]] = []
    for u in data.get("users", []):
        name = u.get("email") or u.get("name")
        if not name:
            continue
        out.append({
            "name": name,
            "uuid": u.get("id") or u.get("uuid") or "",
            "enabled": 1 if u.get("active", True) else 0,
            # installer may store quota/used in bytes or GB — accept either.
            "quota_bytes": int(u.get("quota_bytes")
                               or (u.get("quota_gb", 0) * 1073741824) or 0),
            "used_bytes": int(u.get("used_bytes") or 0),
            "expires_at": int(u["expiry"]) if u.get("expiry") else None,
        })
    return out


def import_users(conn: sqlite3.Connection, path: str = USERS_JSON) -> dict:
    """Sync installer users -> panel db (upsert). Returns counts."""
    rows = read_installer_users(path)
    added = updated = 0
    for r in rows:
        existing = conn.execute(
            "SELECT id FROM users WHERE name=?", (r["name"],)).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET uuid=?, enabled=?, quota_bytes=?, "
                "used_bytes=?, expires_at=? WHERE name=?",
                (r["uuid"], r["enabled"], r["quota_bytes"], r["used_bytes"],
                 r["expires_at"], r["name"]))
            updated += 1
        else:
            conn.execute(
                "INSERT INTO users (name, uuid, enabled, quota_bytes, "
                "used_bytes, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                (r["name"], r["uuid"], r["enabled"], r["quota_bytes"],
                 r["used_bytes"], r["expires_at"]))
            added += 1
    return {"added": added, "updated": updated, "total": len(rows)}


def cli_available() -> bool:
    return shutil.which(CLI) is not None


def cli(*args: str, timeout: float = 60.0) -> tuple[int, str]:
    """Run the installer CLI; returns (exit_code, output)."""
    if not cli_available():
        return 127, f"{CLI} not found on this host"
    try:
        p = subprocess.run([CLI, *args], capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "timeout"


def add_user(name: str, quota_gb: int = 0, days: int = 0) -> tuple[int, str]:
    return cli("add", name, str(quota_gb), str(days))


def remove_user(name: str) -> tuple[int, str]:
    return cli("remove", name)
