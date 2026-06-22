"""panel.repo — data access for the web panel, over core.db (sqlite3).

A thin repository so the routers never write raw SQL. Every mutating method
also writes an audit entry, so the admin trail is automatic. Pure stdlib.
"""

from __future__ import annotations

import sqlite3
import time
import uuid as _uuid
from typing import Any, Optional

from core import audit


def _row(r: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return dict(r) if r is not None else None


def list_users(conn: sqlite3.Connection, q: str = "",
               limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    sql = "SELECT * FROM users"
    args: list[Any] = []
    if q:
        sql += " WHERE name LIKE ?"
        args.append(f"%{q}%")
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    args += [limit, offset]
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


def get_user(conn: sqlite3.Connection, name: str) -> Optional[dict[str, Any]]:
    return _row(conn.execute(
        "SELECT * FROM users WHERE name=?", (name,)).fetchone())


def create_user(conn: sqlite3.Connection, *, actor: str, name: str,
                quota_bytes: int = 0, expires_at: Optional[int] = None,
                ip_limit: int = 0, speed_kbps: int = 0,
                hwid: Optional[str] = None, routing: Optional[str] = None,
                dns: Optional[str] = None) -> dict[str, Any]:
    user_uuid = str(_uuid.uuid4())
    conn.execute(
        "INSERT INTO users (name, uuid, quota_bytes, expires_at, ip_limit, "
        "speed_kbps, hwid, routing, dns) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, user_uuid, quota_bytes, expires_at, ip_limit, speed_kbps, hwid,
         routing, dns),
    )
    audit.record(conn, actor=actor, action="user.add", target=name,
                 detail=f"quota={quota_bytes} ip_limit={ip_limit}")
    return get_user(conn, name)  # type: ignore[return-value]


def update_user(conn: sqlite3.Connection, *, actor: str, name: str,
                **fields: Any) -> Optional[dict[str, Any]]:
    allowed = {"quota_bytes", "used_bytes", "expires_at", "ip_limit",
               "speed_kbps", "hwid", "enabled", "routing", "dns"}
    sets = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not sets:
        return get_user(conn, name)
    assignments = ", ".join(f"{k}=?" for k in sets)
    conn.execute(f"UPDATE users SET {assignments} WHERE name=?",
                 [*sets.values(), name])
    audit.record(conn, actor=actor, action="user.update", target=name,
                 detail=",".join(sets))
    return get_user(conn, name)


def set_enabled(conn: sqlite3.Connection, *, actor: str, name: str,
                enabled: bool) -> None:
    conn.execute("UPDATE users SET enabled=? WHERE name=?",
                 (1 if enabled else 0, name))
    audit.record(conn, actor=actor,
                 action="user.enable" if enabled else "user.disable",
                 target=name)


def delete_user(conn: sqlite3.Connection, *, actor: str, name: str) -> bool:
    cur = conn.execute("DELETE FROM users WHERE name=?", (name,))
    audit.record(conn, actor=actor, action="user.remove", target=name)
    return cur.rowcount > 0


def bulk_action(conn: sqlite3.Connection, *, actor: str, action: str,
                names: list[str]) -> int:
    """Apply enable/disable/delete to many users. Returns affected count."""
    n = 0
    for name in names:
        if action == "enable":
            set_enabled(conn, actor=actor, name=name, enabled=True); n += 1
        elif action == "disable":
            set_enabled(conn, actor=actor, name=name, enabled=False); n += 1
        elif action == "delete":
            if delete_user(conn, actor=actor, name=name):
                n += 1
    return n


def auto_disable_expired(conn: sqlite3.Connection, *, actor: str = "system",
                         now: Optional[int] = None) -> int:
    """Disable users whose quota is used up or whose validity has expired."""
    ts = int(now if now is not None else time.time())
    rows = conn.execute(
        "SELECT name FROM users WHERE enabled=1 AND ("
        "(quota_bytes > 0 AND used_bytes >= quota_bytes) OR "
        "(expires_at IS NOT NULL AND expires_at <= ?))", (ts,)).fetchall()
    for r in rows:
        set_enabled(conn, actor=actor, name=r["name"], enabled=False)
    return len(rows)


def stats(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM users WHERE enabled=1").fetchone()[0]
    used = conn.execute(
        "SELECT COALESCE(SUM(used_bytes),0) FROM users").fetchone()[0]
    return {"total_users": total, "active_users": active,
            "total_used_bytes": int(used)}


# --------------------------------------------------------------------------- #
# nodes (phase 5 multi-server)
# --------------------------------------------------------------------------- #
def list_nodes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM nodes ORDER BY name").fetchall()]


def upsert_node(conn: sqlite3.Connection, *, actor: str, name: str,
                address: str, token: str, api_port: int = 8443,
                geo: Optional[str] = None) -> dict[str, Any]:
    conn.execute(
        "INSERT INTO nodes (name, address, api_port, token, geo) "
        "VALUES (?, ?, ?, ?, ?) ON CONFLICT(name) DO UPDATE SET "
        "address=excluded.address, api_port=excluded.api_port, "
        "token=excluded.token, geo=excluded.geo",
        (name, address, api_port, token, geo))
    audit.record(conn, actor=actor, action="node.upsert", target=name)
    return _row(conn.execute("SELECT * FROM nodes WHERE name=?",
                             (name,)).fetchone())  # type: ignore[return-value]


def delete_node(conn: sqlite3.Connection, *, actor: str, name: str) -> bool:
    cur = conn.execute("DELETE FROM nodes WHERE name=?", (name,))
    audit.record(conn, actor=actor, action="node.remove", target=name)
    return cur.rowcount > 0


def node_heartbeat(conn: sqlite3.Connection, *, name: str, load: float,
                   bandwidth_gb: float = 0.0, healthy: bool = True,
                   now: Optional[int] = None) -> bool:
    ts = int(now if now is not None else time.time())
    cur = conn.execute(
        "UPDATE nodes SET last_seen=?, load=?, bandwidth_gb=?, healthy=? "
        "WHERE name=?",
        (ts, load, bandwidth_gb, 1 if healthy else 0, name))
    return cur.rowcount > 0


def get_setting(conn: sqlite3.Connection, key: str) -> Optional[str]:
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r["value"] if r else None


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))
