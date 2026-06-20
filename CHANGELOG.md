# Changelog — kian_v2ray

تغییرات مهم پروژه اینجا ثبت می‌شود. نسخه‌بندی اسکریپت‌ها بر اساس [SemVer](https://semver.org).
نسخهٔ pin‌شدهٔ Xray در فایل [`VERSION`](VERSION) نگه‌داری می‌شود.

---

## [core + tooling] — 2026-06-20  (فاز ۱: زیرساختِ کد — auto-rp)

### افزوده شد
- **پکیجِ `core/` (stdlib-only):**
  - `core/db.py` — لایهٔ SQLite با schemaِ کامل (users با IP/Speed/HWID/quota/expiry، audit_log، nodes، settings) +
    pragmaهای WAL/foreign_keys/busy_timeout.
  - `core/migrate.py` — Migration runnerِ forward-only مبتنی بر `PRAGMA user_version` (idempotent).
  - `core/logging.py` — لاگِ ساختاریافتهٔ JSON تک‌خطی (سازگار با jq/Loki).
  - `core/audit.py` — ثبتِ audit (`record`/`tail`) + mirror در لاگ.
- **`scripts/kian-backup.py`** — بکاپِ رمزنگاری‌شده (tar.gz → openssl AES-256-CBC) + آپلود به Telegram/S3/rclone (cron-ready).
- **`scripts/config-health.py`** — اعتبارسنجیِ واقعیِ config.json (یکتاییِ پورت، پروتکلِ شناخته‌شده، فیلدهای Reality،
  cipherِ مجازِ Shadowsocks) + گزینهٔ `--probe` برای تستِ شنونده‌بودنِ پورت‌ها.
- **`scripts/release.sh` + `docs/VERSIONING.md`** — SemVer + git tagging رسمی.
- **تست:** `tests/test_core.py` + `tests/test_scripts.py` (۸ تست) — به `validate.yml` وصل شد (py_compile coreها + pytest).

### تأیید
- `python3 -m py_compile core/* scripts/*` سبز · `pytest -q` → **۸ passed**.
- یک باگِ واقعی پیدا و رفع شد: تداخلِ کلیدِ `name` با LogRecord در لاگِ ساختاریافته (namespace به `kian_fields`).

---

## [site + docs] — 2026-06-20  (PRD + دوزبانه‌سازیِ کاملِ صفحه — auto-rp)

### افزوده شد
- **PRD کامل** (`docs/PRD.md`) + **PLANِ تسک‌محورِ کامل** تا انتهای پروژه (۷ فاز، هر تسک با شناسه).
- **LANDING-i18n-FULL:** `assets/js/i18n.js` بازنویسی شد — پشتیبانیِ `data-i18n-ph` (placeholder) و
  `data-i18n-title` + دیکشنریِ **۱۰۴‌کلیدیِ** FA/EN. کلِ سطحِ تعاملی دوزبانه شد: فرمِ ساختِ کانفیگ
  (لیبل‌ها/placeholderها/option‌ها/کارت‌های حالت/دکمه‌ها/راهنماها)، فرمِ مدیریتِ کاربر (اکشن‌ها/فیلدها)،
  هدینگِ همه‌ی تب‌ها (server/android/pc/tips/domain/manage/about)، و بخشِ about.

### تأیید
- `node --check assets/js/i18n.js` + `node --check assets/js/app.js` سبز.
- ۱۰۴/۱۰۴ کلیدِ ارجاع‌شده در HTML در دیکشنری تعریف شده‌اند؛ تگ‌های HTML متوازن.
- jsdom smoke test سبز (سازنده‌ی کانفیگ دست‌نخورده)؛ سوییچِ زبان به‌درستی FA↔EN و `dir` را عوض می‌کند.
- **باقی‌مانده:** ترجمه‌ی عمیقِ پاراگراف‌های troubleshooting در tab‌های tips/domain (هدینگ‌ها ترجمه شد).

---

## [installer 2.1.0 + site] — 2026-06-20  (خودتشخیصی + صفحهٔ دوزبانه + حقوقی)

### افزوده شد
- **خودتشخیصیِ `status` (فاز ۰.۳):** `kian-v2ray status` (و alias‌های `health`/`doctor`) حالا کرش‌لوپِ Xray
  (RestartCount در آپ‌تایمِ کوتاه)، وضعیتِ WARP (با آگاهی از fallback)، پورت‌های شنونده‌نبودنِ reality/ss،
  سلامتِ Shadowsocks، و سرویس Subscription را تشخیص می‌دهد و برای هر مشکل **دستورِ رفع** چاپ می‌کند.
- **صفحهٔ تعاملی دوزبانه (FA/EN):** سوییچِ زبان با `dir` صحیح (`assets/js/i18n.js`) + سکشنِ **نقشهٔ راه/چشم‌انداز**
  (پلتفرمِ چندسروره، پنلِ وب، اپ موبایل، پروتکل‌های جدید، پایش) با کارت‌های شیشه‌ای و آیکنِ SVG.
- **صفحاتِ حقوقی:** `privacy.html` + `terms.html` دوزبانه (پیش‌نیازِ مارکت‌ها)، لینک در footer.
- **README + ROADMAP:** README بازنویسیِ حرفه‌ای و دوزبانه؛ ROADMAP — فاز ۰ علامتِ ✅ کامل.

### تأیید
- فاز ۰ (۰.۱ پورت API، ۰.۲ WARP fallback، ۰.۴ BBR، ۰.۵ نصبِ امن) از قبل در کد بود و حالا در PLAN/ROADMAP تیک خورد.
- `bash -n install.sh` + `node --check` + HTML well-formed سبز. (۰.۶ SS و تستِ TLS = نیازِ سرور.)

---

## [kv2m 3.0.2] — 2026-06-03  (رفع‌های مهم سرعت/اتصال)

### رفع شد (بحرانی)
- **افت شدید سرعت (در حد کیلوبایت):** `sockopt` با `tcpFastOpen`/`tcpcongestion`/`tcpKeepAliveIdle` که در v2.4 به outbound اضافه شده بود، حذف شد. `tcpFastOpen` روی outbound باعث رفت‌وبرگشت ناموفق SYN و کندی شدید می‌شد. BBR در سطح OS از قبل اعمال می‌شود. (هم اپ هم صفحهٔ وب)
- **کانفیگ‌های نرم‌افزار کار نمی‌کردند / دامنه مشکل داشت:** نرم‌افزار پورت‌ها را از 8443 می‌داد (اغلب توسط ISP/CGNAT کند/بسته)، اما صفحهٔ تعاملی از پورت‌های «تقریباً همیشه باز» (443/2083/2087/2096/8080) استفاده می‌کرد. حالا اپ هم دقیقاً همان pool را دارد و موقع TLS، پورت‌های 443/80 را برای Caddy رزرو می‌کند.
- **دکمهٔ Uninstall کار نمی‌کرد:** سرور برای حذف نیاز به تایپ `DELETE` دارد؛ روی SSH غیرتعاملی هرگز اجرا نمی‌شد. دستور به `echo DELETE | kian-v2ray uninstall` تغییر کرد.

### افزوده شد (پاریتی با صفحهٔ تعاملی)
- **انتخاب SNI:** حالت خودکار/دستی + تعداد SNI + دامنهٔ دلخواه (مثل صفحهٔ تعاملی).
- **کانال دامنه «سریع + WARP» باهم:** علاوه بر direct/warp، حالا گزینهٔ both هم هست (برای هر پروتکل دو کانفیگ ساخته می‌شود).
- **توضیحات داخل اپ:** راهنمای کانفیگ دامنه/TLS و نکتهٔ ابر کلودفلر.
- **صفحات Settings و About پرمحتوا شد:** زبان، مسیرها، کانال‌ها، امکانات، و بخش حمایت (TRC20).

---

## [kv2m 3.0.1] — 2026-06-03

### رفع شد
- **لینک Subscription روی HTTPS (Gist) در نرم‌افزار:** اپ دسکتاپ حالا مثل صفحهٔ تعاملی از **Cloudflare Worker + GitHub Gist** لینک HTTPS Subscription می‌سازد (قبلاً فقط `http://ip:port/sub/...` داشت). payload شامل `gist_proxy` و `install_id` شد تا install.sh هم گیست‌ها را sync کند.
- **علت 403 کشف شد:** Worker روی User-Agent پیش‌فرض urllib خطای 403 کلودفلر می‌داد؛ با UA مرورگری رفع شد و لینک Gist واقعی برمی‌گردد (تست‌شده).
- **کانفیگ‌های دامنه (TLS):** `encode gzip` از Caddyfile حذف شد — می‌توانست استریم gRPC/WebSocket را خراب کند (هم در صفحهٔ وب هم اپ).

### مستندات
- README پروژه به نسخهٔ کامل و غنی بازگردانده شد (جدول ویژگی‌ها، معماری، پروتکل‌ها، دستورها، امنیت) + هشدار «ابر کلودفلر موقع نصب خاکستری باشد».

---

## [kv2m 3.0.0] — 2026-06-02

### تغییر بزرگ — بازنویسی کامل رابط کاربری
- **رابط جدید با PySide6/Qt:** الگوی Termius (چیدمان تمیز، sidebar آیکونی، پنجرهٔ بدون-فریم با title-bar سفارشی) + لهجهٔ سبز NVIDIA (`#76B900`). کارت‌های گرد با سایه، دکمه‌های سبز، فیلدهای فوکوس-سبز.
- **دو-زبانه (i18n):** زبان پایهٔ کد انگلیسی؛ در **اولین اجرا** انتخاب زبان (English | فارسی) پرسیده می‌شود و ذخیره می‌گردد؛ از **Settings** قابل‌تغییر است. فارسی RTL.
- **معماری ماژولار:** کد از یک فایل ۱۱۰۰ خطی به پکیج تمیز تبدیل شد: `core.py` (منطق محض + SSH، تست‌شده)، `i18n.py`، `theme.py`، `app.py` (Qt)، `cli.py`، `kv2m.py` (entry). همهٔ منطق ساخت کانفیگ (Reality/WARP/SS/TLS) دست‌نخورده بازاستفاده شد.

### رفع شد
- **`validate.yml`:** به فایل‌های ناموجود (`kv2m_core.py` و…) اشاره می‌کرد و همیشه fail می‌شد؛ به ساختار ماژولار جدید اصلاح شد.

### تغییر کرد
- وابستگی build از `customtkinter` به `PySide6-Essentials`. نسخه ۳.۰.۰. exe بزرگ‌تر (~۴۵-۶۰MB).

---

## [kv2m 2.5] — 2026-06-02

### افزوده شد
- **کانفیگ‌های دامنه‌دار (TLS) در اپ دسکتاپ:** اپ kv2m حالا مثل صفحهٔ وب، کانفیگ‌های پشت دامنه می‌سازد — VLESS-WS، VMess-WS، VLESS/VMess-gRPC، Trojan-WS، VLESS/VMess-HTTPUpgrade. شامل ساخت Caddyfile، inboundهای داخلی روی localhost، انتخاب کانال (direct/warp)، و لینک‌های کلاینت. payload شامل `tls_domain` و `caddyfile_b64` شد تا install.sh خودکار Caddy + گواهی Let's Encrypt را راه بیندازد. (قبلاً فقط Reality/WARP/Shadowsocks بود.)

---

## [kv2m 2.4] — 2026-06-02

### بهبود یافت
- **بهینه‌سازی سرعت (xray):** افزودن `sockopt` با `tcpFastOpen` + `tcpcongestion: bbr` به outbound مستقیم در هر دو ساخت‌کنندهٔ کانفیگ (صفحهٔ وب و اپ دسکتاپ). همراه با tune سطح-OS (BBR+fq + بافرهای بزرگ) که از قبل موجود بود.

### مستندسازی
- **توضیح شفاف «سایت‌های بلاک‌شده مثل PornHub»:** در تب «دامنه» توضیح داده شد که Cloudflare فقط مسیر *ورودی* را پنهان می‌کند؛ خروجی همچنان از IP سرور است. باز نشدن این سایت‌ها باگِ کانفیگ نیست، بلکه به IP/کشورِ خروجیِ سرور مربوط است (تستِ `curl` روی سرور + راه‌حل‌ها اضافه شد).

### یادداشت
- اپ دسکتاپ kv2m فعلاً فقط Reality/WARP/Shadowsocks می‌سازد؛ کانفیگ‌های دامنه/TLS فقط از طریق صفحهٔ وب در دسترس‌اند (در دست توسعه برای اپ).

---

## [kv2m 2.3] — 2026-06-02

### رفع شد
- **خطای ساخت/انتشار اپ ویندوزی (kv2m):** مرحلهٔ `Create Release` با خطای `403 Resource not accessible by integration` شکست می‌خورد چون `GITHUB_TOKEN` فقط مجوز `contents: read` داشت. با افزودن `permissions: contents: write` به workflow رفع شد. اپ از قبل سالم build می‌شد، فقط انتشار release ناموفق بود.
- **سه باگ NameError در kv2m.py:** متغیر `e` در بلوک‌های `except ... as e:` پس از خروج از بلوک حذف می‌شود، اما داخل `lambda`های async (`self._ui(...)`) فراخوانی می‌شد. با bind کردن `e=e` به‌عنوان آرگومان پیش‌فرض lambda رفع شد.

### تغییر کرد
- نسخهٔ اپ kv2m به `2.3` رسید (هماهنگ با tag انتشار).

---

## [2.0.0] — 2026-05-29

### افزوده شد
- **لینک Subscription کامل (مرورگر + سرور):** برای هر کاربر یک لینک واحد (`http://IP:port/sub/<token>`) که همهٔ کانفیگ‌ها را می‌آورد و خودکار به‌روز می‌شود. سرویس امن `kian-sub` (فقط `/sub/<token>`، بدون path traversal).
- **بنر راهنمای صفحه:** کارت‌های «بار اولمه / کاربر اضافه کنم / لینک کاربر / حذف نصب» برای جلوگیری از سردرگمی.
- **`kian-v2ray sub`** — ساخت/نمایش لینک Subscription هر کاربر.
- **`kian-v2ray update` هوشمند:** نسخه را از `VERSION` می‌خواند، اسکریپت‌ها + Xray (pin) را آپدیت می‌کند، با **بکاپ و rollback خودکار** و **حفظ کامل کاربران/کانفیگ**.
- **`kian-v2ray warp` / `fixport` / `untune`** — مدیریت دستی WARP، رفع تداخل پورت، بازگرداندن tune.
- فایل `VERSION` و همین `CHANGELOG`.

### بهبود یافت
- **WARP پایدار:** اول WireGuard بعد MASQUE، ثبت‌نام مطمئن‌تر، و **fallback خودکار به مستقیم** اگر WARP وصل نشد (کاربر بی‌نت نمی‌ماند) + بازگشت خودکار در watchdog.
- **خودتشخیصی `status`:** کرش‌لوپ، تداخل پورت و WARP مرده را تشخیص می‌دهد و دستور رفع تک‌خطی می‌دهد.
- **auto-fix پورت:** پورت API و پورت‌های reality/ss اگر اشغال بودند خودکار با پورت آزاد جایگزین می‌شوند (به‌جای توقف نصب).
- **نصب مجدد امن:** نصب دوباره کاربران قبلی را پاک نمی‌کند (بکاپ + ادغام خودکار).
- **بهینه‌سازی سرعت (BBR):** فعال‌سازی امن و idempotent BBR/fq + بافرهای TCP (مخصوص استریم/اینستاگرام).
- **SNI_POOL واقعی:** دامنه‌های تست‌شده روی شبکهٔ ایران (icloud, cloudflare, s3.amazonaws, fonts.gstatic, speedtest, amazon)؛ دامنه‌های فیلتر حذف شدند.

---

## [1.x] — فاز ۱
- ساخت کلید/کانفیگ در مرورگر، نصب تک‌دستوری مقاوم به قطع SSH، VLESS Reality (مستقیم + WARP) + Shadowsocks، مدیریت کاربر/حجم، چند SNI/پورت، watchdog.
