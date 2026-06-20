#!/usr/bin/env python3
"""kian node-agent — lightweight per-VPS agent (phase 5).

A tiny stdlib HTTP service that the central panel talks to. It exposes:

    GET  /health   -> {ok, load, mem_used_pct, ts}   (token-gated)
    POST /apply    -> accept a new Xray config, write + reload   (token-gated)

Auth is a shared bearer token (KIAN_NODE_TOKEN). One file, no dependencies, so
it drops onto any VPS and runs under systemd.

    KIAN_NODE_TOKEN=secret KIAN_NODE_PORT=8443 python3 agent.py
"""

from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONFIG_PATH = os.environ.get("KIAN_NODE_CONFIG", "/opt/kian-v2ray/config.json")


def read_load() -> dict:
    out: dict = {"ts": int(time.time())}
    try:
        with open("/proc/loadavg") as fh:
            out["load"] = float(fh.read().split()[0])
    except OSError:
        out["load"] = None
    try:
        mem: dict[str, int] = {}
        with open("/proc/meminfo") as fh:
            for line in fh:
                k, _, rest = line.partition(":")
                mem[k] = int(rest.strip().split()[0])
        total, avail = mem.get("MemTotal", 0), mem.get("MemAvailable", 0)
        out["mem_used_pct"] = round((total - avail) / total * 100, 1) if total else None
    except OSError:
        out["mem_used_pct"] = None
    return out


def make_handler(token: str):
    class Handler(BaseHTTPRequestHandler):
        def _auth_ok(self) -> bool:
            got = self.headers.get("Authorization", "")
            return got == f"Bearer {token}"

        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):  # silence default logging
            pass

        def do_GET(self):
            if not self._auth_ok():
                return self._send(401, {"error": "unauthorized"})
            if self.path.startswith("/health"):
                return self._send(200, {"ok": True, **read_load()})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if not self._auth_ok():
                return self._send(401, {"error": "unauthorized"})
            if self.path.startswith("/apply"):
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    cfg = json.loads(raw)
                except json.JSONDecodeError:
                    return self._send(400, {"error": "bad json"})
                ok, msg = apply_config(cfg)
                return self._send(200 if ok else 500, {"ok": ok, "msg": msg})
            self._send(404, {"error": "not found"})
    return Handler


def apply_config(cfg: dict, path: str = CONFIG_PATH) -> tuple[bool, str]:
    """Validate + atomically write a new config. Reload is left to systemd/docker."""
    if "inbounds" not in cfg:
        return False, "config missing inbounds"
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True, f"wrote {len(cfg['inbounds'])} inbound(s)"
    except OSError as exc:
        return False, str(exc)


def main() -> int:
    token = os.environ.get("KIAN_NODE_TOKEN")
    if not token:
        print("set KIAN_NODE_TOKEN"); return 2
    port = int(os.environ.get("KIAN_NODE_PORT", "8443"))
    srv = ThreadingHTTPServer(("::", port), make_handler(token))
    print(f"kian node-agent on :{port}")
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
