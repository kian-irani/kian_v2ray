<div align="center">

# ⚡ KIAN V2Ray

**نصب خودکار و مدیریت سرور V2Ray — فقط با کپی-پِیست، بدون دانش فنی**

VLESS Reality · WARP · Shadowsocks · کانفیگ‌های دامنه‌دار (TLS/Caddy) · لینک Subscription

<br>

[![Release](https://img.shields.io/github/v/release/kian-irani/kian_v2ray?style=for-the-badge&logo=github&color=76B900&label=Kv2m%20App)](https://github.com/kian-irani/kian_v2ray/releases/latest)
[![License](https://img.shields.io/github/license/kian-irani/kian_v2ray?style=for-the-badge&color=1f6feb)](LICENSE)
[![Stars](https://img.shields.io/github/stars/kian-irani/kian_v2ray?style=for-the-badge&logo=github&color=e3b341)](https://github.com/kian-irani/kian_v2ray/stargazers)
[![Xray](https://img.shields.io/badge/Xray--core-REALITY-76B900?style=for-the-badge&logo=v&logoColor=white)](https://github.com/XTLS/Xray-core)

[🌐 صفحهٔ تعاملی (ساخت کانفیگ)](https://kian-irani.github.io/kian_v2ray/) ·
[💻 دانلود نرم‌افزار Kv2m](https://github.com/kian-irani/kian_v2ray/releases/latest) ·
[📦 ریلیزها](https://github.com/kian-irani/kian_v2ray/releases) ·
[🆘 پشتیبانی](https://t.me/Kian_irani_t)

</div>

---

## ✨ چیست؟

KIAN V2Ray یک ابزار **رایگان و متن‌باز** است که روی **سرورِ خودت** کانفیگ V2Ray می‌سازد.
کلیدها در مرورگر/دستگاهِ خودت ساخته می‌شوند و **هیچ‌جا ذخیره نمی‌شوند**. هدف: کار کردن فقط با **یک کپی-پِیست**.

دو راهِ استفاده:

| راه | برای چه کسی |
|-----|-------------|
| 🌐 **صفحهٔ تعاملی** (مرورگر) | بدون نصب چیزی — آی‌پی را وارد کن، دستور نصب و لینک‌ها را بگیر |
| 💻 **نرم‌افزار Kv2m** (ویندوز) | مدیریت حرفه‌ای: خودش SSH می‌زند، نصب/ساخت/مدیریت کاربر را انجام می‌دهد |

## 🚀 شروع سریع (سرور)

```bash
# دستور دقیق را از صفحهٔ تعاملی یا نرم‌افزار Kv2m بگیر (شامل کلیدهای یکتای تو):
export KIAN_PAYLOAD='...'
curl -fsSL https://raw.githubusercontent.com/kian-irani/kian_v2ray/main/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh
```

## 💻 نرم‌افزار Kv2m (v3.0)

رابط کاربری مدرن با **PySide6/Qt** (سبک Termius + سبز NVIDIA)، **دو-زبانه** (English/فارسی با انتخاب در اولین اجرا).
خودش به سرور SSH می‌زند و همه‌چیز را مدیریت می‌کند — نصب، ساخت کانفیگ، مدیریت کاربر، QR.

| فایل | توضیح |
|------|-------|
| `Kv2m-Setup-x64.exe` | نصب کامل (Start Menu + Desktop) |
| `Kv2m-Portable-x64.exe` | بدون نصب — مستقیم اجرا |

> ویندوز ۱۰/۱۱ ۶۴-بیتی · نیازی به Python ندارد · [دانلود آخرین نسخه](https://github.com/kian-irani/kian_v2ray/releases/latest)

## 🧩 امکانات

- **VLESS Reality** سریع (xtls-rprx-vision) + استتار SNI خودکار
- **WARP** پایدار (WireGuard/MASQUE + بازگشت خودکار به مستقیم)
- **Shadowsocks** (chacha20-ietf-poly1305)
- **کانفیگ‌های دامنه‌دار TLS:** VLESS/VMess-WS، gRPC، Trojan، HTTPUpgrade پشت Caddy + گواهی خودکار Let's Encrypt
- **لینک Subscription** واحد برای هر کاربر (خودکار به‌روز)
- مدیریت **حجم و انقضا**، رفع تداخل پورت، بهینه‌سازی شبکه (BBR + fq)، نصب مجدد امن

## 🔐 امنیت

کلیدها سمتِ کلاینت ساخته می‌شوند و ذخیره نمی‌شوند. برای جزئیات: [SECURITY.md](SECURITY.md).

> یادآوری: کانفیگ‌های دامنه/CDN خروجی را از **IP سرورِ تو** می‌فرستند؛ Cloudflare فقط مسیر ورودی را پنهان می‌کند. باز نشدن بعضی سایت‌ها به IP/کشورِ سرور بستگی دارد، نه به نوع کانفیگ.

## 📡 کانال‌ها

[![Telegram](https://img.shields.io/badge/کانال_آموزش-0088cc?style=flat&logo=telegram&logoColor=white)](https://t.me/kian_irani_cdn_f)
[![Support](https://img.shields.io/badge/پشتیبانی-0088cc?style=flat&logo=telegram&logoColor=white)](https://t.me/Kian_irani_t)

## 🙏 ساخته‌شده با

[Xray-core (REALITY)](https://github.com/XTLS/Xray-core) · [Cloudflare WARP](https://developers.cloudflare.com/warp-client/) · [Caddy](https://caddyserver.com) · PySide6 · qrcode

<div align="center">

ساخته شده با ❤️ توسط **Kian Irani** · [GitHub](https://github.com/kian-irani)

</div>
