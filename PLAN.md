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
- [x] ۱.۱۰ **LANDING-i18n-FULL — ۱۰۰٪ کامل** — i18n.js: `data-i18n-ph`/`data-i18n-title` + دیکشنریِ **۲۲۵کلیدی** FA/EN. **هر ۸ تب کاملاً دوزبانه شد** تا عمیق‌ترین prose: فرمِ ساخت + مدیریت + about + hero/roadmap/footer + نکات (کامل) + **دامنه (کامل: رکوردِ A، Cloudflare، راهنمای پروتکل، ترتیبِ کار، و هر ۴ بلوکِ troubleshooting شاملِ توضیحِ geoblock)** + server/android/pc (همه‌ی stepها). اعتبارسنجی: `node --check` سبز، ۲۲۵/۲۲۵ کلید، HTML متوازن (p:66/66، b:132/132، details:5/5)، generator دست‌نخورده، toggle همه را به EN سوییچ می‌کند. **(دیگر باقی‌مانده‌ای ندارد.)**
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
- [x] ۲.۷ Frontend پنل (`panel/web/index.html` + `app.js`): UI Dark/Glass (OLED، اکسنتِ سبزِ #22C55E، طبق ui-ux-pro-max)، دوزبانه FA/EN + RTL/LTR، لاگین+refreshِ توکن، جدولِ CRUD + bulk + جستجو + toggle، مودالِ ساخت/ویرایش، نمودارِ canvas، **تبِ سرورها (Nodes): افزودن/حذف + مسیریابی/failover/هشدارِ پهنای‌باند**، آیکنِ SVG (نه ایموجی). در FastAPI روی `/app` mount شد.
- [x] ۲.۸ System Monitor (CPU load + RAM از `/proc` → `/api/system` + pill) + Audit Log Viewer (`/api/audit` + تبِ گزارش) + Export CSV. (Backup/Restore از UI = follow-on؛ اسکریپتِ `kian-backup.py` موجود.)
- [x] ۲.۹ امنیت: Rate-Limit + Security Headers + CORS + **2FA TOTP** (backend + **UIِ تبِ تنظیمات**: setup/enable/disable با نمایشِ secret) + **IP whitelist** + تغییرِ رمز + چرخشِ کلید از UI. (Fail2ban = لایهٔ سیستمی/ops.)
- [x] ۲.۱۰ Key Rotation (`/api/keys/rotate` — چرخشِ secretِ JWT، ابطالِ همه توکن‌ها).

---

## 🟡 فاز ۳ — Kv2m Desktop چندسروره
- [x] ۳.۱ مدیریتِ چندسرور **وایر شد**: `kv2m/servers.py` (`ServerStore`) حالا در `kv2m/cli.py` استفاده می‌شود — منویِ انتخاب/افزودن/حذفِ سرور + persist. نسخهٔ دسکتاپ به **v3.1.0** bump شد و در `build-kv2m.yml` hidden-import شد.
- [x] ۳.۲ اتصال به REST API پنل: `kv2m/panel_client.py` (login + refreshِ خودکار + CRUDِ کاربر + stats، stdlib urllib).
- [x] ۳.۳ Auto-update (GitHub Releases): `kv2m/updater.py` (`parse_version`/`is_newer`/`check` با مقایسهٔ نسخهٔ مقاوم به نامِ محصول) — تست سبز.
- [x] ۳.۴ Dark/Light ذخیره‌شده — `kv2m/settings.py` (persistِ theme/lang/last-server/tray با toggle، تست سبز). macOS/Linux + crash-reporter = follow-onِ بسته‌بندی.

---

## 🟡 فاز ۴ — پروتکل‌ها و ضدسانسور
- [x] ۴.۱ Hysteria2 inbound — منطق در `core/protocols.py` + **در install.sh وایر شد** (`scripts/kian-protocols.sh`: sing-box companion، opt-in با `KIAN_EXTRA_PROTOCOLS=1` یا `kian-v2ray protocols enable`؛ TLS از Caddy یا self-signed؛ systemd؛ لینکِ کلاینت).
- [x] ۴.۲ TUIC v5 inbound — همان `kian-protocols.sh` (bbr، 0-RTT روی sing-box). `(srv)` تستِ نهایی روی سرور.
- [x] ۴.۳ WireGuard inbound + Mux.cool — `wireguard_inbound` + `mux_settings` در core (WG inbound نیازِ کلیدِ کلاینت = تنظیمِ سرور).
- [x] ۴.۴ خروجیِ Sing-box format — `core/protocols.to_singbox`.
- [x] ۴.۵ خروجیِ Clash Meta + تشخیصِ خودکارِ کلاینت — `to_clash` + `detect_client` (singbox/clash/v2ray/base64).
- [x] ۴.۶ Self-hosted Sub — موتورِ `scripts/sub-format.py` + **صفحهٔ `panel/web/sub.html`** (dark، usage bar/انقضا/کپی/**QR**) + endpointِ `/sub/{name}/info`.
- [x] ۴.۷ ضدِDPI کامل — Fragment + uTLS (`fragment_settings`/`utls_settings`/`is_valid_fingerprint`) + **TTL** (`ttl_settings`) + **Noise padding** (`noise_settings`).
- [x] ۴.۸ REALITY SNI Scanner (offline brain) — `core/censorship.score_sni`/`rank_sni_candidates`/`best_sni`.
- [x] ۴.۹ Tor Bridge Fallback — `core/censorship.tor_bridge_outbound` (obfs4/snowflake) + `fallback_routing_rule`.
- [x] ۴.۱۰ بات تلگرام + **Webhook + Email + Push انقضا** — `scripts/kian-bot.py` + `core/notify.py` (Telegram/SMTP/Webhook، fan-out، graceful) + `scripts/kian-notify-expiry.py` (اسکنِ انقضا/سهمیه → اعلانِ سمت‌سرور، بدون FCM؛ cron-ready). ۵ تستِ سبز.

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
- [x] ۶.۱ **پروژهٔ واقعیِ Flutter+Android** — `app/android/` کامل: Gradle (ABIهای 32/64، signing، minSdk23/targetSdk35)، `AndroidManifest.xml` (VpnService + permissions، بدونِ GMS)، `MainActivity.kt` (کانالِ `kv2m/vpn`)، `KianVpnService.kt` (راه‌اندازیِ tun + foreground notification + هوک هستهٔ native). `flutter create .` فقط boilerplate تولیدی را پر می‌کند.
- [x] ۶.۲ صفحاتِ اصلی + **اتصالِ واقعی** — `home_screen.dart` (اتصال/قطعِ واقعی از طریقِ `VpnController`، busy state، restore از cache، دکمهٔ best-server) + import sheet + parseِ subscription + QR (`mobile_scanner`). `lib/services/vpn_service.dart` کانالِ native. **[تنها باقی‌مانده: bundleِ `.aar`ِ xray-core برای packet-forwarding واقعی — تک‌مرحلهٔ native.]**
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

## 🟣 فاز ۸ — «واقعاً کار کند» (بستنِ شکافِ done-روی-کاغذ ↔ کارکردنِ واقعی)
> بازخوردِ کاربر (2026-06-21): نصب از اپ موبایل خراب بود (Xray بالا نمی‌آمد، پورت‌ها گوش نمی‌دادند)،
> اپ کانفیگ را خودکار اضافه نمی‌کرد، پروتکل‌های جدید قابلِ‌انتخاب نبودند، و اپ «چیزی نشان نمی‌داد».
> این فاز این‌ها را واقعی می‌کند — با تستِ زنده روی سرور، نه فقط compile.

- [x] ۸.۱ **رفعِ بحرانیِ نصبِ خراب (REALITY `dest`)** — `config_gen.dart` فیلدِ `dest` را جا انداخته بود
  → Xray 26.x اصلاً start نمی‌شد. رفع: `dest:"<sni>:443"` در `config_gen.dart` + **اصلاح‌گرِ dest در
  `install.sh`** (دفاعی برای همهٔ کلاینت‌ها). **تأییدِ زنده روی سرور با ایمیجِ واقعیِ xray-core:26.5.9.**
- [x] ۸.۲ **پروتکل‌های جدید قابلِ‌انتخاب + قابلِ‌نصب** — صفحه (چک‌باکس) + اپ (سوییچ) → `extra_protocols`
  در payload → `install.sh` پروتکل‌ها را enable می‌کند و **لینک‌ها را به Subscription می‌افزاید + Gist را sync**.
- [x] ۸.۳ **افزودنِ خودکارِ کانفیگ به اپ بعد از نصب** — `setup_screen` کانفیگ‌ها را در `Cache` می‌ریزد،
  خانه reload می‌شود، دکمهٔ «بازگشت به خانه و دیدنِ کانفیگ‌ها». (شکایتِ #۱ کاربر)
- [x] ۸.۴ **اپ کانفیگ‌ها/سابسکرایب را نشان می‌دهد** — صفحهٔ `config_detail_screen.dart` (QR + URIِ کامل +
  کپی + چیپِ پروتکل/هاست/پورت)، دکمهٔ QR روی هر سرور در خانه، و **کارتِ لینکِ Subscription** در خانه
  (نمایش/کپی، persist در Cache). شکافِ «اپ چیزی نشان نمی‌دهد» بسته شد.
- [x] ۸.۵ **پنل از داخلِ اپ** — سوییچِ «راه‌اندازیِ پنلِ وب» در ویزارد (user/pass) → SSH `kian-v2ray panel
  enable` → **نمایشِ URL + user/pass** در اپ (parse از خروجی). (`manage_screen` از قبل به همین پنل وصل می‌شود.)
- [x] ۸.۶ **پروتکل‌های جدید در همهٔ نسخه‌ها** — دسکتاپ (kv2m: چک‌باکسِ Hysteria2/TUIC در GUI + `extra_protocols`
  در payload، **v3.2.0**)، اپ (سوییچ)، صفحه (چک‌باکس). کاربر گزارش داد ویندوز پشتیبانی نمی‌کرد → رفع شد.
- [x] ۸.۷ **تاریخچهٔ نصب در اپ** — `InstallRecord` + persist در Cache؛ هر نصب (لینکِ sub، URL+یوزر/پسِ پنل،
  پروتکل‌ها، تاریخ) ذخیره و در `history_screen` با کپی/نمایشِ رمز/حذف نشان داده می‌شود.
- [x] ۸.۸ **کپیِ آسانِ کانفیگ‌ها/سابسکرایب** — صفحهٔ جزئیات (QR+کپی) + کارتِ sub + دکمهٔ «کپیِ همهٔ کانفیگ‌ها».
- [x] ۸.۹ **نسخه‌های منتشرشده مرتب** — Android **universal + arm64 (+arm32)** در `build-app.yml`؛ Windows
  Setup+Portable از قبل؛ README با جدولِ دانلود + رونماییِ قابلیت‌ها بازنویسی شد.
- [ ] ۸.۱۰ **(srv)** تستِ end-to-end روی سرورِ `37.221.79.91`: ویزاردِ موبایل + Hysteria2/TUIC + پنل پشتِ TLS.

---

## 🔴 بلاکر
- (فعلاً نیست) · `(srv)`-ها نیازِ دسترسیِ سرورِ `37.221.79.91`.

---
← [[kian-workspace/01-projects/01-kian-v2ray/kian-v2ray|kian-v2ray]]
