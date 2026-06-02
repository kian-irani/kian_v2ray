#!/usr/bin/env python3
"""
Kv2m v2.0 — مدیریت سرور Kian V2Ray
یک فایل، همه‌چیز داخل. نیازها: pip install customtkinter paramiko cryptography qrcode[pil]
اجرا: python kv2m.py | python kv2m.py --cli
"""
import base64, io, json, os, queue, re, secrets, sys, threading, uuid
import tkinter as tk
from tkinter import messagebox

# ── UTF-8 on Windows ─────────────────────────────────────────
for _s in ("stdout","stderr"):
    _st = getattr(sys,_s,None)
    if not _st: continue
    try: _st.reconfigure(encoding="utf-8",errors="replace")
    except: 
        try: setattr(sys,_s,io.TextIOWrapper(_st.buffer,encoding="utf-8",errors="replace"))
        except: pass

# ══════════════════════════════════════════════════════════════
# CORE — کلید، کانفیگ، لینک، SSH
# ══════════════════════════════════════════════════════════════
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

APP_VERSION = "2.0"
RAW_BASE    = "https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main"
WARP_PORT   = 40000
SUB_PORTS   = [80, 8888, 2086]
SS_METHOD   = "chacha20-ietf-poly1305"
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
CH_LABEL = {"direct":"سریع","warp":"WARP"}

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
    q=f"encryption=none&flow=xtls-rprx-vision&security=reality&sni={sni}&fp=chrome&pbk={pubkey}&sid={short_id}&type=tcp"
    return f"vless://{uuid_}@{ip}:{port}?{q}#{_quote(label)}"

def ss_link(ip,port,password,label):
    creds=base64.b64encode(f"{SS_METHOD}:{password}".encode()).decode()
    return f"ss://{creds}@{ip}:{port}#{_quote(label)}"

def build_config(profiles,reality,users,ss,api_port=10085):
    clients=[{"id":u["id"],"email":u["email"],"flow":"xtls-rprx-vision"} for u in users]
    any_warp=any(p["channel"]=="warp" for p in profiles)
    def ri(p):
        return {"listen":"0.0.0.0","port":p["port"],"protocol":"vless","tag":p["tag"],
                "settings":{"clients":[dict(c) for c in clients],"decryption":"none"},
                "streamSettings":{"network":"tcp","security":"reality","realitySettings":{
                    "show":False,"dest":f'{p["sni"]}:443',"xver":0,
                    "serverNames":[p["sni"]],"privateKey":reality["privateKey"],
                    "shortIds":[reality["shortId"]]}},
                "sniffing":{"enabled":True,"destOverride":["http","tls","quic"]}}
    inbounds=[{"listen":"127.0.0.1","port":api_port,"protocol":"dokodemo-door",
               "settings":{"address":"127.0.0.1"},"tag":"api"}]
    for p in profiles: inbounds.append(ri(p))
    if ss.get("enabled"):
        inbounds.append({"listen":"0.0.0.0","port":ss["port"],"protocol":"shadowsocks","tag":"shadowsocks",
                         "settings":{"method":SS_METHOD,"password":ss["password"],"network":"tcp,udp"},
                         "sniffing":{"enabled":True,"destOverride":["http","tls","quic"]}})
    outbounds=[{"tag":"direct","protocol":"freedom","settings":{"domainStrategy":"UseIP"}}]
    if any_warp: outbounds.append({"tag":"warp","protocol":"socks","settings":{"servers":[{"address":"127.0.0.1","port":WARP_PORT}]}})
    outbounds.append({"tag":"block","protocol":"blackhole","settings":{}})
    direct_tags=[p["tag"] for p in profiles if p["channel"]=="direct"]
    warp_tags  =[p["tag"] for p in profiles if p["channel"]=="warp"]
    ss_out="direct" if (direct_tags or not any_warp) else "warp"
    rules=[{"type":"field","inboundTag":["api"],"outboundTag":"api"},
           {"type":"field","ip":["geoip:private"],"outboundTag":"block"}]
    if warp_tags:   rules.append({"type":"field","inboundTag":warp_tags,  "outboundTag":"warp"})
    if direct_tags: rules.append({"type":"field","inboundTag":direct_tags,"outboundTag":"direct"})
    if ss.get("enabled"): rules.append({"type":"field","inboundTag":["shadowsocks"],"outboundTag":ss_out})
    return {"log":{"loglevel":"warning","access":"/var/log/xray/access.log","error":"/var/log/xray/error.log"},
            "dns":{"servers":["1.1.1.1","8.8.8.8"]},"api":{"tag":"api","services":["HandlerService","StatsService"]},
            "stats":{},"policy":{"levels":{"0":{"statsUserUplink":True,"statsUserDownlink":True}},
            "system":{"statsInboundUplink":True,"statsInboundDownlink":True}},
            "inbounds":inbounds,"outbounds":outbounds,
            "routing":{"domainStrategy":"IPIfNonMatch","rules":rules}}

