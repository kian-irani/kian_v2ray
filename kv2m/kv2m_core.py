"""
Kv2m — هستهٔ مدیریت (SSH + ساخت کانفیگ + مدیریت کاربر)
این ماژول هیچ UI ندارد؛ GUI و CLI روی همین هسته سوارند.
خروجیِ ساخت کانفیگ دقیقاً با install.sh و صفحهٔ تعاملی هماهنگ است.
"""
import base64
import json
import re
import secrets
import uuid

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

# ---------------------------------------------------------------- ثابت‌ها
RAW_BASE = "https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main"
SS_METHOD = "chacha20-ietf-poly1305"
WARP_PORT = 40000
GIB = 1073741824
BASE_PORT = 8443
APP_VERSION = "1.0"

# دامنه‌های استتار در-دسترس-در-ایران (هم‌سان با app.js)
SNI_POOL = [
    # تست‌شده روی شبکهٔ ایران (TLS1.3، در دسترس) — هماهنگ با app.js
    "www.icloud.com", "cloudflare.com", "s3.amazonaws.com",
    "fonts.gstatic.com", "speedtest.net", "www.amazon.com",
]
CH_LABEL = {"direct": "سریع", "warp": "WARP"}


# ---------------------------------------------------------------- helpers
def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode()


def _quote(label: str) -> str:
    # شبیه encodeURIComponent: فقط A-Za-z0-9 و - _ . ! ~ * ' ( ) سالم می‌ماند
    safe = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!~*'()")
    out = []
    for b in label.encode("utf-8"):
        c = chr(b)
        out.append(c if c in safe else f"%{b:02X}")
    return "".join(out)


def gen_reality() -> dict:
    priv = X25519PrivateKey.generate()
    priv_raw = priv.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()
    )
    pub_raw = priv.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    return {"privateKey": _b64url(priv_raw), "publicKey": _b64url(pub_raw), "shortId": secrets.token_hex(8)}


def gen_password(nbytes: int = 16) -> str:
    return _b64url(secrets.token_bytes(nbytes))[:22]


def pick_snis(n: int) -> list:
    import random
    pool = SNI_POOL[:]
    random.shuffle(pool)
    return pool[: max(1, min(n, len(pool)))]


def re_expiry(days: int):
    if not days or days <= 0:
        return None
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ---------------------------------------------------------------- ساخت کانفیگ Xray
def build_config(profiles: list, reality: dict, users: list, ss: dict, api_port: int = 10085) -> dict:
    clients = [{"id": u["id"], "email": u["email"], "flow": "xtls-rprx-vision"} for u in users]
    any_warp = any(p["channel"] == "warp" for p in profiles)

    def reality_inbound(p):
        return {
            "listen": "0.0.0.0", "port": p["port"], "protocol": "vless", "tag": p["tag"],
            "settings": {"clients": [dict(c) for c in clients], "decryption": "none"},
            "streamSettings": {
                "network": "tcp", "security": "reality",
                "realitySettings": {
                    "show": False, "dest": f'{p["sni"]}:443', "xver": 0,
                    "serverNames": [p["sni"]], "privateKey": reality["privateKey"],
                    "shortIds": [reality["shortId"]],
                },
            },
            "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
        }

    inbounds = [{"listen": "127.0.0.1", "port": api_port, "protocol": "dokodemo-door",
                 "settings": {"address": "127.0.0.1"}, "tag": "api"}]
    for p in profiles:
        inbounds.append(reality_inbound(p))
    if ss.get("enabled"):
        inbounds.append({
            "listen": "0.0.0.0", "port": ss["port"], "protocol": "shadowsocks", "tag": "shadowsocks",
            "settings": {"method": SS_METHOD, "password": ss["password"], "network": "tcp,udp"},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"]},
        })

    outbounds = [{"tag": "direct", "protocol": "freedom", "settings": {"domainStrategy": "UseIP"}}]
    if any_warp:
        outbounds.append({"tag": "warp", "protocol": "socks",
                          "settings": {"servers": [{"address": "127.0.0.1", "port": WARP_PORT}]}})
    outbounds.append({"tag": "block", "protocol": "blackhole", "settings": {}})

    direct_tags = [p["tag"] for p in profiles if p["channel"] == "direct"]
    warp_tags = [p["tag"] for p in profiles if p["channel"] == "warp"]
    ss_out = "direct" if (direct_tags or not any_warp) else "warp"

    rules = [
        {"type": "field", "inboundTag": ["api"], "outboundTag": "api"},
        {"type": "field", "ip": ["geoip:private"], "outboundTag": "block"},
    ]
    if warp_tags:
        rules.append({"type": "field", "inboundTag": warp_tags, "outboundTag": "warp"})
    if direct_tags:
        rules.append({"type": "field", "inboundTag": direct_tags, "outboundTag": "direct"})
    if ss.get("enabled"):
        rules.append({"type": "field", "inboundTag": ["shadowsocks"], "outboundTag": ss_out})

    return {
        "log": {"loglevel": "warning", "access": "/var/log/xray/access.log", "error": "/var/log/xray/error.log"},
        "dns": {"servers": ["1.1.1.1", "8.8.8.8"]},
        "api": {"tag": "api", "services": ["HandlerService", "StatsService"]},
        "stats": {},
        "policy": {"levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
                   "system": {"statsInboundUplink": True, "statsInboundDownlink": True}},
        "inbounds": inbounds, "outbounds": outbounds,
        "routing": {"domainStrategy": "IPIfNonMatch", "rules": rules},
    }


