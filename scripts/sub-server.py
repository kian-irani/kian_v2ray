#!/usr/bin/env python3
# ============================================================================
#  KIAN V2Ray — Subscription server (سبک و امن)
#   فقط GET /sub/<token> را سرو می‌کند: محتوای فایل /etc/kian-v2ray/sub/<token>.txt
#   که همان لینک‌های کانفیگِ خودِ همان کاربر است (فرمت base64 استاندارد v2rayNG).
#   - بدون directory listing
#   - توکن با regex سخت‌گیرانه اعتبارسنجی می‌شود → path traversal ممکن نیست
#   - هیچ مسیر دیگری سرو نمی‌شود (404)
#  اجرا: sub-server.py <port[,port,port...]> <subdir>
#   چند پورت با کاما جدا می‌شوند تا اگر یکی توسط پروایدر بسته بود،
#   دیگری از بیرون قابل دسترس باشد (بدون نیاز به اقدام کاربر).
# ============================================================================
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTS_ARG = sys.argv[1] if len(sys.argv) > 1 else "80"
SUBDIR = sys.argv[2] if len(sys.argv) > 2 else "/etc/kian-v2ray/sub"

TOKEN_RE = re.compile(r"^[A-Za-z0-9]{8,64}$")  # letters/digits only — no / or .

# ETC dir = parent of the sub dir (e.g. /etc/kian-v2ray/sub -> /etc/kian-v2ray)
_ETC = os.path.dirname(os.path.realpath(SUBDIR))


def _user_info(token: str) -> str:
    """Build the standard 'Subscription-Userinfo' header value for a token:
    upload=..; download=..; total=..; expire=.. (bytes / epoch seconds).
    Reads sub_tokens.json (email->token) and users.json. Fail-safe: returns ""
    on any error so the subscription still serves."""
    import json as _json
    import time as _time
    try:
        with open(os.path.join(_ETC, "sub_tokens.json"), encoding="utf-8") as fh:
            toks = _json.load(fh)
        email = next((e for e, t in toks.items() if t == token), "")
        if not email:
            return ""
        with open(os.path.join(_ETC, "users.json"), encoding="utf-8") as fh:
            users = _json.load(fh).get("users", [])
        u = next((x for x in users if x.get("email") == email), None)
        if not u:
            return ""
        used = int(u.get("used_bytes") or 0)
        total = int(u.get("quota_bytes") or 0)   # 0 = unlimited
        exp = u.get("expires_at")
        expire = 0
        if exp:
            try:
                from datetime import datetime, timezone
                s = str(exp).replace("Z", "+00:00")
                expire = int(datetime.fromisoformat(s).replace(
                    tzinfo=timezone.utc).timestamp())
            except Exception:
                expire = 0
        # download carries the used bytes; upload 0 (we don't split directions)
        return (f"upload=0; download={used}; total={total}; expire={expire}")
    except Exception:
        return ""


class Handler(BaseHTTPRequestHandler):
    server_version = "kian-sub/1.1"

    def _deny(self, code=404):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"not found\n")

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in ("/health", "/healthz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok\n")
            return
        m = re.match(r"^/sub/([^/]+)$", path)
        if not m:
            return self._deny()
        token = m.group(1)
        if not TOKEN_RE.match(token):
            return self._deny()
        # مسیر امن: فقط داخل SUBDIR، نام فایل دقیقاً <token>.txt
        fpath = os.path.join(SUBDIR, token + ".txt")
        real = os.path.realpath(fpath)
        if os.path.dirname(real) != os.path.realpath(SUBDIR) or not os.path.isfile(real):
            return self._deny()
        try:
            with open(real, "rb") as f:
                data = f.read()
        except OSError:
            return self._deny()
        self.send_response(200)
        # Format v2rayNG/NekoBox understand for a subscription
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Profile-Update-Interval", "12")
        # Standard Subscription-Userinfo header so clients (v2rayNG, NekoBox,
        # Streisand…) can show usage + expiry, like Marzban/3x-ui. Fail-safe:
        # any lookup error simply omits the header.
        info = _user_info(token)
        if info:
            self.send_header("Subscription-Userinfo", info)
            self.send_header("Profile-Title", token[:8])
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # خاموش‌کردن لاگ پرحجم پیش‌فرض
    def log_message(self, *a):
        pass


def serve(port: int):
    """یک سرور روی پورت داده‌شده اجرا می‌کند. اگر bind نشد، خاموش می‌شود (بقیه پورت‌ها فعال می‌مانند)."""
    try:
        srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    except OSError as e:
        print(f"[!] kian sub-server: bind فلد روی :{port} — {e}", flush=True)
        return
    print(f"[+] kian sub-server on :{port} serving {SUBDIR}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    os.makedirs(SUBDIR, exist_ok=True)
    ports = []
    for p in PORTS_ARG.split(","):
        p = p.strip()
        if p.isdigit():
            n = int(p)
            if 1 <= n <= 65535 and n not in ports:
                ports.append(n)
    if not ports:
        ports = [80]
    threads = []
    for p in ports:
        t = threading.Thread(target=serve, args=(p,), daemon=True)
        t.start()
        threads.append(t)
    # تا وقتی حداقل یکی از سرورها زنده است، سرویس را زنده نگه دار
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        sys.exit(0)