def generate(opts):
    reality=gen_reality()
    ss={"enabled":bool(opts.get("ss_enabled")),"port":int(opts.get("ss_port") or 8388),"password":""}
    mode=opts.get("mode","both")
    if mode=="nosni": ss["enabled"]=True
    if ss["enabled"]:  ss["password"]=gen_password()
    channels=["direct","warp"] if mode=="both" else ([] if mode=="nosni" else [mode])
    if opts.get("sni_mode")=="manual" and opts.get("sni_manual"):
        sni_list=[opts["sni_manual"]]
    elif mode!="nosni":
        sni_list=pick_snis(int(opts.get("sni_count") or 2))
    else:
        sni_list=[]
    profiles,port=[],int(opts.get("base_port") or BASE_PORT)
    def next_port():
        nonlocal port
        while ss["enabled"] and port==ss["port"]: port+=1
        p=port; port+=1; return p
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
    import random as _rnd
    used=[p["port"] for p in profiles]+([ss["port"]] if ss["enabled"] else [])
    api_port=_rnd.randint(20000,49999)
    while api_port in used: api_port=_rnd.randint(20000,49999)
    config=build_config(profiles,reality,users,ss,api_port)
    sub_tokens,per_user={},[]
    ip=opts["server_ip"]
    for u in users:
        local=u["email"].split("@")[0]
        items=[{"channel":p["channel"],"sni":p["sni"],"port":p["port"],
                "link":vless_link(u["id"],ip,p["port"],p["sni"],reality["publicKey"],
                                  reality["shortId"],f'KIAN-{local}-{CH_LABEL[p["channel"]]}-{p["sni"]}')}
               for p in profiles]
        token=secrets.token_hex(16); sub_tokens[u["email"]]=token
        sub_urls=[f"http://{ip}:{sp}/sub/{token}" for sp in SUB_PORTS]
        per_user.append({"email":u["email"],"local":local,"items":items,
                         "subUrls":sub_urls,"subToken":token})
    ss_out_link=ss_link(ip,ss["port"],ss["password"],"KIAN-Shadowsocks") if ss["enabled"] else None
    links=[it["link"] for u in per_user for it in u["items"]]
    if ss_out_link: links.append(ss_out_link)
    ports=[p["port"] for p in profiles]+([ss["port"]] if ss["enabled"] else [])
    payload={"warp_needed":"warp" in channels,"server_ip":ip,
             "config_b64":_b64(json.dumps(config)),"users_b64":_b64(json.dumps({"users":users})),
             "links":links,"ports":ports,"api_port":api_port,"sub_port":SUB_PORTS,
             "sub_tokens":sub_tokens,"reality_pbk":reality["publicKey"],"reality_sid":reality["shortId"],
             "ss_password":ss["password"] if ss["enabled"] else ""}
    payload_b64=_b64(json.dumps(payload))
    return {"reality":reality,"users":users,"per_user":per_user,"ss_link":ss_out_link,
            "ports":ports,"profiles":profiles,"sni_list":sni_list,"config":config,
            "payload_b64":payload_b64,"warp_needed":"warp" in channels,
            "sub_tokens":sub_tokens,"install_cmd":f"export KIAN_PAYLOAD='{payload_b64}'\ncurl -fsSL {RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh"}

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
def cmd_uninstall():       return "kian-v2ray uninstall"

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
# ══════════════════════════════════════════════════════════════
def _run_gui():
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    BG="#0d1117"; SB="#161b22"; CARD="#1c2333"; BORDER="#30363d"
    ACC="#2ea043"; ACC2="#1f6feb"; TXT="#e6edf3"; MUT="#7d8590"
    ERR="#f85149"; WARN="#e3b341"; PURPLE="#6e40c9"

    FT=("Segoe UI",15,"bold"); FC=("Segoe UI",12,"bold")
    FB=("Segoe UI",10); FM=("Cascadia Code",9)

    def ient(e,d=0):
        try: return int(e.get().strip() or d)
        except: return d
    def cln(e): return re.sub(r"[^a-zA-Z0-9_-]","",e.get().strip())

    # ── QR helper ────────────────────────────────────────────
    def make_qr_image(data,size=120):
        try:
            import qrcode
            from PIL import Image
            qr=qrcode.QRCode(border=1,error_correction=qrcode.constants.ERROR_CORRECT_L)
            qr.add_data(data); qr.make(fit=True)
            img=qr.make_image(fill_color="white",back_color="#0d1117")
            return img.resize((size,size),Image.NEAREST)
        except Exception: return None

    # ── mini widgets ─────────────────────────────────────────
    class Card(ctk.CTkFrame):
        def __init__(self,m,**kw): super().__init__(m,fg_color=CARD,corner_radius=10,**kw)

    class LogBox(ctk.CTkTextbox):
        def __init__(self,m,**kw):
            super().__init__(m,state="disabled",font=FM,text_color="#a5d6a7",fg_color="#0a0d10",corner_radius=8,**kw)
        def clear(self): self.configure(state="normal"); self.delete("1.0","end"); self.configure(state="disabled")
        def append(self,t,color=None):
            self.configure(state="normal"); self.insert("end",t+"\n"); self.see("end"); self.configure(state="disabled")

    class UserTable(ctk.CTkScrollableFrame):
        COLS=[("ایمیل",185),("فعال",60),("مصرف",100),("حجم",100),("انقضا",140)]
        def __init__(self,m,on_sel=None):
            super().__init__(m,fg_color=CARD,corner_radius=8)
            self._on_sel=on_sel; self._rows=[]; self._sel=-1
            for ci,(t,w) in enumerate(self.COLS):
                ctk.CTkLabel(self,text=t,font=("Segoe UI",10,"bold"),text_color=ACC2,width=w,anchor="w").grid(
                    row=0,column=ci,padx=(8 if ci==0 else 4,4),pady=(8,4),sticky="w")
        def load(self,rows):
            for rw in self._rows:
                for c in rw: c.destroy()
            self._rows=[]; self._sel=-1
            for ri,d in enumerate(rows):
                vals=[d.get("email",""),d.get("active",""),d.get("used",""),d.get("quota",""),d.get("expiry","")]
                ok=d.get("active","") not in ("❌","غیرفعال","false","0")
                cells=[]
                for ci,(v,(_,w)) in enumerate(zip(vals,self.COLS)):
                    lbl=ctk.CTkLabel(self,text=str(v),font=FB,
                                     text_color=(ACC if ok else ERR) if ci==1 else TXT,
                                     width=w,anchor="w",fg_color="transparent",corner_radius=4)
                    lbl.grid(row=ri+1,column=ci,padx=(8 if ci==0 else 4,4),pady=2,sticky="w")
                    lbl.bind("<Button-1>",lambda e,r=ri:self._pick(r))
                    cells.append(lbl)
                self._rows.append(cells)
        def _pick(self,ri):
            if 0<=self._sel<len(self._rows):
                for c in self._rows[self._sel]: c.configure(fg_color="transparent")
            self._sel=ri
            for c in self._rows[ri]: c.configure(fg_color="#1f3a2a")
            if self._on_sel: self._on_sel(self._rows[ri][0].cget("text"))

    # ════════════════════════════════════════════════════════
    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title(f"Kv2m — مدیریت Kian V2Ray  v{APP_VERSION}")
            self.geometry("1100x700"); self.minsize(960,620)
            self.configure(fg_color=BG)
            self._ssh=None; self._q=queue.Queue()
            self._last_gen=None; self._profiles=[]
            self._load_profs(); self._build(); self._poll()

        # ── skeleton ───────────────────────────────────────
        def _build(self):
            sb=ctk.CTkFrame(self,width=192,fg_color=SB,corner_radius=0)
            sb.pack(side="left",fill="y"); sb.pack_propagate(False)
            self._sb=sb; self._build_sb()
            mn=ctk.CTkFrame(self,fg_color=BG,corner_radius=0)
            mn.pack(side="left",fill="both",expand=True); self._mn=mn
            self._build_conn()
            self._pgs=[self._pg_gen(),self._pg_install(),
                       self._pg_manage(),self._pg_dash(),self._pg_sett()]
            self._nav(0)

        NAV_LABELS=["⚡  ساخت کانفیگ","🚀  نصب روی سرور",
                    "👥  مدیریت کاربر","🖥️  وضعیت","⚙️  تنظیمات"]

        def _build_sb(self):
            f=ctk.CTkFrame(self._sb,fg_color="transparent"); f.pack(fill="x",pady=(22,8))
            ctk.CTkLabel(f,text="⚡",font=("Segoe UI Emoji",30),text_color=ACC).pack()
            ctk.CTkLabel(f,text="Kv2m",font=("Segoe UI",18,"bold"),text_color=TXT).pack()
            ctk.CTkLabel(f,text=f"v{APP_VERSION}  |  kian_v2ray",font=("Segoe UI",8),text_color=MUT).pack()
            ctk.CTkFrame(self._sb,height=1,fg_color=BORDER).pack(fill="x",padx=12,pady=10)
            self._nbts=[]
            for i,label in enumerate(self.NAV_LABELS):
                b=ctk.CTkButton(self._sb,text=f"  {label}",font=FB,anchor="w",
                    fg_color="transparent",hover_color="#21262d",text_color=MUT,corner_radius=8,
                    command=lambda idx=i:self._nav(idx))
                b.pack(fill="x",padx=10,pady=2); self._nbts.append(b)
            ctk.CTkFrame(self._sb,fg_color="transparent").pack(fill="both",expand=True)
            ctk.CTkLabel(self._sb,text="github.com/KIAN-IRANI/kian_v2ray",
                font=("Segoe UI",8),text_color=MUT).pack(pady=12)

        def _nav(self,idx):
            for i,(b,p) in enumerate(zip(self._nbts,self._pgs)):
                if i==idx: b.configure(fg_color="#1f3a2a",text_color=ACC); p.pack(fill="both",expand=True)
                else: b.configure(fg_color="transparent",text_color=MUT); p.pack_forget()

        def _build_conn(self):
            bar=Card(self._mn); bar.pack(fill="x",padx=14,pady=(14,8))
            row=ctk.CTkFrame(bar,fg_color="transparent"); row.pack(fill="x",padx=14,pady=10)
            def lbl(t): return ctk.CTkLabel(row,text=t,font=FB,text_color=MUT)
            def ent(w,ph,dv="",show=None):
                e=ctk.CTkEntry(row,width=w,placeholder_text=ph,show=show)
                if dv: e.insert(0,dv)
                return e
            lbl("آی‌پی / دامنه").grid(row=0,column=0,padx=(0,4))
            self._eh=ent(155,"1.2.3.4"); self._eh.grid(row=0,column=1,padx=(0,10))
            lbl("پورت").grid(row=0,column=2,padx=(0,4))
            self._ep=ent(55,"22","22"); self._ep.grid(row=0,column=3,padx=(0,10))
            lbl("کاربر").grid(row=0,column=4,padx=(0,4))
            self._eu=ent(75,"root","root"); self._eu.grid(row=0,column=5,padx=(0,10))
            lbl("رمز").grid(row=0,column=6,padx=(0,4))
            self._ew=ent(115,"••••••••",show="●"); self._ew.grid(row=0,column=7,padx=(0,12))
            self._bc=ctk.CTkButton(row,text="اتصال SSH",width=100,fg_color=ACC,hover_color="#238636",
                font=("Segoe UI",10,"bold"),command=self._connect)
            self._bc.grid(row=0,column=8,padx=(0,7))
            ctk.CTkButton(row,text="قطع",width=55,fg_color="#21262d",hover_color=ERR,
                text_color=MUT,command=self._disconnect).grid(row=0,column=9,padx=(0,12))
            self._dot=ctk.CTkLabel(row,text="●",font=("Segoe UI",14),text_color=ERR)
            self._dot.grid(row=0,column=10,padx=(0,4))
            self._lst=ctk.CTkLabel(row,text="قطع",font=FB,text_color=MUT)
            self._lst.grid(row=0,column=11)

        # ══════════════════════════════════════════════════
        # صفحه ۱: ساخت کانفیگ
        # ══════════════════════════════════════════════════
        def _pg_gen(self):
            page=ctk.CTkFrame(self._mn,fg_color="transparent")
            ctk.CTkLabel(page,text="ساخت کانفیگ و دستور نصب",font=FT,text_color=TXT).pack(anchor="w",padx=14,pady=(4,8))

            scroll=ctk.CTkScrollableFrame(page,fg_color="transparent")
            scroll.pack(fill="both",expand=True,padx=14,pady=(0,14))

            # ── فرم اصلی ──────────────────────────────────
            fm=Card(scroll); fm.pack(fill="x",pady=(0,10))
            inner=ctk.CTkFrame(fm,fg_color="transparent"); inner.pack(padx=16,pady=14,fill="x")

            def row_lbl(parent,text,r,c):
                ctk.CTkLabel(parent,text=text,font=FB,text_color=MUT).grid(row=r,column=c,sticky="e",padx=(14 if c>0 else 0,6),pady=6)

            row_lbl(inner,"آی‌پی سرور:",0,0)
            self._gi_ip=ctk.CTkEntry(inner,width=150,placeholder_text="1.2.3.4")
            self._gi_ip.grid(row=0,column=1,pady=6)

            row_lbl(inner,"نام کاربر:",0,2)
            self._gi_prefix=ctk.CTkEntry(inner,width=120,placeholder_text="user")
            self._gi_prefix.insert(0,"user"); self._gi_prefix.grid(row=0,column=3,pady=6)

            row_lbl(inner,"تعداد کاربر:",0,4)
            sp_frame=ctk.CTkFrame(inner,fg_color="transparent"); sp_frame.grid(row=0,column=5,pady=6)
            self._gi_num=ctk.CTkEntry(sp_frame,width=50); self._gi_num.insert(0,"1")
            self._gi_num.pack(side="left")
            ctk.CTkButton(sp_frame,text="+",width=28,height=28,fg_color=CARD,command=lambda:self._step(self._gi_num,1)).pack(side="left",padx=2)
            ctk.CTkButton(sp_frame,text="-",width=28,height=28,fg_color=CARD,command=lambda:self._step(self._gi_num,-1)).pack(side="left")

            # حالت اتصال
            row_lbl(inner,"حالت:",1,0)
            self._gi_mode=ctk.CTkComboBox(inner,values=["both — هر دو","direct — سریع","warp — همه‌چیز","nosni — بدون SNI"],
                                           width=200,state="readonly")
            self._gi_mode.set("both — هر دو"); self._gi_mode.grid(row=1,column=1,columnspan=3,pady=6,sticky="w")

            row_lbl(inner,"حجم:",1,4)
            self._gi_gb=ctk.CTkComboBox(inner,values=["0 — نامحدود","50","100","200","500"],width=120,state="readonly")
            self._gi_gb.set("0 — نامحدود"); self._gi_gb.grid(row=1,column=5,pady=6)

            row_lbl(inner,"مدت:",2,0)
            self._gi_days=ctk.CTkComboBox(inner,values=["0 — دائمی","30","60","90"],width=120,state="readonly")
            self._gi_days.set("0 — دائمی"); self._gi_days.grid(row=2,column=1,pady=6)

            # ── تنظیمات پیشرفته ────────────────────────────
            adv=Card(scroll); adv.pack(fill="x",pady=(0,10))
            adv_btn=ctk.CTkButton(adv,text="▶  تنظیمات پیشرفته",font=FB,anchor="w",
                fg_color="transparent",hover_color="#21262d",text_color=MUT,command=lambda:self._toggle_adv(adv_body,adv_btn))
            adv_btn.pack(anchor="w",padx=14,pady=8)
            adv_body=ctk.CTkFrame(adv,fg_color="transparent")
            # adv_body شروع پنهان است

            adv_in=ctk.CTkFrame(adv_body,fg_color="transparent"); adv_in.pack(padx=16,pady=(0,14),fill="x")

            row_lbl(adv_in,"حالت SNI:",0,0)
            self._gi_sni_mode=ctk.CTkComboBox(adv_in,values=["auto — خودکار","manual — دستی"],
                width=160,state="readonly",command=lambda v:self._sync_sni_vis())
            self._gi_sni_mode.set("auto — خودکار"); self._gi_sni_mode.grid(row=0,column=1,pady=6)

            row_lbl(adv_in,"تعداد SNI:",0,2)
            self._gi_sni_count=ctk.CTkComboBox(adv_in,values=["1","2","3"],width=80,state="readonly")
            self._gi_sni_count.set("2"); self._gi_sni_count.grid(row=0,column=3,pady=6)

            row_lbl(adv_in,"دامنه دستی:",1,0)
            self._gi_sni_manual=ctk.CTkComboBox(adv_in,
                values=SNI_MANUAL_OPTIONS+["دلخواه…"],width=200,state="readonly",
                command=lambda v:self._sync_sni_vis())
            self._gi_sni_manual.set(SNI_MANUAL_OPTIONS[0])
            self._gi_sni_manual.grid(row=1,column=1,columnspan=3,pady=6,sticky="w")

            row_lbl(adv_in,"دامنه دلخواه:",2,0)
            self._gi_sni_custom=ctk.CTkEntry(adv_in,width=200,placeholder_text="example.com")
            self._gi_sni_custom.grid(row=2,column=1,columnspan=3,pady=6,sticky="w")

            self._gi_ss_var=tk.BooleanVar(value=False)
            ctk.CTkCheckBox(adv_in,text="Shadowsocks هم اضافه کن",variable=self._gi_ss_var,
                font=FB,text_color=TXT).grid(row=3,column=0,columnspan=2,pady=6,sticky="w")

            row_lbl(adv_in,"پورت Shadowsocks:",3,2)
            self._gi_ss_port=ctk.CTkEntry(adv_in,width=90); self._gi_ss_port.insert(0,"8388")
            self._gi_ss_port.grid(row=3,column=3,pady=6)

            row_lbl(adv_in,"پورت پایه (اختیاری):",4,0)
            self._gi_base=ctk.CTkEntry(adv_in,width=90,placeholder_text="8443")
            self._gi_base.grid(row=4,column=1,pady=6)

            self._sync_sni_vis()

            # ── دکمه ساخت ──────────────────────────────────
            btn_row=ctk.CTkFrame(scroll,fg_color="transparent"); btn_row.pack(fill="x",pady=(0,10))
            self._gen_btn=ctk.CTkButton(btn_row,text="⚡  ساخت کانفیگ",width=200,height=42,
                fg_color=ACC,hover_color="#238636",font=("Segoe UI",12,"bold"),command=self._do_gen)
            self._gen_btn.pack(side="left",padx=(0,12))
            ctk.CTkLabel(btn_row,text="آی‌پی سرور را وارد کن، بزن ساخت. دستور نصب و لینک‌ها ظاهر می‌شود.",
                font=FB,text_color=MUT).pack(side="left")

            # ── نتیجه ──────────────────────────────────────
            self._gen_result=ctk.CTkScrollableFrame(scroll,fg_color="transparent",height=340)
            self._gen_result.pack(fill="x")

            return page

        def _toggle_adv(self,body,btn):
            if body.winfo_ismapped(): body.pack_forget(); btn.configure(text="▶  تنظیمات پیشرفته")
            else: body.pack(fill="x"); btn.configure(text="▼  تنظیمات پیشرفته")

        def _sync_sni_vis(self):
            is_manual="manual" in self._gi_sni_mode.get()
            is_custom="دلخواه" in self._gi_sni_manual.get()
            self._gi_sni_count.configure(state="readonly" if not is_manual else "disabled")
            self._gi_sni_manual.configure(state="readonly" if is_manual else "disabled")
            self._gi_sni_custom.configure(state="normal" if (is_manual and is_custom) else "disabled")

        def _step(self,entry,delta):
            try: v=int(entry.get() or 1); v=max(1,min(50,v+delta)); entry.delete(0,"end"); entry.insert(0,str(v))
            except: pass

        def _do_gen(self):
            ip=self._gi_ip.get().strip() or self._eh.get().strip()
            if not ip: self._toast("آی‌پی سرور را وارد کن.",True); return
            mode_raw=self._gi_mode.get().split(" ")[0]
            gb_raw=self._gi_gb.get().split(" ")[0]
            days_raw=self._gi_days.get().split(" ")[0]
            sni_mode="manual" if "manual" in self._gi_sni_mode.get() else "auto"
            sni_manual=self._gi_sni_custom.get().strip() if "دلخواه" in self._gi_sni_manual.get() else self._gi_sni_manual.get().split(" ")[0]
            opts={"server_ip":ip,"mode":mode_raw,"prefix":cln(self._gi_prefix) or "user",
                  "num_users":ient(self._gi_num,1),"quota_gb":int(gb_raw) if gb_raw.isdigit() else 0,
                  "days":int(days_raw) if days_raw.isdigit() else 0,
                  "sni_mode":sni_mode,"sni_manual":sni_manual if sni_mode=="manual" else "",
                  "sni_count":int(self._gi_sni_count.get()),
                  "ss_enabled":self._gi_ss_var.get(),"ss_port":ient(self._gi_ss_port,8388),
                  "base_port":ient(self._gi_base,8443) if self._gi_base.get().strip() else None}
            try: g=generate(opts)
            except Exception as e: self._toast(f"خطا: {e}",True); return
            self._last_gen=g
            self._render_gen(g)

        def _render_gen(self,g):
            # پاک کردن نتیجه قبلی
            for w in self._gen_result.winfo_children(): w.destroy()

            # ── دستور نصب ──────────────────────────────────
            ic=Card(self._gen_result); ic.pack(fill="x",pady=(0,8))
            hdr=ctk.CTkFrame(ic,fg_color="transparent"); hdr.pack(fill="x",padx=14,pady=(10,4))
            ctk.CTkLabel(hdr,text="دستور نصب",font=FC,text_color=TXT).pack(side="left")
            ctk.CTkButton(hdr,text="📋 کپی",width=80,fg_color=ACC2,hover_color="#1158c7",
                command=lambda:self._copy(g["install_cmd"])).pack(side="right")
            ctk.CTkButton(hdr,text="🚀 اجرا روی سرور",width=140,fg_color=ACC,hover_color="#238636",
                command=lambda:self._run_install_from_gen(g),
                font=("Segoe UI",10,"bold")).pack(side="right",padx=(0,8))
            cmd_box=ctk.CTkTextbox(ic,height=60,font=("Cascadia Code",8),
                text_color="#a5d6a7",fg_color="#0a0d10",corner_radius=6,state="disabled")
            cmd_box.pack(fill="x",padx=14,pady=(0,12))
            cmd_box.configure(state="normal"); cmd_box.insert("1.0",g["install_cmd"]); cmd_box.configure(state="disabled")

            # ── لینک هر کاربر ──────────────────────────────
            for pu in g["per_user"]:
                uc=Card(self._gen_result); uc.pack(fill="x",pady=(0,8))
                uh=ctk.CTkFrame(uc,fg_color="transparent"); uh.pack(fill="x",padx=14,pady=(10,4))
                ctk.CTkLabel(uh,text=f"کاربر: {pu['local']}",font=FC,text_color=ACC2).pack(side="left")
                all_links=[it["link"] for it in pu["items"]]
                if g["ss_link"]: all_links.append(g["ss_link"])
                ctk.CTkButton(uh,text="📋 کپی همه لینک‌ها",width=140,fg_color=CARD,hover_color="#21262d",
                    command=lambda ls=all_links:self._copy("\n".join(ls))).pack(side="right")

                for it in pu["items"]:
                    self._link_row(uc,it["link"],f'{it["channel"]} — {it["sni"]}')

                # Subscription URL
                sub_frame=ctk.CTkFrame(uc,fg_color="#161b22",corner_radius=6)
                sub_frame.pack(fill="x",padx=10,pady=4)
                ctk.CTkLabel(sub_frame,text="لینک Subscription:",font=FB,text_color=MUT).pack(side="left",padx=10,pady=6)
                sub_url=pu["subUrls"][0]
                ctk.CTkLabel(sub_frame,text=sub_url,font=("Cascadia Code",8),text_color=WARN).pack(side="left",padx=4,pady=6)
                ctk.CTkButton(sub_frame,text="📋",width=30,height=26,fg_color=CARD,hover_color="#21262d",
                    command=lambda u=sub_url:self._copy(u)).pack(side="right",padx=8,pady=4)

                uc.pack_configure(pady=(0,10))

            # SS link اگر بود
            if g["ss_link"]:
                sc=Card(self._gen_result); sc.pack(fill="x",pady=(0,8))
                ctk.CTkLabel(sc,text="Shadowsocks",font=FC,text_color=TXT).pack(anchor="w",padx=14,pady=(10,4))
                self._link_row(sc,g["ss_link"],"Shadowsocks")

            self._nav(0)

        def _link_row(self,parent,link,title=""):
            row=ctk.CTkFrame(parent,fg_color="#0d1117",corner_radius=6); row.pack(fill="x",padx=10,pady=3)
            left=ctk.CTkFrame(row,fg_color="transparent"); left.pack(side="left",fill="x",expand=True,padx=10,pady=6)
            if title:
                ctk.CTkLabel(left,text=title,font=("Segoe UI",9),text_color=MUT).pack(anchor="w")
            ctk.CTkLabel(left,text=link,font=FM,text_color="#a5d6a7",anchor="w",wraplength=680).pack(anchor="w")
            btns=ctk.CTkFrame(row,fg_color="transparent"); btns.pack(side="right",padx=8,pady=4)
            ctk.CTkButton(btns,text="📋",width=32,height=28,fg_color=CARD,hover_color="#21262d",
                command=lambda l=link:(self._copy(l))).pack(side="left",padx=2)
            ctk.CTkButton(btns,text="QR",width=32,height=28,fg_color=CARD,hover_color="#21262d",
                command=lambda l=link:self._show_qr(l)).pack(side="left")

        def _run_install_from_gen(self,g):
            if not self._need(): return
            self._nav(1)
            self._inst_log.clear()
            cmd=f"export KIAN_PAYLOAD='{g['payload_b64']}'\ncurl -fsSL {RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh"
            self._execute_install(cmd,g)

        def _show_qr(self,data):
            img=make_qr_image(data,180)
            if not img: self._toast("qrcode/Pillow نصب نیست."); return
            win=ctk.CTkToplevel(self); win.title("QR Code"); win.configure(fg_color=BG)
            win.resizable(False,False)
            try:
                from PIL import ImageTk
                ph=ImageTk.PhotoImage(img)
                lbl=tk.Label(win,image=ph,bg=BG); lbl.image=ph; lbl.pack(padx=20,pady=20)
            except Exception as e: ctk.CTkLabel(win,text=str(e),font=FB).pack(padx=20,pady=20)

        # ══════════════════════════════════════════════════
        # صفحه ۲: نصب روی سرور
        # ══════════════════════════════════════════════════
        def _pg_install(self):
            page=ctk.CTkFrame(self._mn,fg_color="transparent")
            ctk.CTkLabel(page,text="نصب روی سرور",font=FT,text_color=TXT).pack(anchor="w",padx=14,pady=(4,8))

            note=ctk.CTkLabel(page,text="ابتدا در تب «ساخت کانفیگ» کانفیگ بساز، سپس «اجرا روی سرور» را بزن — یا اینجا IP را وارد کن و نصب کن.",
                font=FB,text_color=MUT,wraplength=800,justify="left")
            note.pack(anchor="w",padx=14,pady=(0,8))

            fm=Card(page); fm.pack(fill="x",padx=14,pady=(0,10))
            r1=ctk.CTkFrame(fm,fg_color="transparent"); r1.pack(padx=14,pady=12,fill="x")

            def lbl(t): return ctk.CTkLabel(r1,text=t,font=FB,text_color=MUT)
            lbl("حالت:").pack(side="left")
            self._im=ctk.CTkComboBox(r1,values=["both — هر دو","direct","warp","nosni"],width=155,state="readonly")
            self._im.set("both — هر دو"); self._im.pack(side="left",padx=(6,18))
            lbl("کاربران:").pack(side="left")
            self._iu=ctk.CTkEntry(r1,width=50); self._iu.insert(0,"1"); self._iu.pack(side="left",padx=(6,18))
            lbl("SNI:").pack(side="left")
            self._is=ctk.CTkEntry(r1,width=40); self._is.insert(0,"2"); self._is.pack(side="left",padx=(6,18))
            lbl("پورت پایه:").pack(side="left")
            self._ib=ctk.CTkEntry(r1,width=70,placeholder_text="8443"); self._ib.pack(side="left",padx=(6,0))

            br=ctk.CTkFrame(fm,fg_color="transparent"); br.pack(padx=14,pady=(0,12),fill="x")
            self._inst_btn=ctk.CTkButton(br,text="🚀  نصب روی سرور",width=180,height=40,
                fg_color=ACC,hover_color="#238636",font=("Segoe UI",11,"bold"),command=self._do_install_fresh)
            self._inst_btn.pack(side="left",padx=(0,10))
            self._inst_prog=ctk.CTkProgressBar(br,width=180,mode="indeterminate"); self._inst_prog.pack(side="left"); self._inst_prog.set(0)

            ctk.CTkLabel(page,text="خروجی زنده سرور:",font=FB,text_color=MUT).pack(anchor="w",padx=14,pady=(4,4))
            self._inst_log=LogBox(page)
            self._inst_log.pack(fill="both",expand=True,padx=14,pady=(0,14))
            return page

        def _do_install_fresh(self):
            if not self._need(): return
            ip=self._eh.get().strip()
            mode_raw=self._im.get().split(" ")[0]
            opts={"server_ip":ip,"mode":mode_raw,"prefix":"user",
                  "num_users":ient(self._iu,1),"sni_count":ient(self._is,2),
                  "base_port":ient(self._ib,8443),"quota_gb":0,"days":0,"sni_mode":"auto"}
            try: g=generate(opts)
            except Exception as e: self._toast(f"خطا: {e}",True); return
            self._last_gen=g
            cmd=f"export KIAN_PAYLOAD='{g['payload_b64']}'\ncurl -fsSL {RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh"
            self._inst_log.clear()
            self._execute_install(cmd,g)

        def _execute_install(self,cmd,g):
            self._inst_log.append(f"پورت‌ها: {g['ports']}\nشروع نصب…\n")
            self._inst_btn.configure(state="disabled")
            self._inst_prog.start()
            def work():
                try: self._ssh.run_stream(cmd,lambda l:self._ui(lambda x=l:self._inst_log.append(x)))
                except Exception as e: self._ui(lambda:self._inst_log.append(f"\nخطا: {e}"))
                def done():
                    self._inst_prog.stop(); self._inst_prog.set(1); self._inst_btn.configure(state="normal")
                    self._inst_log.append("\n✅ نصب اجرا شد. لینک‌ها:\n")
                    for u in g["per_user"]:
                        for it in u["items"]: self._inst_log.append(it["link"])
                    if g["ss_link"]: self._inst_log.append(g["ss_link"])
                self._ui(done); self._ui(self._bg_refresh)
            threading.Thread(target=work,daemon=True).start()

        # ══════════════════════════════════════════════════
        # صفحه ۳: مدیریت کاربر
        # ══════════════════════════════════════════════════
        def _pg_manage(self):
            page=ctk.CTkFrame(self._mn,fg_color="transparent")
            ctk.CTkLabel(page,text="مدیریت کاربران",font=FT,text_color=TXT).pack(anchor="w",padx=14,pady=(4,8))

            fm=Card(page); fm.pack(fill="x",padx=14,pady=(0,10))
            inn=ctk.CTkFrame(fm,fg_color="transparent"); inn.pack(padx=14,pady=12)

            def lbl(t,r,c): ctk.CTkLabel(inn,text=t,font=FB,text_color=MUT).grid(row=r,column=c,sticky="e",padx=(12 if c>0 else 0,6),pady=6)
            lbl("عملیات:",0,0)
            self._mg_act=ctk.CTkComboBox(inn,values=["configs — لینک‌ها","sub — Subscription","add — افزودن","renew — تمدید",
                "reset — ریست حجم","remove — حذف","users — لیست","status — وضعیت","update — آپدیت","uninstall — حذف کامل"],
                width=220,state="readonly",command=lambda v:self._sync_mg_vis())
            self._mg_act.set("configs — لینک‌ها"); self._mg_act.grid(row=0,column=1,pady=6,sticky="w")

            lbl("نام کاربر:",0,2)
            self._mg_name=ctk.CTkEntry(inn,width=140,placeholder_text="user-1"); self._mg_name.grid(row=0,column=3,pady=6)

            lbl("حجم (گیگ):",1,0)
            self._mg_gb=ctk.CTkEntry(inn,width=90,placeholder_text="100"); self._mg_gb.insert(0,"100"); self._mg_gb.grid(row=1,column=1,pady=6,sticky="w")

            lbl("مدت (روز):",1,2)
            self._mg_days=ctk.CTkEntry(inn,width=90,placeholder_text="30"); self._mg_days.insert(0,"30"); self._mg_days.grid(row=1,column=3,pady=6,sticky="w")

            br=ctk.CTkFrame(fm,fg_color="transparent"); br.pack(padx=14,pady=(0,12),anchor="w")
            def mbtn(text,fc,hc,cmd): return ctk.CTkButton(br,text=text,width=130,fg_color=fc,hover_color=hc,font=FB,command=cmd)
            mbtn("▶  اجرا",ACC,"#238636",self._mg_run_action).pack(side="left",padx=(0,8))
            mbtn("📋 کپی دستور",CARD,"#21262d",self._mg_copy_cmd).pack(side="left",padx=(0,8))
            mbtn("↻ تازه‌سازی",ACC2,"#1158c7",lambda:(self._nav(2),self._bg_refresh())).pack(side="left")

            # پیش‌نمایش دستور
            prev_frame=ctk.CTkFrame(fm,fg_color="#0a0d10",corner_radius=6); prev_frame.pack(fill="x",padx=14,pady=(0,12))
            self._mg_prev=ctk.CTkLabel(prev_frame,text="",font=FM,text_color=MUT,anchor="w")
            self._mg_prev.pack(padx=10,pady=6,anchor="w")
            self._mg_name.bind("<KeyRelease>",lambda e:self._upd_mg_prev())
            self._mg_act.configure(command=lambda v:(self._sync_mg_vis(),self._upd_mg_prev()))
            self._upd_mg_prev()

            self._mg_out=LogBox(page,height=160)
            self._mg_out.pack(fill="x",padx=14,pady=(0,8))

            # جدول کاربران
            tc=Card(page); tc.pack(fill="both",expand=True,padx=14,pady=(0,14))
            ctk.CTkLabel(tc,text="لیست کاربران",font=FC,text_color=TXT).pack(anchor="w",padx=14,pady=(10,4))
            self._mg_tbl=UserTable(tc,on_sel=lambda e:(self._mg_name.delete(0,"end"),self._mg_name.insert(0,e.split("@")[0]),self._upd_mg_prev()))
            self._mg_tbl.pack(fill="both",expand=True,padx=8,pady=(0,8))
            return page

        def _sync_mg_vis(self):
            act=self._mg_act.get().split(" ")[0]
            show_gb   = act in ("add","reset")
            show_days = act in ("add","renew")
            show_name = act not in ("users","status","update","uninstall")
            for w,show in [(self._mg_gb,show_gb),(self._mg_days,show_days),(self._mg_name,show_name)]:
                w.configure(state="normal" if show else "disabled")

        def _upd_mg_prev(self):
            try: cmd=self._mg_build_cmd(); self._mg_prev.configure(text=f"$ {cmd[:120]}")
            except: pass

        def _mg_build_cmd(self):
            act=self._mg_act.get().split(" ")[0]
            name=re.sub(r"[^a-zA-Z0-9_-]","",self._mg_name.get().strip())
            if act=="configs":   return cmd_configs(name)
            if act=="sub":       return cmd_sub(name)
            if act=="add":       return cmd_add(name,ient(self._mg_gb),ient(self._mg_days))
            if act=="renew":     return cmd_renew(name,ient(self._mg_days))
            if act=="reset":     return cmd_reset(name,ient(self._mg_gb))
            if act=="remove":    return cmd_remove(name)
            if act=="users":     return cmd_users()
            if act=="status":    return cmd_status()
            if act=="update":    return cmd_update()
            if act=="uninstall": return cmd_uninstall()
            return ""

        def _mg_run_action(self):
            if not self._need(): return
            act=self._mg_act.get().split(" ")[0]
            if act=="remove" and not messagebox.askyesno("حذف",f"کاربر «{cln(self._mg_name)}» حذف شود؟"): return
            if act=="uninstall" and not messagebox.askyesno("حذف کامل","kian-v2ray کاملاً از سرور حذف شود؟"): return
            cmd=self._mg_build_cmd()
            def work():
                _,out,err=self._ssh.run(cmd)
                links=parse_links(out)
                self._ui(lambda:self._mg_out.append(f"$ {cmd[:80]}…\n{out or err or 'انجام شد.'}\n"))
                if links:
                    self._ui(lambda ls=links:self._show_links_popup(ls))
                self._ui(self._bg_refresh)
            threading.Thread(target=work,daemon=True).start()

        def _mg_copy_cmd(self):
            try: self._copy(self._mg_build_cmd())
            except Exception as e: self._toast(str(e),True)

        def _show_links_popup(self,links):
            win=ctk.CTkToplevel(self); win.title("لینک‌های کاربر"); win.configure(fg_color=BG)
            win.geometry("900x400")
            sc=ctk.CTkScrollableFrame(win,fg_color=BG); sc.pack(fill="both",expand=True,padx=10,pady=10)
            ctk.CTkButton(win,text="📋 کپی همه",fg_color=ACC2,hover_color="#1158c7",
                command=lambda:self._copy("\n".join(links))).pack(pady=(0,8))
            for lnk in links: self._link_row(sc,lnk)

        # ══════════════════════════════════════════════════
        # صفحه ۴: وضعیت (داشبورد)
        # ══════════════════════════════════════════════════
        def _pg_dash(self):
            page=ctk.CTkFrame(self._mn,fg_color="transparent")
            hdr=ctk.CTkFrame(page,fg_color="transparent"); hdr.pack(fill="x",padx=14,pady=(4,8))
            ctk.CTkLabel(hdr,text="وضعیت سرور",font=FT,text_color=TXT).pack(side="left")
            ctk.CTkButton(hdr,text="↻  تازه‌سازی",width=110,fg_color=CARD,hover_color="#21262d",
                command=self._bg_refresh).pack(side="right")

            cr=ctk.CTkFrame(page,fg_color="transparent"); cr.pack(fill="x",padx=14,pady=(0,10))
            def sc(icon,label,color):
                f=Card(cr); f.pack(side="left",expand=True,fill="both",padx=(0,8) if label!="آپتایم" else (0,0))
                ctk.CTkLabel(f,text=icon,font=("Segoe UI Emoji",22),text_color=color).pack(pady=(12,2))
                ctk.CTkLabel(f,text=label,font=FB,text_color=MUT).pack()
                v=ctk.CTkLabel(f,text="—",font=FC,text_color=TXT); v.pack(pady=(2,12))
                return v
            self._ds=sc("🟢","Xray",ACC); self._du=sc("👥","کاربران فعال",ACC2)
            self._dt=sc("📊","ترافیک",WARN); self._da=sc("⏱️","آپتایم",MUT)

            tc=Card(page); tc.pack(fill="both",expand=True,padx=14,pady=(0,14))
            ctk.CTkLabel(tc,text="کاربران",font=FC,text_color=TXT).pack(anchor="w",padx=14,pady=(10,4))
            self._dash_tbl=UserTable(tc,on_sel=lambda e:(self._mg_name.delete(0,"end"),self._mg_name.insert(0,e.split("@")[0])))
            self._dash_tbl.pack(fill="both",expand=True,padx=8,pady=(0,8))
            return page

        def _bg_refresh(self):
            if not self._need(): return
            def work():
                try:
                    _,st,_=self._ssh.run(cmd_status()); _,us,_=self._ssh.run(cmd_users())
                    rows=parse_users(us)
                    active=sum(1 for r in rows if r.get("active","") not in ("❌","غیرفعال","false","0"))
                    ok="active" in st.lower() or "running" in st.lower()
                    def upd():
                        self._ds.configure(text="فعال ✓" if ok else "متوقف ✗",text_color=ACC if ok else ERR)
                        self._du.configure(text=f"{active} / {len(rows)}",text_color=ACC2)
                        self._dt.configure(text="—",text_color=MUT); self._da.configure(text="—",text_color=MUT)
                        self._dash_tbl.load(rows); self._mg_tbl.load(rows)
                    self._ui(upd)
                except Exception as e: self._ui(lambda:self._toast(f"خطا: {e}",True))
            threading.Thread(target=work,daemon=True).start()

        # ══════════════════════════════════════════════════
        # صفحه ۵: تنظیمات
        # ══════════════════════════════════════════════════
        def _pg_sett(self):
            page=ctk.CTkFrame(self._mn,fg_color="transparent")
            ctk.CTkLabel(page,text="تنظیمات",font=FT,text_color=TXT).pack(anchor="w",padx=14,pady=(4,8))

            pc=Card(page); pc.pack(fill="x",padx=14,pady=(0,10))
            ctk.CTkLabel(pc,text="پروفایل‌های سرور ذخیره‌شده",font=FC,text_color=TXT).pack(anchor="w",padx=14,pady=(10,6))
            ctk.CTkButton(pc,text="💾  ذخیرهٔ اتصال فعلی",width=180,fg_color=ACC2,hover_color="#1158c7",
                command=self._save_prof).pack(anchor="w",padx=14,pady=(0,6))
            self._psc=ctk.CTkScrollableFrame(pc,height=110,fg_color="#0d1117",corner_radius=6)
            self._psc.pack(fill="x",padx=14,pady=(0,12)); self._render_profs()

            ac=Card(page); ac.pack(fill="x",padx=14,pady=(0,10))
            ctk.CTkLabel(ac,text="ظاهر",font=FC,text_color=TXT).pack(anchor="w",padx=14,pady=(10,6))
            tr=ctk.CTkFrame(ac,fg_color="transparent"); tr.pack(anchor="w",padx=14,pady=(0,12))
            ctk.CTkLabel(tr,text="تم:",font=FB,text_color=MUT).pack(side="left",padx=(0,8))
            ctk.CTkSegmentedButton(tr,values=["Dark","Light","System"],
                command=lambda v:ctk.set_appearance_mode(v.lower())).pack(side="left")

            about=Card(page); about.pack(fill="x",padx=14)
            ctk.CTkLabel(about,text=f"Kv2m v{APP_VERSION}  —  بخشی از kian_v2ray  |  github.com/KIAN-IRANI/kian_v2ray",
                font=FB,text_color=MUT).pack(padx=14,pady=12)
            return page

        # ── SSH ────────────────────────────────────────────
        def _connect(self):
            host=self._eh.get().strip()
            if not host: self._toast("آی‌پی سرور را وارد کن.",True); return
            self._bc.configure(state="disabled",text="…")
            self._setstatus("connecting")
            def work():
                try:
                    ssh=SSH().connect(host,int(self._ep.get().strip() or 22),
                        self._eu.get().strip() or "root",password=self._ew.get() or None)
                    self._ssh=ssh
                    _,out,_=ssh.run(cmd_installed())
                    self._ui(lambda:self._setstatus("connected"))
                    self._ui(lambda:self._bc.configure(state="normal",text="اتصال SSH"))
                    if "KV2M_OK" in out: self._ui(self._bg_refresh)
                    else: self._ui(lambda:self._toast("kian-v2ray نصب نیست — تب «نصب روی سرور» را بزن.",True))
                except Exception as e:
                    self._ui(lambda:self._setstatus("disconnected"))
                    self._ui(lambda:self._bc.configure(state="normal",text="اتصال SSH"))
                    self._ui(lambda:self._toast(f"خطای اتصال:\n{e}",True))
            threading.Thread(target=work,daemon=True).start()

        def _disconnect(self):
            if self._ssh: self._ssh.close(); self._ssh=None
            self._setstatus("disconnected")

        def _setstatus(self,s):
            if s=="connected":
                self._dot.configure(text_color=ACC); self._lst.configure(text=f"متصل — {self._eh.get().strip()}",text_color=ACC)
            elif s=="connecting":
                self._dot.configure(text_color=WARN); self._lst.configure(text="در حال اتصال…",text_color=WARN)
            else:
                self._dot.configure(text_color=ERR); self._lst.configure(text="قطع",text_color=MUT)

        def _need(self):
            if not (self._ssh and self._ssh.client): self._toast("اول به سرور وصل شو.",True); return False
            return True

        # ── profiles ──────────────────────────────────────
        def _prof_path(self): return os.path.join(os.path.expanduser("~"),".kv2m_profiles.json")
        def _load_profs(self):
            try:
                with open(self._prof_path(),"r",encoding="utf-8") as f: self._profiles=json.load(f)
            except: self._profiles=[]
        def _save_profs_file(self):
            try:
                with open(self._prof_path(),"w",encoding="utf-8") as f: json.dump(self._profiles,f,ensure_ascii=False,indent=2)
            except: pass
        def _save_prof(self):
            h=self._eh.get().strip()
            if not h: self._toast("مشخصات اتصال را وارد کن.",True); return
            p={"host":h,"port":self._ep.get().strip() or "22","user":self._eu.get().strip() or "root","pass":self._ew.get()}
            if not any(x["host"]==h and x["user"]==p["user"] for x in self._profiles):
                self._profiles.append(p); self._save_profs_file(); self._render_profs(); self._toast("ذخیره شد ✓")
            else: self._toast("قبلاً ذخیره شده.")
        def _load_prof(self,p):
            self._eh.delete(0,"end"); self._eh.insert(0,p.get("host",""))
            self._ep.delete(0,"end"); self._ep.insert(0,p.get("port","22"))
            self._eu.delete(0,"end"); self._eu.insert(0,p.get("user","root"))
            self._ew.delete(0,"end"); self._ew.insert(0,p.get("pass",""))
            self._toast(f"پروفایل {p['host']} بارگذاری شد.")
        def _del_prof(self,i):
            self._profiles.pop(i); self._save_profs_file(); self._render_profs()
        def _render_profs(self):
            for w in self._psc.winfo_children(): w.destroy()
            if not self._profiles:
                ctk.CTkLabel(self._psc,text="پروفایلی ذخیره نشده.",text_color=MUT,font=FB).pack(pady=8); return
            for i,p in enumerate(self._profiles):
                row=ctk.CTkFrame(self._psc,fg_color="#161b22",corner_radius=6); row.pack(fill="x",padx=4,pady=3)
                ctk.CTkLabel(row,text=f"{p['user']}@{p['host']}:{p['port']}",font=FB,text_color=TXT).pack(side="left",padx=10,pady=6)
                ctk.CTkButton(row,text="استفاده",width=76,fg_color=ACC2,hover_color="#1158c7",
                    command=lambda pr=p:self._load_prof(pr)).pack(side="right",padx=6,pady=4)
                ctk.CTkButton(row,text="🗑️",width=34,fg_color=CARD,hover_color=ERR,
                    command=lambda idx=i:self._del_prof(idx)).pack(side="right",padx=(0,4),pady=4)

        # ── utils ──────────────────────────────────────────
        def _copy(self,text):
            self.clipboard_clear(); self.clipboard_append(text); self._toast("کپی شد ✓")

        def _toast(self,msg,error=False):
            color=ERR if error else ACC
            t=ctk.CTkToplevel(self); t.overrideredirect(True); t.attributes("-topmost",True); t.configure(fg_color=CARD)
            ctk.CTkLabel(t,text=msg,font=FB,text_color=color,wraplength=320).pack(padx=16,pady=12)
            self.update_idletasks()
            x=self.winfo_x()+self.winfo_width()-340; y=self.winfo_y()+self.winfo_height()-90
            t.geometry(f"+{x}+{y}"); t.after(3000,t.destroy)

        def _ui(self,fn): self._q.put(fn)
        def _poll(self):
            try:
                while True: self._q.get_nowait()()
            except queue.Empty: pass
            self.after(60,self._poll)

    App().mainloop()

# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════
def _run_cli():
    try:
        from rich.console import Console; from rich.table import Table
        from rich.panel import Panel; from rich.prompt import Prompt,IntPrompt,Confirm
        RICH=True; con=Console()
    except: RICH=False; con=None
    def _say(m): (con.print(m) if RICH else print(m))
    def _ask(l,d=""): return Prompt.ask(l,default=d) if RICH else (input(f"{l} [{d}]: ").strip() or d)
    def _ask_int(l,d): return IntPrompt.ask(l,default=d) if RICH else (int(input(f"{l} [{d}]: ").strip() or d))
    if RICH: con.print(Panel.fit(f"Kv2m v{APP_VERSION} — kian_v2ray",style="bold cyan"))
    else: print(f"Kv2m v{APP_VERSION}")
    host=_ask("آی‌پی سرور"); port=_ask_int("پورت SSH",22); user=_ask("کاربری","root")
    import getpass; pwd=getpass.getpass("رمز: ") if not RICH else __import__("rich.prompt",fromlist=["Prompt"]).Prompt.ask("رمز",password=True)
    try: ssh=SSH().connect(host,port,user,password=pwd); _say("✔ متصل")
    except Exception as e: _say(f"✘ {e}"); return 1
    MENU=[("status",lambda:_say(ssh.run(cmd_status())[1])),
          ("users",lambda:_say(ssh.run(cmd_users())[1])),
          ("configs",lambda:_say(ssh.run(cmd_configs(_ask("نام","")))[1])),
          ("add",lambda:_say(ssh.run(cmd_add(_ask("نام"),_ask_int("GB",100),_ask_int("روز",30)))[1])),
          ("renew",lambda:_say(ssh.run(cmd_renew(_ask("نام"),_ask_int("روز",30)))[1])),
          ("reset",lambda:_say(ssh.run(cmd_reset(_ask("نام"),_ask_int("GB",100)))[1])),
          ("remove",lambda:_say(ssh.run(cmd_remove(_ask("نام")))[1])),]
    try:
        while True:
            _say("\n"+"─"*36)
            for i,(l,_) in enumerate(MENU,1): _say(f"  {i}) {l}")
            _say("  0) خروج")
            c=_ask("انتخاب","0")
            if c=="0": break
            try: MENU[int(c)-1][1]()
            except Exception as e: _say(f"خطا: {e}")
    finally: ssh.close(); _say("خداحافظ")
    return 0

# ══════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════
def main():
    if "--cli" in sys.argv or "-c" in sys.argv: return _run_cli()
    try:
        import customtkinter; return _run_gui()
    except ImportError:
        print("نصب: pip install customtkinter paramiko cryptography qrcode[pil]")
        return _run_cli()

if __name__=="__main__":
    sys.exit(main() or 0)
