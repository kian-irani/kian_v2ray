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
import tempfile
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
    import secrets as _sec
    rows = read_installer_users(path)
    added = updated = 0
    for r in rows:
        existing = conn.execute(
            "SELECT id, sub_token FROM users WHERE name=?",
            (r["name"],)).fetchone()
        if existing:
            conn.execute(
                "UPDATE users SET uuid=?, enabled=?, quota_bytes=?, "
                "used_bytes=?, expires_at=? WHERE name=?",
                (r["uuid"], r["enabled"], r["quota_bytes"], r["used_bytes"],
                 r["expires_at"], r["name"]))
            # Backfill sub_token for users that were imported before migration 0007
            if not existing[1]:
                conn.execute("UPDATE users SET sub_token=? WHERE name=?",
                             (_sec.token_urlsafe(16), r["name"]))
            updated += 1
        else:
            conn.execute(
                "INSERT INTO users (name, uuid, enabled, quota_bytes, "
                "used_bytes, expires_at, sub_token) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (r["name"], r["uuid"], r["enabled"], r["quota_bytes"],
                 r["used_bytes"], r["expires_at"], _sec.token_urlsafe(16)))
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
ETC_DIR = os.environ.get("KIAN_ETC_DIR", "/etc/kian-v2ray")

_URI_PREFIXES = ("vless://", "vmess://", "ss://", "trojan://",
                 "hysteria2://", "tuic://", "anytls://")


def _links_from_sub_file(name: str) -> list[str]:
    """Decode the user's subscription file ($ETC_DIR/sub/<token>.txt = base64 of
    that user's links). This is the authoritative per-user source the server uses,
    so it works even when links.txt is absent or UUID filtering misses. Returns []
    if the token/file isn't found."""
    import base64
    import json as _json
    tokmap = os.path.join(ETC_DIR, "sub_tokens.json")
    try:
        with open(tokmap, "r", encoding="utf-8") as fh:
            m = _json.load(fh)
    except (OSError, ValueError):
        return []
    # sub_tokens.json is keyed by email (e.g. "ali@kian"); accept name or local part.
    token = ""
    for email, tok in (m.items() if isinstance(m, dict) else []):
        local = str(email).split("@")[0]
        if email == name or local == name:
            token = str(tok)
            break
    if not token:
        return []
    fpath = os.path.join(ETC_DIR, "sub", token + ".txt")
    try:
        with open(fpath, "rb") as fh:
            raw = fh.read()
    except OSError:
        return []
    try:
        decoded = base64.b64decode(raw).decode("utf-8", "ignore")
    except Exception:
        decoded = raw.decode("utf-8", "ignore")
    return [l.strip() for l in decoded.splitlines()
            if l.strip().startswith(_URI_PREFIXES)]


def read_user_links(name: str) -> list[str]:
    """Return the share-URI config links that belong to ``name``.

    Primary source: the user's own subscription file (authoritative, always has
    every protocol). Falls back to links.txt (UUID-filtered) and then the CLI.
    """
    sub = _links_from_sub_file(name)
    if sub:
        return sub
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
            # Match whole-word UUID to avoid leaking links whose URI contains
            # a different user's UUID as a substring of a longer path segment.
            import re as _re
            pattern = _re.compile(r'\b' + _re.escape(uuid) + r'\b')
            return [l.strip() for l in fh
                    if l.strip() and pattern.search(l)]
    except OSError:
        return []


def read_all_links() -> list[str]:
    """Return every config share-URI on the server (the whole links.txt).

    Lets the panel offer "copy all configs" so an operator never has to SSH in
    and copy from the terminal when a subscription link fails.
    """
    if os.path.exists(LINKS_FILE):
        try:
            with open(LINKS_FILE, "r", encoding="utf-8") as fh:
                return [l.strip() for l in fh
                        if l.strip().startswith(
                            ("vless://", "vmess://", "ss://", "trojan://",
                             "hysteria2://", "tuic://"))]
        except OSError:
            pass
    # fall back to the CLI (strip ANSI colour codes)
    rc, out = cli("configs", timeout=20.0)
    if rc == 0:
        import re
        ansi = re.compile(r'\x1b\[[0-9;]*m')
        return [l for l in ansi.sub("", out).splitlines()
                if l.startswith(("vless://", "vmess://", "ss://", "trojan://",
                                 "hysteria2://", "tuic://"))]
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


# --------------------------------------------------------------------------- #
# raw Xray config editor (advanced panel) — read the live config and apply an
# edited one through the CLI's safe path (backup → apply → restart → rollback).
# --------------------------------------------------------------------------- #
XRAY_CONFIG = os.environ.get("KIAN_XRAY_CONFIG", "/etc/kian-v2ray/config.json")


def read_xray_config() -> dict[str, Any]:
    """Return the live Xray config.json as parsed JSON (or {} if missing)."""
    try:
        with open(XRAY_CONFIG, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def apply_xray_config(cfg: dict[str, Any]) -> tuple[int, str]:
    """Validate + apply an edited Xray config through the CLI's safe path.

    Writes the JSON to a temp file and calls ``kian-v2ray apply-config <file>``
    which backs up, swaps, restarts, and rolls back if Xray fails to come up.
    Returns ``(exit_code, output)``; non-zero means the change was rejected and
    the previous config is still live.
    """
    if not isinstance(cfg, dict):
        return 2, "config must be a JSON object"
    ins, outs = cfg.get("inbounds"), cfg.get("outbounds")
    # Require NON-EMPTY arrays: an empty inbounds is valid to xray-core and would
    # start cleanly (so rollback never triggers) while silently taking every user
    # offline — reject it up front instead.
    if not isinstance(ins, list) or not ins:
        return 2, "config must have a non-empty inbounds array"
    if not isinstance(outs, list) or not outs:
        return 2, "config must have a non-empty outbounds array"
    fd, tmp = tempfile.mkstemp(prefix="kian-xray-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
        return cli("apply-config", tmp, timeout=90.0)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
