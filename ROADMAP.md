# 🗺️ نقشهٔ راه — KIAN V2RAY + Kv2m (نسخه ۲.۴)
> از ابزار CLI تا پلتفرم VPN + Multi-Server + اکوسیستم موبایل.
> **این فایل = ادغامِ بهینهٔ رودمپ v2.4 + باگ‌فیکس‌های بحرانیِ فعلی + وضعیت done.**
> جزئیاتِ پیاده‌سازیِ تسک‌محور (db schema، panel/app.py و…) در `ROADMAP-legacy.md` و suggestها بایگانی شد.

---

## ✅ وضعیت فعلی (Done) — به‌روزرسانیِ 2026-06-20 (نسخهٔ نصب‌کننده **v2.1.0**)
- **صفحهٔ تعاملی (browser):** ساخت کلید X25519 کاملاً در مرورگر (مزیت اختصاصی)، چند SNI/پورت خودکار، حالت‌های سریع/WARP/هردو/بدون‌SNI، نصب ایزولهٔ مقاوم به قطع SSH. **+ دوزبانه (FA/EN) + سکشنِ رودمپ** + لینکِ privacy/terms.
- **Subscription سه‌لایه:** Gist HTTPS (Cloudflare Worker) + چندپورت محلی + کانفیگ‌های تکی.
- **TLS دامنه‌دار:** VLESS/VMess/Trojan روی WS/gRPC/HTTPUpgrade پشت Caddy :443 + گواهی خودکار Let's Encrypt.
- **هسته:** VLESS Reality+Vision، WARP outbound، Shadowsocks، Multi-user (UUID/سهمیه/انقضا)، CLI مدیریتی، Watchdog، BBR، Kv2m دسکتاپ (Win/مک/لینوکس + CLI/Termux).
- **✅ فاز ۰ کامل شد (v2.1.0):** auto-fixِ پورت API، WARP fallback، **خودتشخیصیِ `status`/`health`/`doctor`**، BBR، نصبِ مجددِ امن. (فقط ۰.۶ SS باز.)
- **حقوقی:** `privacy.html` + `terms.html` دوزبانه (پیش‌نیازِ مارکت‌ها).

---

## 🔧 فاز ۰ — رفع باگ‌های بحرانی — ✅ کامل شد (v2.1.0، 2026-06-20)
> این‌ها برای پایداری حیاتی بودند و همگی در `install.sh` پیاده و منتشر شدند.

- ✅ **۰.۱ تداخل پورت API:** auto-fix — پورتِ آزادِ تصادفی + تزریق در config + `api.txt`.
- ✅ **۰.۲ پایدارسازی WARP:** `warp_fallback()` (افتِ WARP → خروجی مستقیم، بازگشتِ خودکار) + چکِ اتصالِ socks.
- ✅ **۰.۳ خودتشخیصیِ `status`:** `cmd_status` کرش‌لوپ/WARP/پورت/SS/Subscription را تشخیص می‌دهد و **دستورِ رفع** چاپ می‌کند؛ + alias `health`/`doctor`.
- ✅ **۰.۴ بهینه‌سازی سرعت (BBR):** بخشِ «بهینه‌سازی شبکه» (BBR+fq، امن، idempotent، با verifyِ cc).
- ✅ **۰.۵ نصب مجدد امن:** بکاپِ users/config + ادغامِ کاربرانِ قبلیِ غایب در payload (پاک نمی‌شوند).
- 🟠 **۰.۶ رفع/بازطراحی Shadowsocks:** سلامتِ SS حالا در `status` دیده می‌شود؛ بازطراحیِ کامل **نیازِ تستِ روی سرور** دارد.

---

---

## ۱. تحلیل وضعیت فعلی (Audit)

