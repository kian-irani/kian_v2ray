---
title: PRD v2 — KIAN/Kv2m feature parity + new capabilities
tags: [project, kian-v2ray, prd, parity, active]
date: 2026-06-22
status: active
project: 01-kian-v2ray
---

# 📑 PRD v2 — «همه‌چیزِ رقبا + بهتر»

> هدف: Kv2m هرچه **sing-box app / v2rayNG / Hiddify** دارند را داشته باشد —
> پروتکل‌ها، تنظیمات، مسیریابی، راهنما — و مزیتِ منحصربه‌فرد (کلید در مرورگر) را نگه دارد.
> همه‌چیز **دوزبانه** با **انگلیسیِ پیش‌فرض** (شاملِ کنسولِ نصب).

## 0. وضعیتِ فعلی (داریم)
پروتکل‌ها: VLESS/VMess/Trojan/Shadowsocks/Reality/Hysteria2/TUIC/WireGuard/**XHTTP** ·
ضدDPI: Fragment/uTLS/TTL/Noise · هستهٔ روی‌دستگاه (flutter_v2ray) · ساخت کانفیگ client-side ·
SSH نصب از اپ · پنلِ وب · تاریخچهٔ نصب · QR · auto-refreshِ subscription · multi-server.

## 1. شکافِ رقابتی (رقبا دارند، ما نه) → تسک‌ها

### فاز ۹ — کلاینتِ موبایلِ کامل (parity با v2rayNG/Hiddify)
- [x] ۹.۱ **صفحهٔ تنظیماتِ اختصاصی** — theme (system/dark/light)، زبان، routing، DNS، kill-switch، auto-connect، auto-refresh + راهنما.
- [ ] ۹.۲ **Per-app proxy / split-tunnel** — نیازِ installed-apps picker (پلتفرمی). [بعدی]
- [x] ۹.۳ **Routing presets** — global / bypass-LAN / bypass-Iran / both → `bypassSubnets` در connect.
- [x] ۹.۴ **DNS سفارشی** — remote/direct DNS در تنظیمات (اعمال در connect/config).
- [x] ۹.۵ **Kill-switch** — گزینه در تنظیمات (flutter_v2ray).
- [x] ۹.۶ **پینگِ هر سرور** — TCP ping (SmartSelection) + دکمهٔ «بهترین سرور» (تستِ همه). (real-delay = follow-on)
- [x] ۹.۷ **آمارِ زندهٔ مصرف** — up/down + uptime حینِ اتصال روی صفحهٔ اصلی.
- [x] ۹.۸ **Auto-connect** — گزینه در تنظیمات (اتصال به آخرین سرور هنگامِ launch).
- [x] ۹.۹ **Deep-link import** — intent-filter (vless/vmess/trojan/ss/hy2/tuic/kv2m) + initialLink → import در launch.
- [x] ۹.۱۰ **Proxy-only** — گزینه در تنظیمات (flutter_v2ray `proxyOnly`).
- [x] ۹.۱۱ **مدیریتِ کانفیگ** — تغییرِ نام + حذف (با undo) از منویِ هر سرور. (drag-reorder = follow-on)
- [x] ۹.۱۲ **راهنمای درون‌برنامه‌ای** — `HelpCard` دوزبانه در home/setup/manage/history/settings.

### فاز ۱۰ — پروتکل/transportهای بیشتر (parity با sing-box)
- [x] ۱۰.۰ **VLESS-XHTTP** — جدیدترین transport، در هر سه نسخه؛ تأییدِ زنده روی xray 26.5.9.
> **یادداشتِ مهندسی (2026-06-22):** پروتکل‌های زیر بدونِ تأییدِ واقعی **اضافه نمی‌شوند** تا باگِ «کانفیگِ خراب»
> دوباره رخ ندهد. mKCP روی xray 26.x تست شد و **schema عوض شده** (header/seed حذف) → اضافه نشد. ECH نیازِ cert/DNS،
> ShadowTLS/AnyTLS نیازِ sing-box که اینجا قابلِ اجرا نیست. مجموعهٔ عملیِ پروتکل‌ها (Reality/VLESS/VMess/Trojan/SS/
> Hysteria2/TUIC/WireGuard/**XHTTP**/WS/gRPC/HTTPUpgrade) کامل و تأییدشده است.
- [x] ۱۰.۰ **VLESS-XHTTP** — اضافه و روی xray 26.5.9 تأیید شد.
- [ ] ۱۰.۱ **ECH** — نیازِ cert/DNS؛ موقعِ راه‌اندازیِ TLS واقعی روی سرور (HITL). [deferred با دلیل]
- [ ] ۱۰.۲ **ShadowTLS v3** — sing-box companion؛ نیازِ تستِ runtime. [deferred]
- [ ] ۱۰.۳ **AnyTLS** — sing-box؛ نیازِ تستِ runtime. [deferred]
- [ ] ۱۰.۴ **SSH outbound** — کلاینت-ساید (نه inboundِ ما). [deferred]
- [x] ۱۰.۵ **mKCP** — تست شد؛ schemaِ xray 26.x عوض شده → **اضافه نشد** (low-value، در حالِ تغییر).
- [ ] ۱۰.۶ **Reality advanced (shortId/spiderX)** — بهبودِ آینده. [deferred]

### فاز ۱۱ — وب/صفحه و پنل (کامل‌تر و یکدست)
- [x] ۱۱.۱ **صفحهٔ تعاملی: XHTTP** در فرم (DNS/routing روی اپ پیاده شد؛ صفحه کانفیگِ سروری می‌سازد).
- [ ] ۱۱.۲ **پنل: per-user routing/DNS** — تغییرِ بک‌اند. [deferred]
- [x] ۱۱.۳ **دوزبانهٔ کاملِ صفحه (۲۴۶ کلید) و پنل (۵۲ کلید)** — صفرِ کلیدِ گم‌شده؛ توضیحاتِ پروتکل هم اضافه شد.
- [x] ۱۱.۴ **بازبینیِ طراحی (ui-ux-pro-max)** — empty-stateِ غنی، آیکن‌های Material outlined، help cardها، انگلیسیِ پیش‌فرض.

### فاز ۱۲ — کیفیت
- [x] ۱۲.۱ **چکِ کلیِ باگ** — همهٔ syntax/dart/yaml سبز، pytest ۵۶، پنل تستِ زنده ۹/۹، xray واقعی. (ادامه‌دار)
- [x] ۱۲.۲ **همه‌جا دوزبانه** — صفحه (۲۴۶ کلید، صفرِ گم‌شده)/اپ (صفرِ گم‌شده)/نصب (KIAN_LANG)؛ انگلیسیِ پیش‌فرض.
- [ ] ۱۲.۳ **تستِ end-to-end** روی سرورِ زنده (`(srv)`).

## 2. اولویت اجرا
۹.۱ (تنظیمات) → ۹.۶ (پینگ) → ۹.۲/۹.۳ (per-app/routing) → ۹.۷ (آمار) → ۹.۱۲ (help) →
۱۱.۳/۱۱.۴ (راهنما/دیزاین) → ۱۰.x (پروتکل‌های بیشتر) → ۱۲ (کیفیت).

## 3. خارج از scope (تجاری — نیازِ کاربر)
حساب‌های مارکت، Keystore/AAB، submission، ویدیو، Discussions toggle.

---
*PRD v2 | 2026-06-22 | منبعِ تسک: همین فایل + `PLAN.md`*
