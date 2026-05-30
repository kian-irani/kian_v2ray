<div align="center">

# KIAN ⟶ V2RAY

**سازندهٔ کانفیگ V2Ray روی سرور خودت — Reality، WARP، Shadowsocks و حالا کانفیگ‌های دامنه‌دار TLS — با یک دستور.**

![Phase](https://img.shields.io/badge/Phase%203-LIVE-2ee6a6?style=flat-square)
![Sub](https://img.shields.io/badge/Subscription-HTTPS%20Gist-22c55e?style=flat-square)
![Reality](https://img.shields.io/badge/VLESS%20Reality-Vision-22d3ee?style=flat-square)
![TLS](https://img.shields.io/badge/WS%20%2F%20gRPC%20%2F%20HTTPUpgrade-TLS-9333ea?style=flat-square)
![Engine](https://img.shields.io/badge/Xray--core-latest-7c5cff?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-9fb6c8?style=flat-square)

**🌐 صفحهٔ تعاملی:** https://kian-irani.github.io/kian_v2ray/
**📢 کانال:** [@kian_irani_cdn_f](https://t.me/kian_irani_cdn_f) · **💬 پشتیبانی:** [@Kian_irani_t](https://t.me/Kian_irani_t)

</div>

---

## این چیه؟

ابزار **متن‌باز و قانونی** برای ساخت کانفیگ V2Ray روی **سرور خودت** (VPS شخصی). هیچ سرور مرکزی، هیچ وابستگی، هیچ اشتراک ماهانه. تو IP سرورت را به صفحه می‌دهی، یک **دستور نصب** می‌گیری، روی سرور می‌زنی، و کانفیگ‌های آماده تحویل می‌گیری.

## چه چیزهایی دارد؟

| ویژگی | توضیح |
|------|------|
| 🛡️ **VLESS Reality + Vision** | حالت پیش‌فرض — بدون دامنه کار می‌کند، چند SNI خودکار |
| ☁️ **WARP outbound** | دور زدن بلاک‌های خروجی سرور (مثلاً پروایدرهای ترکیه) |
| 🔒 **Shadowsocks** | به‌عنوان پشتیبان یا حالت بدون SNI |
| 🌐 **TLS با دامنه (فاز ۳)** | VLESS/VMess/Trojan روی WS/gRPC/HTTPUpgrade پشت Caddy روی :443 |
| ⭐ **Subscription روی HTTPS** | لینک قطعیِ روی `gist.githubusercontent.com` — روی هر پروایدری کار می‌کند |
| 👥 **مدیریت چند کاربر** | هر کاربر UUID + توکن sub جداگانه، با نام مشخص |
| 📊 **حجم و انقضا** | برای هر کاربر سهمیه و تاریخ انقضا |
| 🔧 **مدیر CLI** | `kian-v2ray status/configs/users/add/remove/renew/reset` |
| 🐾 **Watchdog** | هر ۱۰ دقیقه چک سهمیه و وضعیت |
| 🚀 **BBR + بهینه‌سازی شبکه** | خودکار در نصب |

## معماری

```
کاربر (مرورگر)
   ↓ کلید X25519 + UUID همان‌جا ساخته می‌شود
   ↓ صفحه به Cloudflare Worker POST می‌زند → Gist HTTPS Subscription
سرور کاربر (VPS Ubuntu)
   ↓ install.sh: Docker + WARP + Xray container + Caddy (اگر TLS)
Xray (kian-xray, host network)
   ├─ Reality inbounds (پورت‌های پویا) → direct / warp
   ├─ Shadowsocks (اختیاری)
   └─ TLS inbounds روی 127.0.0.1 (پشت Caddy :443، اگر دامنه)
   ↓
🌍 اینترنت آزاد
```

## شروع سریع

1. **سرور Ubuntu بگیر** (هر پروایدر — Hetzner، Netlen، Linode، DigitalOcean، …).
2. برو به https://kian-irani.github.io/kian_v2ray/
3. IP سرور + نام کاربر را وارد کن، دکمه را بزن.
4. دستور نصب را در SSH سرورت Paste کن.
5. لینک **Subscription** را در v2rayNG (اندروید) یا v2rayN (ویندوز) وارد کن.

## پروتکل‌های پشتیبانی‌شده

**بدون دامنه (Reality):**
- VLESS + Reality + Vision (TCP)
- Shadowsocks (chacha20-ietf-poly1305)

**با دامنه (TLS، اختیاری):**
- VLESS + WS + TLS
- VMess + WS + TLS
- VLESS + gRPC + TLS
- VMess + gRPC + TLS
- Trojan + WS + TLS
- VLESS + HTTPUpgrade + TLS
- VMess + HTTPUpgrade + TLS

## امنیت

- **هیچ راز روی سرور ما نیست.** کلیدها در مرورگر تو ساخته می‌شوند و فقط روی سرور خودت می‌روند.
- **توکن Gist** فقط در Cloudflare Worker (secret) است؛ هرگز در صفحه/سرور کاربر دیده نمی‌شود.
- **Worker واسط** کاربرها را با `install_id` تصادفی ۱۲۸ بیتی ایزوله می‌کند.
- ریپو پابلیک — هر کس می‌تواند کد را بازبینی کند.

## دستورهای مدیر روی سرور

```bash
kian-v2ray status              # وضعیت سرویس‌ها
kian-v2ray configs             # نمایش کانفیگ همهٔ کاربران
kian-v2ray sub <نام>           # لینک Subscription یک کاربر
kian-v2ray users               # لیست کاربران + سهمیه
kian-v2ray add <نام> [GB] [روز]  # افزودن کاربر
kian-v2ray remove <نام>        # حذف کاربر
kian-v2ray renew <نام> [روز]   # تمدید
kian-v2ray reset <نام> [GB]    # ریست سهمیه
kian-v2ray update              # آپدیت Xray
kian-v2ray uninstall           # حذف کامل
```

## نرم‌افزار همراه: Kv2m

برای کسانی که می‌خواهند بدون مرورگر کار کنند، **Kv2m** یک نرم‌افزار PC/اندروید (Python) است که خودش SSH می‌زند و همین کارها را انجام می‌دهد. در پوشهٔ `kv2m/` ریپو.

## مشارکت

پیشنهاد و گزارش باگ خوش‌آمد است. لطفاً Issue باز کن یا در کانال تلگرام بنویس.

## لایسنس

MIT. این پروژه برای دسترسی آزاد به اطلاعات است.
