# PLAN — kian_v2ray

> آخرین به‌روزرسانی: 2026-06-25 · نسخهٔ فعلی: **v4.1.0**
> هر آیتم: `[x]` = تمام · `[ ]` = باز · `[~]` = در حال انجام

---

## ✅ فازهای تکمیل‌شده

### فاز ۰ — رفعِ باگ‌های بحرانی (v2.1.0)
- [x] تداخلِ پورت API → auto-fix
- [x] پایدارسازی WARP + warp_fallback
- [x] خودتشخیصیِ `status`/`health`/`doctor`
- [x] بهینه‌سازیِ BBR

### فاز ۱ — ثبات + UI (v2.2.0)
- [x] مسیریابیِ WARP در صفحهٔ تعاملی
- [x] پنلِ واقعی (login/logout/JWTِ expire-aware)
- [x] Gist proxy (Cloudflare Worker HTTPS sub)
- [x] Subscription سه‌لایه

### فاز ۲ — پنلِ کامل (v2.3–v2.4)
- [x] Migration / Schema / Repo / Endpoint کامل
- [x] System Monitor + Audit Log + CSV export
- [x] Rate-Limit + Security Headers + CORS + 2FA TOTP + IP whitelist + Key Rotation

### فاز ۳ — Kv2m Desktop چندسروره (v3.1–v3.6)
- [x] مدیریتِ چندسرور (ServerStore)
- [x] REST API پنل (login + CRUD)
- [x] Auto-update (GitHub Releases)
- [x] Dark/Light + persist settings

### فاز ۴ — پروتکل‌ها و ضدسانسور
- [x] Hysteria2 + TUIC v5 inbound (sing-box companion)
- [x] WireGuard + Mux.cool
- [x] Fragment + uTLS + TTL + Noise padding
- [x] REALITY SNI Scanner + Tor Bridge Fallback
- [x] بات تلگرام + Webhook + Email + Push انقضا

### فاز ۵ — Multi-Server Management
- [x] Node Agent سبک
- [x] یک پنل → چند VPS
- [x] Health Check + Auto Failover
- [x] Load Balancing + GeoIP
- [x] Migration از Marzban/3X-UI

### فاز ۶ — اپ موبایل Flutter (v0.1–v0.5.1)
- [x] پروژهٔ واقعیِ Flutter+Android
- [x] صفحاتِ اصلی + اتصالِ واقعی (flutter_v2ray)
- [x] Smart Server Selection + Offline Mode
- [x] تاریخچهٔ نصب
- [x] بدونِ GMS + Market metadata

### فاز ۷ — CI/CD + Monitoring
- [x] GitHub Actions: validate + release + build-app + build-kv2m
- [x] Docker + GHCR + One-click Deploy
- [x] SAST CodeQL (python+js) + Trivy scan
- [x] Prometheus + Grafana Dashboard + Alert Rules

### فاز ۸ — «واقعاً کار کند» (v2.5–v2.7)
- [x] رفعِ REALITY dest → Xray 26.x start می‌شود
- [x] پروتکل‌های جدید قابلِ‌انتخاب + قابلِ‌نصب
- [x] افزودنِ خودکارِ کانفیگ به اپ بعد از نصب
- [x] اپ کانفیگ‌ها/سابسکرایب را نشان می‌دهد
- [x] پنل از داخلِ اپ + تاریخچهٔ نصب
- [x] رفعِ باگِ پنل: `/api/audit` 500 + دکمهٔ کپیِ sub

### فاز ۹ — تجربهٔ کاربری اپ (v4.0.0 bundle)
- [x] نوارِ بالای اندروید مرتب شد (overflow menu، عنوانِ دیده‌شونده)
- [x] حذفِ گروهیِ کانفیگ‌ها (bulk delete)
- [x] کپیِ گروهیِ همهٔ کانفیگ‌ها (copy-all)
- [x] per-app split-tunnel HelpCard دوزبانه
- [x] QR scanner در افزودنِ سرور

### فاز ۱۰ — پروتکل/Transport پیشرفته (v4.0.0 bundle)
- [x] Reality spiderX (`spx=/`) در همهٔ سه نسخه
- [x] ShadowTLS v3 per-user (پورت ۸۴۴۷/tcp)
- [x] AnyTLS per-user (پورت ۸۴۴۶/tcp، sing-box 1.12.0)
- [x] SSH outbound client-side
- [x] ECH plumbing
- [x] resolve_ports: پورتِ اشغال → پورتِ آزادِ خودکار

