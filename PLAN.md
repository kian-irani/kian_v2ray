---
title: PLAN — kian-v2ray
tags: [v2ray, plan]
date: 2026-06-20
status: active
priority: medium
project: kian-v2ray
---

# 🗺️ PLAN — `01-kian-v2ray` (rev v3.0 — full task breakdown)

> هدف: از نصب‌کنندهٔ V2Ray تک‌دستوری → **پلتفرم VPN چندسروره + اکوسیستم موبایل**.
> سند محصول: `PRD.md` · رودمپ کامل: `repo/ROADMAP.md` (v2.4) · بایگانی: `repo/ROADMAP-legacy.md`.
> مزیتِ اختصاصیِ غیرقابل‌کپی: **کلید خصوصی هرگز به سرور نمی‌رسد** (ساخت در مرورگر).
> هر آیتم یک تسکِ مستقل با شناسه است. `[x]`=done · `[~]`=in-progress · `[ ]`=open · `(srv)`=نیازِ تستِ سرور.

## ✅ Done
- صفحهٔ تعاملی (کلید در مرورگر، چند SNI/پورت) · Subscription سه‌لایه (Gist HTTPS) · TLS دامنه‌دار پشت Caddy · هسته (Reality/WARP/SS/multi-user/CLI/Watchdog/BBR) · Kv2m دسکتاپ.
- **[2026-06-20 auto-rp]** فاز ۰ کامل → نصب‌کننده **v2.1.0** (خودتشخیصیِ `status`/`health`/`doctor`). حقوقی (privacy/terms دوزبانه). صفحهٔ تعاملیِ دوزبانه + سکشنِ رودمپ. README/ROADMAP/CHANGELOG بازنویسی.

---

## 🔴 فاز ۰ — رفع باگ‌های بحرانی
- [x] ۰.۱ تداخل پورت API (10085) → auto-fix در `install.sh`.
- [x] ۰.۲ پایدارسازی WARP → `warp_fallback()` + چکِ socks.
- [x] ۰.۳ خودتشخیصیِ `status` (کرش‌لوپ/WARP/پورت/SS/Subscription) + alias `health`/`doctor`.
- [x] ۰.۴ بهینه‌سازی سرعت BBR (BBR+fq، idempotent).
- [x] ۰.۵ نصب مجدد امن (بکاپ + ادغامِ کاربرانِ قبلی).
- [x] ۰.۶ بازطراحی Shadowsocks (code-side): `SS_METHOD` تک‌منبع (app.js)، لینکِ SS حالا IPv6-safe، و اعتبارسنجیِ cipher در `config-health.py` (لیستِ مجاز شاملِ SS-2022). `(srv)` مهاجرتِ نهاییِ cipher + تستِ روی سرور باقی است.

---

## 🟠 فاز ۱ — پایه‌ریزی
- [x] ۱.۱۰ **LANDING-i18n-FULL** — i18n.js بازنویسی شد: پشتیبانیِ `data-i18n-ph` (placeholder) + `data-i18n-title` + دیکشنریِ ۱۰۴کلیدی FA/EN. کلِ سطحِ تعاملی (فرمِ ساخت: لیبل/placeholder/option/mode/دکمه + فرمِ مدیریت: اکشن‌ها/فیلدها) + همه‌ی هدینگِ تب‌ها + about + hero/roadmap/footer دوزبانه شد. اعتبارسنجی: `node --check` سبز، ۱۰۴/۱۰۴ کلید تعریف‌شده، تگ‌های HTML متوازن، smoke test سبز (generator دست‌نخورده)، toggle درست FA↔EN را سوییچ می‌کند. **[باقی: ترجمه‌ی عمیقِ پاراگراف‌های troubleshooting در tips/domain = ادامه.]**
- [x] ۱.۱ ریفکتورِ ساختار: پکیجِ `core/` (stdlib-only، importable روی VPS) + `tests/` ساخته شد؛ مسیرهای CI نشکست.
- [x] ۱.۲ SQLite schema (`core/db.py`: users/audit_log/nodes/settings + pragmaهای WAL/FK) + Migration سبکِ forward-only (`core/migrate.py` با `user_version`، idempotent).
- [x] ۱.۳ لاگِ ساختاریافتهٔ JSON (`core/logging.py`: خروجیِ تک‌خطیِ JSON، فیلدهای ساختاریافته در `kian_fields`، بدونِ تداخل با LogRecord).
- [x] ۱.۴ SemVer + Git Tagging (`scripts/release.sh` major/minor/patch + tag + `docs/VERSIONING.md`).
- [x] ۱.۵ پشتیبانیِ IPv6 (client/link side): `isIPv6`/`isServerAddr`/`hostForUri` در app.js؛ آدرسِ IPv6 پذیرفته و در لینک‌ها bracket می‌شود (`[2001:db8::1]:port`)؛ اعتبارسنجیِ فرم IPv6 را قبول می‌کند. smoke سبز. `(srv)` بایندِ سروری روی `::` در install.sh باقی است.
- [x] ۱.۶ بکاپِ خودکارِ رمزنگاری‌شده (`scripts/kian-backup.py`: tar.gz + openssl AES-256 + آپلودِ Telegram/S3/rclone، cron-ready).
- [x] ۱.۷ Audit Log (`core/audit.py`: `record`/`tail`، نوشتن در DB + mirror در JSON log).
- [x] ۱.۸ pytest (`tests/test_core.py` + `tests/test_scripts.py`، ۸ تست سبز) + اتصال به CI (`validate.yml`).
- [x] ۱.۹ Config Health Check (`scripts/config-health.py`: اعتبارسنجیِ inbound/port/Reality/SS-cipher + `--probe`).

