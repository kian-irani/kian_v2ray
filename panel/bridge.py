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


LINKS_FILE = os.environ.get("KIAN_LINKS_FILE", "/etc/kian-v2ray/links.txt")
USERS_FILE_PATH = USERS_JSON


def read_user_links(name: str) -> list[str]:
    """Return the share-URI config links that belong to ``name`` (by uuid match).

    Reads the installer's links.txt (one URI per line) and filters lines whose
    path/query contains the user's UUID.  Falls back to CLI if links.txt absent.
    """
    # get uuid from users.json
    uuid = ""
    users = read_installer_users()
    for u in users:
        local = (u.get("name") or "").split("@")[0]
        if u.get("name") == name or local == name:
            uuid = u.get("uuid") or ""
            break

    if not uuid:
        # try CLI (kian-v2ray configs <name>) — strip ANSI, keep URI lines
        rc, out = cli("configs", name, timeout=15.0)
        if rc == 0:
            import re
            ansi = re.compile(r'\x1b\[[0-9;]*m')
            return [l for l in (ansi.sub("", out)).splitlines()
                    if l.startswith(("vless://", "vmess://", "ss://", "trojan://",
                                     "hysteria2://", "tuic://"))]
        return []

    # filter links.txt by uuid
    if not os.path.exists(LINKS_FILE):
        rc, out = cli("configs", name, timeout=15.0)
        if rc == 0:
            import re
            ansi = re.compile(r'\x1b\[[0-9;]*m')
            return [l for l in (ansi.sub("", out)).splitlines()
                    if l.startswith(("vless://", "vmess://", "ss://", "trojan://",
                                     "hysteria2://", "tuic://"))]
        return []

    try:
        with open(LINKS_FILE, "r", encoding="utf-8") as fh:
            return [l.strip() for l in fh if uuid in l and l.strip()]
    except OSError:
        return []


# --------------------------------------------------------------------------- #
# per-user routing / DNS (phase 11.2)
# --------------------------------------------------------------------------- #
# Private/LAN subnets bypassed in bypass-lan/both — kept in sync with the mobile
# app's AppSettings._lan so the panel and the client agree on "LAN".
_LAN = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8",
        "169.254.0.0/16", "224.0.0.0/4", "fc00::/7", "::1/128"]


def per_user_routing(name: str, routing: str | None = None,
                     dns: str | None = None) -> dict:
    """Build the per-user routing + DNS fragment the installer merges into the
    user's block (11.2). Pure data, testable without a running Xray.

    ``routing`` in {global, bypass-lan, bypass-iran, bypass-both}; None/""/global
    means "server default" and yields no routing rules. ``dns`` is a comma/space
    separated server list. Returns ``{}`` when nothing is overridden.
    """
    frag: dict[str, Any] = {}
    rules: list[dict[str, Any]] = []
    if routing in ("bypass-lan", "bypass-both"):
        rules.append({"type": "field", "ip": list(_LAN), "outboundTag": "direct"})
    if routing in ("bypass-iran", "bypass-both"):
        rules.append({"type": "field", "ip": ["geoip:ir"], "outboundTag": "direct"})
        rules.append({"type": "field", "domain": ["geosite:category-ir"],
                      "outboundTag": "direct"})
    if rules:
        frag["rules"] = rules
    servers = [s.strip() for s in (dns or "").replace(",", " ").split() if s.strip()]
    if servers:
        frag["dns"] = {"servers": servers}
    return frag
