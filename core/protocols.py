"""core.protocols — inbound builders + subscription-format converters.

Phase 4 adds new transport protocols (Hysteria2, TUIC v5, WireGuard) and the
ability to emit subscriptions in the formats modern clients expect (sing-box
JSON, Clash-Meta YAML), plus client auto-detection from the User-Agent.

Everything here is pure data transformation (dict/str), stdlib only, so it is
fully unit-testable without a running Xray.
"""

from __future__ import annotations

from typing import Any, Iterable


# --------------------------------------------------------------------------- #
# inbound builders (sing-box style dicts; Xray reads compatible shapes)
# --------------------------------------------------------------------------- #
def hysteria2_inbound(port: int, password: str, *, up_mbps: int = 100,
                      down_mbps: int = 100, obfs: str | None = None) -> dict:
    ib: dict[str, Any] = {
        "type": "hysteria2", "tag": "hysteria2-in", "listen": "::",
        "listen_port": port,
        "users": [{"password": password}],
        "up_mbps": up_mbps, "down_mbps": down_mbps,
    }
    if obfs:
        ib["obfs"] = {"type": "salamander", "password": obfs}
    return ib


def tuic_inbound(port: int, uuid: str, password: str, *,
                 congestion_control: str = "bbr") -> dict:
    return {
        "type": "tuic", "tag": "tuic-in", "listen": "::", "listen_port": port,
        "users": [{"uuid": uuid, "password": password}],
        "congestion_control": congestion_control,
        "zero_rtt_handshake": True,
    }


def wireguard_inbound(port: int, private_key: str, peers: list[dict]) -> dict:
    return {
        "type": "wireguard", "tag": "wg-in", "listen": "::",
        "listen_port": port, "private_key": private_key,
        "peers": peers,
    }


def mux_settings(enabled: bool = True, protocol: str = "h2mux",
                 max_streams: int = 8) -> dict:
    return {"enabled": enabled, "protocol": protocol,
            "max_streams": max_streams}


# --------------------------------------------------------------------------- #
# phase-10 companion protocols (sing-box only — run beside the default REALITY
# path via the opt-in sing-box companion, never replacing it). Pure data here;
# the companion shell (scripts/kian-protocols.sh) is what materializes them.
# --------------------------------------------------------------------------- #
def shadowtls_inbound(port: int, password: str, handshake_server: str, *,
                      version: int = 3, handshake_port: int = 443,
                      detour: str = "shadowtls-ss") -> dict:
    """ShadowTLS v3 (10.2): wraps a real TLS handshake to a decoy server, then
    tunnels the inner connection. ``detour`` is the tag of the inner inbound
    (usually a Shadowsocks listener) that carries the real traffic."""
    if version not in (1, 2, 3):
        raise ValueError("shadowtls version must be 1, 2 or 3")
    ib: dict[str, Any] = {
        "type": "shadowtls", "tag": "shadowtls-in", "listen": "::",
        "listen_port": port, "version": version, "detour": detour,
        "handshake": {"server": handshake_server, "server_port": handshake_port},
    }
    if version >= 2:
        ib["password"] = password
    if version == 3:
        ib["users"] = [{"name": "kian", "password": password}]
    return ib


def anytls_inbound(port: int, password: str, *,
                   padding_scheme: list[str] | None = None) -> dict:
    """AnyTLS (10.3): adaptive padding over TLS to defeat traffic-shape
    fingerprinting. ``padding_scheme`` overrides the default packet-padding."""
    ib: dict[str, Any] = {
        "type": "anytls", "tag": "anytls-in", "listen": "::",
        "listen_port": port, "users": [{"password": password}],
    }
    if padding_scheme:
        ib["padding_scheme"] = list(padding_scheme)
    return ib


def ssh_outbound(server: str, port: int, user: str, *,
                 password: str | None = None,
                 private_key: str | None = None,
                 host_key: list[str] | None = None) -> dict:
    """SSH outbound (10.4): tunnel client traffic out through an SSH server.
    Client-side only — this is an outbound, not one of our server inbounds.
    Provide either a password or a private key."""
    if not password and not private_key:
        raise ValueError("ssh_outbound needs a password or private_key")
    ob: dict[str, Any] = {
        "type": "ssh", "tag": "ssh-out", "server": server,
        "server_port": int(port), "user": user,
    }
    if password:
        ob["password"] = password
    if private_key:
        ob["private_key"] = private_key
    if host_key:
        ob["host_key"] = list(host_key)
    return ob


def ech_settings(config: str | None = None, *, pq_signature: bool = False) -> dict:
    """Encrypted Client Hello (10.1): hides the real SNI inside an encrypted
    ClientHello. ``config`` is the server's base64 ECHConfigList (from DNS/cert
    provisioning). With no config this returns ``{"enabled": False}`` — a no-op,
    so wiring it in never breaks a working REALITY/TLS config until a real
    ECHConfigList is supplied (HITL, needs DNS HTTPS RR)."""
    if not config:
        return {"enabled": False}
    return {"enabled": True, "pq_signature_schemes_enabled": bool(pq_signature),
            "config": config}


