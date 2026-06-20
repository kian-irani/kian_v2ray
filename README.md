<div align="center">

# ⚡ KIAN ⟶ V2RAY

**Build your own V2Ray server config in one minute — Reality · WARP · Shadowsocks · domain TLS — with a single command.**
**سازندهٔ کانفیگ V2Ray روی سرور خودت — با یک دستور.**

[![Latest release](https://img.shields.io/github/v/release/kian-irani/kian_v2ray?style=for-the-badge&logo=github&color=76B900&label=release)](https://github.com/kian-irani/kian_v2ray/releases/latest)
[![Site](https://img.shields.io/badge/Live-kianirani.github.io-1f6feb?style=for-the-badge)](https://kian-irani.github.io/kian_v2ray/)
[![License](https://img.shields.io/github/license/kian-irani/kian_v2ray?style=for-the-badge&color=e3b341)](LICENSE)
[![Xray](https://img.shields.io/badge/Xray--core-REALITY-76B900?style=for-the-badge&logo=v&logoColor=white)](https://github.com/XTLS/Xray-core)

[🌐 Web generator](https://kian-irani.github.io/kian_v2ray/) ·
[💻 Download Kv2m](https://github.com/kian-irani/kian_v2ray/releases/latest) ·
[📢 Channel](https://t.me/kian_irani_cdn_f) ·
[💬 Support](https://t.me/Kian_irani_t)

**[English](#english) · [فارسی](#فارسی)**

</div>

---

<a id="english"></a>

## What is it?

A **free, open-source** tool to build a V2Ray service on **your own server** (a personal VPS). No central server, no dependency, no monthly subscription. You enter your server IP, get one **install command**, run it over SSH, and receive ready configs plus an **HTTPS Subscription link**.

> **The advantage that can't be copied:** your private keys (X25519 / UUID) are generated **in your own browser** and are **never sent to any server** — not even ours (we have none).

## Features

| Feature | Description |
|---|---|
| **VLESS Reality + Vision** | Default mode — works without a domain, multiple auto SNI |
| **WARP outbound** | Bypass server-side egress blocks (WireGuard/MASQUE + auto-fallback to direct) |
| **Shadowsocks** | Backup / no-SNI mode (chacha20-ietf-poly1305) |
| **Domain TLS** | VLESS/VMess/Trojan over WS/gRPC/HTTPUpgrade behind Caddy on :443 (auto Let's Encrypt) |
| **HTTPS Subscription** | Deterministic link on `gist.githubusercontent.com` via a Cloudflare Worker — works on any provider |
| **Multi-user** | Per-user UUID + sub token + name |
| **Quota & expiry** | Per-user data quota and expiry date; watchdog every 10 min |
| **BBR + tuning** | Safe, idempotent network optimization at install |
| **Self-diagnosing status** | `kian-v2ray status` (or `health` / `doctor`) detects crashloop / WARP / port / SS issues and prints the exact fix command |

## Quick start

1. Get an **Ubuntu** VPS (any provider).
2. Open the [web generator](https://kian-irani.github.io/kian_v2ray/) or the **Kv2m** app.
3. Enter your server IP (+ a username).
4. Paste the install command into your server's SSH (or hit "run on server" in Kv2m).
5. Import the **Subscription** link into v2rayNG (Android) or v2rayN (Windows).

## Server commands

```bash
kian-v2ray status              # service status + self-diagnosis (alias: health, doctor)
kian-v2ray configs             # all users' configs
kian-v2ray sub <name>          # one user's Subscription link
kian-v2ray users               # users + quota
kian-v2ray add <name> [GB] [days]
kian-v2ray remove <name>
kian-v2ray renew <name> [days]
kian-v2ray reset <name> [GB]
kian-v2ray update              # update Xray
kian-v2ray uninstall           # full removal
```

## 💻 Kv2m desktop app (v3.0)

A modern **PySide6/Qt** UI (Termius-style + NVIDIA green), **bilingual** (EN/FA). It SSHes into your server to install, generate configs (Reality/WARP/SS/TLS), manage users, render QR, and produce the HTTPS Subscription link. Windows installer + portable builds are on the [releases page](https://github.com/kian-irani/kian_v2ray/releases/latest).

## Supported protocols

**No domain (Reality):** VLESS + Reality + Vision (TCP) · Shadowsocks
**With domain (TLS):** VLESS-WS · VMess-WS · VLESS-gRPC · VMess-gRPC · Trojan-WS · VLESS-HTTPUpgrade · VMess-HTTPUpgrade

## 🗺️ Roadmap

From a one-command installer to a full multi-server VPN platform. Detailed plan: [`ROADMAP.md`](ROADMAP.md).

- ✅ **Now** — Reality/WARP/SS/TLS installer · HTTPS Subscription · multi-user · Kv2m desktop · self-diagnosing `status` · in-browser keys.
- 🟠 **Next** — structured logging · pytest · IPv6 · automated backup.
- 🔭 **Coming** — **multi-server management** (one panel, many VPS; health/failover/geo-routing) · **full web panel** (FastAPI + JWT, IP/speed/HWID limits) · **Flutter mobile app** (Cafe Bazaar → Myket → F-Droid → Play) · **new protocols** (Hysteria2, TUIC v5, WireGuard, Fragment/uTLS) · **monitoring** (Prometheus + Grafana, audit log).

## Security & privacy

- **No secret ever lives on our servers** — keys are generated in your browser/device and only land on **your** server.
- The **Gist token** lives only in the Cloudflare Worker (secret); never visible on the page or the user's server.
- The Worker isolates users with a random 128-bit `install_id`. The repo is public — the code is auditable.
- See the [Privacy Policy](privacy.html) and [Terms of Service](terms.html).

## Contributing & license

Issues and suggestions welcome — open an issue or write in the [channel](https://t.me/kian_irani_cdn_f). License: **MIT**.

---

<a id="فارسی"></a>

## 🇮🇷 فارسی

ابزار **متن‌باز و رایگان** برای ساخت کانفیگ V2Ray روی **سرور خودت** (VPS شخصی). هیچ سرور مرکزی، هیچ وابستگی، هیچ اشتراک ماهانه. IP سرورت را می‌دهی، یک **دستور نصب** می‌گیری، روی سرور می‌زنی، و کانفیگ‌های آماده + **لینک Subscription روی HTTPS** تحویل می‌گیری.

> **مزیتِ غیرقابلِ‌کپی:** کلیدهای خصوصی (X25519/UUID) **در مرورگرِ خودت** ساخته می‌شوند و **هرگز به هیچ سروری نمی‌رسند** — حتی به ما (که اصلاً سروری نداریم).

### چه چیزهایی دارد؟

| ویژگی | توضیح |
|------|------|
| **VLESS Reality + Vision** | حالت پیش‌فرض — بدون دامنه کار می‌کند، چند SNI خودکار |
| **WARP outbound** | دور زدن بلاک‌های خروجی سرور (WireGuard/MASQUE + بازگشت خودکار به direct) |
| **Shadowsocks** | پشتیبان یا حالت بدون SNI (chacha20-ietf-poly1305) |
| **TLS با دامنه** | VLESS/VMess/Trojan روی WS/gRPC/HTTPUpgrade پشت Caddy روی :443 (+ گواهی خودکار) |
| **Subscription روی HTTPS** | لینک قطعی روی `gist.githubusercontent.com` از طریق Cloudflare Worker — روی هر پروایدری |
| **مدیریت چند کاربر** | هر کاربر UUID + توکن sub + نام |
| **حجم و انقضا** | سهمیه و تاریخ انقضا برای هر کاربر، watchdog هر ۱۰ دقیقه |
| **خودتشخیصیِ status** | `kian-v2ray status` (یا `health`/`doctor`): تشخیصِ کرش‌لوپ/WARP/پورت/SS + چاپِ دستورِ رفع |

### شروع سریع

۱. سرور **Ubuntu** بگیر · ۲. برو به [صفحهٔ تعاملی](https://kian-irani.github.io/kian_v2ray/) یا **Kv2m** · ۳. IP سرور (+ نام) را وارد کن · ۴. دستور نصب را در SSH بزن · ۵. لینک **Subscription** را در v2rayNG/v2rayN وارد کن.

### دستورهای مدیر روی سرور

```bash
kian-v2ray status      # وضعیت + خودتشخیصی (alias: health, doctor)
kian-v2ray configs     # کانفیگ همهٔ کاربران
kian-v2ray add <نام> [GB] [روز]   # افزودن کاربر
kian-v2ray users       # لیست کاربران + سهمیه
kian-v2ray update      # آپدیت Xray  ·  kian-v2ray uninstall  # حذف کامل
```

### 🗺️ نقشهٔ راه

از یک نصب‌کنندهٔ تک‌دستوری به یک **پلتفرمِ کاملِ VPN چندسروره**. جزئیات: [`ROADMAP.md`](ROADMAP.md).

- ✅ **اکنون** — نصب‌کنندهٔ Reality/WARP/SS/TLS · Subscription روی HTTPS · چندکاربره · Kv2m دسکتاپ · `status`ِ خودتشخیص · کلید در مرورگر.
- 🟠 **بعدی** — لاگِ ساختاریافته · pytest · IPv6 · بکاپِ خودکار.
- 🔭 **در دست ساخت** — **مدیریتِ چندسرور** (یک پنل، چند VPS) · **پنلِ وبِ کامل** (FastAPI + JWT، محدودیتِ IP/سرعت/HWID) · **اپِ موبایلِ Flutter** (کافه‌بازار → مایکت → F-Droid → پلی) · **پروتکل‌های جدید** (Hysteria2، TUIC v5، WireGuard) · **پایش** (Prometheus + Grafana).

### امنیت و حریم خصوصی

هیچ راز روی سرور ما نیست — کلیدها در دستگاهِ تو ساخته می‌شوند. توکنِ Gist فقط در Cloudflare Worker (secret) است. ریپو پابلیک و قابل‌بازبینی. → [سیاست حریم خصوصی](privacy.html) · [شرایط استفاده](terms.html). لایسنس: **MIT**.

> ℹ️ کانفیگ‌های دامنه/CDN خروجی را از **IP سرورِ تو** می‌فرستند؛ Cloudflare فقط مسیر ورودی را پنهان می‌کند. برای گرفتن گواهی TLS موقع نصب، ابر Cloudflare باید خاکستری (DNS-only) باشد؛ بعد می‌توانی نارنجی کنی.

<div align="center">

Built with ❤️ by **[Kian Irani](https://github.com/kian-irani)** for a free and open internet · ساخته‌شده برای دسترسی آزاد به اینترنت

</div>