### ✅ نقاط قوت فعلی
- VLESS Reality + Vision
- WARP Outbound
- Shadowsocks + TLS (Caddy) — VLESS/VMess/Trojan روی WS/gRPC/HTTPUpgrade
- ساخت کلید X25519 کاملاً در مرورگر (**مزیت امنیتی کلیدی — هیچ رقیبی ندارد**)
- Cloudflare Worker + Gist Subscription (HTTPS)
- Multi-user با UUID + سهمیه + انقضا
- CLI مدیریتی `kian-v2ray`
- Watchdog + BBR
- kv2m Desktop (ویندوز/اندروید پایه)
- صفحه تعاملی وب (index.html)
- ساختار منظم: `docs/`, `scripts/`, `worker/`, `kv2m/`
- CHANGELOG.md + SECURITY.md + LICENSE (MIT)

### ❌ گپ‌های رقابتی (اولویت‌دار)
- وب پنل کامل با داشبورد
- IP Limit + Speed Limit + HWID per user
- مدیریت Multi-Server (چند VPS از یک پنل)
- Subscription Page سفارشی با UI زیبا
- آمار ترافیک واقعی + مانیتورینگ سیستم
- Backup/Restore خودکار
- DPI Evasion پیشرفته (Fragment + uTLS)
- REST API + Export
- Hysteria2 / TUIC / WireGuard inbound / Sing-box
- Test Suite + i18n + Privacy Policy
- **[جدید v2.4]** پشتیبانی از مارکت‌های ایرانی (Cafe Bazaar، Myket)
- **[جدید v2.4]** IPv6 کامل
- **[جدید v2.4]** Prometheus + Grafana stack یکپارچه
- **[جدید v2.4]** Config health check خودکار
- **[جدید v2.4]** Tor Bridge Fallback

**مزیت رقابتی غیرقابل کپی:** کلید خصوصی هرگز به سرور ما نمی‌رسد.

---

## ۲. معماری هدف (Target Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│  Browser (index.html)  │  kv2m Desktop  │  Flutter Mobile  │
└──────────────┬─────────────────┬────────────────┬──────────┘
               │                 │                │
               ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│             KIAN Web Panel (FastAPI + React)                │
│      REST API │ JWT Auth │ WebSocket │ i18n (fa/en)        │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ┌─────────────────┼──────────────────┐
         ▼                 ▼                  ▼
   ┌───────────┐     ┌───────────┐      ┌───────────┐
   │  Node 1   │     │  Node 2   │      │  Node N   │
   │ (VPS IR)  │     │ (VPS DE)  │      │ (VPS NL)  │
   │   Xray    │     │   Xray    │      │   Xray    │
   └───────────┘     └───────────┘      └───────────┘
         │
         ├─ Reality inbounds (پورت‌های پویا)
         ├─ Shadowsocks / Hysteria2 / TUIC / WireGuard
         └─ TLS inbounds (پشت Caddy :443)
         ▼
   🌍 اینترنت آزاد

Subscription Layer:
   ├─ Cloudflare Worker + Gist (فعلی)
   └─ Self-hosted Sub Page (فاز ۴ — بدون Cloudflare)

Monitoring Stack (فاز ۷):
   ├─ Prometheus → Node Exporter + Xray Exporter
   └─ Grafana Dashboard (آماده import)

Tor Bridge Fallback (فاز ۴ — جدید v2.4):
   └─ اگر Xray مسدود شد → Tor obfs4 / Snowflake به عنوان fallback