# --------------------------------------------------------------------------- #
# anti-DPI stream options (Fragment / uTLS)
# --------------------------------------------------------------------------- #
def fragment_settings(packets: str = "tlshello", length: str = "100-200",
                      interval: str = "10-20") -> dict:
    """v2ray/sing-box outbound TLS fragmentation (splits the ClientHello)."""
    return {"packets": packets, "length": length, "interval": interval}


def utls_settings(fingerprint: str = "chrome") -> dict:
    """Mimic a real browser's TLS fingerprint. Valid: chrome/firefox/safari/ios/edge/random."""
    return {"enabled": True, "fingerprint": fingerprint}


_VALID_FP = {"chrome", "firefox", "safari", "ios", "edge", "android", "random"}


def is_valid_fingerprint(fp: str) -> bool:
    return fp in _VALID_FP


def ttl_settings(ttl: int = 64) -> dict:
    """TTL manipulation: low TTL can slip a probe packet past some DPI boxes."""
    if not 1 <= ttl <= 255:
        raise ValueError("ttl must be 1..255")
    return {"sockopt": {"tcpKeepAliveIdle": 100, "ttl": ttl}}


def noise_settings(packets: int = 3, min_len: int = 50,
                   max_len: int = 200) -> dict:
    """Noise padding: inject N meaningless packets to blur traffic shape."""
    if packets < 0 or min_len < 0 or max_len < min_len:
        raise ValueError("bad noise parameters")
    return {"noises": [{"type": "rand", "packet": f"{min_len}-{max_len}",
                        "delay": "5-15"} for _ in range(packets)]}


# --------------------------------------------------------------------------- #
# subscription format converters
# --------------------------------------------------------------------------- #
# A "proxy" here is a normalized descriptor:
#   {name, type, server, port, uuid?/password?, tls?, sni?, network?, path?}
def to_singbox(proxies: Iterable[dict]) -> dict:
    """Convert normalized proxies to a minimal sing-box outbound config."""
    outbounds: list[dict] = []
    tags: list[str] = []
    for p in proxies:
        tag = p["name"]
        tags.append(tag)
        ob: dict[str, Any] = {"type": p["type"], "tag": tag,
                              "server": p["server"], "server_port": int(p["port"])}
        if p.get("uuid"):
            ob["uuid"] = p["uuid"]
        if p.get("password"):
            ob["password"] = p["password"]
        if p.get("tls"):
            ob["tls"] = {"enabled": True, "server_name": p.get("sni", p["server"])}
        outbounds.append(ob)
    outbounds.append({"type": "selector", "tag": "proxy",
                      "outbounds": tags or ["direct"]})
    outbounds.append({"type": "direct", "tag": "direct"})
    return {"outbounds": outbounds}


def to_clash(proxies: Iterable[dict]) -> str:
    """Convert normalized proxies to a Clash-Meta YAML string (hand-rolled)."""
    proxies = list(proxies)
    lines = ["proxies:"]
    names: list[str] = []
    for p in proxies:
        names.append(p["name"])
        t = {"vless": "vless", "vmess": "vmess", "trojan": "trojan",
             "shadowsocks": "ss", "hysteria2": "hysteria2",
             "tuic": "tuic"}.get(p["type"], p["type"])
        line = (f"  - {{name: {_yq(p['name'])}, type: {t}, "
                f"server: {p['server']}, port: {int(p['port'])}")
        if p.get("uuid"):
            line += f", uuid: {p['uuid']}"
        if p.get("password"):
            line += f", password: {_yq(p['password'])}"
        if p.get("tls"):
            line += f", tls: true, servername: {p.get('sni', p['server'])}"
        line += "}"
        lines.append(line)
    lines.append("proxy-groups:")
    lines.append("  - name: PROXY")
    lines.append("    type: select")
    lines.append("    proxies:")
    for n in names or ["DIRECT"]:
        lines.append(f"      - {_yq(n)}")
    return "\n".join(lines) + "\n"


def _yq(s: str) -> str:
    """Quote a YAML scalar only if it needs it."""
    s = str(s)
    if s and all(c.isalnum() or c in "-_.@" for c in s):
        return s
    return '"' + s.replace('"', '\\"') + '"'


# --------------------------------------------------------------------------- #
# client auto-detection (for a smart subscription endpoint)
# --------------------------------------------------------------------------- #
def detect_client(user_agent: str) -> str:
    """Map a subscription request's UA to a format: singbox/clash/v2ray/base64."""
    ua = (user_agent or "").lower()
    if "sing-box" in ua or "singbox" in ua:
        return "singbox"
    if "clash" in ua or "meta" in ua or "stash" in ua or "mihomo" in ua:
        return "clash"
    if "v2rayng" in ua or "v2rayn" in ua or "nekobox" in ua or "v2box" in ua:
        return "v2ray"
    return "base64"
