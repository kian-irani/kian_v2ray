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
- [ ] ۰.۶ بازطراحی Shadowsocks — code-side: cipher انتخابی + اعتبارسنجی؛ `(srv)` تستِ نهایی.

---

## 🟠 فاز ۱ — پایه‌ریزی
- [x] ۱.۱۰ **LANDING-i18n-FULL** — i18n.js بازنویسی شد: پشتیبانیِ `data-i18n-ph` (placeholder) + `data-i18n-title` + دیکشنریِ ۱۰۴کلیدی FA/EN. کلِ سطحِ تعاملی (فرمِ ساخت: لیبل/placeholder/option/mode/دکمه + فرمِ مدیریت: اکشن‌ها/فیلدها) + همه‌ی هدینگِ تب‌ها + about + hero/roadmap/footer دوزبانه شد. اعتبارسنجی: `node --check` سبز، ۱۰۴/۱۰۴ کلید تعریف‌شده، تگ‌های HTML متوازن، smoke test سبز (generator دست‌نخورده)، toggle درست FA↔EN را سوییچ می‌کند. **[باقی: ترجمه‌ی عمیقِ پاراگراف‌های troubleshooting در tips/domain = ادامه.]**
- [ ] ۱.۱ ریفکتورِ ساختار: ماژولِ `core/` (پایتونِ مشترک) + `tests/` + سامان‌دهیِ `scripts/`/`docs/` بدونِ شکستنِ مسیرهای CI.
- [ ] ۱.۲ SQLite schema (`core/db.py`) + سیستمِ Migration سبک (`core/migrate.py`).
- [ ] ۱.۳ لاگِ ساختاریافتهٔ JSON (`core/logging.py`).
- [ ] ۱.۴ SemVer رسمی + Git Tagging (`scripts/release.sh` + سیاستِ نسخه در docs).
- [ ] ۱.۵ پشتیبانیِ IPv6 در inboundها و CLI (`install.sh` + `scripts/kian-v2ray`).
- [ ] ۱.۶ بکاپِ خودکارِ رمزنگاری‌شده (`scripts/kian-backup.py` → Telegram/S3/R2).
- [ ] ۱.۷ Audit Log (`core/audit.py`) + اتصال به CLI.
- [ ] ۱.۸ pytest (`tests/test_core.py`, `tests/test_db.py`) + اتصال به CI.
- [ ] ۱.۹ Config Health Check (`scripts/config-health.py` + subcommandِ CLI).

---

## 🟠 فاز ۲ — وب پنل کامل
- [ ] ۲.۱ اسکلتِ FastAPI (`panel/main.py`) + SQLAlchemy models (`panel/models.py`).
- [ ] ۲.۲ JWT Auth + Refresh Token (`panel/auth.py`).
- [ ] ۲.۳ REST API کاربر CRUD + OpenAPI (`panel/routers/users.py`).
- [ ] ۲.۴ WebSocket آمارِ زنده (`panel/routers/ws.py`).
- [ ] ۲.۵ محدودیتِ IP/Speed/HWID + Auto-Disable + Bulk Actions (مدل + endpoint).
- [ ] ۲.۶ Export (JSON/CSV) + Session Management + Password Recovery.
- [ ] ۲.۷ Frontend پنل: UI Dark/Glass دوزبانه (RTL/LTR) + CRUD + نمودار (`panel/web/`).
- [ ] ۲.۸ System Monitor (CPU/RAM/Net) + Backup/Restore + Audit Log Viewer در UI.
- [ ] ۲.۹ امنیت: Rate-Limit/Fail2ban + 2FA(TOTP) + IP whitelist + Security Headers + CORS.
- [ ] ۲.۱۰ Key Rotation (چرخشِ X25519 بدونِ downtime).

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
