<div align="center">

# ⚡ KIAN V2RAY

**پلتفرمِ ضدسانسورِ متن‌بازِ نسلِ بعدی — از نصبِ تک‌دستوری تا پلتفرمِ کاملِ VPN چندسروره**
**Next-generation open-source anti-censorship platform — from a one-command installer to a full multi-server VPN stack**

[![Latest release](https://img.shields.io/github/v/release/kian-irani/kian_v2ray?style=for-the-badge&logo=github&color=76B900&label=release)](https://github.com/kian-irani/kian_v2ray/releases/latest)
[![Site](https://img.shields.io/badge/Live-kianirani.github.io-1f6feb?style=for-the-badge)](https://kian-irani.github.io/kian_v2ray/)
[![License](https://img.shields.io/badge/license-MIT-e3b341?style=for-the-badge)](LICENSE)
[![Security](https://img.shields.io/badge/CI-CodeQL%20%2B%20Trivy-22C55E?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/kian-irani/kian_v2ray/actions)

[🌐 Web generator](https://kian-irani.github.io/kian_v2ray/) ·
[💻 Download Kv2m](https://github.com/kian-irani/kian_v2ray/releases/latest) ·
[📢 Telegram](https://t.me/kian_irani_cdn_f) ·
[💬 Support](https://t.me/Kian_irani_t)

**[English](#english) · [فارسی](#فارسی)**

</div>

---

<a id="english"></a>

## What is KIAN?

A **free, open-source** stack to run your own anti-censorship VPN on **your own server(s)** — no central server, no subscription, no tracking.

**How it works in 60 seconds:**
1. Open the [web generator](https://kian-irani.github.io/kian_v2ray/) or the **Kv2m** app
2. Enter your server IP + a username — keys are generated **in your browser, never sent anywhere**
3. Paste the one-line install command into SSH
4. Share the **HTTPS Subscription link** with your users — it works in v2rayNG, Hiddify, Kv2m, and any V2Ray client

> **The advantage that can't be copied:** X25519 keys and UUIDs are generated in your browser/device. They never touch any third-party server — not even ours (we have none).

---

## 🧩 Platform components

| Component | Description | Status |
|---|---|---|
| **Installer + CLI** | One-command Reality/WARP/SS/TLS install; `kian-v2ray` CLI with self-diagnosis & auto-repair | ✅ stable |
| **Web generator** | In-browser config builder — 100% bilingual (FA/EN), all keys client-side, auto TLS protocol detection | ✅ stable |
| **Web panel** (`panel/`) | FastAPI + JWT + **TOTP 2FA** · dark-glass dashboard (users / nodes / audit / live stats / settings) · IP / speed / HWID limits · WebSocket stats · per-user routing & DNS · `/metrics` for Prometheus | ✅ complete |
| **Multi-server** | One panel → many VPS · health/failover/load-balance/GeoIP routing · import from Marzban/3X-UI | ✅ complete |
| **New protocols** | **Hysteria2 · TUIC v5 · AnyTLS · ShadowTLS v3** via sing-box companion (opt-in, per-user, auto port-select) · Fragment · uTLS · TTL · Noise anti-DPI · Reality spiderX · Tor fallback | ✅ code · ⏳ field-test |
| **Kv2m desktop** | PySide6/Qt — multi-server, SSH install, web-panel deploy, Hysteria2/TUIC generator — Windows / macOS / Linux | ✅ v3.6 |
| **Kv2m mobile** | Flutter Android — **on-device tunnel** (bundled Xray), in-app SSH install, config QR & copy, install history, split-tunnel, routing/DNS/kill-switch, GMS-free | ✅ v0.5 |
| **Monitoring** | Prometheus + node/Xray exporters + Grafana dashboard + alert rules | ✅ configs |
| **Notifications** | Telegram · Email (SMTP) · Webhook — server-side quota/expiry push, no FCM | ✅ complete |
| **CI/CD** | Validate (bash/js/py/pytest) + CodeQL + Trivy + one-click release via GitHub Actions | ✅ green |

---

## ⬇️ Downloads

All builds are on the **[Releases](https://github.com/kian-irani/kian_v2ray/releases/latest)** page — built automatically by CI on every version.

| Platform | File | Notes |
|---|---|---|
| 🪟 **Windows — Setup** | `Kv2m-Setup-x64.exe` | Full install — Start Menu + Desktop shortcut. No Python needed. |
| 🪟 **Windows — Portable** | `Kv2m-Portable-x64.exe` | Run directly, no install. |
| 🍏 **macOS** | `Kv2m-macOS.zip` | `Kv2m.app` — right-click → Open the first time. |
| 🐧 **Linux** | `Kv2m-Linux-x86_64` | Self-contained binary (`chmod +x`). |
| 🤖 **Android Universal** | `Kv2m-*-universal.apk` | **Works on every phone** — the safe choice. |
| 🤖 **Android 64-bit** | `Kv2m-*-arm64.apk` | New phones (arm64-v8a) — smaller download. |
| 🤖 **Android 32-bit** | `Kv2m-*-arm32.apk` | Very old phones (armeabi-v7a). |
| 🌐 **No install** | [Web generator](https://kian-irani.github.io/kian_v2ray/) | Build + install right in the browser. |

> **Android connects on its own** — the native tunnel core (Xray via `flutter_v2ray`) is bundled. No v2rayNG needed.

---

## Quick start

```bash
# 1. Get an Ubuntu VPS — any provider.
# 2. Open https://kian-irani.github.io/kian_v2ray/ or the Kv2m app.
# 3. Enter your server IP + username → copy the install command.
# 4. SSH into your server and paste it (or hit "Run on server" in Kv2m):
curl -fsSL https://raw.githubusercontent.com/kian-irani/kian_v2ray/main/install.sh | bash
# 5. Import the Subscription link into v2rayNG, Hiddify, Kv2m, or any V2Ray client.
```

### Server management commands

```bash
kian-v2ray status              # service status + self-diagnosis
kian-v2ray users               # list users + quota
kian-v2ray add <name> [GB] [days]
kian-v2ray configs [name]      # copy-ready VPN links
kian-v2ray sub <name>          # user's Subscription URL
kian-v2ray protocols enable    # add Hysteria2 + TUIC (opt-in sing-box companion)
kian-v2ray update              # update Xray-core + scripts in-place, users kept
kian-v2ray resync              # regenerate all users' subscriptions
kian-v2ray uninstall           # full removal
```

---

## 🖥️ Web panel

A **FastAPI** backend + dark-glass dashboard — deploy on your server in one command:

```bash
# Via the installer (recommended):
kian-v2ray panel enable

# Or manually:
kian-panel.sh enable           # installs, creates systemd service, prints URL
```

**Features:** JWT + refresh tokens + **TOTP 2FA** · CRUD users + search + **bulk actions** · per-user **IP / speed / HWID** limits + **auto-disable** · per-user **routing & DNS** · WebSocket live stats · CSV/JSON export · **audit log** · **node cluster** (health / route / GeoIP failover) · key rotation · CSP security headers + rate-limit + CORS · unauthenticated `/metrics` for Prometheus scraping (optional `KIAN_METRICS_IP_WHITELIST` to restrict scrapers — see [`docs/metrics.md`](docs/metrics.md)).

```
http://YOUR-SERVER:8443/app      ← dashboard
http://YOUR-SERVER:8443/docs     ← Swagger API reference
```

---

## Supported protocols

**No domain (Reality / direct IP):**
- VLESS + Reality + Vision (TCP) with **spiderX**
- Shadowsocks

**With domain (TLS / CDN):**
- VLESS-WS · VMess-WS · VLESS-gRPC · VMess-gRPC · Trojan-WS
- VLESS-HTTPUpgrade · VMess-HTTPUpgrade · **VLESS-XHTTP**

**Opt-in companion (sing-box):**
- **Hysteria2** · **TUIC v5** · **AnyTLS** · **ShadowTLS v3**
- Generated **per-user**, each on its own port (auto-moved if busy)
- Layer-guarded: a sing-box build that rejects a newer layer silently drops just that protocol and keeps the rest

**Routing:** all traffic egresses through **Cloudflare WARP** with direct fallback — no misconfigurable "fast mode".

**Anti-DPI:** Fragment (TLS-Hello split, on by default) · uTLS fingerprint · TTL manipulation · Noise padding · ECH plumbing · Tor bridge fallback

---

## 🔐 Security

- **No secret ever touches our servers** — X25519 keys and UUIDs are generated client-side (browser/device) and land only on **your** server.
- **Config file permissions** — `config.json` (REALITY private key) is `chmod 640` root-only.
- **Panel authentication** — JWT + refresh + TOTP 2FA; admin password auto-generated on first boot if not set.
- **Node authentication** — heartbeat API requires a per-node Bearer token verified with `secrets.compare_digest`.
- **Subscription info** — `/sub/{name}/info` requires a per-user token preventing unauthenticated username enumeration.
- **XSS prevention** — DOM is built via `createElement`/`textContent`; no `innerHTML` with user data.
- **CI security scanning** — CodeQL + Trivy run on every push; secret scanning on all PRs.
- The **Gist token** lives only in the Cloudflare Worker secret, never in the page or on the user's server.
- Full public repo — auditable by anyone.

See [SECURITY.md](SECURITY.md) · [Privacy Policy](privacy.html) · [Terms of Service](terms.html)

---

## 💻 Kv2m apps

### Desktop (Windows / macOS / Linux)
- PySide6/Qt — bilingual (FA/EN), frameless dark UI
- **Multi-server profiles** — save multiple servers, switch with one click
- **SSH install** — run the installer directly from the app (no separate terminal)
- **Server management** — add/remove users, view configs, deploy web panel, update in-place
- **Hysteria2/TUIC generator** — build companion-protocol configs
- Auto-update built in

### Mobile (Android)
- Flutter — **GMS-free** (Cafe Bazaar / Myket / F-Droid compatible)
- **On-device tunnel** — bundled Xray core (`flutter_v2ray`), connects without v2rayNG
- **In-app SSH install** — scan or type server IP → install → connect, all in one flow
- **Config QR & one-tap copy** — share configs to any client
- **Install history** — see every server you've configured
- **Per-app split-tunnel** — choose which apps go through VPN
- Routing presets · DNS override · Kill-switch · Auto-connect
- Subscription card — shows usage/quota/expiry at a glance

---

## 🗺️ Roadmap

See [`ROADMAP.md`](ROADMAP.md) for the full phase plan.

- ✅ **Done** — Phases 1–12: installer, web panel + 2FA, cluster, new protocols, on-device tunnel, desktop (Win/macOS/Linux), security hardening, monitoring, notifications, bilingual site, CI/CD
- ⏳ **Field test needed** — end-to-end Hysteria2/TUIC/TLS on a live VPS
- 🙋 **Needs you** — store developer accounts (Google Play / Cafe Bazaar / Myket / F-Droid), signing Keystore, app screenshots & submissions — see [ROADMAP.md §4](ROADMAP.md)

---

## 📚 Documentation

| Area | Document |
|---|---|
| 🚀 Start here | [Web generator](https://kian-irani.github.io/kian_v2ray/) · [Quick start](#quick-start) |
| 🔌 Connectivity | [`docs/connect-now.md`](docs/connect-now.md) — when to use a domain vs direct IP |
| 🔄 Migration | [`docs/MIGRATION.md`](docs/MIGRATION.md) — import from Marzban / 3X-UI |
| 🗺️ Roadmap | [`ROADMAP.md`](ROADMAP.md) |
| 🔐 Security | [`SECURITY.md`](SECURITY.md) · [Privacy](privacy.html) · [Terms](terms.html) |
| 🌍 Translations | [`docs/TRANSLATIONS.md`](docs/TRANSLATIONS.md) |
| 🏷️ Versioning | [`docs/VERSIONING.md`](docs/VERSIONING.md) · [`CHANGELOG.md`](CHANGELOG.md) |
| 🔁 Reproducible builds | [`docs/REPRODUCIBLE-BUILDS.md`](docs/REPRODUCIBLE-BUILDS.md) |
| 🤝 Contributing | [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) |
| 📊 Monitoring | [`monitoring/`](monitoring/) |
| ☁️ Deploy / IaC | [`docker-compose.yml`](docker-compose.yml) · [`deploy/terraform/`](deploy/terraform/) |

### Repository layout

```
install.sh           one-command server installer
index.html           in-browser config generator (client-side keys)
scripts/             kian-v2ray CLI · kian-protocols.sh · watchdog · backup · bot
core/                shared lib: db · cluster · protocols · notify · audit · analytics
panel/               FastAPI web panel + dark-glass UI (panel/web/)
app/                 Flutter Android client (Kv2m mobile)
kv2m/                PySide6/Qt desktop app (Kv2m desktop)
node-agent/          lightweight per-VPS health/metrics agent
monitoring/          Prometheus · Loki · Grafana · alert rules
deploy/              Terraform / IaC
docs/                guides (migration, translations, versioning, …)
```

---

## Contributing & license

Issues and pull requests welcome — see [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md).
License: **MIT** — free to use, modify, and distribute.

---

<a id="فارسی"></a>

## 🇮🇷 فارسی

پلتفرمِ **متن‌بازِ رایگانِ** ضدسانسور برای اجرای VPN روی **سرور(های) خودت** — بدونِ سرورِ مرکزی، بدونِ اشتراک، بدونِ رهگیری.

**چطور کار می‌کند:**
۱. [صفحهٔ ساخت کانفیگ](https://kian-irani.github.io/kian_v2ray/) یا اپِ **Kv2m** را باز کن
۲. IP سرور + نام کاربری → کلیدها **در مرورگرت** ساخته می‌شوند، هرگز جایی ارسال نمی‌شوند
۳. دستورِ نصب را در SSH سرور بزن
۴. لینکِ **Subscription** را با کاربران به اشتراک بگذار

> **مزیتِ غیرقابل‌کپی:** کلیدهای X25519 و UUID روی مرورگر/دستگاهِ شما ساخته می‌شوند. هرگز به هیچ سرور ثالثی نمی‌رسند.

### 🧩 اجزاء

| جزء | توضیح | وضعیت |
|---|---|---|
| **نصب‌کننده + CLI** | نصبِ تک‌دستوری Reality/WARP/SS/TLS + CLIِ `kian-v2ray` با خودتشخیصی | ✅ پایدار |
| **صفحهٔ تعاملی** | سازندهٔ کانفیگ در مرورگر، ۱۰۰٪ دوزبانه، فعال‌سازیِ خودکارِ TLS | ✅ پایدار |
| **پنلِ وب** | FastAPI + JWT + **2FA** · داشبوردِ dark-glass · محدودیتِ IP/سرعت/HWID · آمارِ زنده · routing/DNS هر کاربر | ✅ کامل |
| **چندسرور** | یک پنل → چند VPS · health/failover/GeoIP · مهاجرت از Marzban/3X-UI | ✅ کامل |
| **پروتکل‌های جدید** | Hysteria2 · TUIC v5 · AnyTLS · ShadowTLS v3 (sing-box، اختیاری، per-user) · Fragment · Tor | ✅ کد · ⏳ تست |
| **Kv2m دسکتاپ** | Qt/PySide6 · چندسرور · نصبِ SSH · راه‌اندازی پنل · ویندوز/مک/لینوکس | ✅ v3.6 |
| **Kv2m موبایل** | Flutter اندروید · اتصالِ روی‌دستگاه · نصبِ SSH · QR · split-tunnel · بدونِ GMS | ✅ v0.5 |

### ⬇️ دانلود

همهٔ نسخه‌ها در [صفحهٔ آخرین ریلیز](https://github.com/kian-irani/kian_v2ray/releases/latest):

| پلتفرم | فایل |
|---|---|
| 🪟 ویندوز نصبی | `Kv2m-Setup-x64.exe` |
| 🪟 ویندوز قابل‌حمل | `Kv2m-Portable-x64.exe` |
| 🍏 macOS | `Kv2m-macOS.zip` |
| 🐧 لینوکس | `Kv2m-Linux-x86_64` |
| 🤖 اندروید همه‌کاره | `Kv2m-*-universal.apk` |
| 🤖 اندروید ۶۴ بیتی | `Kv2m-*-arm64.apk` |

### شروعِ سریع

```bash
# سرور Ubuntu → صفحهٔ تعاملی → دستور نصب را در SSH بزن:
# بعد از نصب:
kian-v2ray status              # وضعیت + تشخیص
kian-v2ray add <نام> [GB] [روز]
kian-v2ray protocols enable    # فعال‌سازی Hysteria2 + TUIC
kian-v2ray update | uninstall
```

### پنلِ وب

```bash
kian-panel.sh enable           # نصب + راه‌اندازیِ سرویس systemd + نمایشِ URL
# یا از طریقِ CLI:
kian-v2ray panel enable
```

داشبورد: `http://سرور:8443/app` · Swagger: `http://سرور:8443/docs`

### 🔐 امنیت

- هیچ رازی به سرورهای ما نمی‌رسد — کلیدها در دستگاهِ تو ساخته می‌شوند
- `config.json` (کلیدِ REALITY) با دسترسی ۶۴۰ فقط برای root
- رمزِ ادمین اگر تنظیم نشود، در اولین بوت به‌صورتِ تصادفی ساخته و لاگ می‌شود
- `/sub/{name}/info` نیاز به توکنِ per-user دارد (مانعِ enumerate شدنِ کاربران)
- XSS prevention: DOM فقط با `createElement`/`textContent` ساخته می‌شود
- CI روی هر push: CodeQL + Trivy + secret-scan

### 🗺️ نقشهٔ راه

| وضعیت | موضوع |
|---|---|
| ✅ انجام‌شده | فاز ۱–۱۲: installer، panel+2FA، cluster، پروتکل‌ها، mobile، desktop، CI/CD |
| ⏳ نیازِ تست | Hysteria2/TUIC/TLS روی VPS واقعی |
| 🙋 نیازِ تو | حساب‌های Google Play/Bazaar/Myket/F-Droid + Keystore + انتشار |

---

<div align="center">

Built with ❤️ by **[Kian Irani](https://github.com/kian-irani)** — for a free and open internet

ساخته‌شده برای دسترسیِ آزاد به اینترنت 🇮🇷

</div>
