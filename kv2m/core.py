#!/usr/bin/env python3
"""kv2m core — pure logic + SSH. No GUI imports. Headless-testable."""
import base64, json, re, secrets, uuid
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

APP_VERSION = "4.4.2"  # 4.4.2: perf — disable Xray access log, raise container mem cap
RAW_BASE    = "https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main"
GIST_PROXY  = "https://kian-sub.kian-mhrv.workers.dev"  # Cloudflare Worker → secret Gist HTTPS sub
WARP_PORT   = 40000
SUB_PORTS   = [80, 8888, 2086]
SS_METHOD   = "chacha20-ietf-poly1305"
# Only these geo-blocked services route through WARP (they reject Iranian /
# datacenter IPs). Everything else goes DIRECT at full server speed. Plain
# `domain:` rules — no geosite.dat dependency.
WARP_DOMAINS = [
    "domain:openai.com", "domain:chatgpt.com", "domain:oaistatic.com",
    "domain:oaiusercontent.com", "domain:anthropic.com", "domain:claude.ai",
    "domain:gemini.google.com", "domain:aistudio.google.com",
    "domain:makersuite.google.com", "domain:ai.google.dev",
    "domain:generativelanguage.googleapis.com", "domain:x.ai", "domain:grok.com",
    "domain:perplexity.ai",
]
GIB         = 1_073_741_824
BASE_PORT   = 8443
WELL_KNOWN  = [443,2083,2087,2096,8080,2052,2086]

SNI_POOL = [
    "www.icloud.com","cloudflare.com","s3.amazonaws.com",
    "fonts.gstatic.com","speedtest.net","www.amazon.com",
]
SNI_MANUAL_OPTIONS = [
    "speedtest.net","bing.com","microsoft.com","apple.com",
    "icloud.com","samsung.com","nvidia.com","cloudflare.com",
]

TLS_PROTOS = {
    "vless-ws":          {"proto":"vless", "net":"ws",          "label":"VLESS-WS",          "note":"پایدارترین برای عبور از DPI و CDN"},
    "vmess-ws":          {"proto":"vmess", "net":"ws",          "label":"VMess-WS",          "note":"سازگاری بالا با کلاینت‌های قدیمی"},
    "vless-grpc":        {"proto":"vless", "net":"grpc",        "label":"VLESS-gRPC",        "note":"مالتی‌پلکس، خوب روی شبکه‌های پرتاخیر"},
    "vmess-grpc":        {"proto":"vmess", "net":"grpc",        "label":"VMess-gRPC",        "note":"gRPC با VMess"},
    "trojan-ws":         {"proto":"trojan","net":"ws",          "label":"Trojan-WS",         "note":"شبیه ترافیک HTTPS معمولی"},
    "vless-httpupgrade": {"proto":"vless", "net":"httpupgrade", "label":"VLESS-HTTPUpgrade", "note":"سبک‌تر از WS، عبور خوب از پراکسی"},
    "vmess-httpupgrade": {"proto":"vmess", "net":"httpupgrade", "label":"VMess-HTTPUpgrade", "note":"HTTPUpgrade با VMess"},
    "vless-xhttp":       {"proto":"vless", "net":"xhttp",       "label":"VLESS-XHTTP",       "note":"جدید — مقاوم‌ترین در برابر DPI، عالی روی CDN"},
}

def _b64url(raw): return base64.urlsafe_b64encode(raw).decode().rstrip("=")
def _b64(s):      return base64.b64encode(s.encode()).decode()
def _quote(s):
    safe=set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.!~*'()")
    return "".join(c if c in safe else f"%{ord(c):02X}" for c in s)

def gen_reality():
    priv=X25519PrivateKey.generate()
    priv_raw=priv.private_bytes(serialization.Encoding.Raw,serialization.PrivateFormat.Raw,serialization.NoEncryption())
    pub_raw =priv.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    return {"privateKey":_b64url(priv_raw),"publicKey":_b64url(pub_raw),"shortId":secrets.token_hex(8)}

def gen_password(n=16): return _b64url(secrets.token_bytes(n))[:22]

def pick_snis(n):
    import random; pool=SNI_POOL[:]; random.shuffle(pool); return pool[:max(1,min(n,len(pool)))]

