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
- [ ] ۹.۹ **Deep-link import** — intent-filter برای `vless://`/`sub`. [بعدی]
- [x] ۹.۱۰ **Proxy-only** — گزینه در تنظیمات (flutter_v2ray `proxyOnly`).
- [ ] ۹.۱۱ **ویرایش/مرتب‌سازیِ کانفیگ**. [بعدی]
- [x] ۹.۱۲ **راهنمای درون‌برنامه‌ای** — `HelpCard` دوزبانه در home/setup/manage/history/settings.

### فاز ۱۰ — پروتکل/transportهای بیشتر (parity با sing-box)
- [x] ۱۰.۰ **VLESS-XHTTP** — جدیدترین transport، در هر سه نسخه؛ تأییدِ زنده روی xray 26.5.9.
- [ ] ۱۰.۱ **ECH** (Encrypted Client Hello) — مخفی‌سازیِ SNI؛ روی TLS configها (نیازِ cert/DNS).
- [ ] ۱۰.۲ **ShadowTLS v3** — پوششِ SS پشتِ TLSِ واقعی.
- [ ] ۱۰.۳ **AnyTLS** — transportِ جدیدِ sing-box.
- [ ] ۱۰.۴ **SSH outbound** — مثل Hiddify (تونلِ SSH به‌عنوان fallback).
- [ ] ۱۰.۵ **mKCP** — UDP obfuscation برای شبکه‌های خاص.
- [ ] ۱۰.۶ **Reality «steal yourself»** + گزینهٔ shortId/spiderX پیشرفته.

### فاز ۱۱ — وب/صفحه و پنل (کامل‌تر و یکدست)
- [ ] ۱۱.۱ **صفحهٔ تعاملی: XHTTP + DNS + routing presets** در فرم (هماهنگ با اپ).
- [ ] ۱۱.۲ **پنل: per-user routing/DNS** + نمایشِ پروتکل‌های فعالِ هر node.
- [ ] ۱۱.۳ **راهنمای کاملِ دوزبانه** در همهٔ تب‌های صفحه و پنل (tooltip + help block).
- [ ] ۱۱.۴ **بازبینیِ طراحی** — یکدستیِ glass/dark، کنتراست AA، آیکن SVG، فاصله‌گذاری ۸pt (طبق ui-ux-pro-max).

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
