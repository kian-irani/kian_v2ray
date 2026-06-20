---
title: PRD — KIAN V2Ray Platform
tags: [project, kian-v2ray, prd, product, active]
date: 2026-06-20
status: active
project: 01-kian-v2ray
---

# 📑 PRD — KIAN V2Ray Platform

> سند محصول (Product Requirements Document) — نسخهٔ ۱.۰ · مرجعِ تصمیمِ محصول برای کلِ پروژه.
> رودمپِ اجرایی: `repo/ROADMAP.md` (v2.4) · پلنِ تسک‌محور: `PLAN.md`.
> نصب‌کنندهٔ فعلی: **v2.1.0** · فاز ۰ ✅ کامل.

---

## ۱. خلاصهٔ اجرایی (Executive Summary)

**KIAN V2Ray** یک پلتفرمِ متن‌بازِ ضدِسانسور است که با **یک دستور** روی هر VPS، یک سرورِ VPN امن (VLESS Reality + WARP + Shadowsocks + TLS دامنه‌دار) برپا می‌کند. مزیتِ اصلی و **غیرقابل‌کپیِ** آن: **کلیدِ خصوصی هرگز به سرور نمی‌رسد** — کلیدِ X25519 کاملاً در مرورگرِ کاربر ساخته می‌شود.

مسیرِ محصول: از یک **ابزارِ نصبِ تک‌دستوری** → به یک **پلتفرمِ مدیریتِ زیرساختِ VPN چندسروره** با پنلِ وب، اپِ موبایل، و اکوسیستمِ مانیتورینگ.

---

## ۲. مسئله (Problem Statement)

کاربرانِ ایرانی و کاربرانِ مناطقِ پرسانسور به دسترسیِ پایدار، خصوصی و ساده به اینترنتِ آزاد نیاز دارند. راه‌حل‌های موجود سه مشکلِ بزرگ دارند:

1. **اعتماد:** پنل‌های موجود (3X-UI, Marzban) کلیدِ خصوصی را سمتِ سرور می‌سازند → اپراتورِ سرور می‌تواند ترافیک را رمزگشایی کند.
2. **پیچیدگی:** نصب و مدیریت برای کاربرِ غیرفنی سخت است؛ ادیتِ دستیِ کانفیگ روی موبایل تقریباً غیرممکن است.
3. **شکنندگی:** بلاک‌شدنِ پروتکل/پورت، افتِ WARP، و کرشِ سرویس بدونِ خودتشخیصی و fallback، سرویس را از کار می‌اندازد.

---

## ۳. راه‌حل (Solution)

| ستون | چه‌چیزی |
|------|---------|
| **Privacy-first** | تولیدِ کلید در مرورگر؛ بدون لاگ؛ متن‌باز (MIT). |
| **Zero-friction** | نصب با `curl … | bash`؛ idempotent؛ بدونِ ادیتِ دستی؛ صفحهٔ تعاملیِ دوزبانه. |
| **Resilient** | WARP fallback، خودتشخیصیِ `status/health/doctor`، Watchdog، BBR، نصبِ مجددِ امن. |
| **Scalable** | مسیر به پنلِ وب + Multi-Server + اپِ موبایل + پروتکل‌های جدید. |

---

## ۴. کاربرانِ هدف (Personas)

1. **اپراتورِ شخصی (Power user):** یک VPS دارد؛ برای خود و دوستان کانفیگ می‌سازد. نیاز: نصبِ سریع، مدیریتِ چند کاربر، Subscription.
2. **فروشندهٔ سرویس (Reseller):** چند VPS دارد؛ ده‌ها/صدها کاربر. نیاز: پنلِ وب، محدودیتِ IP/سرعت/HWID، آمار، بکاپ، Multi-Server.
3. **کاربرِ نهایی (End user):** فقط می‌خواهد وصل شود. نیاز: لینکِ Subscription، اپِ موبایلِ ساده، QR، انتخابِ خودکارِ بهترین سرور.
4. **مشارکت‌کنندهٔ متن‌باز (Contributor):** privacy-محور؛ از طریقِ GitHub/F-Droid. نیاز: کدِ تمیز، تست، مستندات، Plugin System.

---

## ۵. اهداف و معیارهای موفقیت (Goals & Success Metrics)

| هدف | معیار |
|-----|-------|
| نصبِ بی‌دردسر | نصب < ۹۰ ثانیه؛ نرخِ موفقیتِ نصب > ۹۵٪ بدونِ دخالتِ دستی. |
| پایداری | uptime > ۹۹٪ با Watchdog + WARP fallback؛ کرش‌لوپ خودکار تشخیص داده شود. |
| اعتماد | ۱۰۰٪ کلیدها client-side؛ صفرِ لاگِ حساس؛ ممیزیِ امنیتیِ سبز (SAST). |
| رشد | انتشار در ۴ مارکت (Cafe Bazaar, Myket, F-Droid, Google Play). |
| کیفیتِ کد | CI سبز روی هر PR؛ پوششِ تستِ core > ۶۰٪. |

