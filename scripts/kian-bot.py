#!/usr/bin/env python3
"""kian-bot — Telegram management bot for kian_v2ray (phase 4.10).

A dependency-free (stdlib urllib) long-polling bot that lets the admin manage
users from Telegram: status, list, add, remove, usage. It talks to the local
SQLite db via core/ + panel.repo, so it works on the same box as the installer.

Only chat IDs in KIAN_BOT_ADMINS (comma-separated) are obeyed.

Env:
    KIAN_BOT_TOKEN     Telegram bot token (required)
    KIAN_BOT_ADMINS    comma-separated admin chat ids (required)
    KIAN_DB_PATH       path to kian.db (default core.db.DEFAULT_DB_PATH)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

from core import db as core_db
from panel import repo

API = "https://api.telegram.org/bot{token}/{method}"


def _call(token: str, method: str, **params) -> dict:
    url = API.format(token=token, method=method)
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(url, data=data, timeout=70) as resp:
        return json.loads(resp.read().decode())


def _get_updates(token: str, offset: int) -> list[dict]:
    try:
        r = _call(token, "getUpdates", offset=offset, timeout=50)
        return r.get("result", [])
    except Exception:
        return []


def _fmt_gb(b: int) -> str:
    return f"{b / 1073741824:.2f}GB"


def handle(text: str, db_path: str) -> str:
    """Return a reply for a command. Pure-ish (db read/write)."""
    parts = text.strip().split()
    if not parts:
        return "?"
    cmd, args = parts[0].lstrip("/").lower(), parts[1:]
    with core_db.session(db_path) as conn:
        if cmd in ("start", "help"):
            return ("KIAN bot:\n/status\n/users\n/add <name> [gb] [days]\n"
                    "/remove <name>\n/usage <name>")
        if cmd == "status":
            s = repo.stats(conn)
            return (f"users: {s['total_users']} (active {s['active_users']})\n"
                    f"traffic: {_fmt_gb(s['total_used_bytes'])}")
        if cmd == "users":
            us = repo.list_users(conn, limit=50)
            if not us:
                return "(no users)"
            return "\n".join(f"{'✅' if u['enabled'] else '⛔'} {u['name']} "
                             f"{_fmt_gb(u['used_bytes'])}" for u in us)
        if cmd == "add" and args:
            name = args[0]
            gb = int(args[1]) if len(args) > 1 else 0
            days = int(args[2]) if len(args) > 2 else 0
            if repo.get_user(conn, name):
                return f"{name} already exists"
            expires = int(time.time()) + days * 86400 if days else None
            repo.create_user(conn, actor="telegram", name=name,
                             quota_bytes=gb * 1073741824, expires_at=expires)
            return f"added {name} (quota {gb}GB, {days or '∞'}d)"
        if cmd == "remove" and args:
            ok = repo.delete_user(conn, actor="telegram", name=args[0])
            return f"removed {args[0]}" if ok else f"no such user {args[0]}"
        if cmd == "usage" and args:
            u = repo.get_user(conn, args[0])
            if not u:
                return f"no such user {args[0]}"
            q = _fmt_gb(u["quota_bytes"]) if u["quota_bytes"] else "∞"
            return f"{u['name']}: {_fmt_gb(u['used_bytes'])} / {q}"
    return "unknown command — /help"


def main(argv: list[str] | None = None) -> int:
    token = os.environ.get("KIAN_BOT_TOKEN")
    admins = {a.strip() for a in os.environ.get("KIAN_BOT_ADMINS", "").split(",") if a.strip()}
    db_path = os.environ.get("KIAN_DB_PATH", core_db.DEFAULT_DB_PATH)
    if not token or not admins:
        print("set KIAN_BOT_TOKEN and KIAN_BOT_ADMINS", file=sys.stderr)
        return 2
    print("kian-bot: polling…", file=sys.stderr)
    offset = 0
    while True:
        for upd in _get_updates(token, offset):
            offset = upd["update_id"] + 1
            msg = upd.get("message") or {}
            chat = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "")
            if chat not in admins:
                continue
            try:
                reply = handle(text, db_path)
            except Exception as exc:       # never die on one bad command
                reply = f"error: {exc}"
            _call(token, "sendMessage", chat_id=chat, text=reply)
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
