"""Tests for core.protocols + core.censorship (phase 4)."""

from __future__ import annotations

from core import censorship, protocols


# ---------- inbound builders ----------

def test_hysteria2_and_tuic_inbounds():
    h = protocols.hysteria2_inbound(443, "pw", obfs="salt")
    assert h["type"] == "hysteria2" and h["listen_port"] == 443
    assert h["users"][0]["password"] == "pw"
    assert h["obfs"]["password"] == "salt"
    t = protocols.tuic_inbound(8443, "uuid-1", "pw")
    assert t["type"] == "tuic" and t["users"][0]["uuid"] == "uuid-1"


def test_wireguard_inbound_and_mux():
    wg = protocols.wireguard_inbound(51820, "priv", [{"public_key": "p"}])
    assert wg["type"] == "wireguard" and wg["peers"][0]["public_key"] == "p"
    assert protocols.mux_settings()["max_streams"] == 8


def test_amneziawg_inbound():
    awg = protocols.amneziawg_inbound(51821, "priv", [{"public_key": "p"}],
                                      jc=5, jmin=30, jmax=80)
    assert awg["type"] == "wireguard"        # WG-compatible base shape
    assert awg["tag"] == "amneziawg-in"
    o = awg["obfs"]
    assert o["type"] == "amnezia" and o["jc"] == 5 and o["jmin"] == 30
    assert (o["h1"], o["h2"], o["h3"], o["h4"]) == (1, 2, 3, 4)
    # bad junk range and non-distinct headers are rejected
    for bad in (lambda: protocols.amneziawg_inbound(1, "k", [], jmin=90, jmax=10),
                lambda: protocols.amneziawg_inbound(1, "k", [], h1=1, h2=1)):
        try:
            bad(); raised = False
        except ValueError:
            raised = True
        assert raised


def test_fragment_profiles():
    assert "aggressive" in protocols.fragment_profiles()
    assert protocols.fragment_profile("off") is None
    agg = protocols.fragment_profile("aggressive")
    assert agg["length"] == "10-40" and agg["interval"] == "30-60"
    # case-insensitive, and a typo raises rather than silently disabling
    assert protocols.fragment_profile("DEFAULT")["packets"] == "tlshello"
    try:
        protocols.fragment_profile("nope"); raised = False
    except ValueError:
        raised = True
    assert raised


def test_phase10_companion_protocols():
    # ShadowTLS v3 (10.2)
    st = protocols.shadowtls_inbound(8443, "pw", "www.microsoft.com")
    assert st["type"] == "shadowtls" and st["version"] == 3
    assert st["handshake"]["server"] == "www.microsoft.com"
    assert st["users"][0]["password"] == "pw" and st["detour"] == "shadowtls-ss"
    try:
        protocols.shadowtls_inbound(8443, "pw", "x", version=9); bad = False
    except ValueError:
        bad = True
    assert bad
    # AnyTLS (10.3)
    at = protocols.anytls_inbound(9443, "pw", padding_scheme=["stop=8"])
    assert at["type"] == "anytls" and at["padding_scheme"] == ["stop=8"]
    assert at["users"][0]["password"] == "pw"
    # SSH outbound (10.4) — client-side
    ssh = protocols.ssh_outbound("1.2.3.4", 22, "root", password="pw")
    assert ssh["type"] == "ssh" and ssh["server_port"] == 22 and ssh["user"] == "root"
    try:
        protocols.ssh_outbound("1.2.3.4", 22, "root"); bad2 = False
    except ValueError:
        bad2 = True
    assert bad2
    # ECH (10.1) — no-op until a real ECHConfigList is supplied
    assert protocols.ech_settings() == {"enabled": False}
    ech = protocols.ech_settings("BASE64ECH", pq_signature=True)
    assert ech["enabled"] and ech["config"] == "BASE64ECH"
    assert ech["pq_signature_schemes_enabled"] is True