---

## ۶. دامنه (Scope)

### درونِ دامنه (In-scope)
- نصب‌کنندهٔ سرور (install.sh) + CLIِ مدیریتی (`kian-v2ray`).
- صفحهٔ تعاملیِ دوزبانهٔ تولیدِ کانفیگ (index.html, client-side keys).
- Subscription (Cloudflare Worker + Gist + self-hosted).
- پنلِ وب (FastAPI) + Multi-Server Management.
- اپِ دسکتاپ (Kv2m) + اپِ موبایل (Flutter).
- مانیتورینگ (Prometheus/Grafana) + CI/CD.

### بیرونِ دامنه (Out-of-scope — فعلاً)
- فروش/پرداختِ درون‌برنامه‌ای (می‌تواند بعداً از طریقِ بات تلگرام).
- پشتیبانیِ رسمیِ سازمانی/SLA.
- اپِ iOS تا پیش از تثبیتِ اندروید.

---

## ۷. نیازمندی‌های کاربردی (Functional Requirements) — به‌تفکیکِ فاز

> جزئیاتِ تسک‌محور و وضعیتِ ✅/⬜ در `PLAN.md`. این بخش = «چه‌چیزی باید کار کند».

### فاز ۰ — پایداریِ بحرانی ✅
- FR-0.1 رفعِ خودکارِ تداخلِ پورتِ API.
- FR-0.2 پایدارسازیِ WARP با fallbackِ خودکار.
- FR-0.3 خودتشخیصیِ `status/health/doctor` با دستورِ رفع.
- FR-0.4 بهینه‌سازیِ شبکه (BBR+fq).
- FR-0.5 نصبِ مجددِ امن (حفظِ کاربرانِ قبلی).
- FR-0.6 بازطراحیِ Shadowsocks (نیازِ تستِ سرور).

### فاز ۱ — پایه‌ریزی
- FR-1.1 ساختارِ ماژولارِ کد (`core/`, `panel/`, `tests/`, `docs/`).
- FR-1.2 پایگاه‌دادهٔ SQLite + سیستمِ Migration.
- FR-1.3 لاگِ ساختاریافتهٔ JSON.
- FR-1.4 SemVer رسمی + Git Tagging خودکار.
- FR-1.5 پشتیبانیِ کاملِ IPv6 در inboundها و CLI.
- FR-1.6 بکاپِ خودکار (Telegram/S3/R2) رمزنگاری‌شده.
- FR-1.7 Audit Log (چه‌کسی، چه‌کاری، کِی، از کدام IP).
- FR-1.8 تستِ pytest (unit/integration).
- FR-1.9 Config Health Check خودکار.
- FR-1.10 دوزبانه‌سازیِ کاملِ صفحهٔ تعاملی (LANDING-i18n-FULL).

### فاز ۲ — پنلِ وب
- FR-2.1 FastAPI + SQLAlchemy + JWT (+ Refresh).
- FR-2.2 REST API با OpenAPI/Swagger.
- FR-2.3 WebSocket برای آمارِ زنده.
- FR-2.4 CRUDِ کاربر + جستجو/فیلتر + Bulk Actions.
- FR-2.5 محدودیتِ IP/سرعت/HWID per-user + Auto-Disable.
- FR-2.6 UIِ Dark/Glass دوزبانه (RTL/LTR) + نمودارِ ترافیک.
- FR-2.7 امنیت: TLS، Rate-Limit/Fail2ban، 2FA (TOTP)، IP whitelist، Key Rotation، Security Headers.
- FR-2.8 Export (JSON/CSV) + Backup/Restore از UI + Audit Log Viewer.

### فاز ۳ — Kv2m Desktop
- FR-3.1 GUIِ حرفه‌ای (PySide6/Qt) چندسرور.
- FR-3.2 نصب/آپدیتِ خودکارِ Xray + اتصال به REST API.
- FR-3.3 Auto-update (GitHub Releases) + System Tray + Dark/Light.
- FR-3.4 macOS + Linux + Crash Reporting.

### فاز ۴ — پروتکل‌ها و ضدِسانسور
- FR-4.1 Hysteria2 + TUIC v5 + WireGuard inbound + Mux.
- FR-4.2 خروجیِ Sing-box + Clash Meta در Subscription.
- FR-4.3 Self-hosted Sub Page (حجم/انقضا/QR) + تشخیصِ خودکارِ کلاینت.
- FR-4.4 ضدِDPI: Fragment، uTLS، TTL، Noise Padding.
- FR-4.5 REALITY IP Scanner + Tor Bridge Fallback.
- FR-4.6 بات تلگرام + Webhook + Email Notification + بکاپِ شبانه.

