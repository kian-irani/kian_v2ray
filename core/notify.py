"""core.notify — event notifications: Telegram, Email (SMTP), Webhook.

Stdlib-only. Used to alert the admin on events (expiry, quota reached, new
login from an unknown IP, node down). Each channel is independent and degrades
gracefully (a failure in one never raises to the caller).

    from core.notify import Notifier
    n = Notifier(telegram=("BOT_TOKEN", "CHAT_ID"),
                 email_smtp={"host": "smtp.x.com", "port": 587, ...},
                 webhook_url="https://hooks.example.com/kian")
    n.event("user.expired", "ali's subscription expired", user="ali")
"""

from __future__ import annotations

import json
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from typing import Any, Optional


class Notifier:
    def __init__(self, *, telegram: Optional[tuple[str, str]] = None,
                 email_smtp: Optional[dict[str, Any]] = None,
                 webhook_url: Optional[str] = None,
                 timeout: float = 15.0):
        self.telegram = telegram
        self.email_smtp = email_smtp
        self.webhook_url = webhook_url
        self.timeout = timeout

    # ---- public ----
    def event(self, kind: str, message: str, **fields: Any) -> dict[str, bool]:
        """Fan out an event to every configured channel. Returns per-channel ok."""
        results: dict[str, bool] = {}
        if self.telegram:
            results["telegram"] = self._telegram(f"🔔 {kind}\n{message}")
        if self.email_smtp:
            results["email"] = self._email(f"[KIAN] {kind}", message)
        if self.webhook_url:
            results["webhook"] = self._webhook(
                {"kind": kind, "message": message, **fields})
        return results

    # ---- channels ----
    def _telegram(self, text: str) -> bool:
        try:
            token, chat = self.telegram  # type: ignore[misc]
            data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            with urllib.request.urlopen(url, data=data, timeout=self.timeout) as r:
                return r.status == 200
        except Exception:
            return False

    def _email(self, subject: str, body: str) -> bool:
        try:
            c = self.email_smtp  # type: ignore[assignment]
            msg = MIMEText(body, _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = c["from"]
            msg["To"] = c["to"]
            ctx = ssl.create_default_context()
            with smtplib.SMTP(c["host"], int(c.get("port", 587)),
                              timeout=self.timeout) as s:
                s.starttls(context=ctx)
                if c.get("user"):
                    s.login(c["user"], c["password"])
                s.sendmail(c["from"], [c["to"]], msg.as_string())
            return True
        except Exception:
            return False

    def _webhook(self, payload: dict[str, Any]) -> bool:
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self.webhook_url, data=data,  # type: ignore[arg-type]
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return 200 <= r.status < 300
        except Exception:
            return False


def build_message(kind: str, **fields: Any) -> str:
    """A consistent human message for the common event kinds."""
    templates = {
        "user.expired": "کاربر {user} منقضی شد.",
        "user.quota": "سهمیهٔ کاربر {user} تمام شد ({used_gb}GB).",
        "user.newip": "ورود از IP ناشناس برای {user}: {ip}",
        "node.down": "نود {node} از دسترس خارج شد.",
        "node.bandwidth": "پهنای‌باند نود {node} به آستانه رسید ({bandwidth_gb}GB).",
    }
    tpl = templates.get(kind, "{kind}")
    try:
        return tpl.format(kind=kind, **fields)
    except KeyError:
        return f"{kind}: {fields}"
