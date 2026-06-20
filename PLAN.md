---
title: PLAN — kian-v2ray
tags: [v2ray, plan]
date: 2026-06-16
status: active
priority: medium
project: kian-v2ray
---

# 🗺️ PLAN — `01-kian-v2ray` (rev v2.4)

> هدف: از نصب‌کنندهٔ V2Ray تک‌دستوری → **پلتفرم VPN چندسروره + اکوسیستم موبایل**.
> رودمپ کامل: `repo/ROADMAP.md` (نسخه ۲.۴، ادغام‌شده 2026-06-16). بایگانی: `repo/ROADMAP-legacy.md`.
> مزیت اختصاصیِ غیرقابل‌کپی: **کلید خصوصی هرگز به سرور نمی‌رسد** (ساخت در مرورگر).

## ✅ Done
- صفحهٔ تعاملی (کلید در مرورگر، چند SNI/پورت) · Subscription سه‌لایه (Gist HTTPS) · TLS دامنه‌دار پشت Caddy · هسته (Reality/WARP/SS/multi-user/CLI/Watchdog/BBR) · Kv2m دسکتاپ.
- **[2026-06-20 auto-rp]** **فاز ۰ کامل** → نصب‌کننده **v2.1.0** (خودتشخیصیِ `status`/`health`/`doctor`، ۰.۱–۰.۵).
  **حقوقی** (privacy/terms دوزبانه). **صفحهٔ تعاملی دوزبانه + سکشنِ رودمپ**. **GitHub project آپدیت شد:** README
  بازنویسیِ حرفه‌ای و دوزبانه + ROADMAP (فاز ۰ ✅) + CHANGELOG (v2.1.0). همه روی main، CI سبز.

## 🔴 اولویت ۰ — رفع باگ‌های بحرانی (قبل از هر چیز)
- [x] ۰.۱ تداخل پورت API (10085) → auto-fix در `install.sh` (پورتِ آزادِ تصادفی + تزریق در config + `api.txt`).
- [x] ۰.۲ پایدارسازی WARP → `warp_fallback()` (افتِ WARP → خروجی مستقیم، بازگشتِ خودکار) + چکِ اتصالِ socks.
- [x] **۰.۳ خودتشخیصیِ `status`** (auto-rp، 2026-06-20): `cmd_status` بازنویسی شد — تشخیصِ **کرش‌لوپِ Xray**
  (RestartCount در آپ‌تایمِ کوتاه)، **WARP** (آگاه از fallback)، **پورت‌های شنونده‌نبودنِ reality/ss**،
  **سلامتِ Shadowsocks**، و **سرویس Subscription**؛ برای هر مشکل **دستورِ رفع** + بخشِ «خودتشخیصی» با شمارشِ
  مشکلات. + alias `kian-v2ray health|doctor`. `bash -n` سبز.
- [x] ۰.۴ بهینه‌سازی سرعت BBR → بخشِ «بهینه‌سازی شبکه» (BBR+fq، امن، idempotent، با verifyِ cc).
- [x] ۰.۵ نصب مجدد امن → بکاپِ users/config + ادغامِ کاربرانِ قبلی که در payload جدید نیستند (پاک نمی‌شوند).
- [ ] ۰.۶ رفع/بازطراحی Shadowsocks (نیازِ تستِ روی سرور — cipher فعلی `chacha20-ietf-poly1305`؛ سلامتش حالا در `status` دیده می‌شود).

## 🟠 اولویت ۱ — پایه‌ریزی (۱-۲ هفته)
- [ ] **LANDING-i18n-FULL — دوزبانه‌کردنِ کاملِ `index.html`** (دستور کاربر 2026-06-20): الان فقط hero/tabs/footer
  با تغییرِ زبان عوض می‌شوند؛ **بدنه‌ی همه‌ی تب‌ها (server/android/pc/tips/domain/manage/about) + لیبل‌ها/placeholder/
  option‌های فرمِ ساخت** باید `data-i18n`/`data-i18n-ph` بگیرند و ترجمه‌ی EN در `assets/js/i18n.js` کامل شود تا
  **هر بخش** دوزبانه باشد. (smoke test سبز بماند چون i18n.js در CI inject نمی‌شود.)
