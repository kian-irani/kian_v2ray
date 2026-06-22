#!/usr/bin/env python3
"""kv2m i18n — English base + Persian translation. Standalone (no Qt)."""
import json, os, sys

def _cfg_dir():
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, "kv2m")
    try: os.makedirs(d, exist_ok=True)
    except Exception: pass
    return d

SETTINGS_PATH = os.path.join(_cfg_dir(), "settings.json")

def load_settings():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {}

def save_settings(s):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f: json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception: pass

STRINGS = {
 "en": {
  "app.title":"Kv2m — Kian V2Ray Manager",
  "lang.pick.title":"Choose language","lang.pick.en":"English","lang.pick.fa":"فارسی",
  "nav.generate":"Generate","nav.install":"Install","nav.manage":"Manage","nav.settings":"Settings","nav.about":"About",
  "conn.host":"Host / IP","conn.user":"User","conn.pass":"Password","conn.port":"Port",
  "conn.connect":"Connect SSH","conn.disconnect":"Disconnect","conn.connected":"Connected","conn.disconnected":"Disconnected","conn.connecting":"Connecting…",
  "gen.title":"Generate config & install command","gen.serverip":"Server IP","gen.mode":"Mode","gen.users":"Users","gen.prefix":"User prefix",
  "gen.quota":"Quota (GB, 0=unlimited)","gen.days":"Days (0=permanent)","gen.advanced":"Advanced settings",
  "gen.snimode":"SNI mode","gen.snicount":"SNI count","gen.snimanual":"Manual domain","gen.snicustom":"Custom domain",
  "gen.ss":"Add Shadowsocks","gen.ssport":"Shadowsocks port","gen.baseport":"Base port (optional)",
  "gen.tls":"Domain configs (TLS — needs a domain + A record)","gen.domain":"Domain","gen.channel":"Channel","gen.protocols":"Protocols",
  "gen.extra":"Extra protocols (UDP — Hysteria2 / TUIC, on sing-box, added to subscription)",
  "gen.button":"Generate","gen.hint":"Enter your server IP and click Generate. The install command and links appear below.",
  "gen.installcmd":"Install command","gen.copy":"Copy","gen.runserver":"Run on server","gen.copyall":"Copy all links","gen.user":"User","gen.sublink":"Subscription link",
  "mode.both":"Fast + WARP","mode.direct":"Fast (direct)","mode.warp":"WARP (everything open)","mode.nosni":"No SNI (Shadowsocks)",
  "ch.direct":"Fast","ch.warp":"WARP",
  "manage.title":"User management — no command to memorize","manage.action":"What do you want to do?","manage.name":"User name","manage.run":"Run this on the server:",
  "manage.panelpass":"Panel password (empty = random)",
  "settings.title":"Settings","settings.language":"Language","settings.theme":"Theme","settings.about":"About",
  "about.title":"About","about.desc":"KIAN V2Ray — free & open-source. Builds V2Ray configs on your own server. Keys are generated locally and never stored.",
  "toast.copied":"Copied","toast.noip":"Enter the server IP.","toast.connected":"Connected","toast.err":"Error",
  "tray.show":"Show Kv2m","tray.quit":"Quit","tray.hidden":"Kv2m is still running in the tray.",
  "common.min":"Minimize","common.close":"Close",
  "sni.mode":"SNI mode","sni.auto":"Auto","sni.manual":"Manual","sni.count":"SNI count","sni.custom":"SNI domain (optional)",
  "ch.both":"Fast + WARP",
  "gen.tlshelp":"Domain configs (WS/gRPC/Trojan) look like normal HTTPS — best for hard filtering. Needs a domain with an A record to your server. Keep Cloudflare cloud GREY (DNS-only) during install so Caddy can get a TLS certificate; turn it orange afterward.",
  "set.section.general":"General","set.section.paths":"Paths & info","set.config":"Server config","set.langhint":"Choose the app language (applies live).",
  "set.channels":"Channels","about.features":"Features","about.donate":"Support (optional)","about.tip":"Tip: domain/CDN configs exit from YOUR server IP — Cloudflare only hides the inbound path.",
  "nav.connectfirst":"Connect to your server (top bar) before Run-on-server actions.",
 },
 "fa": {
  "app.title":"Kv2m — مدیریت Kian V2Ray",
  "lang.pick.title":"زبان را انتخاب کن","lang.pick.en":"English","lang.pick.fa":"فارسی",
  "nav.generate":"ساخت کانفیگ","nav.install":"نصب روی سرور","nav.manage":"مدیریت","nav.settings":"تنظیمات","nav.about":"درباره",
  "conn.host":"هاست / آی‌پی","conn.user":"کاربر","conn.pass":"رمز عبور","conn.port":"پورت",
  "conn.connect":"اتصال SSH","conn.disconnect":"قطع","conn.connected":"متصل","conn.disconnected":"قطع","conn.connecting":"در حال اتصال…",
  "gen.title":"ساخت کانفیگ و دستور نصب","gen.serverip":"آی‌پی سرور","gen.mode":"حالت","gen.users":"تعداد کاربر","gen.prefix":"پیشوند نام",
  "gen.quota":"حجم (گیگ، ۰=نامحدود)","gen.days":"مدت (روز، ۰=دائمی)","gen.advanced":"تنظیمات پیشرفته",
  "gen.snimode":"حالت SNI","gen.snicount":"تعداد SNI","gen.snimanual":"دامنه دستی","gen.snicustom":"دامنه دلخواه",
  "gen.ss":"Shadowsocks هم اضافه کن","gen.ssport":"پورت Shadowsocks","gen.baseport":"پورت پایه (اختیاری)",
  "gen.tls":"کانفیگ‌های دامنه‌دار (TLS — نیاز به دامنه + رکورد A)","gen.domain":"دامنه","gen.channel":"کانال","gen.protocols":"پروتکل‌ها",
  "gen.extra":"پروتکل‌های اضافه (UDP — Hysteria2 / TUIC، روی sing-box، به Subscription اضافه می‌شود)",
  "gen.button":"⚡ ساخت کانفیگ","gen.hint":"آی‌پی سرور را وارد کن و بزن ساخت. دستور نصب و لینک‌ها پایین ظاهر می‌شود.",
  "gen.installcmd":"دستور نصب","gen.copy":"کپی","gen.runserver":"اجرا روی سرور","gen.copyall":"کپی همه لینک‌ها","gen.user":"کاربر","gen.sublink":"لینک Subscription",
  "mode.both":"سریع + WARP","mode.direct":"سریع (مستقیم)","mode.warp":"WARP (همه‌چیز باز)","mode.nosni":"بدون SNI (Shadowsocks)",
  "ch.direct":"سریع","ch.warp":"WARP",
  "manage.title":"مدیریت کاربر — بدون حفظ‌کردن دستور","manage.action":"چه کاری می‌خوای بکنی؟","manage.name":"نام کاربر","manage.run":"این را در ترمینال سرور بزن:",
  "manage.panelpass":"رمزِ پنل (خالی = تصادفی)",
  "settings.title":"تنظیمات","settings.language":"زبان","settings.theme":"تم","settings.about":"درباره",
  "about.title":"درباره","about.desc":"KIAN V2Ray رایگان و متن‌باز است. روی سرور خودت کانفیگ V2Ray می‌سازد. کلیدها در دستگاه تو ساخته می‌شوند و هیچ‌جا ذخیره نمی‌شوند.",
  "toast.copied":"کپی شد","toast.noip":"آی‌پی سرور را وارد کن.","toast.connected":"متصل شد","toast.err":"خطا",
  "tray.show":"نمایشِ Kv2m","tray.quit":"خروج","tray.hidden":"Kv2m هنوز در tray در حال اجراست.",
  "common.min":"کوچک کردن","common.close":"بستن",
  "sni.mode":"حالت SNI","sni.auto":"خودکار","sni.manual":"دستی","sni.count":"تعداد SNI","sni.custom":"دامنهٔ SNI (اختیاری)",
  "ch.both":"سریع + WARP",
  "gen.tlshelp":"کانفیگ‌های دامنه‌دار (WS/gRPC/Trojan) شبیه HTTPS معمولی‌اند — بهترین گزینه در فیلترینگ شدید. نیاز به یک دامنه با رکورد A به سرورت دارند. موقع نصب ابر Cloudflare را خاکستری (DNS-only) نگه دار تا Caddy گواهی TLS بگیرد؛ بعد نارنجی کن.",
  "set.section.general":"عمومی","set.section.paths":"مسیرها و اطلاعات","set.config":"کانفیگ سرور","set.langhint":"زبان نرم‌افزار را انتخاب کن (زنده اعمال می‌شود).",
  "set.channels":"کانال‌ها","about.features":"امکانات","about.donate":"حمایت (اختیاری)","about.tip":"نکته: کانفیگ‌های دامنه/CDN خروجی را از IP سرورِ خودت می‌فرستند — Cloudflare فقط مسیر ورودی را پنهان می‌کند.",
  "nav.connectfirst":"قبل از «اجرا روی سرور» از نوار بالا به سرورت وصل شو.",
 },
}

_state = {"lang": "en"}

def set_lang(code):
    _state["lang"] = code if code in STRINGS else "en"

def get_lang():
    return _state["lang"]

def is_rtl():
    return _state["lang"] == "fa"

def tr(key):
    lang = _state["lang"]
    return STRINGS.get(lang, {}).get(key) or STRINGS["en"].get(key) or key
