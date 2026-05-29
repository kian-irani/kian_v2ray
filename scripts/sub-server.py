#!/usr/bin/env python3
# ============================================================================
#  KIAN V2Ray — Subscription server (سبک و امن)
#   فقط GET /sub/<token> را سرو می‌کند: محتوای فایل /etc/kian-v2ray/sub/<token>.txt
#   که همان لینک‌های کانفیگِ خودِ همان کاربر است (فرمت base64 استاندارد v2rayNG).
#   - بدون directory listing
#   - توکن با regex سخت‌گیرانه اعتبارسنجی می‌شود → path traversal ممکن نیست
#   - هیچ مسیر دیگری سرو نمی‌شود (404)
#  اجرا: sub-server.py <port> <subdir>
# ============================================================================
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
SUBDIR = sys.argv[2] if len(sys.argv) > 2 else "/etc/kian-v2ray/sub"

TOKEN_RE = re.compile(r"^[A-Za-z0-9]{8,64}$")  # فقط حروف/عدد — بدون / یا .


class Handler(BaseHTTPRequestHandler):
    server_version = "kian-sub/1.0"

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
        # فرمتی که v2rayNG برای subscription می‌فهمد
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Profile-Update-Interval", "12")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # خاموش‌کردن لاگ پرحجم پیش‌فرض
    def log_message(self, *a):
        pass


if __name__ == "__main__":
    os.makedirs(SUBDIR, exist_ok=True)
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"kian sub-server on :{PORT} serving {SUBDIR}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
