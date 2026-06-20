"""core.audit — admin audit trail (who did what, when, from where).

Every privileged action (add/remove/renew user, rotate keys, change settings)
should call :func:`record`. The trail lives in the ``audit_log`` table created
by migration 0002 and is also echoed to the structured JSON log so it shows up
in monitoring.

    from core import audit
    audit.record(conn, actor="root", action="user.add",
                 target="ali", ip="1.2.3.4", detail="quota=100GB days=30")
"""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from .logging import get_logger

_log = get_logger("audit")


def record(conn: sqlite3.Connection, actor: str, action: str,
           target: Optional[str] = None, ip: Optional[str] = None,
           detail: Optional[str] = None) -> int:
    """Insert an audit row and mirror it to the JSON log. Returns row id."""
    cur = conn.execute(
        "INSERT INTO audit_log (actor, action, target, ip, detail) "
        "VALUES (?, ?, ?, ?, ?)",
        (actor, action, target, ip, detail),
    )
    _log.info("audit", actor=actor, action=action, target=target, ip=ip,
              detail=detail)
    return int(cur.lastrowid)


def tail(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent *limit* audit entries, newest first."""
    rows = conn.execute(
        "SELECT id, ts, actor, action, target, ip, detail "
        "FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
