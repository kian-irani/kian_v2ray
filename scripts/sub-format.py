#!/usr/bin/env python3
"""sub-format — emit a subscription in the format a client expects.

Reads a JSON array of normalized proxy descriptors (from stdin or a file) and
prints a sing-box config, a Clash-Meta YAML, or a base64 v2ray bundle, chosen
either explicitly (--client) or by sniffing a User-Agent (--ua). This is the
engine behind the self-hosted subscription page (phase 4.4-4.6).

    kian-v2ray configs --json | sub-format.py --ua "clash-verge"
    sub-format.py proxies.json --client singbox

A proxy descriptor: {"name","type","server","port", uuid?/password?, tls?, sni?}
"""

from __future__ import annotations

import argparse
import base64
import json
import sys

from core import protocols


def _read_proxies(path: str | None) -> list[dict]:
    raw = sys.stdin.read() if not path or path == "-" else open(path).read()
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("expected a JSON array of proxy descriptors")
    return data


def _base64_bundle(proxies: list[dict]) -> str:
    """A v2ray-style base64 bundle of share links (best-effort per type)."""
    lines: list[str] = []
    for p in proxies:
        host = p["server"]
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"            # bracket IPv6
        if p["type"] in ("vless", "vmess", "trojan"):
            scheme = p["type"]
            lines.append(f"{scheme}://{p.get('uuid','')}@{host}:{p['port']}"
                         f"#{p['name']}")
        elif p["type"] == "shadowsocks":
            userinfo = base64.b64encode(
                f"chacha20-ietf-poly1305:{p.get('password','')}".encode()).decode()
            lines.append(f"ss://{userinfo}@{host}:{p['port']}#{p['name']}")
    return base64.b64encode("\n".join(lines).encode()).decode()


def render(proxies: list[dict], client: str) -> tuple[str, str]:
    """Return (content, content_type) for the chosen client format."""
    if client == "singbox":
        return json.dumps(protocols.to_singbox(proxies), indent=2), "application/json"
    if client == "clash":
        return protocols.to_clash(proxies), "text/yaml"
    return _base64_bundle(proxies), "text/plain"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="render a subscription")
    ap.add_argument("file", nargs="?", help="proxies JSON (default: stdin)")
    ap.add_argument("--client", choices=["singbox", "clash", "v2ray", "base64"])
    ap.add_argument("--ua", help="User-Agent to auto-detect the client from")
    args = ap.parse_args(argv)

    client = args.client
    if not client and args.ua:
        client = protocols.detect_client(args.ua)
    client = client or "base64"
    if client == "v2ray":
        client = "base64"

    proxies = _read_proxies(args.file)
    content, _ = render(proxies, client)
    sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