```

---

## ۳. فازبندی توسعه

---

### 🔴 فاز ۱ — پایه‌ریزی و تمیزکاری (۱-۲ هفته)

#### کد و ساختار
- [ ] ریفکتور پروژه: `panel/`, `core/`, `scripts/`, `tests/`, `docs/`
- [ ] SQLite Database + Migration System (Alembic)
- [ ] بهبود Watchdog + یکپارچه‌سازی با Xray Stats API
- [ ] لاگینگ مرکزی (structured JSON logs) + Error Reporting (Sentry)
- [ ] Semantic Versioning رسمی + Git Tagging (`v1.0.0`, ...)
- [ ] **[جدید v2.4]** IPv6 پشتیبانی در تمام inbound‌ها و CLI
- [ ] **[جدید v2.4]** Automated Backup — ارسال خودکار پشتیبان به Telegram/S3/Cloudflare R2
- [ ] **[جدید v2.4]** Audit Log — ثبت تمام اعمال ادمین با زمان و IP (چه کی چه کاری کرد)

#### Testing (جدید — غایب بود)
- [ ] راه‌اندازی pytest
- [ ] Unit test برای core functions (user management، quota، expiry)
- [ ] Integration test برای install.sh در Docker
- [ ] **[جدید v2.4]** Config Health Check — تست خودکار هر کانفیگ برای اطمینان از کار کردن واقعی

#### حقوقی (پیش‌نیاز مارکت‌ها)
- [ ] **Privacy Policy** — صفحه عمومی مستقل (GitHub Pages) — الزامی برای همه مارکت‌ها
- [ ] **Terms of Service** — شرایط استفاده برای multi-user
- [ ] **[جدید v2.4]** صفحه Privacy Policy فارسی جداگانه (الزامی برای Cafe Bazaar و Myket)

---

### 🟠 فاز ۲ — وب پنل کامل (۳-۵ هفته)

#### Backend
- [ ] FastAPI Backend + SQLAlchemy
- [ ] JWT Authentication + Refresh Token
- [ ] REST API مستند با OpenAPI/Swagger
- [ ] WebSocket برای real-time stats (بدون نیاز به refresh)
- [ ] Export داده‌ها (JSON / CSV)
- [ ] **[جدید v2.4]** Session Management — نمایش و مدیریت تمام session‌های فعال ادمین
- [ ] **[جدید v2.4]** Admin Password Recovery — مکانیزم ریست رمز عبور پنل

#### Frontend
- [ ] UI مدرن Dark + Glassmorphism (React یا Vue)
- [ ] CRUD کاربران با فیلتر و جستجو
- [ ] نمودار مصرف ترافیک (Chart.js / Recharts)
- [ ] Backup / Restore پنل
- [ ] System Monitor (CPU، RAM، Network I/O)
- [ ] پشتیبانی **fa + en** (i18n + RTL)
- [ ] **[جدید v2.4]** Audit Log Viewer — مشاهده تاریخچه تمام اعمال ادمین از UI

#### ویژگی‌های مدیریت کاربر پیشرفته
- [ ] **IP Limit per user** — محدود کردن تعداد IP همزمان (مثلاً: max 2 device)
- [ ] **Speed Limit per user** — محدود کردن پهنای باند هر کاربر (KB/s یا MB/s)
- [ ] **HWID / Device Token** — بستن subscription به دستگاه یا token خاص
- [ ] **Auto Disable** — غیرفعال شدن خودکار کاربر پس از انقضا یا اتمام سهمیه
- [ ] **Bulk Actions** — اضافه/حذف/تمدید گروهی کاربران

#### امنیت پنل
- [ ] Reverse Proxy با Caddy + TLS
- [ ] Rate Limiting + Fail2ban
- [ ] 2FA اختیاری (TOTP)
- [ ] IP Whitelist برای ادمین
- [ ] **[جدید v2.4]** Key Rotation — مکانیزم چرخش دوره‌ای کلیدهای X25519 بدون downtime
- [ ] **[جدید v2.4]** CORS Policy صریح + Helmet.js / FastAPI Security Headers

---

### 🟠 فاز ۳ — ارتقای kv2m Desktop (۲-۴ هفته)

- [ ] GUI حرفه‌ای با CustomTkinter یا PyQt6
- [ ] مدیریت **چند سرور** همزمان در یک UI
- [ ] نصب + آپدیت خودکار Xray
- [ ] یکپارچه‌سازی با REST API پنل
- [ ] Auto-update مکانیزم (GitHub Releases)
- [ ] پشتیبانی **macOS** و **Linux** (علاوه بر Windows)
- [ ] Crash Reporting (Sentry Desktop)
- [ ] System Tray Integration
- [ ] **[جدید v2.4]** Dark/Light Mode با تنظیمات ذخیره‌شده

---

### 🟡 فاز ۴ — پروتکل‌های پیشرفته و ضد سانسور (۱-۲ ماه)

#### پروتکل‌های جدید
- [ ] **Hysteria2** — پروتکل UDP-based سریع (برای شبکه‌های پرتأخیر)
- [ ] **TUIC v5** — بهینه برای موبایل و شبکه‌های بی‌ثبات
- [ ] **WireGuard inbound** — برای کاربرانی که WG client دارند
- [ ] **Sing-box** Subscription Format
- [ ] **Clash Meta** Subscription Format
- [ ] **Mux.cool** — multiplexing برای کاهش latency
- [ ] **[جدید v2.4]** Tor Bridge Fallback — وقتی همه پروتکل‌ها بلاک شد، obfs4/Snowflake fallback فعال می‌شود

#### Subscription Page سفارشی
- [ ] **Self-hosted Sub Page** — صفحه با حجم باقی‌مانده، تاریخ انقضا، QR code
- [ ] فرمت خودکار: کلاینت ارسال‌شده را تشخیص بده و فرمت مناسب بده (v2rayNG، Clash، Sing-box)
- [ ] Self-hosted Subscription بدون Cloudflare (Fallback)
- [ ] **[جدید v2.4]** REALITY IP Scanner داخلی — اسکن و پیشنهاد بهترین SNI برای Reality

#### ضد DPI پیشرفته
- [ ] **Fragment Mode** — تکه‌تکه کردن TLS Handshake
- [ ] **uTLS Fingerprint** — جعل fingerprint مرورگر (Chrome، Firefox، Safari)
- [ ] **TTL Manipulation**
- [ ] **Noise Padding** (تزریق بسته‌های بی‌معنی)

#### اتوماسیون
- [ ] **بات تلگرامی پیشرفته** — مدیریت کاربران، گزارش مصرف، اعلان انقضا، خرید و تمدید
- [ ] Webhook رویدادها (انقضا، سهمیه، login جدید از IP ناشناس)
- [ ] **Email Notification** (SMTP) — جایگزین/مکمل تلگرام
- [ ] **[جدید v2.4]** Backup خودکار به Telegram Bot — هر شب یک فایل `.db` رمزنگاری‌شده

---

### 🔵 فاز ۵ — Multi-Server Management (۱-۲ ماه)

> این فاز پروژه را از یک "ابزار VPS شخصی" به یک "پلتفرم مدیریت زیرساخت" تبدیل می‌کند.

- [ ] **Node Agent** — یک سرویس سبک روی هر VPS که با پنل مرکزی ارتباط می‌گیرد
- [ ] **یک پنل → چند VPS** — مدیریت تمام سرورها از یک داشبورد
- [ ] **Node Health Check** — مانیتور خودکار uptime، latency، load
- [ ] **Auto Failover** — اگر یک node خوابید، subscription به node بعدی redirect شود
- [ ] **Load Balancing** — توزیع کاربران بین node‌ها بر اساس لود
- [ ] **GeoIP-based Routing** — کاربر ایرانی → نزدیک‌ترین node
- [ ] Migration Tool از Marzban/3X-UI
- [ ] **[جدید v2.4]** Node Bandwidth Alert — اعلان وقتی bandwidth یک node به آستانه خاصی رسید
- [ ] **[جدید v2.4]** Per-Node Config Override — تنظیمات خاص هر node (مثلاً DPI mode برای IR)

---

### 🔵 فاز ۶ — اپلیکیشن موبایل Flutter (۲-۳ ماه)

#### پیش‌نیازهای Google Play
- [ ] Privacy Policy URL معتبر عمومی (فارسی + انگلیسی)
- [ ] Google Play Developer Account ($25 یک‌بار)
- [ ] **Keystore امن** — فایل `.jks` + رمز قوی → حتماً ۳ backup جداگانه بگیر
- [ ] App Bundle (AAB) به‌جای APK خام
- [ ] Target API Level 35+ (Android 15)
- [ ] 64-bit ABI support
- [ ] **مجوز VPN از Google** — VPN apps نیاز به تأیید ویژه دارند (۲-۴ هفته)
- [ ] Data Safety Form در Google Play Console
- [ ] حداقل ۲۰ تستر برای Open Testing قبل از Production

#### **[جدید v2.4] پیش‌نیازهای Cafe Bazaar (کافه‌بازار)**
> بزرگ‌ترین مارکت اندروید ایران — اولویت بالاتر از Google Play برای کاربران ایرانی

- [ ] حساب توسعه‌دهنده کافه‌بازار (bazaar.cafe/developer)
- [ ] **بدون نیاز به Google Play Services** — اپ نباید به GMS وابسته باشد
- [ ] رابط کاربری کامل فارسی (RTL — اجباری)
- [ ] Privacy Policy به زبان فارسی (صفحه جداگانه)
- [ ] Screenshots از دستگاه‌های ایرانی (Xiaomi/Samsung رایج)
- [ ] نسخه APK مستقل (بدون نیاز به Google Play برای نصب)
- [ ] توضیحات اپ به فارسی در صفحه بازار
- [ ] ایمیل ایرانی برای account (یا ایمیل developer)

#### **[جدید v2.4] پیش‌نیازهای Myket (مایکت)**
> دومین مارکت بزرگ اندروید ایران

- [ ] حساب توسعه‌دهنده در myket.ir/developers
- [ ] APK ارسال مستقیم (فرآیند بررسی ۲-۵ روز کاری)
- [ ] بدون وابستگی به Google Play Services
- [ ] رابط کاربری فارسی (RTL)
- [ ] Privacy Policy عمومی (فارسی کافی است)
- [ ] Category مناسب: "ابزار" یا "شبکه"

#### **[جدید v2.4] پیش‌نیازهای F-Droid**
> مارکت اپ‌های متن‌باز — برای کاربران حریم‌خصوصی‌محور جهانی

- [ ] کد کاملاً متن‌باز (MIT — ✅ موجود)
- [ ] هیچ وابستگی proprietary نداشته باشد (بدون Firebase، AdMob، ...)
- [ ] Reproducible Builds (ترجیحی — مستندسازی build steps)
- [ ] Metadata در `fastlane/metadata/android/` یا `metadata/` (شامل description/screenshots)
- [ ] ارسال merge request به [f-droid/fdroiddata](https://gitlab.com/fdroid/fdroiddata)
- [ ] Analytics باید opt-in باشد نه opt-out (یا نداشته باشید)
- [ ] اگر analytics دارید → فقط با رضایت صریح کاربر

#### ساختار اپ Flutter
- [ ] Cross-platform (Android اول، iOS بعد)
- [ ] مدیریت چند سرور + import از پنل
- [ ] QR Code Scanner
- [ ] Subscription Import (لینک + دستی + از پنل)
- [ ] تست سرعد داخلی
- [ ] Push Notification انقضا و سهمیه
- [ ] **Offline Mode** — نمایش آخرین اطلاعات بدون اتصال
- [ ] Dark/Light Mode + RTL فارسی + LTR انگلیسی
- [ ] **Smart Server Selection** — انتخاب خودکار بهترین سرور (latency/speed test)
- [ ] Crash Reporting (Firebase Crashlytics یا Sentry)
- [ ] **Widget برای Home Screen** — وضعیت اتصال + مصرف روزانه
- [ ] **[جدید v2.4]** بدون وابستگی به Google Play Services (برای Cafe Bazaar/Myket)
- [ ] **[جدید v2.4]** حالت Pure Dart برای push notification (بدون FCM — جایگزین: SSE یا Telegram)

#### توزیع
- [ ] Beta: Sideloading + GitHub Releases + کانال تلگرام (اول)
- [ ] **[جدید v2.4] Cafe Bazaar** — قبل از Google Play (کاربران ایرانی بیشتر)
- [ ] **[جدید v2.4] Myket** — همزمان با Cafe Bazaar
- [ ] **[جدید v2.4] F-Droid** — همزمان برای کاربران جهانی حریم‌خصوصی‌محور
- [ ] Google Play (Open Testing) — بعد از Beta
- [ ] Google Play (Production) — بعد از ۲۰ تستر
- [ ] App Store iOS — بعد از موفقیت Android

---

### 🟢 فاز ۷ — CI/CD، مانیتورینگ و مقیاس‌پذیری (مستمر)

#### CI/CD
- [ ] GitHub Actions: lint + test روی هر PR
- [ ] Auto Release با CHANGELOG خودکار
- [ ] Docker Image رسمی در GHCR
- [ ] **One-click Deploy** (Docker Compose یا Ansible)
- [ ] Terraform Provider (مدیریت Infrastructure as Code)
- [ ] **[جدید v2.4]** SAST Security Scan (CodeQL یا Semgrep) روی هر PR
- [ ] **[جدید v2.4]** Container Vulnerability Scan (Trivy) روی Docker image

#### **[جدید v2.4] Monitoring Stack یکپارچه**
- [ ] **Prometheus** + Node Exporter — متریک‌های سیستم
- [ ] **Xray Prometheus Exporter** — آمار ترافیک Xray در Prometheus
- [ ] **Grafana Dashboard** — فایل `.json` آماده import (نه فقط لینک Grafana Cloud)
- [ ] Alert Rules — CPU > 80%، RAM > 90%، bandwidth spike → اعلان تلگرام
- [ ] **Loki** — مدیریت مرکزی لاگ‌ها (اختیاری — برای پیشرفته‌ها)

#### مستندات
- [ ] مستندات کامل fa/en در GitHub Pages
- [ ] Swagger UI عمومی برای REST API
- [ ] ویدیو آموزشی نصب (فارسی)
- [ ] **[جدید v2.4]** Migration Guide — راهنمای مهاجرت از Marzban/3X-UI

#### جامعه
- [ ] **Plugin System** — افزودن پروتکل یا ویژگی بدون تغییر core
- [ ] Anonymous Analytics — opt-in، بدون داده شخصی
- [ ] Contributor Guide + Code of Conduct
- [ ] **[جدید v2.4]** GitHub Discussions فعال — برای پرسش‌ها (جدا از Issues)
- [ ] **[جدید v2.4]** Translations — Crowdin یا Weblate برای اضافه کردن زبان‌های جدید (ru، zh، ar)

---

## ۴. چک‌لیست Google Play

```
□ Privacy Policy URL معتبر عمومی (https://) — فارسی + انگلیسی
□ Google Play Developer Account فعال ($25 یک‌بار)
□ Keystore .jks با رمز قوی — ۳ نسخه backup در مکان‌های مختلف
□ App Bundle (AAB) به‌جای APK
□ Target SDK 35+ (Android 15)
□ 64-bit ABI support
□ مجوز VPN از Google (اگر VpnService API استفاده می‌کنی) — ۲-۴ هفته
□ Data Safety Form تکمیل‌شده
□ Screenshots حداقل ۲ دستگاه
□ Store Listing به فارسی + انگلیسی
□ حداقل ۲۰ تستر برای Open Testing قبل از Production
```

## ۴-الف. چک‌لیست Cafe Bazaar (کافه‌بازار) — جدید v2.4

```
□ حساب توسعه‌دهنده در bazaar.cafe/developer
□ APK مستقل (بدون نیاز به Google Play Services)
□ رابط کاربری کامل فارسی RTL
□ Privacy Policy فارسی عمومی
□ توضیحات فارسی کامل در صفحه اپ
□ Screenshot از دستگاه‌های رایج (Xiaomi، Samsung)
□ Category: "ابزار" یا "شبکه"
□ ایمیل developer معتبر
□ اپ فقط دسترسی‌های لازم را request کند (VPN، اینترنت)
```

## ۴-ب. چک‌لیست Myket — جدید v2.4

```
□ حساب در myket.ir/developers
□ APK مستقل (بدون GMS)
□ Privacy Policy عمومی (فارسی)
□ توضیحات فارسی
□ بررسی ۲-۵ روز کاری
□ Category مناسب
```

## ۴-ج. چک‌لیست F-Droid — جدید v2.4

```
□ کد 100% متن‌باز (MIT ✅)
□ بدون وابستگی proprietary (بدون Firebase، AdMob، ...)
□ Analytics فقط opt-in (یا نداشته باشید)
□ Reproducible Builds مستند شده
□ Metadata در fastlane/metadata/android/
□ Merge Request به gitlab.com/fdroid/fdroiddata
```

---

## ۵. ویژگی‌های پیشرفته‌ای که KIAN را از رقبا متمایز می‌کند

| ویژگی | 3X-UI | Marzban | Remnawave | **KIAN هدف** |
|-------|:-----:|:-------:|:---------:|:-----------:|
| کلید در مرورگر (بدون ارسال به سرور) | ❌ | ❌ | ❌ | ✅ **اختصاصی** |
| Multi-Server Management | ❌ | ✅ | ✅ | ✅ فاز ۵ |
| IP Limit per user | ✅ | ✅ | ✅ | ✅ فاز ۲ |
| Speed Limit per user | ✅ | ❌ | ✅ | ✅ فاز ۲ |
| HWID / Device Token | ❌ | ✅ | ✅ | ✅ فاز ۲ |
| Custom Sub Page | ❌ | ✅ | ✅ | ✅ فاز ۴ |
| Hysteria2 | ✅ | ✅ | ✅ | ✅ فاز ۴ |
| Tor Bridge Fallback | ❌ | ❌ | ❌ | ✅ فاز ۴ **جدید** |
| WireGuard inbound | ✅ | ❌ | ❌ | ✅ فاز ۴ |
| REALITY IP Scanner | ❌ | ❌ | ❌ | ✅ فاز ۴ **جدید** |
| Config Health Check | ❌ | ❌ | ❌ | ✅ فاز ۱ **جدید** |
| Flutter Mobile App | ❌ | ❌ | ❌ | ✅ فاز ۶ |
| Cafe Bazaar / Myket | ❌ | ❌ | ❌ | ✅ فاز ۶ **جدید** |
| F-Droid | ❌ | ❌ | ❌ | ✅ فاز ۶ **جدید** |
| Prometheus + Grafana Stack | ⚠️ | ⚠️ | ⚠️ | ✅ فاز ۷ **جدید** |
| Telegram Bot | ✅ | ✅ | ✅ | ✅ فاز ۴ |
| Automated Backup | ⚠️ | ✅ | ✅ | ✅ فاز ۱ **جدید** |
| نصب تک‌دستوری | ✅ | ✅ | ✅ | ✅ فعلی |
| Privacy-first (open source + MIT) | ✅ | ✅ | ✅ | ✅ فعلی |

---

## ۶. اولویت‌بندی اجرا

| اولویت | فاز | محتوا | زمان تخمینی |
|:-------:|-----|--------|:-----------:|
| ۱ | فاز ۱ | SQLite + ساختار + Privacy Policy + Audit Log + IPv6 | ۱-۲ هفته |
| ۲ | فاز ۲ | پنل وب + IP/Speed Limit + i18n + Key Rotation | ۳-۵ هفته |
| ۳ | فاز ۳ | kv2m Desktop چند‌سرور + macOS/Linux | ۲-۴ هفته |
| ۴ | فاز ۴ | پروتکل‌ها + Sub Page + DPI + Tor Fallback | ۱-۲ ماه |
| ۵ | فاز ۵ | Multi-Server Management + Node Agent | ۱-۲ ماه |
| ۶ | فاز ۶ | Flutter + **Cafe Bazaar اول** + Myket + F-Droid + Google Play | ۲-۳ ماه |
| ۷ | فاز ۷ | CI/CD + Prometheus/Grafana Stack + Plugin System | مستمر |

---

## ۷. نکات مهم مارکت‌ها

### 🏪 توصیه ترتیب انتشار اپ موبایل

```
GitHub Releases (APK مستقیم)
        ↓
کانال تلگرام (Beta تستر)
        ↓
Cafe Bazaar ← اولین مارکت رسمی (کاربر ایرانی بیشتر، فرآیند ساده‌تر)
        +
Myket      ← همزمان با کافه‌بازار
        +
F-Droid    ← همزمان (کاربر جهانی privacy-first)
        ↓
Google Play Open Testing (بعد از ثبات Beta)
        ↓
Google Play Production (بعد از ۲۰+ تستر)
        ↓
App Store iOS (آخر — Apple Developer $99/سال + Network Extension)
```

### ⚠️ نکات حیاتی

**Keystore / Signing:**
> اگر فایل `.jks` را گم کنی، **هرگز** نمی‌توانی اپ موجود در مارکت را آپدیت کنی و باید از صفر شروع کنی. سه نسخه backup در مکان‌های مختلف نگه دار (رمزنگاری‌شده).

**Google VPN Permission:**
> برای VPN apps در Google Play نیاز به تأیید ویژه داری که ۲-۴ هفته طول می‌کشد. قبل از submit، با Google تماس بگیر.

**Cafe Bazaar و GMS:**
> خیلی از دستگاه‌های ایرانی Google Play Services ندارند. اپ نباید برای push notification یا location به FCM وابسته باشد.

**iOS:**
> Apple Developer Account ($99/سال) + Network Extension Entitlement برای VPN نیاز به درخواست مجزا دارد.
> **توصیه:** ابتدا Android (Cafe Bazaar + Google Play) پایدار شود، سپس iOS اضافه شود.

---

## ۸. موارد اضافه‌شده در v2.4 (خلاصه)

| موضوع | فاز | توضیح |
|-------|:---:|--------|
| Cafe Bazaar Support | ۶ | بزرگ‌ترین مارکت ایران — اولویت بالاتر از Google Play |
| Myket Support | ۶ | دومین مارکت بزرگ ایران |
| F-Droid Listing | ۶ | برای کاربران privacy-first جهانی |
| IPv6 کامل | ۱ | پشتیبانی در همه inbound‌ها و CLI |
| Config Health Check | ۱ | تست خودکار کارکرد واقعی کانفیگ |
| Automated Backup | ۱ | ارسال پشتیبان به Telegram/S3/R2 |
| Audit Log | ۱ | ثبت تمام اعمال ادمین |
| Key Rotation | ۲ | چرخش دوره‌ای کلید بدون downtime |
| REALITY IP Scanner | ۴ | اسکن و پیشنهاد SNI مناسب |
| Tor Bridge Fallback | ۴ | آخرین خط دفاعی در صورت بلاک کامل |
| Prometheus + Grafana Stack | ۷ | مانیتورینگ کامل با فایل‌های آماده |
| SAST + Container Scan | ۷ | امنیت CI/CD |
| Crowdin/Weblate i18n | ۷ | مشارکت ترجمه جامعه |

---

*نسخه رودمپ: 2.4.0 | نصب‌کننده: v2.1.0 | فاز ۰ ✅ کامل | آخرین بروزرسانی: 2026-06-20*