### فاز ۵ — Multi-Server
- FR-5.1 Node Agent سبک روی هر VPS.
- FR-5.2 یک پنل → چند VPS + Health/Failover/LoadBalance.
- FR-5.3 GeoIP Routing + Migration از Marzban/3X-UI + Bandwidth Alert + per-node override.

### فاز ۶ — اپِ موبایلِ Flutter
- FR-6.1 کلاینتِ cross-platform (Android اول).
- FR-6.2 import از پنل/لینک/دستی + QR Scanner + Smart Server Selection.
- FR-6.3 بدونِ GMS (مارکت‌های ایرانی) + Offline Mode + Widget + Push بدونِ FCM.
- FR-6.4 انتشار: Cafe Bazaar → Myket → F-Droid → Google Play → iOS.

### فاز ۷ — CI/CD + مانیتورینگ
- FR-7.1 GitHub Actions (lint/test/release) + GHCR + One-click Deploy.
- FR-7.2 SAST (CodeQL/Semgrep) + Trivy.
- FR-7.3 Prometheus + Node/Xray Exporter + Grafana Dashboard + Alert Rules.
- FR-7.4 مستنداتِ fa/en + Swagger عمومی + Plugin System + Translations.

---

## ۸. نیازمندی‌های غیرکاربردی (Non-Functional)

| دسته | الزام |
|------|-------|
| **امنیت** | کلید client-side؛ بدونِ secret در ریپو (CI secret-scan)؛ TLS همه‌جا؛ JWT کوتاه‌عمر + refresh؛ rate-limit. |
| **حریمِ خصوصی** | بدونِ لاگِ ترافیک؛ Analytics فقط opt-in؛ Privacy/Terms دوزبانه. |
| **پایداری** | idempotent installs؛ Watchdog؛ WARP fallback؛ نصبِ مجددِ بدونِ از‌دست‌رفتنِ کاربر. |
| **کارایی** | نصب < ۹۰s؛ BBR+fq؛ پنل با WebSocket (بدونِ polling سنگین). |
| **قابلیتِ حمل** | Win/macOS/Linux/Termux برای دسکتاپ؛ Android بدونِ GMS. |
| **نگه‌داری** | کدِ ماژولار؛ تست؛ SemVer؛ CI سبز؛ مستندات. |
| **دسترس‌پذیری** | کنتراستِ AA؛ RTL/LTR کامل؛ بدونِ ایموجیِ ساختاری به‌جای متن. |

---

## ۹. معماری (خلاصه)

```
Client: Browser(index.html) · Kv2m Desktop · Flutter Mobile
            │            │              │
            ▼ REST/JWT/WebSocket ▼
        KIAN Web Panel (FastAPI + SQLite)
            │
   ┌────────┼─────────┐
   ▼        ▼         ▼
 Node1    Node2     NodeN   (Node Agent → Xray)
 Reality/SS/Hysteria2/TUIC/WG/TLS(Caddy:443)
            │
            ▼  Subscription: CF Worker+Gist / Self-hosted
            ▼  Monitoring: Prometheus + Grafana
```
جزئیات: `ARCHITECTURE.md` و بخشِ ۲ رودمپ.

---

## ۱۰. ریسک‌ها و کاهش (Risks & Mitigations)

| ریسک | کاهش |
|------|------|
| بلاک‌شدنِ پروتکل/IP در ایران | چند پروتکل + Fragment/uTLS + Tor fallback + REALITY scanner. |
| ردِ مارکتِ موبایل (مجوزِ VPN) | privacy policy، بدونِ GMS، انتشارِ مرحله‌ای از کافه‌بازار. |
| گم‌شدنِ Keystore | ۳ بکاپِ رمزنگاری‌شده در مکان‌های مجزا. |
| نشتِ secret | CI secret-scan؛ کلید client-side؛ بدونِ توکن در ریپو. |
| شکستنِ کارِ فعلی هنگامِ توسعه | i18n مستقل از app.js؛ smoke test؛ تغییراتِ idempotent. |

---

## ۱۱. وابستگی‌ها (Dependencies)
- Xray-core (pin‌شده در `VERSION`).
- Cloudflare Worker + GitHub Gist (Subscription).
- Caddy (TLS) + Let's Encrypt.
- GitHub Actions (CI/Release) + GHCR.
- مارکت‌ها: Cafe Bazaar, Myket, F-Droid, Google Play.

---

## ۱۲. نقاطِ تصمیمِ نیازمندِ کاربر (Open Questions / HITL)
- محتوای حقوقیِ Privacy/Terms برای محدودهٔ قضاییِ کاربر بازبینی شود.
- تستِ واقعیِ Shadowsocks/TLS روی سرورِ `37.221.79.91` (نیازِ دسترسیِ سرور).
- کلیدهای ابریِ مارکت‌ها/Keystore (نیازِ اقدامِ انسانی).

---

*PRD v1.0 | 2026-06-20 | منبعِ حقیقتِ تسک‌ها: `PLAN.md` · رودمپ: `repo/ROADMAP.md`*