- [~] **LANDING — صفحه‌ی گیت‌هاب حرفه‌ای و دوزبانه** (auto-rp، 2026-06-20): ✅ **دوزبانه** شد —
  `assets/js/i18n.js` (دیکشنریِ FA/EN، سوییچِ هدر، `dir`+`lang` صحیح، persist در localStorage، مستقل از
  `app.js` پس سازنده‌ی کانفیگ دست‌نخورد و smoke test سبز ماند) روی hero/tabs/footer. ✅ **رودمپ/چشم‌انداز**:
  سکشنِ حرفه‌ایِ «از نصب‌کننده به پلتفرم» با ۶ کارتِ شیشه‌ای + آیکنِ SVG (نه ایموجی) — privacy(موجود)/چندسرور/
  پنل‌وب/اپ‌موبایل/پروتکل‌ها/پایش، با badgeِ موجود|به‌زودی. CSS با همان توکن‌ها، ریسپانسیو، کنتراست AA.
  `node --check i18n.js` + HTML balanced + secret-scan سبز. **[باقی: i18nِ عمیقِ محتوای تب‌های تعاملی = ادامه.]**
- [ ] ریفکتور `panel/ core/ scripts/ tests/ docs/` + SQLite + Migration (Alembic)
- [ ] لاگ ساختاریافته + Semantic Versioning + Git Tagging
- [ ] **[v2.4]** IPv6 کامل · Automated Backup (Telegram/S3/R2) · Audit Log
- [ ] pytest + unit/integration test + **Config Health Check**
- [x] **حقوقی:** Privacy Policy + ToS (fa + en) — پیش‌نیازِ مارکت‌ها ✅ (auto-rp، 2026-06-20): `privacy.html` + `terms.html` دو‌زبانه (فارسیِ RTL + انگلیسیِ LTR)، با همان design-systemِ `assets/css/style.css` (Vazirmatn، dark glass، توکن‌های --acc/--bg)، بدونِ ایموجیِ ساختاری، کنتراست AA، لینک در footerِ `index.html`. پیام: کلید در مرورگر، AS-IS، مسئولیتِ قانونی با کاربر، MIT. **[کاربر باید محتوای حقوقی را برای محدوده‌ی قضاییِ خودش بازبینی کند.]**

## 🟠 اولویت ۲ — وب پنل کامل (۳-۵ هفته)
- [ ] FastAPI + JWT + REST/OpenAPI + WebSocket stats + Export · UI Dark/Glass + i18n/RTL
- [ ] **IP Limit · Speed Limit · HWID · Auto-Disable · Bulk Actions** per user
- [ ] امنیت: Caddy TLS + Rate-Limit/Fail2ban + 2FA + IP whitelist + **[v2.4]** Key Rotation

## 🟡 اولویت ۳ — Kv2m Desktop چندسروره (۲-۴ هفته)
- [ ] PyQt6/CustomTkinter · مدیریت چندسرور · auto-update · macOS/Linux · System Tray

## 🟡 اولویت ۴ — پروتکل‌ها و ضدسانسور (۱-۲ ماه)
- [ ] Hysteria2 · TUIC v5 · WireGuard inbound · Sing-box/Clash sub · Mux
- [ ] **[v2.4]** Tor Bridge Fallback · REALITY IP Scanner · Self-hosted Sub Page · Fragment/uTLS/Noise · بات تلگرام

## 🔵 اولویت ۵ — Multi-Server Management (۱-۲ ماه)
- [ ] Node Agent · یک پنل→چند VPS · Health/Failover/LoadBalance · GeoIP routing · Migration از Marzban/3X-UI

## 🔵 اولویت ۶ — اپ موبایل Flutter (۲-۳ ماه)
- [ ] Flutter cross-platform · **[v2.4] انتشار: Cafe Bazaar اول → Myket → F-Droid → Google Play → iOS**
- [ ] بدون GMS (مارکت‌های ایرانی) · Keystore با ۳ backup · Privacy Policy فارسی

## 🟢 اولویت ۷ — CI/CD + Monitoring (مستمر)
- [ ] GitHub Actions (lint/test/release) · GHCR · **[v2.4]** Prometheus+Grafana stack · SAST/Trivy · Plugin System

## 🔴 بلاکر
- (فعلاً نیست)

---
← [[kian-workspace/01-projects/01-kian-v2ray/kian-v2ray|kian-v2ray]]