### فاز ۱۱ — پنلِ کامل per-user (v4.0.0 bundle)
- [x] Migration 0006: ستون‌های routing/dns
- [x] per-user routing/DNS: schema + repo + endpoint + bridge
- [x] فرمِ پنل دوزبانه (select routing + DNS سفارشی)

### فاز ۱۲ — v4.0.0 یکپارچه (همیشه‌WARP + AnyTLS + آپدیتِ درجا + سینکِ خودکار)
- [x] حذفِ انتخابگرِ حالتِ اتصال (همیشه WARP، fallbackِ مستقیم)
- [x] `kian-v2ray update` کامل: script+Xray+panel+companion+resync
- [x] `kian-v2ray resync` + auto-resync بعد از هر تغییر
- [x] دکمهٔ «به‌روزرسانیِ سرور» در اپ موبایل + دسکتاپ
- [x] Hysteria2/TUIC per-user (هر کاربر اعتبارِ جداگانه)
- [x] صفحهٔ تعاملی ۱۰۰٪ دوزبانه (۳۲۰ کلید)
- [x] python3-venv در پیش‌نیازهای نصب
- [x] one-click release via workflow_dispatch

---

## ✅ v4.1.0 — امنیت + رفعِ باگ (2026-06-25) — [PR #3](https://github.com/kian-irani/kian_v2ray/pull/3)

### رفعِ امنیتی (۶ مورد)
- [x] **GitHub Actions injection** — `${{ inputs.version }}` از `run:` بیرون، از `env:` خوانده می‌شود
- [x] **workflow race condition** — `v*` از trigger build-app و build-kv2m حذف شد؛ job `resolve` در kv2m
- [x] **XSS در linkRow()** — `innerHTML` → `textContent` برای SNI کاربر
- [x] **grep -E injection** — ۳ جا `grep -E` → `grep -F` در install.sh
- [x] **systemd credential injection** — credentials در `EnvironmentFile` با chmod 600
- [x] **UUID substring leakage** — `uuid in line` → `re.compile(r'\b' + re.escape(uuid) + r'\b')`

### رفعِ عملکردی (۷ مورد)
- [x] **sub_token ستونِ گمشده** — migration 0007، create_user/import_users توکن می‌سازند
- [x] **subscription page 404** — `?token=` در sub.html، endpoint جدید `/api/users/{name}/sub-url`
- [x] **KIAN_LANG حذف‌شده در kv2m** — از `g['install_cmd']` مستقیم گرفته می‌شود
- [x] **SSH stderr blocking** — `.timeout(timeout)` به stderr stream اضافه شد
- [x] **_workers memory leak** — helper `_launch()` workerهای تمام را پاک می‌کند
- [x] **stale cache بعد از bulk delete** — `saveSelected('')` وقتی selected=null
- [x] **non-atomic write users.json** — `> .tmp && mv` به‌جای `>`

### بهبود
- [x] README.md بازنویسی کامل
- [x] i18n.js: برچسبِ tlsproto به‌روز شد
- [x] installer.nsi: نسخه 3.0.2 → 4.1.0 (mismatch رفع شد)
- [x] CHANGELOG.md: entry v4.1.0

---

## 🔲 باز — آینده

### امنیت / کیفیت (اولویت متوسط)
- [ ] CSS: رنگ‌های hex hard-coded در `.tls-auto-note` → CSS variables
- [ ] `kian-panel.sh print_url`: پورت را از `.env` بخواند (نه parse از unit file)
- [ ] `panel/web/sub.html`: اگر base URL تنظیم نشده، پیامِ راهنما نشان دهد

### قابلیت‌های جدید (پیشنهاد)
- [ ] اپ موبایل: تست on-device روی دستگاهِ واقعی (flutter_v2ray bundle)
- [ ] macOS/Linux build برای kv2m desktop
- [ ] Import از Marzban در UI پنل
- [ ] صفحهٔ تعاملی: دکمهٔ «کپیِ دستور نصب» بدونِ نیاز به باز کردن developer tools

---

## نسخه‌های منتشرشده

| نسخه | تاریخ | تگ | توضیح |
|------|-------|-----|-------|
| v4.1.0 | 2026-06-25 | `v4.1.0` / `app-v4.1.0` / `kv2m-v4.1.0` | امنیت + رفعِ باگ |
| v4.0.0 | 2026-06-24 | `v4.0.0` / `app-v0.5.1` / `kv2m-v3.6.0` | یکپارچه + همیشه‌WARP |
| v2.7.0 | 2026-06-22 | `v2.7.0` | فازهای ۹-۱۲ |
| v2.5.0 | 2026-06-21 | `v2.5.0` | فاز ۸ |