def re_expiry(days):
    if not days or days<=0: return None
    from datetime import datetime,timedelta,timezone
    return (datetime.now(timezone.utc)+timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def vless_link(uuid_,ip,port,sni,pubkey,short_id,label):
    # spx=/ : spiderX (Reality advanced 10.6) — browser-like fallback probe path.
    q=f"encryption=none&flow=xtls-rprx-vision&security=reality&sni={sni}&fp=chrome&pbk={pubkey}&sid={short_id}&spx=%2F&type=tcp"
    return f"vless://{uuid_}@{ip}:{port}?{q}#{_quote(label)}"

def ss_link(ip,port,password,label):
    creds=base64.b64encode(f"{SS_METHOD}:{password}".encode()).decode()
    return f"ss://{creds}@{ip}:{port}#{_quote(label)}"

def is_domain(d):
    return bool(d) and bool(re.match(r"^(?=.{4,253}$)([a-z0-9](-?[a-z0-9])*\.)+[a-z]{2,}$", d))

def _tls_query(d):  # like URLSearchParams.toString()
    return "&".join(f"{k}={_quote(str(v))}" for k,v in d.items())

def tls_vless_link(uuid_,domain,net,path,label):
    q={"encryption":"none","security":"tls","sni":domain,"fp":"chrome","type":net,"host":domain}
    if net in ("ws","httpupgrade"): q["path"]=path
    if net=="xhttp": q["path"]=path; q["mode"]="auto"
    if net=="grpc": q["serviceName"]=path.lstrip("/"); q["mode"]="gun"
    return f"vless://{uuid_}@{domain}:443?{_tls_query(q)}#{_quote(label)}"

def tls_trojan_link(uuid_,domain,net,path,label):
    q={"security":"tls","sni":domain,"fp":"chrome","type":net,"host":domain}
    if net in ("ws","httpupgrade"): q["path"]=path
    if net=="grpc": q["serviceName"]=path.lstrip("/"); q["mode"]="gun"
    return f"trojan://{uuid_}@{domain}:443?{_tls_query(q)}#{_quote(label)}"

def tls_vmess_link(uuid_,domain,net,path,label):
    v={"v":"2","ps":label,"add":domain,"port":"443","id":uuid_,"aid":"0","scy":"auto",
       "net":net,"type":"none","host":domain,
       "path":(path.lstrip("/") if net=="grpc" else path),
       "tls":"tls","sni":domain,"alpn":"","fp":"chrome"}
    return "vmess://"+base64.b64encode(json.dumps(v,ensure_ascii=False).encode()).decode()

def tls_link(item,user,domain):
    kind=item["kind"]; net=TLS_PROTOS[kind]["net"]; proto=TLS_PROTOS[kind]["proto"]
    if proto=="vmess":  return tls_vmess_link(user["id"],domain,net,item["path"],item["label"])
    if proto=="trojan": return tls_trojan_link(user["id"],domain,net,item["path"],item["label"])
    return tls_vless_link(user["id"],domain,net,item["path"],item["label"])

def build_caddyfile(domain,tls_profiles):
    lines=[f"{domain} {{"]
    for t in tls_profiles:
        if t["net"]=="grpc":
            svc=t["path"].lstrip("/")
            lines+=[f"\t@{t['tag']} {{",f"\t\tpath /{svc}/*","\t}",
                    f"\thandle @{t['tag']} {{",f"\t\treverse_proxy h2c://127.0.0.1:{t['intPort']}","\t}"]
        elif t["net"]=="xhttp":
            lines+=[f"\t@{t['tag']} {{",f"\t\tpath {t['path']} {t['path']}/*","\t}",
                    f"\thandle @{t['tag']} {{",f"\t\treverse_proxy h2c://127.0.0.1:{t['intPort']}","\t}"]
        else:
            lines+=[f"\t@{t['tag']} {{",f"\t\tpath {t['path']}","\t}",
                    f"\thandle @{t['tag']} {{",f"\t\treverse_proxy 127.0.0.1:{t['intPort']}","\t}"]
    lines+=["\thandle {","\t\trespond \"It works!\" 200","\t}","}"]
    return "\n".join(lines)

def build_config(profiles,reality,users,ss,api_port=10085,tls=None,tls_profiles=None):
    clients=[{"id":u["id"],"email":u["email"],"flow":"xtls-rprx-vision"} for u in users]
    tls_items=tls_profiles or []
    def _tls_ch(t): return t.get("channel") or (tls.get("channel") if tls else "direct")
    tls_wants_warp=any(_tls_ch(t)=="warp" for t in tls_items)
    any_warp=any(p["channel"]=="warp" for p in profiles) or tls_wants_warp
    def ri(p):
        return {"listen":"0.0.0.0","port":p["port"],"protocol":"vless","tag":p["tag"],
                "settings":{"clients":[dict(c) for c in clients],"decryption":"none"},
                "streamSettings":{"network":"tcp","security":"reality","realitySettings":{
                    "show":False,"dest":f'{p["sni"]}:443',"xver":0,
                    "serverNames":[p["sni"]],"privateKey":reality["privateKey"],
                    "shortIds":[reality["shortId"]]}},
                "sniffing":{"enabled":True,"destOverride":["http","tls","quic"],"routeOnly":True}}
    inbounds=[{"listen":"127.0.0.1","port":api_port,"protocol":"dokodemo-door",
               "settings":{"address":"127.0.0.1"},"tag":"api"}]
    for p in profiles: inbounds.append(ri(p))
    if ss.get("enabled"):
        inbounds.append({"listen":"0.0.0.0","port":ss["port"],"protocol":"shadowsocks","tag":"shadowsocks",
                         "settings":{"method":SS_METHOD,"password":ss["password"],"network":"tcp,udp"},
                         "sniffing":{"enabled":True,"destOverride":["http","tls","quic"],"routeOnly":True}})
    for t in tls_items:
        net=t["net"]
        if net=="ws":            stream={"network":"ws","security":"none","wsSettings":{"path":t["path"]}}
        elif net=="grpc":        stream={"network":"grpc","security":"none","grpcSettings":{"serviceName":t["path"].lstrip("/")}}
        elif net=="httpupgrade": stream={"network":"httpupgrade","security":"none","httpupgradeSettings":{"path":t["path"]}}
        elif net=="xhttp":       stream={"network":"xhttp","security":"none","xhttpSettings":{"mode":"auto","path":t["path"]}}
        else:                    stream={"network":net,"security":"none"}
        if t["proto"]=="vless":    st={"clients":[{"id":u["id"],"email":u["email"]} for u in users],"decryption":"none"}
        elif t["proto"]=="vmess":  st={"clients":[{"id":u["id"],"email":u["email"]} for u in users]}
        else:                      st={"clients":[{"password":u["id"],"email":u["email"]} for u in users]}
        inbounds.append({"listen":"127.0.0.1","port":t["intPort"],"protocol":t["proto"],"tag":t["tag"],
                         "settings":st,"streamSettings":stream,
                         "sniffing":{"enabled":True,"destOverride":["http","tls","quic"],"routeOnly":True}})
    outbounds=[{"tag":"direct","protocol":"freedom","settings":{"domainStrategy":"AsIs"}}]
    if any_warp: outbounds.append({"tag":"warp","protocol":"socks","settings":{"servers":[{"address":"127.0.0.1","port":WARP_PORT}]}})
    outbounds.append({"tag":"block","protocol":"blackhole","settings":{}})
    # Speed: all proxy traffic goes DIRECT (full server line, like plain Xray /
    # 3x-ui). Only the curated geo-blocked services route through WARP.
    all_tags=[p["tag"] for p in profiles]
    tls_tags=[t["tag"] for t in tls_items]
    rules=[{"type":"field","inboundTag":["api"],"outboundTag":"api"},
           {"type":"field","ip":["geoip:private"],"outboundTag":"block"}]
    if any_warp: rules.append({"type":"field","domain":WARP_DOMAINS,"outboundTag":"warp"})
    if all_tags: rules.append({"type":"field","inboundTag":all_tags,"outboundTag":"direct"})
    if ss.get("enabled"): rules.append({"type":"field","inboundTag":["shadowsocks"],"outboundTag":"direct"})
    if tls_tags: rules.append({"type":"field","inboundTag":tls_tags,"outboundTag":"direct"})
    return {"log":{"loglevel":"warning","access":"none","error":"/var/log/xray/error.log"},
            "dns":{"servers":["1.1.1.1","8.8.8.8"]},"api":{"tag":"api","services":["HandlerService","StatsService"]},
            "stats":{},"policy":{"levels":{"0":{"statsUserUplink":True,"statsUserDownlink":True}},
            "system":{"statsInboundUplink":True,"statsInboundDownlink":True}},
            "inbounds":inbounds,"outbounds":outbounds,
            "routing":{"domainStrategy":"AsIs","rules":rules}}

def generate(opts):
    reality=gen_reality()
    ss={"enabled":bool(opts.get("ss_enabled")),"port":int(opts.get("ss_port") or 8388),"password":""}
    # حالتِ اتصال حذف شد — همیشه از WARP عبور می‌کند (غیرقابل‌انتخاب).
    mode="warp"
    if ss["enabled"]:  ss["password"]=gen_password()
    channels=["warp"]
    if opts.get("sni_mode")=="manual" and opts.get("sni_manual"):
        sni_list=[opts["sni_manual"]]
    elif mode!="nosni":
        sni_list=pick_snis(int(opts.get("sni_count") or 2))
    else:
        sni_list=[]
    # تخصیص پورت مثل صفحهٔ تعاملی: اول پورت‌های «تقریباً همیشه باز» (443/2083/...) بعد 8443+.
    # اگر TLS فعال است 443 و 80 برای Caddy رزرو می‌شوند.
    _tlsd=(opts.get("tls_domain") or "").strip().lower()
    _tls_on=bool(opts.get("tls_enabled") and is_domain(_tlsd) and [k for k in (opts.get("tls_protos") or []) if k in TLS_PROTOS])
    _reserved=[443,80] if _tls_on else []
    _ub=int(opts.get("base_port") or 0)
    if 1<=_ub<=65500:
        port_pool=list(range(_ub,_ub+50))
    else:
        port_pool=[p for p in WELL_KNOWN if p not in _reserved]+list(range(8443,8493))
    _banned=set([WARP_PORT]+_reserved)
    if ss["enabled"]: _banned.add(ss["port"])
    profiles=[]; _pi=[0]
    def next_port():
        while _pi[0]<len(port_pool) and port_pool[_pi[0]] in _banned: _pi[0]+=1
        if _pi[0]>=len(port_pool): raise RuntimeError("پورت کافی پیدا نشد — base_port را عوض کن")
        v=port_pool[_pi[0]]; _pi[0]+=1; return v
    for ch in channels:
        for i,sni in enumerate(sni_list):
            profiles.append({"tag":f"reality-{ch}-{i+1}","port":next_port(),"sni":sni,"channel":ch})
    prefix=re.sub(r"[^a-zA-Z0-9_-]","",opts.get("prefix") or "user") or "user"
    quota_gb=int(opts.get("quota_gb") or 0)
    days=int(opts.get("days") or 0)
    num_users=max(1,min(50,int(opts.get("num_users") or 1)))
    users=[{"id":str(uuid.uuid4()),"email":f"{prefix}-{i}@kian",
            "quota_bytes":quota_gb*GIB if quota_gb>0 else 0,
            "used_bytes":0,"expires_at":re_expiry(days),"active":True,"note":""}
           for i in range(1,num_users+1)]
    # TLS/دامنه (فاز ۳): پروفایل‌های پشت Caddy روی :443 — هر پروتکل پورت داخلی و path یکتا
    tls_domain=(opts.get("tls_domain") or "").strip().lower()
    tls_channel="warp"   # همیشه از WARP — حالتِ مستقیم حذف شد
    tls_channels=["warp"]
    tls_protos=[k for k in (opts.get("tls_protos") or []) if k in TLS_PROTOS]
    tls_enabled=bool(opts.get("tls_enabled") and is_domain(tls_domain) and tls_protos)
    tls_profiles=[]
    if tls_enabled:
        reality_max=max([p["port"] for p in profiles], default=int(opts.get("base_port") or BASE_PORT))
        ss_max=ss["port"] if ss["enabled"] else 0
        ip2=max(20810, reality_max+100, ss_max+100)
        import random as _r2
        rnd="".join(_r2.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(6))
        _idx=0
        for ch in tls_channels:
            for kind in tls_protos:
                net=TLS_PROTOS[kind]["net"]
                path=f"/{rnd}{_idx}{ch[0]}{'grpc' if net=='grpc' else ''}"
                tag=f"tls-{kind}-{ch}" if len(tls_channels)>1 else f"tls-{kind}"
                tls_profiles.append({"kind":kind,"tag":tag,"intPort":ip2,
                                     "net":net,"proto":TLS_PROTOS[kind]["proto"],"path":path,"channel":ch})
                ip2+=1; _idx+=1
    import random as _rnd
    used=[p["port"] for p in profiles]+([ss["port"]] if ss["enabled"] else [])+[t["intPort"] for t in tls_profiles]
    api_port=_rnd.randint(20000,49999)
    while api_port in used: api_port=_rnd.randint(20000,49999)
    config=build_config(profiles,reality,users,ss,api_port,
                        tls={"enabled":tls_enabled,"domain":tls_domain,"channel":tls_channel},
                        tls_profiles=tls_profiles)
    sub_tokens,per_user={},[]
    ip=opts["server_ip"]
    for u in users:
        local=u["email"].split("@")[0]
        # label scheme: <name>-<proto>-<port>  (e.g. ali-reality-2083)
        items=[{"channel":p["channel"],"sni":p["sni"],"port":p["port"],
                "link":vless_link(u["id"],ip,p["port"],p["sni"],reality["publicKey"],
                                  reality["shortId"],f'{local}-reality-{p["port"]}')}
               for p in profiles]
        tls_items_links=[]
        for t in tls_profiles:
            _disp=TLS_PROTOS[t["kind"]]["label"]
            lbl=f'{local}-{_disp.lower()}-443'
            tls_items_links.append({"kind":t["kind"],"label":_disp,
                                    "note":TLS_PROTOS[t["kind"]]["note"],
                                    "link":tls_link({"kind":t["kind"],"path":t["path"],"label":lbl},u,tls_domain)})
        token=secrets.token_hex(16); sub_tokens[u["email"]]=token
        sub_urls=[f"http://{ip}:{sp}/sub/{token}" for sp in SUB_PORTS]
        user_links=[it["link"] for it in items]+[t["link"] for t in tls_items_links]
        if ss["enabled"]:
            user_links.append(ss_link(ip,ss["port"],ss["password"],f'{local}-shadowsocks-{ss["port"]}'))
        per_user.append({"email":u["email"],"local":local,"items":items,
                         "tlsLinks":tls_items_links,"userLinks":user_links,
                         "subUrls":sub_urls,"subToken":token})
    ss_out_link=ss_link(ip,ss["port"],ss["password"],"shadowsocks") if ss["enabled"] else None
    links=[it["link"] for u in per_user for it in u["items"]]
    links+=[t["link"] for u in per_user for t in u.get("tlsLinks",[])]
    if ss_out_link: links.append(ss_out_link)
    install_id=secrets.token_hex(16)
    sub_items={pu["subToken"]:_b64("\n".join(pu["userLinks"])) for pu in per_user}
    ports=[p["port"] for p in profiles]+([ss["port"]] if ss["enabled"] else [])
    tls_wants_warp=tls_enabled and ("warp" in tls_channels)
    warp_needed=("warp" in channels) or tls_wants_warp
    # پروتکل‌های اضافه (Hysteria2/TUIC روی sing-box) — install.sh آن‌ها را enable
    # می‌کند و لینک‌هایشان را به Subscription می‌افزاید. مقدارِ معتبر: ["hysteria2","tuic"].
    extra_protocols=[p for p in (opts.get("extra_protocols") or []) if p in ("hysteria2","tuic")]
    lang="en" if (opts.get("lang") or "en")=="en" else "fa"   # install console language
    payload={"warp_needed":warp_needed,"server_ip":ip,"lang":lang,
             "config_b64":_b64(json.dumps(config)),"users_b64":_b64(json.dumps({"users":users})),
             "links":links,"ports":ports,"api_port":api_port,"sub_port":SUB_PORTS,
             "sub_tokens":sub_tokens,"reality_pbk":reality["publicKey"],"reality_sid":reality["shortId"],
             "gist_proxy":GIST_PROXY,"install_id":install_id,
             "ss_password":ss["password"] if ss["enabled"] else "",
             "tls_domain":tls_domain if tls_profiles else "",
             "caddyfile_b64":_b64(build_caddyfile(tls_domain,tls_profiles)) if tls_profiles else "",
             "extra_protocols":extra_protocols,
             "panel_admin_user":opts.get("panel_user","admin") or "admin",
             "panel_admin_pass":opts.get("panel_pass","") or ""}
    payload_b64=_b64(json.dumps(payload))
    return {"reality":reality,"users":users,"per_user":per_user,"ss_link":ss_out_link,
            "ports":ports,"profiles":profiles,"sni_list":sni_list,"config":config,
            "payload_b64":payload_b64,"warp_needed":warp_needed,"tls_profiles":tls_profiles,
            "install_id":install_id,"sub_items":sub_items,"gist_proxy":GIST_PROXY,
            "sub_tokens":sub_tokens,"install_cmd":f"export KIAN_PAYLOAD='{payload_b64}'\nexport KIAN_LANG='{lang}'\ncurl -fsSL {RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh"}

# ── CLI commands ─────────────────────────────────────────────
def cmd_status():          return "kian-v2ray status"
def cmd_users():           return "kian-v2ray users"
def cmd_configs(name=""):  return f"kian-v2ray configs {re.sub(r'[^a-zA-Z0-9_-]','',name or '')}".strip()
def cmd_add(n,gb=100,d=30):n=re.sub(r'[^a-zA-Z0-9_-]','',n or ''); return f"kian-v2ray add {n} {int(gb)} {int(d)} && kian-v2ray configs {n}"
def cmd_remove(n):         n=re.sub(r'[^a-zA-Z0-9_-]','',n or ''); return f"kian-v2ray remove {n}"
def cmd_renew(n,d=30):     n=re.sub(r'[^a-zA-Z0-9_-]','',n or ''); return f"kian-v2ray renew {n} {int(d)}"
def cmd_reset(n,gb=None):  n=re.sub(r'[^a-zA-Z0-9_-]','',n or ''); return (f"kian-v2ray reset {n} {int(gb)}" if gb not in (None,"") else f"kian-v2ray reset {n}")
def cmd_sub(n=""):         n=re.sub(r'[^a-zA-Z0-9_-]','',n or ''); return f"kian-v2ray sub {n}".strip()
def cmd_installed():       return "command -v kian-v2ray >/dev/null 2>&1 && echo KV2M_OK || echo KV2M_MISSING"
def cmd_update():          return "kian-v2ray update"
def cmd_resync():          return "kian-v2ray resync"
def cmd_uninstall():       return "echo DELETE | kian-v2ray uninstall"
def cmd_panel(user="admin",password=""):
    """Deploy the web panel with the given admin user/pass (empty pass = random
    on the server). Returns the URL + credentials in its output."""
    import shlex
    user=re.sub(r'[^a-zA-Z0-9_-]','',user or 'admin') or 'admin'
    env=f"KIAN_ADMIN_USER={user} "
    if password: env+=f"KIAN_ADMIN_PASSWORD={shlex.quote(password)} "  # shell-safe, NOT url-encoded
    return f"{env}kian-v2ray panel enable"

def parse_users(text):
    rows=[]
    for line in text.splitlines():
        s=line.strip()
        if not s or "ایمیل" in s or set(s)<=set("─-"): continue
        if "@" not in (s.split() or [""])[0]: continue
        parts=re.split(r"\s+",s)
        if len(parts)>=5:
            rows.append({"email":parts[0],"active":parts[1],"used":parts[2],"quota":parts[3],"expiry":" ".join(parts[4:])})
    return rows

def parse_links(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith(("vless://","ss://"))]

class SSH:
    def __init__(self): self.client=None; self.host=None
    def connect(self,host,port=22,username="root",password=None,key_path=None,timeout=15):
        import paramiko
        c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kw=dict(hostname=host,port=int(port),username=username,timeout=timeout,allow_agent=False,look_for_keys=False)
        if key_path: kw["key_filename"]=key_path
        if password:  kw["password"]=password
        c.connect(**kw); self.client=c; self.host=host; return self
    def run(self,command,timeout=180):
        if not self.client: raise RuntimeError("SSH قطع است")
        _,out,err=self.client.exec_command(command,timeout=timeout,get_pty=False)
        o=out.read().decode("utf-8","replace"); e=err.read().decode("utf-8","replace")
        return out.channel.recv_exit_status(),o,e
    def run_stream(self,command,on_line,timeout=600):
        if not self.client: raise RuntimeError("SSH قطع است")
        chan=self.client.get_transport().open_session()
        chan.settimeout(timeout); chan.exec_command(command); buf=b""
        while True:
            if chan.recv_ready():
                buf+=chan.recv(4096); *lines,buf=buf.split(b"\n")
                for ln in lines: on_line(ln.decode("utf-8","replace"))
            if chan.exit_status_ready() and not chan.recv_ready(): break
        if buf: on_line(buf.decode("utf-8","replace"))
        return chan.recv_exit_status()
    def close(self):
        if self.client:
            try: self.client.close()
            except: pass
            self.client=None

# ══════════════════════════════════════════════════════════════
# GUI — customtkinter


def sync_gists(install_id, items, timeout=12):
    """POST sub contents to the Cloudflare Worker → returns {subtoken: https_gist_url}.
    Mirrors the web page so the desktop app also yields HTTPS Gist subscription links."""
    import urllib.request
    if not items: return {}
    body = json.dumps({"install_id": install_id, "items": items}).encode("utf-8")
    req = urllib.request.Request(GIST_PROXY + "/sync", data=body,
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0 (kv2m)",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8"))
    return d.get("urls", {}) if d.get("ok") else {}