def vless_link(uuid_, ip, port, sni, pubkey, short_id, label) -> str:
    q = (f"encryption=none&flow=xtls-rprx-vision&security=reality&sni={sni}"
         f"&fp=chrome&pbk={pubkey}&sid={short_id}&type=tcp")
    return f"vless://{uuid_}@{ip}:{port}?{q}#{_quote(label)}"


def ss_link(ip, port, password, label) -> str:
    creds = base64.b64encode(f"{SS_METHOD}:{password}".encode()).decode()
    return f"ss://{creds}@{ip}:{port}#{_quote(label)}"


# ---------------------------------------------------------------- تولید کامل (مثل صفحهٔ تعاملی)
def generate(opts: dict) -> dict:
    """
    opts: server_ip, mode(both|direct|warp|nosni), sni_mode(auto|manual), manual_sni,
          sni_count, base_port, num_users, prefix, quota_gb, days,
          ss_enabled, ss_port
    """
    reality = gen_reality()
    ss = {"enabled": bool(opts.get("ss_enabled")), "port": int(opts.get("ss_port") or 8388), "password": ""}
    mode = opts.get("mode", "both")
    if mode == "nosni":
        ss["enabled"] = True
    if ss["enabled"]:
        ss["password"] = gen_password()

    channels = ["direct", "warp"] if mode == "both" else ([] if mode == "nosni" else [mode])
    if not channels:
        sni_list = []
    elif opts.get("sni_mode") == "manual" and opts.get("manual_sni"):
        sni_list = [opts["manual_sni"]]
    else:
        sni_list = pick_snis(int(opts.get("sni_count") or 2))

    profiles = []
    port = int(opts.get("base_port") or BASE_PORT)
    def next_port():
        nonlocal port
        while ss["enabled"] and port == ss["port"]:
            port += 1
        p = port
        port += 1
        return p
    for ch in channels:
        for i, sni in enumerate(sni_list):
            profiles.append({"tag": f"reality-{ch}-{i+1}", "port": next_port(), "sni": sni, "channel": ch})

    prefix = re.sub(r"[^a-zA-Z0-9_-]", "", opts.get("prefix") or "user") or "user"
    quota_gb = int(opts.get("quota_gb") or 0)
    days = int(opts.get("days") or 0)
    num_users = max(1, min(50, int(opts.get("num_users") or 1)))
    users = []
    for i in range(1, num_users + 1):
        users.append({
            "id": str(uuid.uuid4()), "email": f"{prefix}-{i}@kian",
            "quota_bytes": quota_gb * GIB if quota_gb > 0 else 0,
            "used_bytes": 0, "expires_at": re_expiry(days), "active": True, "note": "",
        })

    import random as _rnd
    _used = [p["port"] for p in profiles] + ([ss["port"]] if ss["enabled"] else [])
    api_port = _rnd.randint(20000, 49999)
    while api_port in _used:
        api_port = _rnd.randint(20000, 49999)
    config = build_config(profiles, reality, users, ss, api_port)

    links = []
    per_user = []
    sub_tokens = {}
    sub_port = 80
    ip = opts["server_ip"]
    for u in users:
        local = u["email"].split("@")[0]
        items = []
        for p in profiles:
            link = vless_link(u["id"], ip, p["port"], p["sni"], reality["publicKey"],
                              reality["shortId"], f'KIAN-{local}-{CH_LABEL[p["channel"]]}-{p["sni"]}')
            links.append(link)
            items.append({"channel": p["channel"], "sni": p["sni"], "port": p["port"], "link": link})
        token = secrets.token_hex(16)
        sub_tokens[u["email"]] = token
        sub_url = f"http://{ip}:{sub_port}/sub/{token}"
        per_user.append({"email": u["email"], "local": local, "items": items, "subUrl": sub_url})

    ss_out_link = None
    if ss["enabled"]:
        ss_out_link = ss_link(ip, ss["port"], ss["password"], "KIAN-Shadowsocks")
        links.append(ss_out_link)

    ports = [p["port"] for p in profiles] + ([ss["port"]] if ss["enabled"] else [])

    payload = {
        "warp_needed": "warp" in channels,
        "server_ip": ip,
        "config_b64": _b64(json.dumps(config)),
        "users_b64": _b64(json.dumps({"users": users})),
        "links": links,
        "ports": ports,
        "api_port": api_port,
        "sub_port": sub_port,
        "sub_tokens": sub_tokens,
        "reality_pbk": reality["publicKey"],   # کلید عمومی (راز نیست؛ در هر لینک هست) — سرور لینک‌ها را از config می‌سازد
        "reality_sid": reality["shortId"],
        "ss_password": ss["password"] if ss["enabled"] else "",
    }
    payload_b64 = _b64(json.dumps(payload))
    install_cmd = (f"export KIAN_PAYLOAD='{payload_b64}'\n"
                   f"curl -fsSL {RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh")

    return {
        "reality": reality, "users": users, "per_user": per_user, "ss_link": ss_out_link,
        "ports": ports, "profiles": profiles, "sni_list": sni_list, "config": config,
        "payload_b64": payload_b64, "install_cmd": install_cmd, "warp_needed": "warp" in channels,
        "sub_port": sub_port, "sub_tokens": sub_tokens,
    }


