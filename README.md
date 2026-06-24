<div align="center">

# ⚡ KIAN ⟶ V2RAY

**A privacy-first, open-source anti-censorship platform — from a one-command installer to a full multi-server VPN stack with a web panel, mobile & desktop apps, new protocols and monitoring.**
**از نصب‌کنندهٔ تک‌دستوری تا پلتفرمِ کاملِ VPN چندسروره — با پنلِ وب، اپِ موبایل/دسکتاپ، پروتکل‌های جدید و پایش.**

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

A **free, open-source** stack to run your own anti-censorship VPN on **your own server(s)**. No central server, no subscription. At its core: you enter your server IP, get one **install command**, run it over SSH, and receive ready configs + an **HTTPS Subscription link**. Around that core there's now a **web panel**, **multi-server management**, **desktop & mobile apps**, **new UDP protocols**, and **monitoring**.

> **The advantage that can't be copied:** your private keys (X25519 / UUID) are generated **in your own browser/device** and are **never sent to any server** — not even ours (we have none).

## 🧩 Platform components

| Component | What it is | Status |
|---|---|---|
| **Installer + CLI** | One-command Reality/WARP/SS/TLS install; `kian-v2ray` management CLI with self-diagnosis | ✅ stable |
| **Web generator** | In-browser config builder, 100% bilingual (FA/EN), client-side keys | ✅ stable |
| **Web panel** (`panel/`) | FastAPI + JWT/2FA · dark-glass dashboard (users/nodes/audit/charts/settings) · IP/speed/HWID limits · WebSocket stats · `/metrics` | ✅ code-complete |
| **Multi-server** (`core/cluster.py` + `node-agent/`) | One panel → many VPS · health/failover/load-balance/GeoIP · Marzban/3X-UI import | ✅ code-complete |
| **New protocols** (`scripts/kian-protocols.sh` + `core/protocols.py`) | **Hysteria2 + TUIC v5 + AnyTLS + ShadowTLS v3** via a sing-box companion (opt-in, **per-user**, layer-guarded, auto port-resolve) · Fragment/uTLS/TTL/Noise anti-DPI · **Reality spiderX** · sing-box/Clash sub export · REALITY SNI scanner · Tor fallback · SSH-out/ECH builders | ✅ code · ⏳ server test |
| **Kv2m desktop** (`kv2m/`) | PySide6/Qt app, **multi-server**, web-panel deploy, **Hysteria2/TUIC** generator, auto-update — Windows/macOS/Linux | ✅ **v3.6.0** |
| **Kv2m mobile** (`app/`) | Flutter Android client — **on-device tunnel** (bundled Xray core), in-app SSH install, config **QR + copy**, **install history**, **per-app split-tunnel**, routing/DNS/kill-switch settings, web-panel deploy, GMS-free, offline mode | ✅ **v0.5.0** |
| **Monitoring** (`monitoring/`) | Prometheus + node/Xray exporters + Grafana dashboard + alert rules | ✅ configs |
| **Notifications** (`core/notify.py`) | Telegram + Email(SMTP) + Webhook · server-side expiry/quota push (no FCM) | ✅ code-complete |
| **CI/CD** | Validate (bash/js/py/pytest/smoke) + CodeQL + Trivy + auto-release | ✅ green |

## ⬇️ Downloads

