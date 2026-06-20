#!/usr/bin/env python3
"""config-health — verify a kian_v2ray Xray config actually works.

Goes beyond "is the process up?" by statically validating the generated
config.json and (optionally) probing that each inbound port is actually
listening. Designed to be called by the CLI (`kian-v2ray health`) and by CI on
a sample config.

Checks:
    * config.json parses as JSON and has the expected top-level shape
    * every inbound has a unique port and a known protocol
    * Reality inbounds declare privateKey + shortIds + serverNames
    * Shadowsocks inbounds use an allowed cipher
    * (with --probe) each inbound TCP port accepts a local connection

Exit code 0 = healthy, 1 = problems found (printed), 2 = usage error.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys

KNOWN_PROTOCOLS = {
    "vless", "vmess", "trojan", "shadowsocks", "dokodemo-door",
    "http", "socks", "wireguard", "hysteria2", "tuic",
}
# Shadowsocks ciphers we consider safe/modern (matches 0.6 SS redesign).
SS_ALLOWED_CIPHERS = {
    "2022-blake3-aes-128-gcm",
    "2022-blake3-aes-256-gcm",
    "2022-blake3-chacha20-poly1305",
    "aes-256-gcm",
    "aes-128-gcm",
    "chacha20-ietf-poly1305",
}


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check_config(cfg: dict) -> list[str]:
    """Return a list of human-readable problems (empty == healthy)."""
    problems: list[str] = []
    inbounds = cfg.get("inbounds")
    if not isinstance(inbounds, list) or not inbounds:
        problems.append("no inbounds defined")
        return problems

    seen_ports: dict[int, str] = {}
    for i, ib in enumerate(inbounds):
        tag = ib.get("tag", f"#{i}")
        proto = ib.get("protocol")
        port = ib.get("port")
        if proto not in KNOWN_PROTOCOLS:
            problems.append(f"[{tag}] unknown protocol: {proto!r}")
        if not isinstance(port, int):
            problems.append(f"[{tag}] missing/invalid port: {port!r}")
        elif port in seen_ports:
            problems.append(
                f"[{tag}] port {port} already used by {seen_ports[port]}")
        else:
            seen_ports[port] = tag

        stream = ib.get("streamSettings", {}) or {}
        if stream.get("security") == "reality":
            r = stream.get("realitySettings", {}) or {}
            if not r.get("privateKey"):
                problems.append(f"[{tag}] reality: missing privateKey")
            if not r.get("shortIds"):
                problems.append(f"[{tag}] reality: missing shortIds")
            if not r.get("serverNames"):
                problems.append(f"[{tag}] reality: missing serverNames")

        if proto == "shadowsocks":
            settings = ib.get("settings", {}) or {}
            method = settings.get("method")
            if method not in SS_ALLOWED_CIPHERS:
                problems.append(
                    f"[{tag}] shadowsocks: weak/unknown cipher {method!r} "
                    f"(allowed: {', '.join(sorted(SS_ALLOWED_CIPHERS))})")
    return problems


def probe_ports(cfg: dict, host: str = "127.0.0.1",
                timeout: float = 2.0) -> list[str]:
    """Return problems for inbound ports that don't accept a connection."""
    problems: list[str] = []
    for ib in cfg.get("inbounds", []):
        port = ib.get("port")
        tag = ib.get("tag", "?")
        if not isinstance(port, int):
            continue
        try:
            with socket.create_connection((host, port), timeout=timeout):
                pass
        except OSError:
            problems.append(f"[{tag}] port {port} not accepting connections")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="kian_v2ray config health check")
    ap.add_argument("config", nargs="?", default="/opt/kian-v2ray/config.json")
    ap.add_argument("--probe", action="store_true",
                    help="also TCP-probe each inbound port locally")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        print(f"config-health: not found: {args.config}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"config-health: invalid JSON: {exc}", file=sys.stderr)
        return 1

    problems = check_config(cfg)
    if args.probe:
        problems += probe_ports(cfg)

    if problems:
        print(f"✗ {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    n = len(cfg.get("inbounds", []))
    print(f"✓ config healthy — {n} inbound(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