# ---------------------------------------------------------------- دستورهای مدیریت
def cmd_status() -> str:
    return "kian-v2ray status"


def cmd_users() -> str:
    return "kian-v2ray users"


def cmd_configs(name: str = "") -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name or "")
    return f"kian-v2ray configs {name}".strip()


def cmd_add(name: str, gb: int = 100, days: int = 30) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name or "")
    return f"kian-v2ray add {name} {int(gb)} {int(days)} && kian-v2ray configs {name}"


def cmd_remove(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name or "")
    return f"kian-v2ray remove {name}"


def cmd_renew(name: str, days: int = 30) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name or "")
    return f"kian-v2ray renew {name} {int(days)}"


def cmd_reset(name: str, gb=None) -> str:
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name or "")
    return f"kian-v2ray reset {name} {int(gb)}".strip() if gb not in (None, "") else f"kian-v2ray reset {name}"


def cmd_installed_check() -> str:
    return "command -v kian-v2ray >/dev/null 2>&1 && echo KV2M_OK || echo KV2M_MISSING"


# ---------------------------------------------------------------- پارس خروجی
def parse_users(text: str) -> list:
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s or "ایمیل" in s or set(s) <= set("─-"):
            continue
        if "@" not in s.split()[0] if s.split() else True:
            continue
        parts = re.split(r"\s+", s)
        if len(parts) >= 5:
            rows.append({"email": parts[0], "active": parts[1], "used": parts[2],
                         "quota": parts[3], "expiry": " ".join(parts[4:])})
    return rows


def parse_links(text: str) -> list:
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith(("vless://", "ss://"))]


# ---------------------------------------------------------------- SSH (paramiko)
class SSH:
    def __init__(self):
        self.client = None
        self.host = None

    def connect(self, host, port=22, username="root", password=None, key_path=None, timeout=15):
        import paramiko
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kw = dict(hostname=host, port=int(port), username=username, timeout=timeout,
                  allow_agent=False, look_for_keys=False)
        if key_path:
            kw["key_filename"] = key_path
        if password:
            kw["password"] = password
        c.connect(**kw)
        self.client = c
        self.host = host
        return self

    def run(self, command, timeout=180):
        if not self.client:
            raise RuntimeError("اتصال SSH برقرار نیست")
        stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout, get_pty=False)
        out = stdout.read().decode("utf-8", "replace")
        err = stderr.read().decode("utf-8", "replace")
        rc = stdout.channel.recv_exit_status()
        return rc, out, err

    def run_stream(self, command, on_line, timeout=600):
        """اجرای دستور با پخش زندهٔ خروجی خط‌به‌خط (برای نصب)."""
        if not self.client:
            raise RuntimeError("اتصال SSH برقرار نیست")
        chan = self.client.get_transport().open_session()
        chan.settimeout(timeout)
        chan.exec_command(command)
        buf = b""
        while True:
            if chan.recv_ready():
                buf += chan.recv(4096)
                *lines, buf = buf.split(b"\n")
                for ln in lines:
                    on_line(ln.decode("utf-8", "replace"))
            if chan.exit_status_ready() and not chan.recv_ready():
                break
        if buf:
            on_line(buf.decode("utf-8", "replace"))
        return chan.recv_exit_status()

    def close(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
