"""kv2m.panel_client — minimal REST client for the kian_v2ray web panel.

Lets the desktop app manage users through the panel's HTTP API (instead of, or
in addition to, raw SSH). Pure stdlib (urllib). Handles bearer auth + a single
transparent token refresh on 401.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Optional


class PanelError(Exception):
    pass


class PanelClient:
    def __init__(self, base_url: str, *, timeout: float = 15.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self._access: Optional[str] = None
        self._refresh: Optional[str] = None

    # ---- low level ----
    def _request(self, method: str, path: str,
                 body: Optional[dict] = None, auth: bool = True) -> Any:
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json"}
        if auth and self._access:
            headers["Authorization"] = f"Bearer {self._access}"
        req = urllib.request.Request(self.base + path, data=data,
                                     headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and auth and self._refresh:
                if self._do_refresh():
                    return self._request(method, path, body, auth)
            raise PanelError(f"{method} {path}: HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise PanelError(f"{method} {path}: {exc.reason}") from exc

    def _do_refresh(self) -> bool:
        try:
            tok = self._request("POST", "/auth/refresh",
                                {"refresh_token": self._refresh}, auth=False)
        except PanelError:
            return False
        self._access = tok["access_token"]
        self._refresh = tok["refresh_token"]
        return True

    # ---- api ----
    def login(self, username: str, password: str,
              totp: Optional[str] = None) -> None:
        body = {"username": username, "password": password}
        if totp:
            body["totp"] = totp
        tok = self._request("POST", "/auth/login", body, auth=False)
        self._access, self._refresh = tok["access_token"], tok["refresh_token"]

    def list_users(self, q: str = "") -> list[dict]:
        path = "/api/users?limit=500" + (f"&q={q}" if q else "")
        return self._request("GET", path)

    def add_user(self, name: str, *, quota_gb: int = 0,
                 days: int = 0, ip_limit: int = 0) -> dict:
        import time
        body: dict = {"name": name, "quota_bytes": quota_gb * 1073741824,
                      "ip_limit": ip_limit}
        if days > 0:
            body["expires_at"] = int(time.time()) + days * 86400
        return self._request("POST", "/api/users", body)

    def delete_user(self, name: str) -> None:
        self._request("DELETE", f"/api/users/{name}")

    def stats(self) -> dict:
        return self._request("GET", "/api/stats")