---

## 🟠 فاز ۲ — وب پنل کامل
- [x] ۲.۱ اسکلتِ FastAPI (`panel/main.py`) + مدل‌ها (`panel/schemas.py` Pydantic) روی `core.db` (به‌جای ORMِ دوم — تصمیمِ معماری برای تک‌منبعِ schema).
- [x] ۲.۲ JWT Auth + Refresh Token (`panel/security.py` HS256 دست‌ساز + PBKDF2، stdlib؛ `/auth/login`/`/auth/refresh`).
- [x] ۲.۳ REST API کاربر CRUD + OpenAPI خودکار (`/api/users` GET/POST/PATCH/DELETE، `/docs`).
- [x] ۲.۴ WebSocket آمارِ زنده (`/ws/stats` با احرازِ توکن).
- [x] ۲.۵ محدودیتِ IP/Speed/HWID + Auto-Disable + Bulk Actions (`panel/repo.py` + endpointها).
- [x] ۲.۶ Export (JSON/CSV) + Session Management (`/auth/sessions`) + Password Recovery (`/auth/password`).
- [x] ۲.۷ Frontend پنل (`panel/web/index.html` + `app.js`): UI Dark/Glass (OLED، اکسنتِ سبزِ #22C55E، طبق ui-ux-pro-max)، دوزبانه FA/EN + RTL/LTR، لاگین+refreshِ توکن، جدولِ CRUD + bulk + جستجو + toggle، مودالِ ساخت/ویرایش، نمودارِ canvas، آیکنِ SVG (نه ایموجی). در FastAPI روی `/app` mount شد.
- [x] ۲.۸ System Monitor (CPU load + RAM از `/proc` → `/api/system` + pill) + Audit Log Viewer (`/api/audit` + تبِ گزارش) + Export CSV. (Backup/Restore از UI = follow-on؛ اسکریپتِ `kian-backup.py` موجود.)
- [x] ۲.۹ امنیت: Rate-Limit + Security Headers (nosniff/DENY/HSTS/CSP) + CORSِ صریح + **2FA TOTP** (RFC 6238 دست‌ساز، `/auth/2fa/{setup,enable,disable}`) + **IP whitelistِ ادمین**. (Fail2ban = لایهٔ سیستمی/ops، خارج از کدِ پنل.)
- [x] ۲.۱۰ Key Rotation (`/api/keys/rotate` — چرخشِ secretِ JWT، ابطالِ همه توکن‌ها).

---

## 🟡 فاز ۳ — Kv2m Desktop چندسروره
- [x] ۳.۱ مدیریتِ چندسرور: `kv2m/servers.py` (`ServerProfile` + `ServerStore`: add/remove/select/active، persist در JSON، بدونِ ذخیرهٔ رمز) — ۳ تست سبز.
- [x] ۳.۲ اتصال به REST API پنل: `kv2m/panel_client.py` (login + refreshِ خودکار + CRUDِ کاربر + stats، stdlib urllib).
- [x] ۳.۳ Auto-update (GitHub Releases): `kv2m/updater.py` (`parse_version`/`is_newer`/`check` با مقایسهٔ نسخهٔ مقاوم به نامِ محصول) — تست سبز.
- [x] ۳.۴ Dark/Light ذخیره‌شده — `kv2m/settings.py` (persistِ theme/lang/last-server/tray با toggle، تست سبز). macOS/Linux + crash-reporter = follow-onِ بسته‌بندی.

---

## 🟡 فاز ۴ — پروتکل‌ها و ضدسانسور
- [x] ۴.۱ Hysteria2 inbound — `core/protocols.hysteria2_inbound` (+obfs salamander).
- [x] ۴.۲ TUIC v5 inbound — `core/protocols.tuic_inbound` (bbr، 0-RTT).
- [x] ۴.۳ WireGuard inbound + Mux.cool — `wireguard_inbound` + `mux_settings`.
- [x] ۴.۴ خروجیِ Sing-box format — `core/protocols.to_singbox`.
- [x] ۴.۵ خروجیِ Clash Meta + تشخیصِ خودکارِ کلاینت — `to_clash` + `detect_client` (singbox/clash/v2ray/base64).
- [x] ۴.۶ Self-hosted Sub — موتورِ `scripts/sub-format.py` + **صفحهٔ `panel/web/sub.html`** (dark، usage bar/انقضا/کپی/**QR**) + endpointِ `/sub/{name}/info`.
- [x] ۴.۷ ضدِDPI کامل — Fragment + uTLS (`fragment_settings`/`utls_settings`/`is_valid_fingerprint`) + **TTL** (`ttl_settings`) + **Noise padding** (`noise_settings`).
- [x] ۴.۸ REALITY SNI Scanner (offline brain) — `core/censorship.score_sni`/`rank_sni_candidates`/`best_sni`.
- [x] ۴.۹ Tor Bridge Fallback — `core/censorship.tor_bridge_outbound` (obfs4/snowflake) + `fallback_routing_rule`.
- [x] ۴.۱۰ بات تلگرام — `scripts/kian-bot.py` (long-poll، admin-gated، status/users/add/remove/usage روی core.db). Webhook/Email = follow-on.

---

## 🔵 فاز ۵ — Multi-Server Management
- [x] ۵.۱ Node Agent سبک — `node-agent/agent.py` (http.server، token-gated، `/health` + `/apply`، نوشتنِ اتمیکِ config).
- [x] ۵.۲ یک پنل → چند VPS — جدولِ `nodes` + endpointهای `/api/nodes` (CRUD) + `/api/nodes/{name}/heartbeat` + migration 0005.
- [x] ۵.۳ Health Check + Auto Failover — `core/cluster.is_alive`/`failover_order` + heartbeat.
- [x] ۵.۴ Load Balancing + GeoIP — `pick_least_loaded` + `route_by_geo` (country→region) + `/api/route`.
- [x] ۵.۵ Migration از Marzban/3X-UI — `scripts/migrate-import.py` (`normalize_marzban` + `normalize_xui` → `import_users`).
- [x] ۵.۶ Bandwidth Alert + per-Node Override — `cluster.bandwidth_alerts` + هر node کانفیگِ مستقل از `/apply`.

---

## 🔵 فاز ۶ — اپ موبایل Flutter
- [x] ۶.۱ اسکلتِ Flutter — `app/` (pubspec، `main.dart` با RTL/LTR + dark/light، `theme.dart`، `i18n.dart`).
- [x] ۶.۲ صفحاتِ اصلی — `home_screen.dart` (دکمه‌ی اتصالِ گرد + لیستِ سرور + import sheet) + parseِ subscription (`models/server_profile.dart`)؛ QR از `mobile_scanner` (بدونِ GMS).
- [x] ۶.۳ Smart Server Selection + Offline Mode — `services/selection.dart` (TCP latency) + `services/cache.dart` (persistِ server list/stats/prefs با shared_preferences برای حالتِ آفلاین). Home Widget = follow-onِ پلتفرمی.
- [x] ۶.۴ بدونِ GMS + Push بدونِ FCM — deps بدونِ firebase/admob؛ مستندِ SSE/Telegram در README.
- [x] ۶.۵ Metadata + Privacy فارسی + Keystore — `PRIVACY-fa.md` + `KEYSTORE.md` (۳ backup) + دستورِ AAB/APK در README.
- [x] ۶.۶ Market metadata — `fastlane/metadata/android/{fa-IR,en-US}` (title/short/full) برای Cafe Bazaar/Myket/F-Droid.
- نامِ اپ: **Kv2m** (هم‌خانواده با دسکتاپِ Kv2m — طبقِ دستورِ کاربر 2026-06-20؛ package=`kv2m`، title=`Kv2m`).
- توجه: Dart در CI کامپایل نمی‌شود (toolchain نیست)؛ ساختار صحیح و braces متوازن — تستِ Dart (`app/test/`) با Flutter اجرا می‌شود.

---

## 🟢 فاز ۷ — CI/CD + Monitoring
- [x] ۷.۱ GitHub Actions: lint+test (`validate.yml`) + **Auto Release** (`release.yml`، tag `v*` → ساختِ release از CHANGELOG).
- [x] ۷.۲ Docker Image (`Dockerfile`، GHCR، non-root) + One-click Deploy (`docker-compose.yml`: panel+prometheus+node-exporter+grafana).
- [x] ۷.۳ SAST CodeQL (python+javascript) + Trivy fs scan (`security.yml`، هفتگی + روی PR).
- [x] ۷.۴ Prometheus + Node/Xray Exporter (`monitoring/prometheus.yml`) + **endpointِ `/metrics`** در پنل (`panel/metrics.py`، exposition format، تست‌شده).
- [x] ۷.۵ Grafana Dashboard (`monitoring/grafana-dashboard.json` آمادهٔ import) + Alert Rules (`monitoring/alerts.yml`: CPU/RAM/NodeDown/Bandwidth).
- [x] ۷.۶ مستندات + Plugin System: `core/plugins.py` (register/get/discover، ۴ تست) + `docs/MIGRATION.md` + `docs/CONTRIBUTING.md`.

---

## 🔴 بلاکر
- (فعلاً نیست) · `(srv)`-ها نیازِ دسترسیِ سرورِ `37.221.79.91`.

---
← [[kian-workspace/01-projects/01-kian-v2ray/kian-v2ray|kian-v2ray]]
