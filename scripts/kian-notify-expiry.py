#!/usr/bin/env python3
"""kian-notify-expiry — server-side expiry/quota notifications (GMS-free push).

Scans the user db and notifies the admin (Telegram / Email / Webhook) about
users that are about to expire or have nearly used their quota. Runs from cron;
this is the GMS-free alternative to FCM push for "subscription expiring" alerts.

    KIAN_TG_BOT_TOKEN=... KIAN_TG_CHAT_ID=... \
      python3 kian-notify-expiry.py --days 3 --quota-pct 90

Channels are configured via env:
    KIAN_TG_BOT_TOKEN / KIAN_TG_CHAT_ID         -> Telegram
    KIAN_SMTP_HOST/PORT/USER/PASS/FROM/TO       -> Email
    KIAN_WEBHOOK_URL                            -> Webhook
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from core import db as core_db
from core import notify


def _notifier() -> notify.Notifier:
    tg = None
    if os.environ.get("KIAN_TG_BOT_TOKEN") and os.environ.get("KIAN_TG_CHAT_ID"):
        tg = (os.environ["KIAN_TG_BOT_TOKEN"], os.environ["KIAN_TG_CHAT_ID"])
    email = None
    if os.environ.get("KIAN_SMTP_HOST"):
        email = {
            "host": os.environ["KIAN_SMTP_HOST"],
            "port": os.environ.get("KIAN_SMTP_PORT", "587"),
            "user": os.environ.get("KIAN_SMTP_USER"),
            "password": os.environ.get("KIAN_SMTP_PASS"),
            "from": os.environ.get("KIAN_SMTP_FROM"),
            "to": os.environ.get("KIAN_SMTP_TO"),
        }
    return notify.Notifier(telegram=tg, email_smtp=email,
                           webhook_url=os.environ.get("KIAN_WEBHOOK_URL"))


def find_due(conn, *, days: int, quota_pct: int, now: int | None = None):
    """Return (expiring, over_quota) lists of user rows that need an alert."""
    ts = int(now if now is not None else time.time())
    horizon = ts + days * 86400
    expiring = [dict(r) for r in conn.execute(
        "SELECT * FROM users WHERE enabled=1 AND expires_at IS NOT NULL "
        "AND expires_at > ? AND expires_at <= ?", (ts, horizon)).fetchall()]
    over = [dict(r) for r in conn.execute(
        "SELECT * FROM users WHERE enabled=1 AND quota_bytes > 0 "
        "AND used_bytes * 100 >= quota_bytes * ?", (quota_pct,)).fetchall()]
    return expiring, over


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="notify expiring/over-quota users")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--quota-pct", type=int, default=90)
    ap.add_argument("--db", default=core_db.DEFAULT_DB_PATH)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    n = _notifier()
    sent = 0
    with core_db.session(args.db) as conn:
        expiring, over = find_due(conn, days=args.days, quota_pct=args.quota_pct)
        for u in expiring:
            msg = notify.build_message("user.expired", user=u["name"])
            print(f"[expiry] {u['name']}", file=sys.stderr)
            if not args.dry_run:
                n.event("user.expiring", msg, user=u["name"]); sent += 1
        for u in over:
            used_gb = round(u["used_bytes"] / 1073741824, 1)
            msg = notify.build_message("user.quota", user=u["name"], used_gb=used_gb)
            print(f"[quota] {u['name']} {used_gb}GB", file=sys.stderr)
            if not args.dry_run:
                n.event("user.quota", msg, user=u["name"], used_gb=used_gb); sent += 1
    print(f"kian-notify-expiry: {len(expiring)} expiring, {len(over)} over-quota, "
          f"{sent} notifications sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
