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
- [ ] ۳.۱ مدیریتِ چندسرور در core/app (`kv2m/core.py` + `kv2m/app.py`).
- [ ] ۳.۲ اتصال به REST API پنل + نصب/آپدیتِ خودکارِ Xray.
- [ ] ۳.۳ Auto-update (GitHub Releases) + System Tray.
- [ ] ۳.۴ Dark/Light Mode ذخیره‌شده + پشتیبانیِ macOS/Linux + Crash Reporting.

---

## 🟡 فاز ۴ — پروتکل‌ها و ضدسانسور
- [ ] ۴.۱ Hysteria2 inbound (`install.sh` + builder).
- [ ] ۴.۲ TUIC v5 inbound.
- [ ] ۴.۳ WireGuard inbound + Mux.cool.
- [ ] ۴.۴ خروجیِ Sing-box format در Subscription (`worker/` + `scripts/sub-server.py`).
- [ ] ۴.۵ خروجیِ Clash Meta format + تشخیصِ خودکارِ کلاینت.
- [ ] ۴.۶ Self-hosted Sub Page (حجم/انقضا/QR).
- [ ] ۴.۷ ضدِDPI: Fragment + uTLS fingerprint + TTL + Noise Padding.
- [ ] ۴.۸ REALITY IP Scanner داخلی (پیشنهادِ SNI).
- [ ] ۴.۹ Tor Bridge Fallback (obfs4/Snowflake).
- [ ] ۴.۱۰ بات تلگرام + Webhook + Email Notification + بکاپِ شبانه.

---

## 🔵 فاز ۵ — Multi-Server Management
- [ ] ۵.۱ Node Agent سبک (`node-agent/agent.py`).
- [ ] ۵.۲ یک پنل → چند VPS (مدلِ Node + endpointها).
- [ ] ۵.۳ Node Health Check + Auto Failover.
- [ ] ۵.۴ Load Balancing + GeoIP Routing.
- [ ] ۵.۵ Migration Tool از Marzban/3X-UI.
- [ ] ۵.۶ Bandwidth Alert + per-Node Config Override.

---

## 🔵 فاز ۶ — اپ موبایل Flutter
- [ ] ۶.۱ اسکلتِ Flutter (`app/` — pubspec + ساختار + theme + RTL/LTR).
- [ ] ۶.۲ صفحاتِ اصلی: اتصال + لیستِ سرور + import (لینک/دستی/پنل) + QR Scanner.
- [ ] ۶.۳ Smart Server Selection (latency/speed) + Offline Mode + Widget.
- [ ] ۶.۴ بدونِ GMS + Push بدونِ FCM (SSE/Telegram).
- [ ] ۶.۵ Metadata + Privacy فارسی + بسته‌بندیِ AAB/APK + Keystore docs.
- [ ] ۶.۶ آماده‌سازیِ انتشار: Cafe Bazaar / Myket / F-Droid metadata.

---

## 🟢 فاز ۷ — CI/CD + Monitoring
- [ ] ۷.۱ GitHub Actions: lint + test + Auto Release با CHANGELOG.
- [ ] ۷.۲ Docker Image (GHCR) + One-click Deploy (Compose).
- [ ] ۷.۳ SAST (CodeQL/Semgrep) + Trivy container scan.
- [ ] ۷.۴ Prometheus + Node/Xray Exporter (config + scrape).
- [ ] ۷.۵ Grafana Dashboard (`.json` آمادهٔ import) + Alert Rules.
- [ ] ۷.۶ مستنداتِ fa/en + Migration Guide + Plugin System + Contributor Guide.

---

## 🔴 بلاکر
- (فعلاً نیست) · `(srv)`-ها نیازِ دسترسیِ سرورِ `37.221.79.91`.

---
← [[kian-workspace/01-projects/01-kian-v2ray/kian-v2ray|kian-v2ray]]
