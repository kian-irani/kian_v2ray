<div align="center">

# ⚡ KIAN ⟶ V2RAY

**سازندهٔ کانفیگ V2Ray روی سرور خودت — Reality · WARP · Shadowsocks · کانفیگ‌های دامنه‌دار TLS — با یک دستور.**

[![Kv2m App](https://img.shields.io/github/v/release/kian-irani/kian_v2ray?style=for-the-badge&logo=github&color=76B900&label=Kv2m%20App)](https://github.com/kian-irani/kian_v2ray/releases/latest)
[![Subscription](https://img.shields.io/badge/Subscription-HTTPS%20Gist-1f6feb?style=for-the-badge)](#)
[![License](https://img.shields.io/github/license/kian-irani/kian_v2ray?style=for-the-badge&color=e3b341)](LICENSE)
[![Xray](https://img.shields.io/badge/Xray--core-REALITY-76B900?style=for-the-badge&logo=v&logoColor=white)](https://github.com/XTLS/Xray-core)

[🌐 صفحهٔ تعاملی](https://kian-irani.github.io/kian_v2ray/) ·
[💻 دانلود Kv2m](https://github.com/kian-irani/kian_v2ray/releases/latest) ·
[📢 کانال](https://t.me/kian_irani_cdn_f) ·
[💬 پشتیبانی](https://t.me/Kian_irani_t)

</div>

---

## این چیه؟

ابزار **متن‌باز و قانونی** برای ساخت کانفیگ V2Ray روی **سرور خودت** (VPS شخصی). هیچ سرور مرکزی، هیچ وابستگی، هیچ اشتراک ماهانه. IP سرورت را می‌دهی، یک **دستور نصب** می‌گیری، روی سرور می‌زنی، و کانفیگ‌های آماده + **لینک Subscription** تحویل می‌گیری. کلیدها در مرورگر/دستگاهِ خودت ساخته می‌شوند و **هیچ‌جا ذخیره نمی‌شوند**.

## چه چیزهایی دارد؟

| ویژگی | توضیح |
|------|------|
| 🛡️ **VLESS Reality + Vision** | حالت پیش‌فرض — بدون دامنه کار می‌کند، چند SNI خودکار |
| ☁️ **WARP outbound** | دور زدن بلاک‌های خروجی سرور (WireGuard/MASQUE + بازگشت خودکار) |
| 🔒 **Shadowsocks** | پشتیبان یا حالت بدون SNI (chacha20-ietf-poly1305) |
| 🌐 **TLS با دامنه** | VLESS/VMess/Trojan روی WS/gRPC/HTTPUpgrade پشت Caddy روی :443 (+ گواهی خودکار Let's Encrypt) |
| ⭐ **Subscription روی HTTPS** | لینک قطعیِ روی `gist.githubusercontent.com` از طریق Cloudflare Worker — روی هر پروایدری کار می‌کند |
| 👥 **مدیریت چند کاربر** | هر کاربر UUID + توکن sub جداگانه + نام |
| 📊 **حجم و انقضا** | سهمیه و تاریخ انقضا برای هر کاربر، watchdog هر ۱۰ دقیقه |
| 🚀 **BBR + بهینه‌سازی شبکه** | خودکار در نصب |

## معماری

```
کاربر (مرورگر یا نرم‌افزار Kv2m)
   ↓ کلید X25519 + UUID همان‌جا ساخته می‌شود (هیچ‌چیز به ما نمی‌رسد)
   ↓ POST به Cloudflare Worker → Gist HTTPS Subscription
سرور کاربر (VPS Ubuntu)
   ↓ install.sh: Docker + WARP + Xray container + Caddy (اگر TLS)
Xray (kian-xray, host network)
   ├─ Reality inbounds (پورت پویا) → direct / warp
   ├─ Shadowsocks (اختیاری)
   └─ TLS inbounds روی 127.0.0.1 (پشت Caddy :443، اگر دامنه)
   ↓
🌍 اینترنت آزاد
```

## شروع سریع

1. سرور **Ubuntu** بگیر (هر پروایدر).
2. برو به [صفحهٔ تعاملی](https://kian-irani.github.io/kian_v2ray/) یا نرم‌افزار **Kv2m** را باز کن.
3. IP سرور (+ نام کاربر) را وارد کن.
4. دستور نصب را در SSH سرورت Paste کن (یا در Kv2m دکمهٔ «اجرا روی سرور»).
5. لینک **Subscription** را در v2rayNG (اندروید) یا v2rayN (ویندوز) وارد کن.

## 💻 نرم‌افزار Kv2m (v3.0)

رابط مدرن با **PySide6/Qt** (سبک Termius + سبز NVIDIA)، **دو-زبانه** (English/فارسی، انتخاب در اولین اجرا). خودش به سرور SSH می‌زند: نصب، ساخت کانفیگ (Reality/WARP/SS/TLS)، مدیریت کاربر، QR، و لینک Subscription روی HTTPS.

| فایل | توضیح |
|------|-------|
| `Kv2m-Setup-x64.exe` | نصب کامل (Start Menu + Desktop) |
| `Kv2m-Portable-x64.exe` | بدون نصب — مستقیم اجرا |

> ویندوز ۱۰/۱۱ ۶۴-بیتی · بدون نیاز به Python · [دانلود آخرین نسخه](https://github.com/kian-irani/kian_v2ray/releases/latest)

## پروتکل‌های پشتیبانی‌شده

**بدون دامنه (Reality):** VLESS + Reality + Vision (TCP) · Shadowsocks
**با دامنه (TLS):** VLESS-WS · VMess-WS · VLESS-gRPC · VMess-gRPC · Trojan-WS · VLESS-HTTPUpgrade · VMess-HTTPUpgrade

## دستورهای مدیر روی سرور

```bash
kian-v2ray status              # وضعیت سرویس‌ها
kian-v2ray configs             # کانفیگ همهٔ کاربران
kian-v2ray sub <نام>           # لینک Subscription یک کاربر
kian-v2ray users               # لیست کاربران + سهمیه
kian-v2ray add <نام> [GB] [روز]  # افزودن کاربر
kian-v2ray remove <نام>        # حذف کاربر
kian-v2ray renew <نام> [روز]   # تمدید
kian-v2ray reset <نام> [GB]    # ریست سهمیه
kian-v2ray update              # آپدیت Xray
kian-v2ray uninstall           # حذف کامل
```

## امنیت

- **هیچ راز روی سرور ما نیست** — کلیدها در مرورگر/دستگاه تو ساخته می‌شوند و فقط روی سرور خودت می‌روند.
- **توکن Gist** فقط در Cloudflare Worker (secret) است؛ هرگز در صفحه/سرور کاربر دیده نمی‌شود.
- Worker واسط، کاربرها را با `install_id` تصادفی ۱۲۸-بیتی ایزوله می‌کند.
- ریپو پابلیک — کد قابل بازبینی.

> ℹ️ کانفیگ‌های دامنه/CDN خروجی را از **IP سرورِ تو** می‌فرستند؛ Cloudflare فقط مسیر ورودی را پنهان می‌کند. باز نشدن بعضی سایت‌ها به IP/کشورِ سرور بستگی دارد، نه به نوع کانفیگ. **برای گرفتن گواهی TLS موقع نصب، ابر Cloudflare باید خاکستری (DNS-only) باشد؛ بعد از نصب می‌توانی نارنجی کنی.**

## مشارکت و لایسنس

پیشنهاد و گزارش باگ خوش‌آمد است — Issue باز کن یا در [کانال](https://t.me/kian_irani_cdn_f) بنویس. لایسنس: **MIT**.

<div align="center">

ساخته شده با ❤️ توسط **[Kian Irani](https://github.com/kian-irani)** برای دسترسی آزاد به اینترنت

</div>
