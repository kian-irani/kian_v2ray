<div align="center">

# KIAN ⟶ V2RAY

**سازندهٔ کانفیگ V2Ray روی سرور خودت — VLESS Reality + WARP، با یک دستور.**

![Phase](https://img.shields.io/badge/Phase%201-LIVE-2ee6a6?style=flat-square)
![Protocol](https://img.shields.io/badge/VLESS-Reality%20%2B%20Vision-22d3ee?style=flat-square)
![Engine](https://img.shields.io/badge/Xray--core-latest-7c5cff?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-9fb6c8?style=flat-square)

**🌐 صفحهٔ تعاملی:** https://kian-irani.github.io/kian_v2ray/

</div>

---

## این چیه؟

یک ابزار متن‌باز که روی **سرورِ خودت** کانفیگ V2Ray می‌سازد. مشخصات سرور را در صفحهٔ تعاملی وارد می‌کنی، یک دستور می‌گیری، در ترمینال سرور اجرا می‌کنی، و کانفیگ‌های آماده (با QR) تحویل می‌گیری.

- 🔐 **کلیدها در مرورگر خودت ساخته می‌شوند** — هیچ کلید/رمزی به هیچ سروری ارسال نمی‌شود.
- 🧷 **نصب مقاوم در برابر قطعی** — اگر وسط کار SSH قطع شد، نصب در پس‌زمینه ادامه می‌دهد؛ فقط بعد وضعیت می‌گیری.
- ⚙️ **دو حالت Reality**: مستقیم (سرعت بالا) و WARP (همه‌چیز باز، رفع محدودیت پروایدر).
- 👥 **مدیریت کاربر**: تعداد کاربر، حجم، مدت اعتبار — با اعمال خودکار محدودیت.

> ⚠️ **این روش برای کدام سرورها؟** فقط برای سرورهایی که **از داخل ایران بدون فیلترشکن می‌توان به آن‌ها SSH زد** و آی‌پی/پورتشان از ایران در دسترس است. اتصال با دامنه/CDN برای سرورهای کاملاً بلاک‌شده در فازهای بعدی اضافه می‌شود → [docs/connect-now.md](docs/connect-now.md)

---

## شروع سریع

1. صفحهٔ تعاملی را باز کن: **https://kian-irani.github.io/kian_v2ray/**
2. آی‌پی سرور، SNI، حالت اتصال، پورت‌ها، تعداد/حجم/مدت کاربر را پر کن.
3. روی **«ساخت کانفیگ و دستور نصب»** بزن.
4. دستور را کپی و در ترمینال سرور (SSH) اجرا کن:

```bash
export KIAN_PAYLOAD='...'
curl -fsSL https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh
```

5. نصب در پس‌زمینه اجرا می‌شود. بعد از ۲ تا ۵ دقیقه وضعیت بگیر:

```bash
bash /tmp/kian-v2ray.sh status   #  یا بعد از نصب:  kian-v2ray status
```

6. لینک‌های کاربر را از همان صفحهٔ تعاملی کپی/پخش کن — یا روی سرور: `kian-v2ray configs`

---

## معماری

```
کاربر (کلاینت)
   │  VLESS Reality + Vision  (TCP)
   ▼
Xray-core  (Docker · network host)
   ├── reality-direct  ──▶ freedom (مستقیم)  ── 🌍 سریع
   └── reality-warp    ──▶ WARP socks5 :40000 ── 🌍 همه‌چیز باز (رفع بلاک پروایدر)
```

- **مستقیم**: سریع‌ترین مسیر؛ ولی بعضی دسته‌سایت‌ها را پروایدرِ سرور می‌بندد.
- **WARP**: تمام ترافیک از WARP (Cloudflare) خارج می‌شود؛ محدودیت‌های پروایدر برداشته می‌شود.

---

## پروتکل‌ها

| پروتکل | وضعیت |
|---|---|
| VLESS + Reality + Vision (مستقیم) | ✅ فاز ۱ |
| VLESS + Reality + Vision (WARP) | ✅ فاز ۱ |
| Shadowsocks (chacha20-ietf-poly1305) | ✅ اختیاری |
| VLESS/VMess + WS / gRPC / HTTPUpgrade + TLS (دامنه) | 🔜 فاز ۲ |
| فرانت CDN (Cloudflare) | 🔜 فاز ۳ |
| Hysteria2 / TUIC | 🔜 فاز ۵+ |

نقشهٔ کامل: [ROADMAP.md](ROADMAP.md)

---

## دستورهای مدیریت (روی سرور)

```bash
kian-v2ray status                  # وضعیت سرویس، WARP، کاربرها
kian-v2ray configs [نام]           # نمایش لینک‌ها + QR ترمینالی
kian-v2ray users                   # فهرست کاربرها + مصرف/انقضا
kian-v2ray add <نام> [حجم_GB] [روز]   # افزودن کاربر (پیش‌فرض 100GB / 30روز)
kian-v2ray remove <نام>            # حذف کاربر
kian-v2ray reset  <نام> [حجم_GB]   # صفر کردن مصرف
kian-v2ray renew  <نام> [روز]      # تمدید اعتبار
kian-v2ray update                  # آپدیت Xray به آخرین نسخه
kian-v2ray uninstall               # حذف کامل
```

یک watchdog هر ۱۰ دقیقه: سلامت Xray و WARP را چک می‌کند، مصرف هر کاربر را می‌خواند و حجم/انقضا را اعمال می‌کند.

---

## امنیت

- 🚫 **هیچ توکن/رمز/کلیدی در این ریپو نیست.** همه‌چیز عمومی و امن است.
- 🔑 کلیدهای Reality (X25519) و UUIDها در **مرورگرِ خودت** با کتابخانهٔ رمزنگاری لوکال ساخته می‌شوند.
- 📄 کلید خصوصی فقط داخل دستور نصب (که خودت اجرا می‌کنی) و در `‎/etc/xray/config.json` روی سرورِ خودت قرار می‌گیرد.
- جزئیات: [SECURITY.md](SECURITY.md)

---

## ساختار ریپو

```
kian_v2ray/
├── index.html              صفحهٔ تعاملی (GitHub Pages)
├── assets/
│   ├── css/style.css
│   ├── js/app.js           ساخت کانفیگ/کلید/لینک در مرورگر
│   └── vendor/             tweetnacl + qrcodejs (لوکال)
├── install.sh              نصب‌کنندهٔ مقاوم به قطعی (idempotent)
├── scripts/
│   ├── kian-v2ray          ابزار مدیریت
│   └── watchdog.sh         چک سلامت + اعمال حجم/انقضا
└── docs/connect-now.md
```

---

## اعتبارها

ساخته‌شده روی شانه‌های این پروژه‌های متن‌باز:
[Xray-core](https://github.com/XTLS/Xray-core) (REALITY) · [Cloudflare WARP](https://developers.cloudflare.com/warp-client/) · [TweetNaCl.js](https://github.com/dchest/tweetnacl-js) · [qrcodejs](https://github.com/davidshimjs/qrcodejs)

## مجوز

MIT — به [LICENSE](LICENSE) نگاه کن.
