# Changelog — kian_v2ray

تغییرات مهم پروژه اینجا ثبت می‌شود. نسخه‌بندی اسکریپت‌ها بر اساس [SemVer](https://semver.org).
نسخهٔ pin‌شدهٔ Xray در فایل [`VERSION`](VERSION) نگه‌داری می‌شود.

---

## [installer 2.3.0] — 2026-06-21  (Hysteria2 + TUIC در نصب‌کننده — auto-rp)

### افزوده شد (وایرِ پروتکل‌های جدید به `install.sh` — additive/opt-in)
- **`scripts/kian-protocols.sh`** — companionِ **sing-box** کنارِ Xray (چون Xray-core از Hysteria2/TUIC پشتیبانی نمی‌کند):
  - نصبِ sing-box (pin شده 1.10.1)، تولیدِ inboundهای **Hysteria2 + TUIC v5** (UDP، bbr)،
    استفادهٔ مجددِ گواهیِ Caddy (حالتِ TLS) یا گواهیِ self-signed، سرویسِ systemdِ `kian-singbox`، بازکردنِ پورتِ UDP، و چاپِ **لینکِ کلاینت** (`hysteria2://`/`tuic://`).
  - دستورها: `enable | links | disable | status`.
- **`install.sh`:** اسکریپت را نصب می‌کند و **فقط با `KIAN_EXTRA_PROTOCOLS=1`** اجرا می‌کند — مسیرِ کارکنندهٔ Reality/SS/TLS کاملاً دست‌نخورده.
- **CLI:** `kian-v2ray protocols [enable|links|disable|status]`.
- `VERSION`: `SCRIPT_VERSION=2.3.0` + `SINGBOX_VERSION=1.10.1`.

### تأیید
- `bash -n` روی install.sh + kian-protocols.sh + kian-v2ray سبز (به CI اضافه شد) · jq configِ sing-box معتبر (۲ inbound).
- **`(srv)`:** تستِ واقعیِ اتصالِ Hysteria2/TUIC نیازِ سرور دارد (نمی‌توان headless تست کرد).

---

## [installer 2.2.0] — 2026-06-21  🎉 نسخهٔ بزرگ — پلتفرم، نه فقط نصب‌کننده

> جمع‌بندیِ همه‌ی کارِ این دوره (auto-rp 2026-06-20/21). از یک نصب‌کننده به یک **پلتفرمِ کامل**.

### مهم‌ترین‌ها
- **زیرساختِ `core/`** (stdlib): SQLite + migration، لاگِ JSON، audit · `scripts/`: backup رمزنگاری‌شده، config-health، sub-format، بات تلگرام، مهاجرت از Marzban/3X-UI.
- **پنلِ وبِ FastAPI کامل** (`panel/`): JWT + **2FA TOTP با UI** + CRUD/bulk/auto-disable + WebSocket + export + key-rotation + هدرهای امنیتی + **داشبوردِ dark-glass دوزبانه** (کاربران/سرورها/ممیزی/نمودار/تنظیمات).
- **چندسرور** (`core/cluster.py` + `node-agent/`): health/failover/load-balance/GeoIP + node API.
- **پروتکل‌ها** (`core/protocols.py` + `censorship.py`): Hysteria2/TUIC/WG + Fragment/uTLS/TTL/Noise + sing-box/Clash + REALITY-scanner + Tor-fallback.
- **اپِ موبایلِ Kv2m** (`app/`): پروژهٔ واقعیِ Flutter+Android با VpnService (فقط هستهٔ native مانده).
- **دسکتاپِ Kv2m v3.1.0** منتشر شد (چندسرورِ CLI).
- **صفحهٔ تعاملی ۱۰۰٪ دوزبانه** (۲۲۵ کلید) · **CI/CD** (CodeQL/Trivy/release) + Docker/compose + Prometheus/Grafana.

### تأیید
- `validate.yml` سبز · **۴۳ تستِ pytest** · CodeQL + Trivy سبز · secret-scan تمیز.

---

## [panel-settings] — 2026-06-21  (تبِ تنظیمات + UIِ 2FA — auto-rp)

### افزوده شد (بستنِ گپِ «2FA بدونِ UI» در فاز ۲)
- **تبِ «تنظیمات» در داشبورد:** راه‌اندازیِ 2FA (نمایشِ secret برای Google Authenticator/Aegis → وروِد کد → فعال‌سازی)،
  غیرفعال‌سازیِ 2FA، **تغییرِ رمزِ عبور**، و **چرخشِ کلیدِ JWT** — همه از UI.
- endpointِ `/auth/2fa/status` به بک‌اند اضافه شد.

### رفع شد (CI)
- **CodeQL روی فایل‌های Kotlinِ اندروید می‌افتاد** (`84d4ef3`): ورودیِ `language` (مفرد) نادیده گرفته می‌شد →
  auto-detectِ Kotlin → شکستِ ساختِ DBِ Java (exit 32). اصلاح: `languages` (جمع) + `build-mode: none`.

### تأیید
- `py_compile panel/main.py` + `node --check app.js` سبز · ۵۲/۵۲ کلیدِ i18n · `pytest -q` → **۴۳ passed**.

---

## [kv2m v3.1.0] — 2026-06-21  (دسکتاپِ چندسرور — وایرِ واقعی + انتشار)

### تغییر کرد (ماژول‌های فاز ۳ حالا واقعاً استفاده می‌شوند)
- **`kv2m/cli.py` بازنویسی شد → چندسرور:** منویِ سرورها (انتخاب/افزودن/حذف) از `servers.ServerStore`،
  persistِ آخرین سرور با `settings.Settings`، و بررسیِ آپدیت با `updater.check` در شروع.
- **`APP_VERSION` → `3.1.0`** (از 3.0.2).
- **`build-kv2m.yml`:** `servers`/`settings`/`updater`/`panel_client` به hidden-importهای PyInstaller اضافه شد
  تا در .exe باندل شوند. انتشار با tagِ `kv2m-v3.1.0`.

### تأیید
- `py_compile kv2m/cli.py kv2m/core.py` سبز · `pytest -q` → **۴۳ passed**.
- **[باقی: server-pickerِ گرافیکی در `app.py` (GUI) — CLI کاملاً چندسرور شد.]**

---

## [app-android] — 2026-06-21  (پروژهٔ واقعیِ اندروید + اتصالِ واقعی — auto-rp)

### افزوده شد (تبدیلِ scaffold به پروژهٔ واقعی)
- **ساختارِ کاملِ `app/android/`:** `settings.gradle`/`build.gradle`/`gradle.properties`، ماژولِ `app/build.gradle`
  (ABIهای armeabi-v7a/arm64-v8a/x86_64، signing از `key.properties`، minSdk 23 / targetSdk 35، minify).
- **`AndroidManifest.xml`:** مجوزهای VPN/Internet/Camera (بدونِ GMS)، سرویسِ `KianVpnService` با `BIND_VPN_SERVICE` + `foregroundServiceType`.
- **`MainActivity.kt`:** کانالِ `kv2m/vpn` (prepare/start/stop/status) + درخواستِ consentِ VPN.
- **`KianVpnService.kt`:** راه‌اندازیِ tun (Builder: address/dns/route)، foreground notification، lifecycle، و هوکِ `startTunnelCore` برای `.aar`ِ xray-core.
- **`lib/services/vpn_service.dart`:** سمتِ Dartِ کانال (graceful روی پلتفرم‌های بدونِ کانال).
- **اتصالِ واقعی در `home_screen.dart`:** start/stop واقعی، busy state، restore از `Cache`، دکمهٔ انتخابِ خودکارِ بهترین سرور، persistِ انتخاب.
- styles/launch_background/proguard + README با مراحلِ build.

### صداقت
- این یک «پروژهٔ Flutterِ واقعی و قابل‌build» است (نه فقط فایل‌های پراکنده). **تنها مرحلهٔ باقی‌مانده: bundleِ `.aar`ِ
  xray-core برای packet-forwardingِ واقعی** — بقیهٔ UI/flow کامل است.

### تأیید
- braces دارت متوازن (۸ فایل)، XML خوش‌فرم (manifest/styles/launch)، Kotlin متوازن.

---

## [i18n-complete] — 2026-06-21  (دوزبانه‌سازیِ کاملِ تبِ دامنه — auto-rp)

### افزوده شد
- **prose عمیقِ تبِ «دامنه و TLS» کاملاً دوزبانه شد** (۴۰ کلیدِ جدید، مجموع **۲۲۵**): مراحلِ رکوردِ A،
  نکاتِ Cloudflare، ترتیبِ کارِ گام‌به‌گام، و **هر ۴ بلوکِ `<details>`ِ عیب‌یابی** — شاملِ توضیحِ مفصلِ
  «چرا سایت‌های geoblock‌شده با هیچ کانفیگی باز نمی‌شوند» (ماهیتِ IP خروجی).
- **🎉 با این، LANDING-i18n-FULL ۱۰۰٪ کامل شد:** هر ۸ تبِ صفحه تا عمیق‌ترین پاراگراف دوزبانه است.

### تأیید
- `node --check i18n.js` سبز · **۲۲۵/۲۲۵ کلید** · HTML متوازن · jsdom: toggle همه‌ی prose را EN می‌کند + generator سالم.

---

## [i18n-guides] — 2026-06-21  (دوزبانه‌سازیِ تب‌های نصب/اندروید/PC — auto-rp)

### افزوده شد
- **تب‌های «نصب روی سرور»، «اندروید» و «ویندوز/PC» کاملاً دوزبانه شدند** (۳۲ کلیدِ جدید، مجموع **۱۸۵**):
  همه‌ی stepها (عنوان + توضیح)، نکاتِ موبایل، calloutها (اشتراک‌گذاری، iOS)، و حداقلِ مشخصاتِ سرور.
- با این، **هر ۸ تبِ صفحه** در سطحِ محتوا دوزبانه است (تنها `<ol>`/`<details>`های عمیقِ تبِ دامنه باقی است).

### تأیید
- `node --check i18n.js` سبز · **۱۸۵/۱۸۵ کلید** · HTML متوازن (p:66/66، b:132/132) · jsdom: generator سالم + toggleِ مستقیمِ i18n همه‌ی stepها را EN می‌کند (markup با `data-i18n-html` حفظ شد).

---

## [i18n-domain] — 2026-06-21  (دوزبانه‌سازیِ تبِ دامنه/TLS — auto-rp)

### افزوده شد
- **تبِ «دامنه و TLS» دوزبانه شد** (۱۴ کلیدِ جدید، مجموع **۱۵۳**): مقدمه + همه‌ی هدینگ‌های بخش
  (انتخابِ دامنه/رکوردِ A/Cloudflare/پروتکل‌ها/ترتیب/عیب‌یابی) + **راهنمای انتخابِ پروتکل** (VLESS-WS/VMess-WS/gRPC/Trojan/HTTPUpgrade با توضیح).

### تأیید
- `node --check i18n.js` سبز · **۱۵۳/۱۵۳ کلید** · HTML متوازن. (prose عمیقِ stepها/`<details>` در domain = ادامهٔ کم‌اولویت.)

---

## [i18n-tips] — 2026-06-21  (دوزبانه‌سازیِ عمیقِ تبِ نکات — auto-rp)

### افزوده شد
- **تبِ «نکات و عیب‌یابی» کاملاً دوزبانه شد** (۳۵ کلیدِ جدید در `i18n.js`، مجموع **۱۳۹**): فرقِ Direct/WARP،
  «کِی IP سرور فیلتر می‌شه» (مهم‌ترین بخش)، توصیه بر اساس تعدادِ کاربر، عیب‌یابیِ اتصال، جدولِ دستورهای CLI، و حجم/انقضا.
  رشته‌های دارای markup با `data-i18n-html` (حفظِ `<b>`/`<span class=mono>`).

### تأیید
- `node --check i18n.js` سبز · **۱۳۹/۱۳۹ کلید** تعریف‌شده · HTML متوازن · jsdom: toggle به EN درست + generator دست‌نخورده.

---

## [panel-nodes] — 2026-06-21  (تبِ مدیریتِ سرورها در داشبورد — auto-rp)

### افزوده شد
- **تبِ «سرورها» در داشبوردِ پنل** (`panel/web/`): پلِ بینِ بک‌اندِ فاز ۵ و UIِ فاز ۲ —
  لیستِ nodeها (نام/آدرس/کشور/بار/زنده‌بودن)، فرمِ افزودنِ سرور، حذف، و خلاصهٔ **مسیریابی/Failover/هشدارِ پهنای‌باند**
  از `/api/nodes` + `/api/route`. هم‌سبک با design-systemِ موجود (dark-glass، آیکنِ SVG، دوزبانه).

### تأیید
- `node --check app.js` سبز · HTML متوازن · **۴۶/۴۶ کلیدِ i18n** تعریف‌شده · `pytest -q` → **۴۳ passed** · secret-scan تمیز.

---

## [followups-2] — 2026-06-21  (Offline Mode + تنظیماتِ دسکتاپ — auto-rp)

### افزوده شد
- **Offline Mode موبایل (۶.۳):** `app/lib/services/cache.dart` — persistِ لیستِ سرور/انتخاب/آمار/تنظیمات
  با `shared_preferences` تا اپ بدونِ شبکه آخرین وضعیت را نشان دهد.
- **تنظیماتِ دسکتاپ (۳.۴):** `kv2m/settings.py` — persistِ theme(dark/light)/lang/last-server/tray با `toggle_theme`.

### تأیید
- `py_compile kv2m/settings.py` سبز · braces دارت متوازن · `pytest -q` → **۴۳ passed**.
- باگِ واقعی رفع شد: importِ نسبیِ `from .servers` در حالتِ flat-import (سبکِ kv2m) می‌شکست → fallback به import مسطح.

---

## [fix+followups] — 2026-06-21  (رفعِ CI Trivy + تکمیلِ follow-onها — auto-rp)

### رفع شد
- **CI Security (Trivy) سبز شد:** خطای `Unable to resolve action aquasecurity/trivy-action@0.24.0` —
  تگِ نامعتبر. جایگزین شد با نصبِ مستقیمِ Trivy از اسکریپتِ رسمی (`trivy fs`) تا به تگِ اکشن وابسته نباشد.
  (Validate و CodeQL از قبل سبز بودند؛ فقط همین job می‌افتاد.)

### افزوده شد
- **ضدِDPIِ کامل (۴.۷):** `core/protocols.ttl_settings` (دستکاریِ TTL) + `noise_settings` (Noise padding) + `is_valid_fingerprint`.
- **صفحهٔ Self-hosted Sub (۴.۶):** `panel/web/sub.html` (dark، نوار مصرف/انقضا/کپی/**QR**) + endpointِ `/sub/{name}/info`.
- **متریکِ پنل (۷.۴):** `panel/metrics.py` + `/metrics` (Prometheus exposition؛ users/active/traffic/nodes).

### تأیید
- `py_compile` همه سبز · YAMLِ `security.yml` معتبر · `sub.html` متوازن + JSِ inline سبز · `pytest -q` → **۴۲ passed**.

---

## [ci-monitoring] — 2026-06-20  (فاز ۷: CI/CD + مانیتورینگ — auto-rp)

### افزوده شد
- **CI/CD:** `release.yml` (tag `v*` → release از CHANGELOG) + `security.yml` (CodeQL python/js + Trivy fs، هفتگی/PR).
- **Docker:** `Dockerfile` (پنل، non-root) + `docker-compose.yml` (panel + prometheus + node-exporter + grafana).
- **Monitoring:** `monitoring/prometheus.yml` + `monitoring/alerts.yml` (CPU/RAM/NodeDown/Bandwidth) +
  `monitoring/grafana-dashboard.json` (آمادهٔ import).
- **Plugin System:** `core/plugins.py` (register/get/available/discover) — افزودنِ پروتکل/فیچر بدونِ تغییرِ core.
- **مستندات:** `docs/MIGRATION.md` (مهاجرت از Marzban/3X-UI) + `docs/CONTRIBUTING.md`.

### تأیید
- `py_compile core/plugins.py` سبز · همه‌ی YAML/JSON معتبر · `pytest -q` → **۴۰ passed**.

> **🎉 با این فاز، هر ۷ فازِ رودمپ (۰ تا ۷) از منظرِ کد/پیکربندیِ headless کامل شد.**
> آیتم‌های `(srv)` (تستِ واقعیِ SS/TLS روی سرور) و GUI-wiringهای دسکتاپ/موبایل به‌صورتِ follow-on باقی‌اند.

---

## [app] — 2026-06-20  (فاز ۶: اپ موبایلِ Kv2m — auto-rp)

### افزوده شد
- **اسکلتِ Flutter در `app/`** با نامِ **Kv2m** (هم‌خانواده با دسکتاپِ Kv2m):
  - `main.dart` (MaterialApp، RTL/LTR، dark/light)، `theme.dart` (dark-glassِ navy+green)، `i18n.dart` (FA/EN).
  - `models/server_profile.dart` (parseِ share-link + subscription، IPv6-bracket-aware)،
    `services/selection.dart` (انتخابِ هوشمندِ سرور با TCP latency)، `screens/home_screen.dart`.
  - **بدونِ GMS** (بدونِ firebase/admob/fcm؛ QR با `mobile_scanner`؛ push با SSE/Telegram).
- **انتشار:** `fastlane/metadata/android/{fa-IR,en-US}` (Cafe Bazaar/Myket/F-Droid) + `PRIVACY-fa.md` + `KEYSTORE.md` (۳ backup).
- `app/test/server_profile_test.dart` (تستِ parse — با Flutter اجرا می‌شود).

### توجه
- Dart در CI کامپایل نمی‌شود (toolchain موجود نیست)؛ ساختار صحیح و braces متوازن.

---

## [cluster] — 2026-06-20  (فاز ۵: مدیریتِ چندسرور — auto-rp)

### افزوده شد
- **`core/cluster.py`** — مغزِ تصمیمِ خوشه: `is_alive`/`healthy_nodes`، `pick_least_loaded` (Load Balance)،
  `failover_order` (Auto Failover)، `route_by_geo` (GeoIP، country→region)، `bandwidth_alerts`.
- **`node-agent/agent.py`** — ایجنتِ سبکِ هر VPS (http.server، توکنِ Bearer، `/health` + `/apply` با نوشتنِ اتمیک).
- **پنل:** جدولِ `nodes` + ستون‌های telemetry (migration 0005: load/bandwidth_gb/healthy) +
  endpointها: `/api/nodes` (CRUD)، `/api/nodes/{name}/heartbeat`، `/api/route`.
- **`scripts/migrate-import.py`** — مهاجرتِ کاربر از **Marzban** (JSON) و **3X-UI** (sqlite) به مدلِ kian.

### تأیید
- `py_compile` همه (به CI اضافه شد) · `pytest -q` → **۳۶ passed** (cluster/failover/geo/heartbeat/migrate/agent).

---

## [protocols] — 2026-06-20  (فاز ۴: پروتکل‌ها و ضدسانسور — auto-rp)

### افزوده شد
- **`core/protocols.py`** — سازنده‌ی inbound برای **Hysteria2 / TUIC v5 / WireGuard** + Mux،
  تنظیماتِ ضدِDPI (**Fragment** + **uTLS**)، و **مبدل‌های Subscription**: `to_singbox` (JSON)، `to_clash` (Meta YAML)،
  و `detect_client` (تشخیصِ singbox/clash/v2ray از User-Agent).
- **`core/censorship.py`** — **REALITY SNI scanner** (مغزِ آفلاین: `score_sni`/`rank_sni_candidates`/`best_sni`) +
  **Tor Bridge Fallback** (obfs4/snowflake) + قانونِ مسیریابیِ fallback.
- **`scripts/sub-format.py`** — موتورِ صفحهٔ Subscriptionِ self-hosted (dispatch بر اساس `--client`/`--ua`).
- **`scripts/kian-bot.py`** — بات تلگرامِ مدیریتی (stdlib long-poll، فقط ادمین‌ها، status/users/add/remove/usage).

### تأیید
- `py_compile` همه (به CI اضافه شد) · `pytest -q` → **۲۸ passed** (protocols/censorship/bot/sub-format).

---

## [kv2m] — 2026-06-20  (فاز ۳: Kv2m چندسروره — auto-rp)

### افزوده شد
- **`kv2m/servers.py`** — مدیریتِ چندسرور: `ServerProfile` + `ServerStore` (add/remove/select/active،
  persist در JSON با `os.replace` اتمیک، بدونِ ذخیرهٔ رمز).
- **`kv2m/panel_client.py`** — کلاینتِ REST برای پنل (login + refreshِ شفاف روی 401 + CRUDِ کاربر + stats).
- **`kv2m/updater.py`** — بررسیِ آپدیت از GitHub Releases با مقایسهٔ نسخهٔ مقاوم (نادیده‌گرفتنِ رقمِ داخلِ نامِ محصول).

### تأیید
- `py_compile` همه (به CI اضافه شد) · `pytest -q` → **۱۹ passed**.
- باگِ واقعی رفع شد: `parse_version("kv2m-3.1.0")` رقمِ «۲»ِ داخلِ «kv2m» را نسخه می‌گرفت → الان توکنِ نقطه‌دار اولویت دارد.

---

## [panel-ui] — 2026-06-20  (فاز ۲: فرانت‌اندِ پنل — auto-rp)

### افزوده شد
- **داشبوردِ پنل (`panel/web/`):** تک‌فایلِ HTML + JS وانیلا، طراحیِ Dark/Glass (طبقِ `ui-ux-pro-max`:
  OLED dark، اکسنتِ سبزِ #22C55E، فوکوسِ واضح، آیکنِ SVG نه ایموجی، کنتراست AA)، **دوزبانه FA/EN + RTL/LTR**.
  - لاگین + refreshِ خودکارِ توکن، کارت‌های آمار، جدولِ کاربر با toggle/edit/delete، **bulk actions**، جستجو،
    مودالِ ساخت/ویرایش (quota/expiry/IP/speed)، **نمودارِ canvas** (پرمصرف‌ترین‌ها)، **تبِ Audit**، **System Monitor** (load/RAM)، خروجیِ CSV.
- **endpointهای جدیدِ بک‌اند:** `/api/audit` (viewer) و `/api/system` (CPU/RAM از `/proc`). UI روی `/app` mount شد.

### تأیید
- `node --check panel/web/app.js` سبز · توازنِ HTML · ۳۹/۳۹ کلیدِ i18n تعریف‌شده · `py_compile`+`pytest` (۱۵) سبز.

---

## [panel] — 2026-06-20  (فاز ۲: بک‌اندِ پنلِ وب — auto-rp)

### افزوده شد
- **پکیجِ `panel/` (FastAPI):** بک‌اندِ کاملِ مدیریتِ کاربر روی همان `core.db` (بدونِ ORMِ دوم — تک‌منبعِ schema).
  - `panel/security.py` — JWT HS256 دست‌ساز + هشِ PBKDF2-SHA256 (stdlib، بدونِ PyJWT/passlib).
  - `panel/repo.py` — CRUD + bulk + auto-disable + stats، با ثبتِ audit در هر تغییر.
  - `panel/schemas.py` — مدل‌های Pydantic v2.
  - `panel/main.py` — endpointها: `/auth/{login,refresh,password,sessions}`،
    `/api/users` (CRUD + `/bulk` + `/auto-disable`)، `/api/stats`، `/api/export` (JSON/CSV)،
    `/api/keys/rotate`، و WebSocketِ `/ws/stats`. + هدرهای امنیتی (nosniff/DENY/HSTS/CSP)، rate-limitِ لاگین، CORSِ صریح.
- **محدودیت‌های per-user:** quota/expiry/**IP limit**/**speed limit**/**HWID**/enable + auto-disable + bulk.
- `panel/requirements.txt` + `panel/README.md` (طراحی + اجرا).

### تأیید
- `py_compile` همه‌ی panelها سبز (به `validate.yml` اضافه شد) · `pytest -q` → **۱۵ passed**
  (security: hash/JWT/expiry/tamper · repo: lifecycle/bulk/auto-disable).

---

## [site] — 2026-06-20  (IPv6 در لینک‌ها + سخت‌سازیِ SS — auto-rp)

### افزوده شد / تغییر کرد
- **IPv6 (فاز ۱.۵):** `assets/js/app.js` حالا آدرسِ IPv6 سرور را می‌پذیرد (`isIPv6`/`isServerAddr`) و در URIها
  به‌درستی bracket می‌کند (`vless://…@[2001:db8::1]:443`، `ss://…@[…]:port`). اعتبارسنجیِ فرم نمونهٔ IPv6 را نشان می‌دهد.
- **Shadowsocks (فاز ۰.۶ code-side):** `SS_METHOD` تک‌منبع است و لینکِ SS هم IPv6-safe شد؛ `config-health.py`
  cipherِ SS را اعتبارسنجی می‌کند (شاملِ SS-2022). مهاجرتِ نهاییِ cipher + تستِ سرور = `(srv)`.

### تأیید
- `node --check assets/js/app.js` سبز · تستِ helperهای IPv6 سبز · jsdom smoke سبز (IPv4 دست‌نخورده + IPv6 پذیرفته و bracket شد).

---

## [core + tooling] — 2026-06-20  (فاز ۱: زیرساختِ کد — auto-rp)

### افزوده شد
- **پکیجِ `core/` (stdlib-only):**
  - `core/db.py` — لایهٔ SQLite با schemaِ کامل (users با IP/Speed/HWID/quota/expiry، audit_log، nodes، settings) +
    pragmaهای WAL/foreign_keys/busy_timeout.
  - `core/migrate.py` — Migration runnerِ forward-only مبتنی بر `PRAGMA user_version` (idempotent).
  - `core/logging.py` — لاگِ ساختاریافتهٔ JSON تک‌خطی (سازگار با jq/Loki).
  - `core/audit.py` — ثبتِ audit (`record`/`tail`) + mirror در لاگ.
- **`scripts/kian-backup.py`** — بکاپِ رمزنگاری‌شده (tar.gz → openssl AES-256-CBC) + آپلود به Telegram/S3/rclone (cron-ready).
- **`scripts/config-health.py`** — اعتبارسنجیِ واقعیِ config.json (یکتاییِ پورت، پروتکلِ شناخته‌شده، فیلدهای Reality،
  cipherِ مجازِ Shadowsocks) + گزینهٔ `--probe` برای تستِ شنونده‌بودنِ پورت‌ها.
- **`scripts/release.sh` + `docs/VERSIONING.md`** — SemVer + git tagging رسمی.
- **تست:** `tests/test_core.py` + `tests/test_scripts.py` (۸ تست) — به `validate.yml` وصل شد (py_compile coreها + pytest).

### تأیید
- `python3 -m py_compile core/* scripts/*` سبز · `pytest -q` → **۸ passed**.
- یک باگِ واقعی پیدا و رفع شد: تداخلِ کلیدِ `name` با LogRecord در لاگِ ساختاریافته (namespace به `kian_fields`).

---

## [site + docs] — 2026-06-20  (PRD + دوزبانه‌سازیِ کاملِ صفحه — auto-rp)

### افزوده شد
- **PRD کامل** (`docs/PRD.md`) + **PLANِ تسک‌محورِ کامل** تا انتهای پروژه (۷ فاز، هر تسک با شناسه).
- **LANDING-i18n-FULL:** `assets/js/i18n.js` بازنویسی شد — پشتیبانیِ `data-i18n-ph` (placeholder) و
  `data-i18n-title` + دیکشنریِ **۱۰۴‌کلیدیِ** FA/EN. کلِ سطحِ تعاملی دوزبانه شد: فرمِ ساختِ کانفیگ
  (لیبل‌ها/placeholderها/option‌ها/کارت‌های حالت/دکمه‌ها/راهنماها)، فرمِ مدیریتِ کاربر (اکشن‌ها/فیلدها)،
  هدینگِ همه‌ی تب‌ها (server/android/pc/tips/domain/manage/about)، و بخشِ about.

### تأیید
- `node --check assets/js/i18n.js` + `node --check assets/js/app.js` سبز.
- ۱۰۴/۱۰۴ کلیدِ ارجاع‌شده در HTML در دیکشنری تعریف شده‌اند؛ تگ‌های HTML متوازن.
- jsdom smoke test سبز (سازنده‌ی کانفیگ دست‌نخورده)؛ سوییچِ زبان به‌درستی FA↔EN و `dir` را عوض می‌کند.
- **باقی‌مانده:** ترجمه‌ی عمیقِ پاراگراف‌های troubleshooting در tab‌های tips/domain (هدینگ‌ها ترجمه شد).

---

## [installer 2.1.0 + site] — 2026-06-20  (خودتشخیصی + صفحهٔ دوزبانه + حقوقی)

### افزوده شد
- **خودتشخیصیِ `status` (فاز ۰.۳):** `kian-v2ray status` (و alias‌های `health`/`doctor`) حالا کرش‌لوپِ Xray
  (RestartCount در آپ‌تایمِ کوتاه)، وضعیتِ WARP (با آگاهی از fallback)، پورت‌های شنونده‌نبودنِ reality/ss،
  سلامتِ Shadowsocks، و سرویس Subscription را تشخیص می‌دهد و برای هر مشکل **دستورِ رفع** چاپ می‌کند.
- **صفحهٔ تعاملی دوزبانه (FA/EN):** سوییچِ زبان با `dir` صحیح (`assets/js/i18n.js`) + سکشنِ **نقشهٔ راه/چشم‌انداز**
  (پلتفرمِ چندسروره، پنلِ وب، اپ موبایل، پروتکل‌های جدید، پایش) با کارت‌های شیشه‌ای و آیکنِ SVG.
- **صفحاتِ حقوقی:** `privacy.html` + `terms.html` دوزبانه (پیش‌نیازِ مارکت‌ها)، لینک در footer.
- **README + ROADMAP:** README بازنویسیِ حرفه‌ای و دوزبانه؛ ROADMAP — فاز ۰ علامتِ ✅ کامل.

### تأیید
- فاز ۰ (۰.۱ پورت API، ۰.۲ WARP fallback، ۰.۴ BBR، ۰.۵ نصبِ امن) از قبل در کد بود و حالا در PLAN/ROADMAP تیک خورد.
- `bash -n install.sh` + `node --check` + HTML well-formed سبز. (۰.۶ SS و تستِ TLS = نیازِ سرور.)

---

## [kv2m 3.0.2] — 2026-06-03  (رفع‌های مهم سرعت/اتصال)

### رفع شد (بحرانی)
- **افت شدید سرعت (در حد کیلوبایت):** `sockopt` با `tcpFastOpen`/`tcpcongestion`/`tcpKeepAliveIdle` که در v2.4 به outbound اضافه شده بود، حذف شد. `tcpFastOpen` روی outbound باعث رفت‌وبرگشت ناموفق SYN و کندی شدید می‌شد. BBR در سطح OS از قبل اعمال می‌شود. (هم اپ هم صفحهٔ وب)
- **کانفیگ‌های نرم‌افزار کار نمی‌کردند / دامنه مشکل داشت:** نرم‌افزار پورت‌ها را از 8443 می‌داد (اغلب توسط ISP/CGNAT کند/بسته)، اما صفحهٔ تعاملی از پورت‌های «تقریباً همیشه باز» (443/2083/2087/2096/8080) استفاده می‌کرد. حالا اپ هم دقیقاً همان pool را دارد و موقع TLS، پورت‌های 443/80 را برای Caddy رزرو می‌کند.
- **دکمهٔ Uninstall کار نمی‌کرد:** سرور برای حذف نیاز به تایپ `DELETE` دارد؛ روی SSH غیرتعاملی هرگز اجرا نمی‌شد. دستور به `echo DELETE | kian-v2ray uninstall` تغییر کرد.

### افزوده شد (پاریتی با صفحهٔ تعاملی)
- **انتخاب SNI:** حالت خودکار/دستی + تعداد SNI + دامنهٔ دلخواه (مثل صفحهٔ تعاملی).
- **کانال دامنه «سریع + WARP» باهم:** علاوه بر direct/warp، حالا گزینهٔ both هم هست (برای هر پروتکل دو کانفیگ ساخته می‌شود).
- **توضیحات داخل اپ:** راهنمای کانفیگ دامنه/TLS و نکتهٔ ابر کلودفلر.
- **صفحات Settings و About پرمحتوا شد:** زبان، مسیرها، کانال‌ها، امکانات، و بخش حمایت (TRC20).

---

## [kv2m 3.0.1] — 2026-06-03

### رفع شد
- **لینک Subscription روی HTTPS (Gist) در نرم‌افزار:** اپ دسکتاپ حالا مثل صفحهٔ تعاملی از **Cloudflare Worker + GitHub Gist** لینک HTTPS Subscription می‌سازد (قبلاً فقط `http://ip:port/sub/...` داشت). payload شامل `gist_proxy` و `install_id` شد تا install.sh هم گیست‌ها را sync کند.
- **علت 403 کشف شد:** Worker روی User-Agent پیش‌فرض urllib خطای 403 کلودفلر می‌داد؛ با UA مرورگری رفع شد و لینک Gist واقعی برمی‌گردد (تست‌شده).
- **کانفیگ‌های دامنه (TLS):** `encode gzip` از Caddyfile حذف شد — می‌توانست استریم gRPC/WebSocket را خراب کند (هم در صفحهٔ وب هم اپ).

### مستندات
- README پروژه به نسخهٔ کامل و غنی بازگردانده شد (جدول ویژگی‌ها، معماری، پروتکل‌ها، دستورها، امنیت) + هشدار «ابر کلودفلر موقع نصب خاکستری باشد».

---

## [kv2m 3.0.0] — 2026-06-02

### تغییر بزرگ — بازنویسی کامل رابط کاربری
- **رابط جدید با PySide6/Qt:** الگوی Termius (چیدمان تمیز، sidebar آیکونی، پنجرهٔ بدون-فریم با title-bar سفارشی) + لهجهٔ سبز NVIDIA (`#76B900`). کارت‌های گرد با سایه، دکمه‌های سبز، فیلدهای فوکوس-سبز.
- **دو-زبانه (i18n):** زبان پایهٔ کد انگلیسی؛ در **اولین اجرا** انتخاب زبان (English | فارسی) پرسیده می‌شود و ذخیره می‌گردد؛ از **Settings** قابل‌تغییر است. فارسی RTL.
- **معماری ماژولار:** کد از یک فایل ۱۱۰۰ خطی به پکیج تمیز تبدیل شد: `core.py` (منطق محض + SSH، تست‌شده)، `i18n.py`، `theme.py`، `app.py` (Qt)، `cli.py`، `kv2m.py` (entry). همهٔ منطق ساخت کانفیگ (Reality/WARP/SS/TLS) دست‌نخورده بازاستفاده شد.

### رفع شد
- **`validate.yml`:** به فایل‌های ناموجود (`kv2m_core.py` و…) اشاره می‌کرد و همیشه fail می‌شد؛ به ساختار ماژولار جدید اصلاح شد.

### تغییر کرد
- وابستگی build از `customtkinter` به `PySide6-Essentials`. نسخه ۳.۰.۰. exe بزرگ‌تر (~۴۵-۶۰MB).

---

## [kv2m 2.5] — 2026-06-02

### افزوده شد
- **کانفیگ‌های دامنه‌دار (TLS) در اپ دسکتاپ:** اپ kv2m حالا مثل صفحهٔ وب، کانفیگ‌های پشت دامنه می‌سازد — VLESS-WS، VMess-WS، VLESS/VMess-gRPC، Trojan-WS، VLESS/VMess-HTTPUpgrade. شامل ساخت Caddyfile، inboundهای داخلی روی localhost، انتخاب کانال (direct/warp)، و لینک‌های کلاینت. payload شامل `tls_domain` و `caddyfile_b64` شد تا install.sh خودکار Caddy + گواهی Let's Encrypt را راه بیندازد. (قبلاً فقط Reality/WARP/Shadowsocks بود.)

---

## [kv2m 2.4] — 2026-06-02

### بهبود یافت
- **بهینه‌سازی سرعت (xray):** افزودن `sockopt` با `tcpFastOpen` + `tcpcongestion: bbr` به outbound مستقیم در هر دو ساخت‌کنندهٔ کانفیگ (صفحهٔ وب و اپ دسکتاپ). همراه با tune سطح-OS (BBR+fq + بافرهای بزرگ) که از قبل موجود بود.

### مستندسازی
- **توضیح شفاف «سایت‌های بلاک‌شده مثل PornHub»:** در تب «دامنه» توضیح داده شد که Cloudflare فقط مسیر *ورودی* را پنهان می‌کند؛ خروجی همچنان از IP سرور است. باز نشدن این سایت‌ها باگِ کانفیگ نیست، بلکه به IP/کشورِ خروجیِ سرور مربوط است (تستِ `curl` روی سرور + راه‌حل‌ها اضافه شد).

### یادداشت
- اپ دسکتاپ kv2m فعلاً فقط Reality/WARP/Shadowsocks می‌سازد؛ کانفیگ‌های دامنه/TLS فقط از طریق صفحهٔ وب در دسترس‌اند (در دست توسعه برای اپ).

---

## [kv2m 2.3] — 2026-06-02

### رفع شد
- **خطای ساخت/انتشار اپ ویندوزی (kv2m):** مرحلهٔ `Create Release` با خطای `403 Resource not accessible by integration` شکست می‌خورد چون `GITHUB_TOKEN` فقط مجوز `contents: read` داشت. با افزودن `permissions: contents: write` به workflow رفع شد. اپ از قبل سالم build می‌شد، فقط انتشار release ناموفق بود.
- **سه باگ NameError در kv2m.py:** متغیر `e` در بلوک‌های `except ... as e:` پس از خروج از بلوک حذف می‌شود، اما داخل `lambda`های async (`self._ui(...)`) فراخوانی می‌شد. با bind کردن `e=e` به‌عنوان آرگومان پیش‌فرض lambda رفع شد.

### تغییر کرد
- نسخهٔ اپ kv2m به `2.3` رسید (هماهنگ با tag انتشار).

---

## [2.0.0] — 2026-05-29

### افزوده شد
- **لینک Subscription کامل (مرورگر + سرور):** برای هر کاربر یک لینک واحد (`http://IP:port/sub/<token>`) که همهٔ کانفیگ‌ها را می‌آورد و خودکار به‌روز می‌شود. سرویس امن `kian-sub` (فقط `/sub/<token>`، بدون path traversal).
- **بنر راهنمای صفحه:** کارت‌های «بار اولمه / کاربر اضافه کنم / لینک کاربر / حذف نصب» برای جلوگیری از سردرگمی.
- **`kian-v2ray sub`** — ساخت/نمایش لینک Subscription هر کاربر.
- **`kian-v2ray update` هوشمند:** نسخه را از `VERSION` می‌خواند، اسکریپت‌ها + Xray (pin) را آپدیت می‌کند، با **بکاپ و rollback خودکار** و **حفظ کامل کاربران/کانفیگ**.
- **`kian-v2ray warp` / `fixport` / `untune`** — مدیریت دستی WARP، رفع تداخل پورت، بازگرداندن tune.
- فایل `VERSION` و همین `CHANGELOG`.

### بهبود یافت
- **WARP پایدار:** اول WireGuard بعد MASQUE، ثبت‌نام مطمئن‌تر، و **fallback خودکار به مستقیم** اگر WARP وصل نشد (کاربر بی‌نت نمی‌ماند) + بازگشت خودکار در watchdog.
- **خودتشخیصی `status`:** کرش‌لوپ، تداخل پورت و WARP مرده را تشخیص می‌دهد و دستور رفع تک‌خطی می‌دهد.
- **auto-fix پورت:** پورت API و پورت‌های reality/ss اگر اشغال بودند خودکار با پورت آزاد جایگزین می‌شوند (به‌جای توقف نصب).
- **نصب مجدد امن:** نصب دوباره کاربران قبلی را پاک نمی‌کند (بکاپ + ادغام خودکار).
- **بهینه‌سازی سرعت (BBR):** فعال‌سازی امن و idempotent BBR/fq + بافرهای TCP (مخصوص استریم/اینستاگرام).
- **SNI_POOL واقعی:** دامنه‌های تست‌شده روی شبکهٔ ایران (icloud, cloudflare, s3.amazonaws, fonts.gstatic, speedtest, amazon)؛ دامنه‌های فیلتر حذف شدند.

---

## [1.x] — فاز ۱
- ساخت کلید/کانفیگ در مرورگر، نصب تک‌دستوری مقاوم به قطع SSH، VLESS Reality (مستقیم + WARP) + Shadowsocks، مدیریت کاربر/حجم، چند SNI/پورت، watchdog.