def test_antidpi_ttl_noise_utls():
    assert protocols.is_valid_fingerprint("chrome")
    assert not protocols.is_valid_fingerprint("internet-explorer")
    assert protocols.ttl_settings(40)["sockopt"]["ttl"] == 40
    noise = protocols.noise_settings(packets=3)
    assert len(noise["noises"]) == 3
    for bad in (lambda: protocols.ttl_settings(0),
                lambda: protocols.noise_settings(min_len=300, max_len=10)):
        try:
            bad(); raised = False
        except ValueError:
            raised = True
        assert raised


# ---------- format converters ----------

PROXIES = [
    {"name": "DE-reality", "type": "vless", "server": "1.2.3.4", "port": 443,
     "uuid": "u1", "tls": True, "sni": "www.speedtest.net"},
    {"name": "NL ss", "type": "shadowsocks", "server": "5.6.7.8", "port": 8388,
     "password": "p@ss word"},
]


def test_to_singbox():
    cfg = protocols.to_singbox(PROXIES)
    tags = [o["tag"] for o in cfg["outbounds"]]
    assert "DE-reality" in tags and "proxy" in tags and "direct" in tags
    sel = [o for o in cfg["outbounds"] if o["type"] == "selector"][0]
    assert "DE-reality" in sel["outbounds"]


def test_to_clash_yaml_quotes_when_needed():
    yaml = protocols.to_clash(PROXIES)
    assert "proxies:" in yaml and "proxy-groups:" in yaml
    assert "type: vless" in yaml
    assert '"NL ss"' in yaml          # name with space gets quoted
    assert '"p@ss word"' in yaml      # password with space gets quoted


def test_converters_carry_transport_and_quic_tuning():
    proxies = [
        {"name": "ws", "type": "vless", "server": "1.1.1.1", "port": 443,
         "uuid": "u", "tls": True, "network": "ws", "path": "/v"},
        {"name": "hy", "type": "hysteria2", "server": "2.2.2.2", "port": 443,
         "password": "p", "up_mbps": 50, "down_mbps": 100},
    ]
    sb = protocols.to_singbox(proxies)
    ws = [o for o in sb["outbounds"] if o.get("tag") == "ws"][0]
    assert ws["transport"] == {"type": "ws", "path": "/v"}
    hy = [o for o in sb["outbounds"] if o.get("tag") == "hy"][0]
    assert hy["up_mbps"] == 50 and hy["down_mbps"] == 100
    clash = protocols.to_clash(proxies)
    assert "network: ws" in clash and 'ws-opts: {path: "/v"}' in clash


def test_detect_client():
    assert protocols.detect_client("sing-box/1.8") == "singbox"
    assert protocols.detect_client("clash-verge/1.0") == "clash"
    assert protocols.detect_client("mihomo") == "clash"
    assert protocols.detect_client("v2rayNG/1.8.5") == "v2ray"
    assert protocols.detect_client("curl/8") == "base64"


# ---------- censorship ----------

def test_sni_ranking_prefers_good_fronts():
    ranked = censorship.rank_sni_candidates(
        ["evil.ir", "www.speedtest.net", "random.com", "youtube.com"])
    assert ranked[0]["domain"] == "www.speedtest.net"
    scores = {r["domain"]: r["score"] for r in ranked}
    assert scores["evil.ir"] < scores["random.com"]
    assert scores["youtube.com"] < scores["random.com"]
    assert censorship.best_sni(["evil.ir", "www.cloudflare.com"]) == "www.cloudflare.com"
    assert censorship.best_sni(["evil.ir"]) is None


def test_tor_fallback():
    ob = censorship.tor_bridge_outbound("snowflake")
    assert ob["mode"] == "snowflake" and "broker" in ob
    ob2 = censorship.tor_bridge_outbound("obfs4", bridge_line="obfs4 1.2.3.4:1")
    assert ob2["bridges"] == ["obfs4 1.2.3.4:1"]
    try:
        censorship.tor_bridge_outbound("nope")
        raised = False
    except ValueError:
        raised = True
    assert raised