All builds are on the **[latest release](https://github.com/kian-irani/kian_v2ray/releases/latest)** page (CI-built on every version tag).

| Platform | File | For whom |
|---|---|---|
| 🪟 **Windows — Setup** | `Kv2m-Setup-x64.exe` | Full install (Start Menu + Desktop shortcut). No Python needed. |
| 🪟 **Windows — Portable** | `Kv2m-Portable-x64.exe` | Run directly, no install. |
| 🍏 **macOS** | `Kv2m-macOS.zip` | `Kv2m.app` (right-click → Open the first time). |
| 🐧 **Linux** | `Kv2m-Linux-x86_64` | Self-contained binary (`chmod +x`). |
| 🤖 **Android — Universal** | `Kv2m-*-universal.apk` | **Works on every phone** — the safe choice. |
| 🤖 **Android — 64-bit** | `Kv2m-*-arm64.apk` | New phones (arm64-v8a) — smaller download. |
| 🤖 **Android — 32-bit** | `Kv2m-*-arm32.apk` | Very old phones (armeabi-v7a). |
| 🌐 **No install** | [Web generator](https://kian-irani.github.io/kian_v2ray/) | Build configs right in the browser. |

> **Android now connects on its own** — the native tunnel core (Xray via `flutter_v2ray`) is bundled, no v2rayNG needed. The web generator, desktop apps (Windows/macOS/Linux) and installer are production-ready.

## Quick start (the installer)

1. Get an **Ubuntu** VPS (any provider).
2. Open the [web generator](https://kian-irani.github.io/kian_v2ray/) or the **Kv2m** app.
3. Enter your server IP (+ a username).
4. Paste the install command into your server's SSH (or hit "run on server" in Kv2m).
5. Import the **Subscription** link into a client. **Recommended: Kv2m (this project) or [Hiddify](https://github.com/hiddify/hiddify-app)** — they support **every** protocol we generate on one link (Reality, Hysteria2, TUIC, AnyTLS, ShadowTLS). v2rayNG / v2rayN read the same link too (they just skip the UDP-based ones). One link works everywhere.

### Server commands

```bash
kian-v2ray status              # service status + self-diagnosis (alias: health, doctor)
kian-v2ray configs             # all users' configs
kian-v2ray sub <name>          # one user's Subscription link
kian-v2ray users               # users + quota
kian-v2ray add <name> [GB] [days]
kian-v2ray protocols enable    # add Hysteria2 + TUIC (sing-box companion, opt-in)
kian-v2ray update              # update Xray
kian-v2ray uninstall           # full removal
```

## 🖥️ Web panel

A **FastAPI** backend reusing the installer's SQLite schema (one source of truth) + a **dark-glass dashboard** (`panel/web/`).

```bash
python3 -m pip install -r panel/requirements.txt
export KIAN_ADMIN_PASSWORD='change-me-strong'
uvicorn panel.main:app --host 0.0.0.0 --port 8443     # open /app  ·  Swagger at /docs
```

Features: JWT + refresh + **TOTP 2FA** (with UI) · user CRUD + search + **bulk actions** · per-user **IP / speed / HWID** limits + **auto-disable** · **per-user routing / DNS** · WebSocket live stats · CSV/JSON export · **audit log** · **node management** (health/route/failover) · key rotation · security headers + rate-limit + CORS · `/metrics` for Prometheus. One-click stack: `docker compose up -d`.

## Supported protocols

**No domain (Reality):** VLESS + Reality + Vision (TCP), with **spiderX** · Shadowsocks
**With domain (TLS):** VLESS-WS · VMess-WS · VLESS-gRPC · VMess-gRPC · Trojan-WS · VLESS-HTTPUpgrade · VMess-HTTPUpgrade · **VLESS-XHTTP**
**Opt-in companion (sing-box):** **Hysteria2** · **TUIC v5** · **AnyTLS** · **ShadowTLS v3** — each generated **per-user** on its own port (Hy2 8443/udp · TUIC 8444/udp · AnyTLS 8446/tcp · ShadowTLS 8447/tcp, auto-moved if busy), additive and **layer-guarded**: a sing-box build that rejects a newer layer silently drops just that one and keeps the rest, so the working protocols never break · WireGuard / SSH-out builders in `core/protocols.py`
**Routing:** every config egresses through **Cloudflare WARP** (with automatic direct-fallback so you never go offline) — no "fast/direct" mode to misconfigure.
**Anti-DPI:** Fragment (TLS-Hello split, on by default, toggle in the app) · uTLS fingerprint · TTL · Noise padding · ECH plumbing · Tor bridge fallback

## 💻 Kv2m apps

- **Desktop v3.6.0** — PySide6/Qt, bilingual, **multi-server** (saved profiles, auto-update), **web-panel deploy** over SSH, and the **Hysteria2/TUIC** generator. Windows (Setup + Portable), macOS and Linux builds on [releases](https://github.com/kian-irani/kian_v2ray/releases/latest).
- **Mobile (Kv2m v0.5.0, Flutter)** — Android-first, **GMS-free** (Cafe Bazaar / Myket / F-Droid friendly). **Connects on its own** via a bundled native Xray core (`flutter_v2ray`) — no v2rayNG needed. In-app SSH install + **config QR & one-tap copy** + **subscription card** (auto-refresh) + **install history** + **web-panel deploy** + **per-app split-tunnel** + routing / DNS / kill-switch / auto-connect settings + smart server selection + offline mode.

> **Connect from your phone:** the Kv2m app **builds, installs, manages and tunnels** everything itself. On a dev/desktop build without the native core it stays honest (it won't black-hole your traffic) and offers to copy the config for v2rayNG instead.

## 🗺️ Roadmap

From a one-command installer to a full multi-server VPN platform. Full plan & status: [`ROADMAP.md`](ROADMAP.md).

- ✅ **Done** — Phases 1–7: core infra, web panel + 2FA, multi-server cluster + node agent, new protocols (Hysteria2/TUIC), on-device tunnel, desktop on Windows/macOS/Linux + system tray, Terraform/IaC, Loki logs, opt-in analytics, reproducible-build & translation docs, 100% bilingual site, CI/CD + monitoring.
- 🙋 **Only the commercial phase is left (needs you)** — market developer accounts (Google Play / Cafe Bazaar / Myket / F-Droid), a signing **Keystore**, store screenshots & submissions, and turning on GitHub Discussions. These all require your accounts/identity — see [`ROADMAP.md`](ROADMAP.md) §4.

## Security & privacy

- **No secret ever lives on our servers** — keys are generated in your browser/device and only land on **your** server.
- The **Gist token** lives only in the Cloudflare Worker (secret); never on the page or the user's server.
- Public repo, auditable code. CI runs a secret-scan + CodeQL + Trivy on every push.
- See the [Privacy Policy](privacy.html) and [Terms of Service](terms.html).

## 📚 Documentation & project map

Everything in the repo, indexed in one place:

| Area | Document | What's inside |
|---|---|---|
| 🚀 **Start here** | [Web generator](https://kian-irani.github.io/kian_v2ray/) · [Quick start](#quick-start-the-installer) | Build configs & install in minutes |
| 🔌 **Connectivity** | [`docs/connect-now.md`](docs/connect-now.md) | Which servers the direct-IP method works on, and when to use a domain |
| 🔄 **Migrating in** | [`docs/MIGRATION.md`](docs/MIGRATION.md) | Import users from **Marzban / 3X-UI** |
| 🗺️ **Roadmap** | [`ROADMAP.md`](ROADMAP.md) · [legacy](ROADMAP-legacy.md) | Phase plan & current status |
| 📋 **Product spec** | [`docs/PRD.md`](docs/PRD.md) · [`PRD-V2.md`](PRD-V2.md) | Product requirements (v1 + feature-parity v2) |
| ✅ **Task plan** | [`PLAN.md`](PLAN.md) | Task-level breakdown & ✅/⬜ status |
| 🔐 **Security** | [`SECURITY.md`](SECURITY.md) · [Privacy](privacy.html) · [Terms](terms.html) | Threat model, secret-free repo policy, legal |
| 🌍 **Translations** | [`docs/TRANSLATIONS.md`](docs/TRANSLATIONS.md) | Add a language (single flat key→string map) |
| 🏷️ **Versioning** | [`docs/VERSIONING.md`](docs/VERSIONING.md) · [`CHANGELOG.md`](CHANGELOG.md) | SemVer scheme + release history |
| 🔁 **Reproducible builds** | [`docs/REPRODUCIBLE-BUILDS.md`](docs/REPRODUCIBLE-BUILDS.md) | Verify release artifacts from a tagged commit |
| 🤝 **Contributing** | [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) | How to contribute, code style, PR flow |
| 📊 **Monitoring** | [`monitoring/`](monitoring/) | Prometheus + Loki + Grafana dashboard & alerts |
| ☁️ **Deploy / IaC** | [`deploy/terraform/`](deploy/terraform/) · [`docker-compose.yml`](docker-compose.yml) | One-command stack + Terraform VPS provisioning |

### Repository layout

```
install.sh           one-command server installer (Reality/WARP/SS/TLS)
index.html           in-browser config generator (client-side keys)
scripts/             kian-v2ray CLI · kian-protocols.sh (Hy2/TUIC) · watchdog · backup · bot
core/                shared lib: db · cluster · protocols · notify · audit · analytics · censorship
panel/               FastAPI web panel (main/bridge/repo/security) + dark-glass UI (web/)
app/                 Flutter Android client (Kv2m) — on-device tunnel
kv2m/                PySide6/Qt desktop app (Kv2m)
node-agent/          lightweight per-VPS health/metrics agent
monitoring/          Prometheus · Loki · Grafana · alert rules
deploy/              Terraform / IaC
docs/                guides (migration, translations, versioning, reproducible builds, …)
```

## Contributing & license

Issues and suggestions welcome — see [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md), open an issue, or write in the [channel](https://t.me/kian_irani_cdn_f). License: **MIT**.

---

<a id="فارسی"></a>

## 🇮🇷 فارسی

پلتفرمِ **متن‌باز و رایگانِ** ضدسانسور برای اجرای VPN روی **سرور(های) خودت**. هیچ سرور مرکزی، هیچ اشتراک. هسته: IP سرورت را می‌دهی، یک **دستور نصب** می‌گیری، روی سرور می‌زنی، و کانفیگِ آماده + **لینک Subscription روی HTTPS** می‌گیری. حالا دورِ این هسته یک **پنلِ وب**، **مدیریتِ چندسرور**، **اپِ موبایل/دسکتاپ**، **پروتکل‌های جدید** و **پایش** هم هست.

> **مزیتِ غیرقابلِ‌کپی:** کلیدهای خصوصی **در مرورگر/دستگاهِ خودت** ساخته می‌شوند و **هرگز به هیچ سروری نمی‌رسند** — حتی به ما (که اصلاً سروری نداریم).

### 🧩 اجزای پلتفرم

| جزء | چیست | وضعیت |
|---|---|---|
| **نصب‌کننده + CLI** | نصبِ تک‌دستوریِ Reality/WARP/SS/TLS + CLIِ `kian-v2ray` با خودتشخیصی | ✅ پایدار |
| **صفحهٔ تعاملی** | سازندهٔ کانفیگ در مرورگر، **۱۰۰٪ دوزبانه**، کلید سمتِ کاربر | ✅ پایدار |
| **پنلِ وب** | FastAPI + JWT/**2FA** · داشبوردِ dark-glass (کاربران/سرورها/ممیزی/نمودار/تنظیمات) · محدودیتِ IP/سرعت/HWID · آمارِ زنده | ✅ کد کامل |
| **چندسرور** | یک پنل → چند VPS · health/failover/load-balance/GeoIP · مهاجرت از Marzban/3X-UI | ✅ کد کامل |
| **پروتکل‌های جدید** | **Hysteria2 + TUIC v5 + AnyTLS + ShadowTLS v3** روی sing-box (اختیاری، per-user، گارد‌دار، انتخابِ خودکارِ پورت) · ضدِDPI: Fragment/uTLS/TTL/Noise · **Reality spiderX** · خروجیِ sing-box/Clash · REALITY scanner · Tor fallback | ✅ کد · ⏳ تستِ سرور |
| **Kv2m دسکتاپ** | اپِ PySide6/Qt، **چندسرور**، راه‌اندازیِ پنل، سازندهٔ **Hysteria2/TUIC**، auto-update — ویندوز/مک/لینوکس | ✅ **v3.6.0** |
| **Kv2m موبایل** | کلاینتِ Flutter اندروید — **اتصالِ روی‌دستگاه** (هستهٔ Xray bundle‌شده)، نصبِ SSH داخلِ اپ، **QR و کپیِ کانفیگ**، **تاریخچهٔ نصب**، **split-tunnel per-app**، تنظیماتِ routing/DNS/kill-switch، بدونِ GMS، آفلاین | ✅ **v0.5.0** |
| **پایش** | Prometheus + اکسپورترها + داشبوردِ Grafana + قوانینِ هشدار | ✅ پیکربندی |
| **اعلان‌ها** | Telegram + Email + Webhook · Push انقضا/سهمیه (بدونِ FCM) | ✅ کد کامل |

### ⬇️ دانلود

همهٔ نسخه‌ها در [صفحهٔ آخرین ریلیز](https://github.com/kian-irani/kian_v2ray/releases/latest):

| پلتفرم | فایل | برای |
|---|---|---|
| 🪟 ویندوز — نصبی | `Kv2m-Setup-x64.exe` | نصبِ کامل (شورتکات) |
| 🪟 ویندوز — قابل‌حمل | `Kv2m-Portable-x64.exe` | بدونِ نصب |
| 🤖 اندروید — همه‌کاره | `Kv2m-*-universal.apk` | **هر گوشی** (مطمئن‌ترین) |
| 🤖 اندروید — ۶۴ بیتی | `Kv2m-*-arm64.apk` | گوشی‌های جدید |

### شروع سریع

۱. سرور **Ubuntu** بگیر · ۲. برو به [صفحهٔ تعاملی](https://kian-irani.github.io/kian_v2ray/) یا **Kv2m** · ۳. IP سرور (+ نام) · ۴. دستور نصب را در SSH بزن · ۵. لینک **Subscription** را در v2rayNG/v2rayN وارد کن.

```bash
kian-v2ray status                 # وضعیت + خودتشخیصی (alias: health, doctor)
kian-v2ray add <نام> [GB] [روز]   # افزودن کاربر
kian-v2ray protocols enable       # افزودنِ Hysteria2 + TUIC (sing-box، اختیاری)
kian-v2ray update | uninstall
```

### پنلِ وب

```bash
python3 -m pip install -r panel/requirements.txt
export KIAN_ADMIN_PASSWORD='یک-رمزِ-قوی'
uvicorn panel.main:app --host 0.0.0.0 --port 8443   # داشبورد: /app  ·  Swagger: /docs
```
ویژگی‌ها: JWT + **2FA** + CRUD + bulk + محدودیتِ IP/سرعت/HWID + auto-disable + **routing/DNS هر کاربر** + آمارِ زنده + export + **ممیزی** + **مدیریتِ نود** + چرخشِ کلید + هدرهای امنیتی. اجرای کامل: `docker compose up -d`.

### 🗺️ نقشهٔ راه

از نصب‌کنندهٔ تک‌دستوری به **پلتفرمِ کاملِ چندسروره**. جزئیات و وضعیت: [`ROADMAP.md`](ROADMAP.md).

- ✅ **انجام‌شده (در کد)** — فاز ۱ تا ۱۲: زیرساختِ core، پنلِ وب + 2FA + routing/DNSِ هر کاربر، چندسرور + node agent، پروتکل‌ها (Reality spiderX/XHTTP + builderهای ShadowTLS/AnyTLS/SSH/ECH)، اپِ موبایلِ خوداتصال + split-tunnel، **صفحهٔ ۱۰۰٪ دوزبانه (هر تب)**، CI/CD + پایش، اعلان‌ها.
- ⏳ **نیازِ سرورِ زنده** — تستِ واقعیِ end-to-end اتصالِ Hysteria2/TUIC/TLS روی VPS.
- 🙋 **نیازِ تو** — حساب‌های مارکت (گوگل‌پلی/کافه‌بازار/مایکت/F-Droid)، Keystore، انتشار.

### 📚 مستندات

| موضوع | فایل |
|---|---|
| 🔌 روشِ اتصالِ فعلی | [`docs/connect-now.md`](docs/connect-now.md) |
| 🔄 مهاجرت از Marzban/3X-UI | [`docs/MIGRATION.md`](docs/MIGRATION.md) |
| 🗺️ نقشهٔ راه | [`ROADMAP.md`](ROADMAP.md) |
| 📋 سندِ محصول | [`docs/PRD.md`](docs/PRD.md) · [`PRD-V2.md`](PRD-V2.md) |
| 🔐 امنیت | [`SECURITY.md`](SECURITY.md) · [حریم خصوصی](privacy.html) · [شرایط](terms.html) |
| 🌍 ترجمه | [`docs/TRANSLATIONS.md`](docs/TRANSLATIONS.md) |
| 🏷️ نسخه‌بندی | [`docs/VERSIONING.md`](docs/VERSIONING.md) · [`CHANGELOG.md`](CHANGELOG.md) |
| 🤝 مشارکت | [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) |
| 📊 پایش | [`monitoring/`](monitoring/) |

### امنیت و حریم خصوصی

هیچ راز روی سرور ما نیست — کلیدها در دستگاهِ تو ساخته می‌شوند. توکنِ Gist فقط در Cloudflare Worker (secret). ریپو پابلیک و قابل‌بازبینی؛ CI روی هر پوش secret-scan + CodeQL + Trivy می‌زند. → [حریم خصوصی](privacy.html) · [شرایط استفاده](terms.html). لایسنس: **MIT**.

> ℹ️ کانفیگ‌های دامنه/CDN خروجی را از **IP سرورِ تو** می‌فرستند؛ Cloudflare فقط مسیر ورودی را پنهان می‌کند. موقعِ نصب ابر باید خاکستری (DNS-only) باشد؛ بعد می‌توانی نارنجی کنی.

<div align="center">

Built with ❤️ by **[Kian Irani](https://github.com/kian-irani)** for a free and open internet · ساخته‌شده برای دسترسی آزاد به اینترنت

</div>
