/* KIAN V2Ray — bilingual (FA ↔ EN) layer for the landing page.
 * Loaded after app.js and intentionally independent of it: it only swaps the
 * textContent / innerHTML / placeholder of tagged elements and flips
 * <html lang|dir>, so it can never break the interactive config generator.
 * Persian is the in-HTML default; English comes from this dictionary.
 *
 * Attributes:
 *   data-i18n="key"        → swaps textContent
 *   data-i18n-html="key"   → swaps innerHTML (use for strings containing markup)
 *   data-i18n-ph="key"     → swaps the placeholder attribute (form inputs)
 *   data-i18n-title="key"  → swaps the title attribute (tooltips)
 */
(function () {
  "use strict";

  var DICT = {
    "phase":        { fa: "رایگان · متن‌باز", en: "Free · Open-source" },
    "hero.title":   { fa: "کانفیگ سرورت رو در یک دقیقه بساز", en: "Build your server config in one minute" },
    "hero.lede":    {
      fa: "فقط <b>آی‌پی سرورت</b> رو وارد کن. یک دستور می‌گیری، توی سرور می‌زنی، و کانفیگ آماده (با QR) تحویل می‌گیری. نیازی نیست چیزی از پورت و تنظیمات فنی بدونی — همه‌چیز خودکاره.",
      en: "Just enter <b>your server IP</b>. You get one command, run it on your server, and receive a ready config (with QR). No need to know anything about ports or technical settings — it's all automatic."
    },
    "hero.chip1":   { fa: "🟢 فقط کپی-پیست", en: "🟢 Copy-paste only" },
    "hero.chip2":   { fa: "🔐 کلیدها توی مرورگر خودت", en: "🔐 Keys stay in your browser" },
    "hero.chip3":   { fa: "📱 اندروید + 💻 ویندوز", en: "📱 Android + 💻 Windows" },

    "tab.gen":      { fa: "⚙️ ساخت کانفیگ", en: "⚙️ Build config" },
    "tab.server":   { fa: "🖥️ نصب روی سرور", en: "🖥️ Install on server" },
    "tab.android":  { fa: "📱 اندروید", en: "📱 Android" },
    "tab.pc":       { fa: "💻 ویندوز / PC", en: "💻 Windows / PC" },
    "tab.tips":     { fa: "💡 نکات و عیب‌یابی", en: "💡 Tips & troubleshooting" },
    "tab.domain":   { fa: "🌐 دامنه و TLS", en: "🌐 Domain & TLS" },
    "tab.manage":   { fa: "👥 مدیریت کاربر", en: "👥 User management" },
    "tab.about":    { fa: "ℹ️ درباره", en: "ℹ️ About" },

    /* ---------- GEN tab: guide + notice + card head ---------- */
    "g.guide.q":    { fa: "کدوم وضعیت تویی؟ 👇", en: "Which situation are you in? 👇" },
    "g.guide.c1t":  { fa: "بار اولمه", en: "First time" },
    "g.guide.c1d":  { fa: "می‌خوام روی یه سرور تازه نصب کنم و کانفیگ بگیرم — فرم پایین رو پر کن", en: "I want to install on a fresh server and get a config — fill in the form below" },
    "g.guide.c2t":  { fa: "قبلاً نصب کردم، کاربر اضافه کنم", en: "Already installed, add a user" },
    "g.guide.c2d":  { fa: "سرورم آماده‌ست؛ فقط می‌خوام کاربر/کانفیگ جدید بسازم — <b>نیازی به نصب دوباره نیست</b>", en: "My server is ready; I just want a new user/config — <b>no need to reinstall</b>" },
    "g.guide.c3t":  { fa: "لینک کاربرم رو می‌خوام", en: "I want my user's link" },
    "g.guide.c3d":  { fa: "می‌خوام لینک Subscription یا کانفیگ یه کاربر موجود رو بگیرم", en: "I want the subscription link or config of an existing user" },
    "g.guide.c4t":  { fa: "می‌خوام کلاً حذف کنم", en: "I want to remove it entirely" },
    "g.guide.c4d":  { fa: "سرویس رو کامل از سرور پاک کنم (uninstall)", en: "Completely uninstall the service from the server" },
    "g.guide.warn": {
      fa: "⚠️ اگه قبلاً نصب کردی و فقط می‌خوای کاربر اضافه کنی، <b>دوباره نصب نکن</b> — از «مدیریت کاربر» استفاده کن. نصب دوباره فقط وقتی لازمه که بخوای تنظیمات پایه (پورت/SNI) رو عوض کنی (کاربرهای قبلی خودکار حفظ می‌شن).",
      en: "⚠️ If you've already installed and only want to add a user, <b>do not reinstall</b> — use “User management”. Reinstalling is only needed to change base settings (port/SNI); existing users are preserved automatically."
    },
    "g.notice.t":   { fa: "قبل از شروع: این روش برای چه سروری کار می‌کند؟", en: "Before you start: which server does this work for?" },
    "g.notice.d":   {
      fa: "برای سروری که <b>از داخل ایران بدون فیلترشکن بهش SSH می‌خوره</b> و آی‌پی‌اش از ایران بازه (بیشتر سرورهای خارجِ تازه). اگه سرور نداری، توی تب <b>«نصب روی سرور»</b> گفتم از کجا بخری.",
      en: "For a server that is <b>reachable over SSH from inside Iran without a VPN</b> and whose IP is open from Iran (most fresh foreign servers). If you don't have a server, the <b>“Install on server”</b> tab explains where to buy one."
    },
    "g.head.t":     { fa: "⚙️ ساخت کانفیگ", en: "⚙️ Build config" },
    "g.head.d":     { fa: "فقط آی‌پی سرورت رو بزن و دکمه رو فشار بده. همین.", en: "Just enter your server IP and press the button. That's it." },

    /* ---------- GEN tab: form fields ---------- */
    "g.f.ip.l":     { fa: "🖥️ آی‌پی سرور", en: "🖥️ Server IP" },
    "g.f.ip.ph":    { fa: "مثلاً ۱۸۵.۱۲.۳.۴۵", en: "e.g. 185.12.3.45" },
    "g.f.ip.h":     { fa: "همون آی‌پی که با اون به سرور وصل می‌شی (SSH). بعد از خرید سرور بهت داده می‌شه.", en: "The same IP you use to connect to the server (SSH). It's given to you after you buy the server." },
    "g.f.user.l":   { fa: "👤 نام کاربر", en: "👤 User name" },
    "g.f.user.ph":  { fa: "مثلاً ali یا reza", en: "e.g. ali or reza" },
    "g.f.user.h":   { fa: "یک نام انگلیسی برای این کاربر بذار (حروف/عدد). <b>این نام مهمه:</b> لینک Subscription و کانفیگ‌های هر کاربر با همین نام از هم جدا می‌شن تا قاطی نشن. برای چند کاربر، خودکار شماره می‌خوره (مثلاً ali-1, ali-2).", en: "Pick an English name for this user (letters/digits). <b>This name matters:</b> each user's subscription link and configs are separated by it so they don't mix. For multiple users it is auto-numbered (e.g. ali-1, ali-2)." },

    "g.tips.head":  { fa: "💡 سرور ایده‌آل برای نصب", en: "💡 The ideal server to install on" },
    "g.tips.p1":    { fa: "یک VPS با <b>Ubuntu ۲۲.۰۴ یا ۲۴.۰۴ تازه نصب‌شده</b> (یا «Reinstall OS» از پنل پروایدر). بهتر است هیچ پنل V2Ray دیگری (مثل 3x-ui، X-UI، Marzban)، هیچ Docker قبلی، هیچ Caddy/Nginx از قبل نباشد — این‌طور نصب از همان بار اول بدون تداخل کار می‌کند.", en: "A VPS with <b>a fresh Ubuntu 22.04 or 24.04</b> (or “Reinstall OS” from the provider panel). Ideally there is no other V2Ray panel (3x-ui, X-UI, Marzban), no prior Docker, and no existing Caddy/Nginx — so the install works the first time without conflicts." },
    "g.tips.p2":    { fa: "اگر روی سرورت پنل دیگری داری، یا اول uninstallش کن، یا در «تنظیمات پیشرفته» پایین، پورت پایه را به عددی بالاتر (مثل ۹۴۴۳) عوض کن تا با چیزی که داری برخورد نکند.", en: "If you have another panel on your server, either uninstall it first, or in “Advanced settings” below change the base port to a higher number (e.g. 9443) so it doesn't clash with what you have." },

    "g.mode.l":     { fa: "🌐 حالت اتصال", en: "🌐 Connection mode" },
    "g.mode.both.t":{ fa: "هر دو ✨", en: "Both ✨" },
    "g.mode.both.s":{ fa: "پیشنهادی — هم سریع، هم همه‌چیز باز. دو لینک می‌گیری.", en: "Recommended — fast and everything open. You get two links." },
    "g.mode.dir.t": { fa: "سریع", en: "Fast" },
    "g.mode.dir.s": { fa: "سریع‌ترین، ولی شاید بعضی سایت‌ها باز نشه.", en: "Fastest, but some sites may not open." },
    "g.mode.warp.t":{ fa: "همه‌چیز باز", en: "Everything open" },
    "g.mode.warp.s":{ fa: "از WARP رد می‌شه، کمی کندتر.", en: "Routes through WARP, a bit slower." },
    "g.mode.ns.t":  { fa: "بدون SNI ⚠️", en: "No SNI ⚠️" },
    "g.mode.ns.s":  { fa: "Shadowsocks ساده — بدون استتار. فقط برای خودت.", en: "Plain Shadowsocks — no camouflage. For personal use only." },
    "g.mode.h":     { fa: "نمی‌دونی کدوم؟ همون «هر دو» رو بذار — هر دو لینک رو می‌گیری و هرکدوم بهتر بود استفاده کن. «بدون SNI» ساده‌ست ولی ممکنه آی‌پی سرورت زودتر فیلتر بشه (پایین توضیح دادم).", en: "Not sure which? Leave it on “Both” — you get both links and use whichever works best. “No SNI” is simple but may get your server IP blocked sooner (explained below)." },

    "g.num.l":      { fa: "👥 چند نفر می‌خوان استفاده کنن؟", en: "👥 How many people will use it?" },
    "g.num.h":      { fa: "برای هر نفر یک کانفیگ جدا ساخته می‌شه. اگه فقط خودتی، روی ۱ بذار.", en: "A separate config is built for each person. If it's just you, set it to 1." },

    "g.adv.toggle": { fa: "تنظیمات پیشرفته (اختیاری — اگه نمی‌دونی دست نزن)", en: "Advanced settings (optional — leave it if unsure)" },

    "g.btn":        { fa: "🚀 ساخت کانفیگ و دستور نصب", en: "🚀 Build config & install command" },
    "g.btn.note":   { fa: "هیچ اطلاعاتی به جایی ارسال نمی‌شه — همه‌چیز همین‌جا توی مرورگر تو ساخته می‌شه.", en: "Nothing is sent anywhere — everything is built right here in your browser." },

    /* ---------- Tab section headings ---------- */
    "s.server.h":   { fa: "🖥️ نصب روی سرور — قدم به قدم", en: "🖥️ Install on server — step by step" },
    "s.server.buy": { fa: "🛒 سرور نداری؟ از کجا بخری", en: "🛒 No server? Where to buy one" },
    "s.android.h":  { fa: "📱 راه‌اندازی روی اندروید", en: "📱 Set up on Android" },
    "s.pc.h":       { fa: "💻 راه‌اندازی روی ویندوز / کامپیوتر", en: "💻 Set up on Windows / PC" },
    "s.tips.h":     { fa: "💡 نکات و عیب‌یابی", en: "💡 Tips & troubleshooting" },
    "s.domain.h":   { fa: "🌐 راهنمای کامل کانفیگ‌های دامنه‌دار (TLS)", en: "🌐 Full guide to domain-based (TLS) configs" },
    "s.manage.h":   { fa: "👥 مدیریت کاربر — بدون حفظ‌کردن دستور", en: "👥 User management — no commands to memorize" },
    "s.about.h":    { fa: "ℹ️ درباره", en: "ℹ️ About" },

    /* ---------- MANAGE form ---------- */
    "m.action.l":   { fa: "چه کاری می‌خوای بکنی؟", en: "What do you want to do?" },
    "m.act.add":    { fa: "➕ افزودن کاربر جدید", en: "➕ Add a new user" },
    "m.act.configs":{ fa: "🔗 دیدن کانفیگ یک کاربر (با QR)", en: "🔗 View a user's config (with QR)" },
    "m.act.sub":    { fa: "⭐ گرفتن لینک Subscription یک کاربر", en: "⭐ Get a user's subscription link" },
    "m.act.renew":  { fa: "🔄 تمدید اعتبار کاربر", en: "🔄 Renew a user's validity" },
    "m.act.reset":  { fa: "♻️ صفر/تغییر حجم کاربر", en: "♻️ Reset/change a user's quota" },
    "m.act.remove": { fa: "🗑️ حذف کاربر", en: "🗑️ Remove a user" },
    "m.act.users":  { fa: "📋 لیست همهٔ کاربرها و مصرف", en: "📋 List all users and usage" },
    "m.act.status": { fa: "📊 وضعیت سرویس", en: "📊 Service status" },
    "m.act.update": { fa: "⬆️ آپدیت کامل سرور (Xray+پنل+پروتکل‌ها، حفظ کاربران)", en: "⬆️ Full server update (Xray+panel+protocols, keeps users)" },
    "m.act.protocols": { fa: "➕ فعال‌سازی پروتکل‌های جدید (Hysteria2/TUIC/AnyTLS)", en: "➕ Enable new protocols (Hysteria2/TUIC/AnyTLS)" },
    "m.act.resync": { fa: "🔁 سینک لینک‌های Subscription (بعد از تغییرات)", en: "🔁 Resync subscription links (after changes)" },
    "m.act.uninst": { fa: "❌ حذف کامل نصب از سرور", en: "❌ Fully uninstall from the server" },
    "m.name.l":     { fa: "نام کاربر (انگلیسی — مثل ali یا user-2)", en: "User name (English — e.g. ali or user-2)" },
    "m.name.h":     { fa: "همان نامی که موقع ساخت گذاشتی، یا یک نام جدید برای کاربر تازه.", en: "The name you set when creating it, or a new name for a new user." },
    "m.gb.l":       { fa: "حجم (گیگ — ۰ یعنی نامحدود)", en: "Quota (GB — 0 means unlimited)" },
    "m.days.l":     { fa: "مدت (روز — ۰ یعنی دائمی)", en: "Duration (days — 0 means permanent)" },
    "m.run.l":      { fa: "👇 این دستور را در ترمینال سرور بزن:", en: "👇 Run this command in the server terminal:" },

    /* ---------- web panel setup (manage tab) ---------- */
    "pn.head":      { fa: "🖥️ پنلِ وبِ مدیریت (اختیاری)", en: "🖥️ Web management panel (optional)" },
    "pn.desc":      { fa: "به‌جای ترمینال، یک پنلِ گرافیکی (داشبورد) روی سرورت راه بینداز: مدیریتِ کاربر، آمار، محدودیتِ IP/سرعت، ۲FA و مدیریتِ چندسرور. نام کاربری و رمزِ ادمین را بزن تا دستورِ آماده بگیری.", en: "Instead of the terminal, run a graphical dashboard on your server: user management, stats, IP/speed limits, 2FA and multi-server. Enter an admin username & password to get a ready command." },
    "pn.user":      { fa: "نام کاربری ادمین", en: "Admin username" },
    "pn.pass":      { fa: "رمز عبور ادمین", en: "Admin password" },
    "pn.gen":       { fa: "ساخت دستورِ راه‌اندازی", en: "Generate setup command" },
    "pn.cmdlabel":  { fa: "این را روی سرور بزن (نصب باید قبلاً انجام شده باشد):", en: "Run this on the server (install must already be done):" },
    "pn.urllabel":  { fa: "آدرس پنل بعد از راه‌اندازی:", en: "Panel URL after setup:" },

    /* ---------- ABOUT headings ---------- */
    "ab.roadmap":   { fa: "🗺️ نقشهٔ راه", en: "🗺️ Roadmap" },
    "ab.kv2m":      { fa: "🛠️ نرم‌افزار Kv2m (جدید)", en: "🛠️ Kv2m app (new)" },
    "ab.channels":  { fa: "👤 کانال‌ها و ارتباط", en: "👤 Channels & contact" },
    "ab.donate":    { fa: "💝 حمایت (اختیاری)", en: "💝 Support (optional)" },
    "ab.builtwith": { fa: "🙏 ساخته‌شده با استفاده از", en: "🙏 Built with" },
    "ab.desc": { fa: "KIAN V2Ray یک ابزار رایگان و متن‌بازه که روی <b>سرورِ خودت</b> کانفیگ V2Ray (VLESS Reality + WARP) می‌سازه. کلیدها توی مرورگر خودت ساخته می‌شن و هیچ‌جا ذخیره نمی‌شن. هدف اینه که حتی بدون دانش فنی، فقط با کپی-پیست کار کنه.", en: "KIAN V2Ray is a free, open-source tool that builds V2Ray configs (VLESS Reality + WARP) on <b>your own server</b>. Keys are generated in your browser and stored nowhere. The goal: it works with copy-paste only, even without technical knowledge." },
    "ab.roadmap.f": {
      fa: "<li>✅ <b>فاز ۱:</b> Reality سریع + WARP، نصب تک‌دستوری، مدیریت کاربر/حجم.</li><li>✅ <b>پایداری و سرعت:</b> WARP با WireGuard/MASQUE + بازگشت خودکار به مستقیم، خودتشخیصی در <span class=\"mono\">status</span>، رفع تداخل پورت، نصب مجدد امن، بهینه‌سازی BBR.</li><li>✅ <b>فاز ۲ (الان):</b> لینک Subscription — برای هر کاربر یک لینک واحد که در v2rayNG واردش می‌کنی و همهٔ کانفیگ‌ها خودکار می‌آیند و به‌روز می‌مانند.</li><li>🔜 <b>فاز ۳:</b> دامنه + TLS واقعی (WS/gRPC پشت Caddy) برای سرورهای سخت‌گیر.</li><li>🔜 <b>فاز ۴:</b> فرانت CDN برای سرورهایی که آی‌پی‌شون از ایران بسته‌ست.</li><li>🔜 <b>فاز ۵:</b> اتصال مستقیم به ربات تلگرام + هشدار حجم.</li>",
      en: "<li>✅ <b>Phase 1:</b> Fast Reality + WARP, one-command install, user/quota management.</li><li>✅ <b>Stability & speed:</b> WARP over WireGuard/MASQUE + auto-fallback to direct, self-diagnosis in <span class=\"mono\">status</span>, port-conflict fixing, safe reinstall, BBR tuning.</li><li>✅ <b>Phase 2 (now):</b> Subscription link — one link per user that you import into v2rayNG; all configs arrive automatically and stay up to date.</li><li>🔜 <b>Phase 3:</b> Domain + real TLS (WS/gRPC behind Caddy) for strict servers.</li><li>🔜 <b>Phase 4:</b> CDN fronting for servers whose IP is blocked from Iran.</li><li>🔜 <b>Phase 5:</b> Direct Telegram-bot control + quota alerts.</li>"
    },
    "ab.kv2m.d": { fa: "برای مدیریت حرفه‌ای‌تر، نرم‌افزار <b>Kv2m</b> خودش به سرورت SSH می‌زند و همه‌چیز را مدیریت/نصب می‌کند — برای ویندوز/مک/لینوکس و اندروید (Termux).", en: "For more pro management, the <b>Kv2m</b> app SSHes into your server itself and manages/installs everything — for Windows/macOS/Linux and Android (Termux)." },
    "ab.kv2m.dl": { fa: "💻 دانلود و راهنما: <a href=\"https://github.com/kian-irani/kian_v2ray/tree/main/kv2m\" target=\"_blank\" rel=\"noopener\">پوشهٔ kv2m در گیت‌هاب</a>", en: "💻 Download & guide: <a href=\"https://github.com/kian-irani/kian_v2ray/tree/main/kv2m\" target=\"_blank\" rel=\"noopener\">the kv2m folder on GitHub</a>" },
    "ab.ch.learn": { fa: "🎓 آموزش و کانال<br><span>@kian_irani_cdn_f</span>", en: "🎓 Tutorials & channel<br><span>@kian_irani_cdn_f</span>" },
    "ab.ch.support": { fa: "🆘 پشتیبانی<br><span>@Kian_irani_t</span>", en: "🆘 Support<br><span>@Kian_irani_t</span>" },
    "ab.ch.mhrv": { fa: "🤖 ربات MHRV<br><span>@Mhrv_script_bot</span>", en: "🤖 MHRV bot<br><span>@Mhrv_script_bot</span>" },
    "ab.ch.zyrln": { fa: "🤖 ربات Zyrln<br><span>@Zyrln_script_bot</span>", en: "🤖 Zyrln bot<br><span>@Zyrln_script_bot</span>" },
    "ab.ch.src": { fa: "⭐ سورس در گیت‌هاب<br><span>kian_v2ray</span>", en: "⭐ Source on GitHub<br><span>kian_v2ray</span>" },
    "ab.donate.d": { fa: "این پروژه رایگانه ولی هزینهٔ سرور و وقت توسعه واقعیه. اگه دوست داشتی:", en: "This project is free, but server costs and dev time are real. If you'd like to help:" },
    "ab.copy": { fa: "کپی", en: "Copy" },
    "ab.footer": { fa: "ساخته شده با ❤️ توسط Kian Irani", en: "Made with ❤️ by Kian Irani" },
    "mg.intro": { fa: "عملیات را انتخاب کن و فیلدها را پر کن؛ یک <b>دستور آمادهٔ کپی</b> می‌گیری. کافی است یک‌بار آن را در ترمینال سرور (SSH) Paste کنی — نیازی نیست چیزی را به‌خاطر بسپاری یا دستی بنویسی.", en: "Pick an action and fill the fields; you get a <b>ready-to-copy command</b>. Just paste it once into the server terminal (SSH) — no need to memorize or type anything by hand." },
    "mg.note": { fa: "برای «افزودن کاربر»، بعد از اجرا، کانفیگ همان کاربر با QR در ترمینال نشان داده می‌شود. این دستورها فقط روی سروری کار می‌کنند که قبلاً نصب را روی آن انجام داده‌ای.", en: "For “Add user”, after running it the user's config with a QR is shown in the terminal. These commands only work on a server where you've already installed." },
    "mg.callout": { fa: "🔭 در فازهای بعدی، این کارها مستقیم از <b>ربات تلگرام</b> بدون ترمینال انجام می‌شود (نقشهٔ راه را در تب «درباره» ببین).", en: "🔭 In future phases these will be done straight from a <b>Telegram bot</b> without a terminal (see the roadmap in the “About” tab)." },

    /* ---------- TIPS tab (deep prose) ---------- */
    "tp.h.diff":      { fa: "چرا همه‌چیز از WARP می‌رود؟", en: "Why does everything go through WARP?" },
    "tp.diff.1":      { fa: "<b>همهٔ کانفیگ‌ها از WARP کلودفلر خارج می‌شوند</b> — تقریباً همه‌چیز باز می‌شود (سایت‌هایی که پروایدرِ سرور بسته، یا تحریم‌های جغرافیایی) و IP واقعیِ خروجیِ سرورت کمتر دیده می‌شود.", en: "<b>Every config egresses through Cloudflare WARP</b> — almost everything opens (sites the server's provider blocks, or geo-restrictions) and your server's real exit IP is less exposed." },
    "tp.diff.2":      { fa: "اگر WARP موقتاً قطع شود، سرور خودکار به خروجیِ مستقیم سوییچ می‌کند تا بی‌نت نمانی و بعد دوباره به WARP برمی‌گردد — این کاملاً خودکار است و انتخابی نداری.", en: "If WARP drops momentarily, the server auto-switches to a direct exit so you stay online, then returns to WARP — fully automatic, no choice to make." },
    "tp.diff.3":      { fa: "حالتِ «سریع/مستقیم» حذف شده است؛ دیگر لازم نیست بینِ کانفیگ‌ها انتخاب کنی.", en: "The old “Fast/Direct” mode is gone; you no longer pick between configs." },
    "tp.h.filter":    { fa: "🚨 آی‌پی سرورت کِی فیلتر می‌شه؟ (مهم‌ترین نکته)", en: "🚨 When does your server IP get blocked? (the key point)" },
    "tp.filter.lead": { fa: "سامانه فیلترینگ ایران الگوی ترافیک رو تحلیل می‌کنه. هر چی <b>الگوی ترافیک یک IP \"مشکوک‌تر\"</b> باشه، احتمال فیلتر شدنش بیشتره. عوامل اصلی:", en: "Iran's filtering system analyzes traffic patterns. The <b>more \"suspicious\" an IP's pattern</b>, the more likely it gets blocked. Main factors:" },
    "tp.filter.1":    { fa: "<b>تعداد کاربران روی یک IP:</b> ۱-۳ نفر معمولاً امن. <b>بیشتر از ۵ نفر</b> ⟵ ریسک بالا. ۲۰+ نفر ⟵ تقریباً قطعاً فیلتر می‌شه.", en: "<b>Users per IP:</b> 1–3 is usually safe. <b>More than 5</b> ⟵ high risk. 20+ ⟵ almost certainly blocked." },
    "tp.filter.2":    { fa: "<b>حجم ترافیک:</b> چند گیگ در هفته OK. <b>چند صد گیگ در هفته</b> روی یک IP ⟵ خطر جدی.", en: "<b>Traffic volume:</b> a few GB/week is OK. <b>Hundreds of GB/week</b> on one IP ⟵ serious risk." },
    "tp.filter.3":    { fa: "<b>مدت اتصال:</b> اتصال‌های طولانی و پایدار به یک پورت غیرمعمول، الگوی واضحی به DPI می‌ده.", en: "<b>Connection duration:</b> long, steady connections to an unusual port give DPI a clear signature." },
    "tp.filter.type": { fa: "نوع کانفیگ:", en: "Config type:" },
    "tp.filter.reality": { fa: "<b>Reality (TCP، IP لخت):</b> چون پورت غیرمعمول و IP مستقیمه، ریسک متوسط تا بالا.", en: "<b>Reality (TCP, bare IP):</b> unusual port + direct IP, so medium-to-high risk." },
    "tp.filter.ss":   { fa: "<b>Shadowsocks (بدون SNI):</b> چون استتار TLS نداره، <b>بیشترین ریسک</b> ⟵ فقط برای استفادهٔ شخصی.", en: "<b>Shadowsocks (no SNI):</b> no TLS camouflage, so <b>highest risk</b> ⟵ personal use only." },
    "tp.filter.tls":  { fa: "<b>TLS با دامنه پشت Cloudflare:</b> ترافیک به IPهای Cloudflare می‌ره نه IP سرورت ⟵ <b>کم‌ترین ریسک</b>. اگر یک IP CF بسته شد، خودش IP دیگه می‌ده.", en: "<b>Domain TLS behind Cloudflare:</b> traffic goes to Cloudflare IPs, not your server's ⟵ <b>lowest risk</b>. If one CF IP is blocked, it serves another." },
    "tp.h.advice":    { fa: "📊 توصیه بر اساس کاربری", en: "📊 Recommendation by usage" },
    "tp.advice.1":    { fa: "<b>فقط خودت (۱ نفر):</b> هر کدام از حالت‌ها OK. Reality کافیه.", en: "<b>Just you (1 person):</b> any mode is fine. Reality is enough." },
    "tp.advice.2":    { fa: "<b>۲-۳ نفر (خانواده/دوستان نزدیک):</b> Reality + WARP کافیه. مصرف معمولی مشکلی نمی‌سازه.", en: "<b>2–3 people (family/close friends):</b> Reality + WARP is enough. Normal usage is fine." },
    "tp.advice.3":    { fa: "<b>۴ نفر به بالا، یا پخش عمومی:</b> <b>حتماً</b> دامنه بگیر و حالت TLS رو فعال کن. ابر Cloudflare رو نارنجی کن (Proxied). این‌طوری IP اصلیت مخفی می‌مونه.", en: "<b>4+ people, or public sharing:</b> <b>definitely</b> get a domain and enable TLS. Turn the Cloudflare cloud orange (Proxied) so your real IP stays hidden." },
    "tp.advice.4":    { fa: "<b>اگر آی‌پی فیلتر شد:</b> یا یک سرور جدید بگیر (~$۲/ماه)، یا اگر دامنه داری، فقط رکورد A رو به IP جدید عوض کن — کاربران چیزی نمی‌فهمن.", en: "<b>If the IP gets blocked:</b> either get a new server (~$2/mo), or if you have a domain just point the A record to the new IP — users won't notice." },
    "tp.h.noconn":    { fa: "اتصال برقرار نمی‌شه؟", en: "Connection won't establish?" },
    "tp.noconn.1":    { fa: "مطمئن شو آی‌پی سرور درست وارد شده و سرور روشنه.", en: "Make sure the server IP is correct and the server is up." },
    "tp.noconn.2":    { fa: "صبر کن نصب کامل بشه (با <span class=\"mono\">status</span> چک کن کانتینر Xray بالا باشه).", en: "Wait for the install to finish (use <span class=\"mono\">status</span> to check the Xray container is up)." },
    "tp.noconn.3":    { fa: "توی تب «ساخت کانفیگ» → تنظیمات پیشرفته → یک <b>SNI</b> دیگه امتحان کن.", en: "In the “Build config” tab → Advanced settings → try a different <b>SNI</b>." },
    "tp.noconn.4":    { fa: "اگه سرور فایروال (ufw) داره، پورت‌های ۸۴۴۳ و ۸۴۴۴ باید باز باشن.", en: "If the server has a firewall (ufw), ports 8443 and 8444 must be open." },
    "tp.h.cmds":      { fa: "دستورهای مدیریت (روی سرور)", en: "Management commands (on the server)" },
    "tp.cmds.lead":   { fa: "بعد از نصب، این دستورها رو داری:", en: "After installing, you have these commands:" },
    "tp.cmd.status":  { fa: "وضعیت سرویس و کاربرها", en: "Service & user status" },
    "tp.cmd.configs": { fa: "نمایش لینک‌ها + QR", en: "Show links + QR" },
    "tp.cmd.users":   { fa: "لیست کاربرها و مصرف", en: "List users and usage" },
    "tp.cmd.add":     { fa: "کاربر جدید: ۱۰۰گیگ، ۳۰روز", en: "New user: 100GB, 30 days" },
    "tp.cmd.renew":   { fa: "تمدید ۳۰ روزه", en: "Renew for 30 days" },
    "tp.cmd.remove":  { fa: "حذف کاربر", en: "Remove user" },
    "tp.cmd.update":  { fa: "آپدیت Xray به آخرین نسخه", en: "Update Xray to the latest version" },
    /* ---------- DOMAIN tab (headings + protocol guide) ---------- */
    "dm.intro":       { fa: "کانفیگ‌های دامنه‌دار (VLESS-WS، VMess-WS، gRPC، Trojan، HTTPUpgrade) از نظر امنیت و پایداری در ایران <b>بهترین گزینه</b> هستند، چون شبیه ترافیک HTTPS معمولی‌اند. ولی به یک <b>دامنه</b> نیاز دارند. اگر دامنه نداری، حالت Reality (پیش‌فرض) همچنان عالی است.", en: "Domain-based configs (VLESS-WS, VMess-WS, gRPC, Trojan, HTTPUpgrade) are the <b>best option</b> for security and resilience in Iran because they look like ordinary HTTPS traffic. But they need a <b>domain</b>. If you don't have one, Reality mode (default) is still excellent." },
    "dm.h.which":     { fa: "🎯 چه دامنه‌ای بگیرم؟", en: "🎯 Which domain should I get?" },
    "dm.which.lead":  { fa: "هر دامنه‌ای کار می‌کند، ولی <b>پیشنهادها</b>:", en: "Any domain works, but <b>recommendations</b>:" },
    "dm.which.f": {
      fa: "<li><b>دامنه‌های ارزان (~$۲-۱۰ سالانه):</b> <a href=\"https://www.namecheap.com/\" target=\"_blank\">Namecheap</a> · <a href=\"https://porkbun.com/\" target=\"_blank\">Porkbun</a> · <a href=\"https://www.cloudflare.com/products/registrar/\" target=\"_blank\">Cloudflare Registrar</a> (با قیمت اصلی، بدون سود)</li><li><b>دامنه‌های رایگان:</b> <a href=\"https://www.duckdns.org/\" target=\"_blank\">DuckDNS</a> (ساب‌دامنه رایگان) · <a href=\"https://eu.org/\" target=\"_blank\">EU.org</a> (رایگان، ولی تأیید چند روز طول می‌کشد)</li><li><b>پسوندهای ارزان:</b> <code>.xyz</code>, <code>.shop</code>, <code>.online</code>, <code>.site</code> — معمولاً سال اول ~$۱-۲</li><li><b>بپرهیز از:</b> <code>.tk</code>, <code>.ml</code>, <code>.ga</code> (فریمنوم — بسیاری از کلاینت‌ها بلاک می‌کنند)</li>",
      en: "<li><b>Cheap domains (~$2-10/yr):</b> <a href=\"https://www.namecheap.com/\" target=\"_blank\">Namecheap</a> · <a href=\"https://porkbun.com/\" target=\"_blank\">Porkbun</a> · <a href=\"https://www.cloudflare.com/products/registrar/\" target=\"_blank\">Cloudflare Registrar</a> (at cost, no markup)</li><li><b>Free domains:</b> <a href=\"https://www.duckdns.org/\" target=\"_blank\">DuckDNS</a> (free subdomain) · <a href=\"https://eu.org/\" target=\"_blank\">EU.org</a> (free, but approval takes a few days)</li><li><b>Cheap TLDs:</b> <code>.xyz</code>, <code>.shop</code>, <code>.online</code>, <code>.site</code> — usually ~$1-2 the first year</li><li><b>Avoid:</b> <code>.tk</code>, <code>.ml</code>, <code>.ga</code> (Freenom — many clients block them)</li>"
    },
    "dm.h.arecord":   { fa: "📡 تنظیم رکورد A — مهم‌ترین قدم", en: "📡 Setting the A record — the most important step" },
    "dm.h.cf":        { fa: "☁️ اگر از Cloudflare استفاده می‌کنی", en: "☁️ If you use Cloudflare" },
    "dm.h.proto":     { fa: "🔧 پروتکل‌ها — کدام را انتخاب کنم؟", en: "🔧 Protocols — which should I pick?" },
    "dm.h.order":     { fa: "🚀 ترتیب کار", en: "🚀 Step order" },
    "dm.h.trouble":   { fa: "❗ عیب‌یابی متداول", en: "❗ Common troubleshooting" },
    "dm.rec":         { fa: "پیشنهاد اول", en: "Top pick" },
    "dm.p.vlessws":   { fa: "پایدارترین، کم‌سربار، عبور عالی از DPI. اگر گیج هستی، فقط همین را تیک بزن.", en: "Most stable, low overhead, great DPI evasion. If unsure, just tick this one." },
    "dm.p.vmessws":   { fa: "مشابه VLESS-WS ولی با امضای امنیتی اضافه. سازگار با کلاینت‌های قدیمی‌تر. کمی سربار بیشتر.", en: "Like VLESS-WS but with an extra security signature. Compatible with older clients. Slightly more overhead." },
    "dm.p.grpc":      { fa: "مالتی‌پلکس روی HTTP/2. روی شبکه‌های پرتاخیر بهتر، ولی تنظیم سخت‌تر و گاهی توسط DPI شناسایی می‌شود.", en: "Multiplexed over HTTP/2. Better on high-latency networks, but harder to set up and sometimes detected by DPI." },
    "dm.p.trojan":    { fa: "طراحی‌شده برای شبیه‌بودن کامل به ترافیک HTTPS. خوب در ایران، ولی کمی کندتر از VLESS.", en: "Designed to fully mimic HTTPS traffic. Good in Iran, but a bit slower than VLESS." },
    "dm.p.httpupgrade": { fa: "سبک‌تر از WebSocket. عبور خوب از پراکسی‌های شرکتی. نسبتاً جدید، در همهٔ کلاینت‌ها پشتیبانی نمی‌شود.", en: "Lighter than WebSocket. Passes corporate proxies well. Fairly new, not supported in all clients." },
    "dm.proto.note":  { fa: "می‌توانی همه را تیک بزنی — هیچ ضرری ندارد. هر کاربر برای هر پروتکل یک لینک می‌گیرد و در v2rayNG کدام بهتر کار کرد، همان را نگه می‌دارد.", en: "You can tick all of them — no harm. Each user gets a link per protocol, and in v2rayNG you keep whichever works best." },

    /* ---------- protocol descriptions + extra protocols ---------- */
    "gen.tlsproto.label": { fa: "پروتکل‌ها (هرکدام را می‌خواهی تیک بزن)", en: "Protocols (tick whichever you want)" },
    "proto.vless-ws":          { fa: "پایدارترین، عبور خوب از DPI و CDN", en: "Most stable, good over DPI and CDN" },
    "proto.vmess-ws":          { fa: "سازگاری بالا با کلاینت‌های قدیمی", en: "High compatibility with older clients" },
    "proto.vless-grpc":        { fa: "مالتی‌پلکس، خوب روی شبکهٔ پرتاخیر", en: "Multiplexed, good on high-latency networks" },
    "proto.vmess-grpc":        { fa: "gRPC با VMess", en: "gRPC with VMess" },
    "proto.trojan-ws":         { fa: "شبیه HTTPS معمولی", en: "Looks like ordinary HTTPS" },
    "proto.vless-httpupgrade": { fa: "سبک‌تر از WS", en: "Lighter than WS" },
    "proto.vmess-httpupgrade": { fa: "HTTPUpgrade با VMess", en: "HTTPUpgrade with VMess" },
    "proto.vless-xhttp":       { fa: "جدید — مقاوم‌ترین در برابر DPI، عالی روی CDN", en: "New — most DPI-resistant, great over CDN" },
    "gen.extra.label": { fa: "پروتکل‌های اضافه (ضدِ DPI قوی)", en: "Extra protocols (strong anti-DPI)" },
    "gen.extra.note":  { fa: "با فعال‌کردن، یک سرویسِ مستقلِ sing-box کنارِ Xray نصب می‌شود که هر چهار پروتکلِ Hysteria2، TUIC v5، AnyTLS و ShadowTLS v3 را برای هر کاربر می‌سازد (هرکدام پورتِ جدا، اگر اشغال بود خودکار جابه‌جا می‌شود). مسیرِ Reality/SS/TLS دست‌نخورده می‌ماند و لینک‌ها خودکار به Subscription اضافه می‌شوند. اگر نسخهٔ sing-box پروتکلی را نپذیرفت، فقط همان حذف و بقیه فعال می‌مانند.", en: "Enabling this installs a standalone sing-box service next to Xray that builds all four — Hysteria2, TUIC v5, AnyTLS and ShadowTLS v3 — per user (each on its own port, auto-moved if busy). The Reality/SS/TLS path stays untouched and links are added to your subscription automatically. If a sing-box build rejects one protocol, only that one is dropped and the rest stay live." },
    "gen.extra.hy2":   { fa: "سریع روی شبکهٔ پُرافت/پُرتأخیر، عبورِ عالی از DPI", en: "Fast on lossy/high-latency networks, great DPI evasion" },
    "gen.extra.tuic":  { fa: "QUIC، 0-RTT، کنترلِ ازدحام BBR", en: "QUIC, 0-RTT, BBR congestion control" },

    /* ---------- GEN: IP-filter warning (was Persian-only) ---------- */
    "g.ipwarn.head": { fa: "⚠️ هشدار مهم — فیلتر شدن IP سرور", en: "⚠️ Important — your server IP can get blocked" },
    "g.ipwarn.body": {
      fa: "چون کانفیگ‌های Reality و Shadowsocks <b>مستقیم به IP لخت سرورت</b> می‌روند (بدون دامنه/CDN)، اگر کانفیگ را به <b>بیش از ۲-۳ نفر</b> بدهی و <b>مصرف هفتگی بالا</b> داشته باشد (مثلاً چند صد گیگ)، سامانه فیلترینگ ISP می‌تواند الگوی ترافیک را شناسایی کند و <b>IP سرورت را برای همیشه فیلتر کند.</b><br><br><b>راه‌حل برای پخش عمومی یا کاربران زیاد:</b> از حالت <b>«کانفیگ‌های دامنه‌دار (TLS)»</b> در پایین استفاده کن — ترافیک پشت Cloudflare می‌رود، IP واقعی سرورت دیده نمی‌شود، و اگر یک IP بسته شد، Cloudflare خودش IP دیگر می‌دهد.<br><br><span class=\"ip-warn-rule\">قانون ساده: <b>تا ۲-۳ نفر</b> ⟵ Reality کافی است. <b>بیشتر</b> یا <b>پخش عمومی</b> ⟵ حتماً دامنه + TLS.</span>",
      en: "Because Reality and Shadowsocks configs go <b>straight to your server's bare IP</b> (no domain/CDN), if you hand the config to <b>more than 2-3 people</b> with <b>heavy weekly usage</b> (hundreds of GB), the ISP's filtering system can fingerprint the traffic pattern and <b>block your server IP for good.</b><br><br><b>Fix for public sharing or many users:</b> use the <b>“Domain-based (TLS) configs”</b> below — traffic rides behind Cloudflare, your real server IP stays hidden, and if one IP is blocked Cloudflare just hands out another.<br><br><span class=\"ip-warn-rule\">Simple rule: <b>up to 2-3 people</b> ⟵ Reality is enough. <b>More</b> or <b>public sharing</b> ⟵ definitely domain + TLS.</span>"
    },

    /* ---------- GEN: advanced settings (was Persian-only) ---------- */
    "g.adv.sni.l": { fa: "دامنهٔ استتار (SNI)", en: "Camouflage domain (SNI)" },
    "g.adv.sni.auto": { fa: "خودکار — چند دامنهٔ امن (پیشنهادی)", en: "Auto — several safe domains (recommended)" },
    "g.adv.sni.manual": { fa: "دستی — یک دامنهٔ مشخص", en: "Manual — one specific domain" },
    "g.adv.sni.h": { fa: "حالت خودکار چند دامنهٔ در-دسترس روی چند پورت می‌سازه تا اگه یکی بسته شد، بقیه کار کنن.", en: "Auto mode builds several reachable domains across multiple ports, so if one is blocked the others still work." },
    "g.adv.snicount.l": { fa: "چند دامنه/کانفیگ ساخته بشه؟", en: "How many domains/configs to build?" },
    "g.adv.snicount.1": { fa: "۱ دامنه", en: "1 domain" },
    "g.adv.snicount.2": { fa: "۲ دامنه (پیشنهادی)", en: "2 domains (recommended)" },
    "g.adv.snicount.3": { fa: "۳ دامنه", en: "3 domains" },
    "g.adv.snisel.l": { fa: "دامنهٔ دستی", en: "Manual domain" },
    "g.adv.snisel.h": { fa: "دامنه‌ای انتخاب کن که در ایران فیلتر نباشه و TLS 1.3 داشته باشه.", en: "Pick a domain that isn't blocked in Iran and supports TLS 1.3." },
    "g.adv.sni.customopt": { fa: "دامنهٔ دلخواه…", en: "Custom domain…" },
    "g.adv.snicustom.l": { fa: "دامنهٔ دلخواه", en: "Custom domain" },
    "g.adv.ss.l": { fa: "Shadowsocks هم اضافه کن <span class=\"muted small\">(پروتکل پشتیبان)</span>", en: "Add Shadowsocks too <span class=\"muted small\">(backup protocol)</span>" },
    "g.adv.ssport.l": { fa: "پورت Shadowsocks", en: "Shadowsocks port" },
    "g.adv.ports.head": { fa: "📋 پورت‌های kian-v2ray — راهنمای کامل", en: "📋 kian-v2ray ports — full guide" },
    "g.adv.ports.body": {
      fa: "<p><b>پورت‌های Reality (روی این‌ها کانفیگ V2Ray سرو می‌شود — قابل تنظیم):</b></p><ul><li>پیش‌فرض خودکار (پیشنهاد): <code>۴۴۳</code>، <code>۲۰۸۳</code>، <code>۲۰۸۷</code>، <code>۲۰۹۶</code>، <code>۸۰۸۰</code> — پورت‌های وب معروف که با ترافیک HTTPS عادی قاطی می‌شوند و کم به‌چشم می‌آیند.</li><li>گزینه‌های جایگزین (در صورت تداخل): <code>۹۴۴۳</code>، <code>۵۴۴۳</code>، <code>۸۴۴۳</code>، <code>۲۰۵۲</code>، <code>۲۰۸۶</code>.</li></ul><p><b>پورت‌های ثابت سیستمی (نباید جای دیگری استفاده شوند):</b></p><ul><li><code>۴۰۰۰۰</code> ⟵ WARP socks (فقط localhost)</li><li><code>۲۰۰۰۰-۵۰۰۰۰</code> (تصادفی) ⟵ API داخلی Xray (فقط localhost)</li><li><code>۸۰، ۸۸۸۸، ۲۰۸۶</code> ⟵ سرویس Subscription محلی</li><li><code>۴۴۳، ۸۰</code> ⟵ <b>اگر</b> TLS با دامنه فعال کنی، این پورت‌ها برای Caddy رزرو می‌شوند</li></ul><p class=\"muted small\">💡 <b>اگر سرورت تمیز است</b> (تازه نصب OS) و هیچ سرویس دیگری نداری، نیازی به تغییر چیزی نیست — صفحه خودش بهترین پورت‌ها را انتخاب می‌کند. فقط در این موارد عدد بده:</p><ul class=\"muted small\"><li>روی سرور پنل دیگری (3x-ui، Marzban، X-UI) داری و پورت‌های ۴۴۳ یا ۸۰۸۰ را گرفته → عددی بالاتر مثل ۹۴۴۳ بده</li><li>می‌خواهی پورت خاصی استفاده شود (مثلاً برای CDN سفارشی) → همان را وارد کن</li></ul>",
      en: "<p><b>Reality ports (your V2Ray configs are served here — adjustable):</b></p><ul><li>Auto default (recommended): <code>443</code>, <code>2083</code>, <code>2087</code>, <code>2096</code>, <code>8080</code> — well-known web ports that blend in with normal HTTPS traffic.</li><li>Fallback options (on conflict): <code>9443</code>, <code>5443</code>, <code>8443</code>, <code>2052</code>, <code>2086</code>.</li></ul><p><b>Fixed system ports (don't reuse elsewhere):</b></p><ul><li><code>40000</code> ⟵ WARP socks (localhost only)</li><li><code>20000-50000</code> (random) ⟵ Xray internal API (localhost only)</li><li><code>80, 8888, 2086</code> ⟵ local subscription service</li><li><code>443, 80</code> ⟵ <b>if</b> you enable domain TLS, these are reserved for Caddy</li></ul><p class=\"muted small\">💡 <b>If your server is clean</b> (fresh OS) with no other services, you don't need to change anything — the page picks the best ports. Only set a value when:</p><ul class=\"muted small\"><li>another panel (3x-ui, Marzban, X-UI) already took 443 or 8080 → give a higher number like 9443</li><li>you want a specific port (e.g. for a custom CDN) → enter it</li></ul>"
    },
    "g.adv.baseport.l": { fa: "پورت پایه (اختیاری — خالی بگذار)", en: "Base port (optional — leave empty)" },
    "g.adv.baseport.ph": { fa: "خودکار: ۴۴۳، ۲۰۸۳، ۲۰۸۷، ۲۰۹۶، ۸۰۸۰...", en: "Auto: 443, 2083, 2087, 2096, 8080..." },
    "g.adv.baseport.h": { fa: "🎯 <b>خالی بگذار</b> تا از پورت‌های وب معروف (۴۴۳، ۲۰۸۳، ۸۰۸۰، ...) استفاده شود.<br>⚠️ فقط اگه پنل دیگری روی سرور داری که این پورت‌ها را گرفته، عددی بده (مثلاً <code>9443</code>) تا پورت‌ها از آنجا ترتیبی شروع شوند.", en: "🎯 <b>Leave empty</b> to use well-known web ports (443, 2083, 8080, ...).<br>⚠️ Only set a value if another panel on the server already took these ports (e.g. <code>9443</code>) so ports start sequentially from there." },
    "g.adv.quota.l": { fa: "حجم هر کاربر", en: "Quota per user" },
    "g.adv.quota.50": { fa: "۵۰ گیگ", en: "50 GB" },
    "g.adv.quota.100": { fa: "۱۰۰ گیگ", en: "100 GB" },
    "g.adv.quota.200": { fa: "۲۰۰ گیگ", en: "200 GB" },
    "g.adv.quota.500": { fa: "۵۰۰ گیگ", en: "500 GB" },
    "g.adv.quota.0": { fa: "نامحدود", en: "Unlimited" },
    "g.adv.days.l": { fa: "مدت اعتبار", en: "Validity period" },
    "g.adv.days.30": { fa: "۳۰ روز", en: "30 days" },
    "g.adv.days.60": { fa: "۶۰ روز", en: "60 days" },
    "g.adv.days.90": { fa: "۹۰ روز", en: "90 days" },
    "g.adv.days.0": { fa: "دائمی", en: "Forever" },
    "g.adv.portnote": { fa: "پورت‌ها خودکار انتخاب می‌شن (از ۸۴۴۳ به بعد) — لازم نیست کاری بکنی.", en: "Ports are picked automatically (from 8443 up) — you don't need to do anything." },

    /* ---------- GEN: TLS domain block (was Persian-only) ---------- */
    "g.tls.summary": { fa: "🌐 کانفیگ‌های دامنه‌دار (WS / gRPC / HTTPUpgrade + TLS) — پیشرفته", en: "🌐 Domain-based configs (WS / gRPC / HTTPUpgrade + TLS) — advanced" },
    "g.tls.intro": { fa: "این کانفیگ‌ها به‌جای IP، روی <b>دامنه + گواهی TLS واقعی</b> کار می‌کنند و پشت <b>Caddy</b> روی پورت ۴۴۳ سرو می‌شوند. مزیت: عبور بهتر از DPI، امکان استفاده پشت CDN (مثل Cloudflare)، و شبیه‌بودن کامل به ترافیک HTTPS معمولی.", en: "Instead of an IP, these configs run on a <b>domain + a real TLS certificate</b>, served behind <b>Caddy</b> on port 443. Benefits: better DPI evasion, works behind a CDN (like Cloudflare), and looks exactly like normal HTTPS traffic." },
    "g.tls.req": { fa: "<b>پیش‌نیازها (مهم):</b>", en: "<b>Prerequisites (important):</b>" },
    "g.tls.req1": { fa: "یک <b>دامنه</b> داشته باش (مثلاً از Namecheap، Cloudflare، Freenom).", en: "Have a <b>domain</b> (e.g. from Namecheap, Cloudflare, Freenom)." },
    "g.tls.req2": { fa: "یک رکورد <b>A</b> بساز که دامنه (یا یک ساب‌دامنه مثل <code>vpn.example.com</code>) به <b>IP سرورت</b> اشاره کند.", en: "Create an <b>A</b> record pointing the domain (or a subdomain like <code>vpn.example.com</code>) to <b>your server IP</b>." },
    "g.tls.req3": { fa: "اگر از Cloudflare استفاده می‌کنی، موقع نصب اول ابر را <b>خاکستری (DNS only)</b> کن تا گواهی گرفته شود؛ بعد می‌تونی نارنجی (Proxied) کنی.", en: "If you use Cloudflare, set the cloud to <b>grey (DNS only)</b> during install so the cert is issued; you can switch it to orange (Proxied) afterwards." },
    "g.tls.req4": { fa: "پورت‌های <b>۴۴۳</b> و <b>۸۰</b> سرور باید آزاد باشند (برای گرفتن گواهی Let's Encrypt).", en: "Server ports <b>443</b> and <b>80</b> must be free (to obtain the Let's Encrypt certificate)." },
    "g.tls.toggle": { fa: "کانفیگ‌های دامنه‌دار را فعال کن", en: "Enable domain-based configs" },
    "g.tls.domain.l": { fa: "دامنه (که به IP سرور اشاره می‌کند)", en: "Domain (pointing to the server IP)" },
    "g.tls.domain.ph": { fa: "مثلاً vpn.example.com", en: "e.g. vpn.example.com" },
    "g.tls.domain.h": { fa: "حتماً رکورد A این دامنه باید روی IP همین سرور تنظیم شده باشد، وگرنه گواهی TLS گرفته نمی‌شود.", en: "The domain's A record must point to this exact server IP, otherwise the TLS certificate cannot be issued." },
    "g.tls.proto.h": { fa: "پیشنهاد: اگر مطمئن نیستی، فقط <b>VLESS-WS</b> را بگذار — برای اکثر موارد بهترین است.", en: "Tip: if unsure, leave only <b>VLESS-WS</b> — it's best for most cases." },
    "g.tls.channel.l": { fa: "مسیر خروجی این کانفیگ‌ها", en: "Outbound path for these configs" },
    "g.tls.channel.direct": { fa: "سریع (مستقیم)", en: "Fast (direct)" },
    "g.tls.channel.warp": { fa: "از WARP (دور زدن بلاک خروجی سرور)", en: "Via WARP (bypass server-side egress blocks)" },
    "g.tls.channel.h": { fa: "اگر سرورت سایت‌هایی را بلاک می‌کند (مثل بعضی پروایدرهای ترکیه)، WARP را انتخاب کن.", en: "If your server blocks some sites (like some Turkey providers), choose WARP." },

    /* ---------- DOMAIN tab (deep prose) ---------- */
    "dm.ar.lead": { fa: "بعد از خرید دامنه، در پنل DNS رجیسترار:", en: "After buying a domain, in the registrar's DNS panel:" },
    "dm.ar.1": { fa: "یک رکورد <b>A</b> بساز.", en: "Create an <b>A</b> record." },
    "dm.ar.2": { fa: "<b>Name</b> (نام ساب‌دامنه): مثلاً <code>vpn</code> (یعنی <code>vpn.example.com</code>)، یا <code>@</code> برای دامنهٔ اصلی.", en: "<b>Name</b> (subdomain): e.g. <code>vpn</code> (i.e. <code>vpn.example.com</code>), or <code>@</code> for the root domain." },
    "dm.ar.3": { fa: "<b>Value / IP Address</b>: <b>IP سرورت</b> (دقیقاً همان که در صفحه وارد کردی).", en: "<b>Value / IP Address</b>: <b>your server IP</b> (exactly the one you entered on the page)." },
    "dm.ar.4": { fa: "<b>TTL</b>: پیش‌فرض (Auto یا 300) خوب است.", en: "<b>TTL</b>: the default (Auto or 300) is fine." },
    "dm.ar.note": { fa: "انتشار DNS معمولاً ۱-۱۰ دقیقه طول می‌کشد. می‌توانی با <code>nslookup vpn.example.com</code> یا سایت <a href=\"https://dnschecker.org/\" target=\"_blank\">dnschecker.org</a> بررسی کنی.", en: "DNS propagation usually takes 1–10 minutes. You can check with <code>nslookup vpn.example.com</code> or <a href=\"https://dnschecker.org/\" target=\"_blank\">dnschecker.org</a>." },
    "dm.cf.1": { fa: "<b>⚠️ مهم:</b> موقع نصب اول، آیکن ابر باید <b>خاکستری (DNS only)</b> باشد، نه نارنجی (Proxied). دلیل: Caddy باید روی پورت ۸۰ گواهی Let's Encrypt بگیرد، که اگر Cloudflare proxy فعال باشد، نمی‌گیرد.", en: "<b>⚠️ Important:</b> during the first install the cloud icon must be <b>grey (DNS only)</b>, not orange (Proxied). Reason: Caddy needs to get a Let's Encrypt cert on port 80, which fails if the Cloudflare proxy is on." },
    "dm.cf.2": { fa: "بعد از نصب موفق و اطمینان از کار کردن کانفیگ‌ها، می‌توانی Cloudflare proxy را <b>روشن</b> کنی (ابر نارنجی) که مزیت‌های اضافی دارد:", en: "After a successful install and confirming the configs work, you can turn the Cloudflare proxy <b>on</b> (orange cloud), which has extra benefits:" },
    "dm.cf.l1": { fa: "پنهان شدن IP واقعی سرور (در برابر فیلتر شدن)", en: "Hiding the server's real IP (against blocking)" },
    "dm.cf.l2": { fa: "دسترسی از طریق IP‌های Cloudflare که در ایران اغلب باز هستند", en: "Access via Cloudflare IPs, which are often open in Iran" },
    "dm.cf.l3": { fa: "محدودیت: فقط روی پورت‌های <a href=\"https://developers.cloudflare.com/fundamentals/reference/network-ports/\" target=\"_blank\">۴۴۳، ۲۰۵۳، ۲۰۸۳، ۲۰۸۷، ۲۰۹۶، ۸۴۴۳</a> کار می‌کند. کانفیگ‌های ما روی ۴۴۳ هستند، پس مشکلی نیست.", en: "Limitation: works only on ports <a href=\"https://developers.cloudflare.com/fundamentals/reference/network-ports/\" target=\"_blank\">443, 2053, 2083, 2087, 2096, 8443</a>. Our configs use 443, so it's fine." },
    "dm.o.1": { fa: "دامنه بخر و رکورد A را تنظیم کن.", en: "Buy a domain and set the A record." },
    "dm.o.2": { fa: "صبر کن DNS منتشر شود (~۱-۱۰ دقیقه).", en: "Wait for DNS to propagate (~1–10 min)." },
    "dm.o.3": { fa: "برگرد به تب «ساخت کانفیگ»، گزینه «🌐 کانفیگ‌های دامنه‌دار» را باز کن و فعال کن.", en: "Back in the “Build config” tab, open and enable “🌐 Domain-based configs”." },
    "dm.o.4": { fa: "دامنه و پروتکل‌ها را وارد کن.", en: "Enter the domain and protocols." },
    "dm.o.5": { fa: "دستور نصب را روی سرورت اجرا کن.", en: "Run the install command on your server." },
    "dm.o.6": { fa: "نصب‌کنندهٔ Caddy نصب می‌کند و گواهی Let's Encrypt را خودکار می‌گیرد (~۳۰ ثانیه - ۲ دقیقه).", en: "The installer sets up Caddy and gets a Let's Encrypt cert automatically (~30s–2min)." },
    "dm.o.7": { fa: "تست کن: <code>curl -I https://vpn.example.com</code> باید HTTP 200 برگرداند.", en: "Test: <code>curl -I https://vpn.example.com</code> should return HTTP 200." },
    "dm.t1.s": { fa: "Caddy گواهی نگرفت / اتصال نمی‌گیرد", en: "Caddy didn't get a cert / no connection" },
    "dm.t1.1": { fa: "مطمئن شو رکورد A به IP درست اشاره می‌کند: <code>nslookup vpn.example.com</code>", en: "Make sure the A record points to the right IP: <code>nslookup vpn.example.com</code>" },
    "dm.t1.2": { fa: "پورت‌های ۸۰ و ۴۴۳ سرور آزاد باشند: <code>ss -tlnp | grep -E ':80|:443'</code>", en: "Ports 80 and 443 must be free: <code>ss -tlnp | grep -E ':80|:443'</code>" },
    "dm.t1.3": { fa: "اگر Cloudflare proxy فعال است، موقتاً خاموش کن.", en: "If the Cloudflare proxy is on, turn it off temporarily." },
    "dm.t1.4": { fa: "لاگ Caddy: <code>journalctl -u caddy -n 50</code>", en: "Caddy log: <code>journalctl -u caddy -n 50</code>" },
    "dm.t2.s": { fa: "کانفیگ TLS وصل می‌شود ولی نت نمی‌آید", en: "TLS config connects but no internet" },
    "dm.t2.1": { fa: "چک کن کانتینر Xray بالا است: <code>docker ps | grep kian-xray</code>", en: "Check the Xray container is up: <code>docker ps | grep kian-xray</code>" },
    "dm.t2.2": { fa: "کانفیگ‌های Reality کار می‌کنند؟ اگر آن‌ها هم نه، مشکل از خروجی سرور است (WARP/Direct).", en: "Do the Reality configs work? If they don't either, the issue is the server's outbound (WARP/Direct)." },
    "dm.t2.3": { fa: "پشت Cloudflare proxy هستی؟ گاهی نیاز است <code>fp=chrome</code> را به <code>fp=ios</code> یا <code>fp=firefox</code> عوض کنی.", en: "Behind the Cloudflare proxy? Sometimes you need to change <code>fp=chrome</code> to <code>fp=ios</code> or <code>fp=firefox</code>." },
    "dm.t3.s": { fa: "دامنه فیلتر شد", en: "The domain got blocked" },
    "dm.t3.p": { fa: "اگر دامنه‌ات از ایران بسته شد، یا Cloudflare proxy را روشن کن (ابر نارنجی) یا یک ساب‌دامنهٔ جدید بساز با همان رکورد A. کانفیگ‌ها همچنان روی همان IP کار می‌کنند، فقط دامنهٔ مرجع عوض می‌شود.", en: "If your domain is blocked from Iran, either turn on the Cloudflare proxy (orange cloud) or create a new subdomain with the same A record. The configs keep working on the same IP; only the reference domain changes." },
    "dm.t4.s": { fa: "سایت‌هایی مثل PornHub / استریم باز نمی‌شوند (با اینکه کانفیگ وصل است)", en: "Sites like PornHub / streaming won't open (even though the config is connected)" },
    "dm.t4.p1": { fa: "<b>این باگِ کانفیگ نیست — ماهیتِ IP خروجی است.</b> یک نکتهٔ مهم که اغلب اشتباه فهمیده می‌شود:", en: "<b>This isn't a config bug — it's the nature of the exit IP.</b> An important point often misunderstood:" },
    "dm.t4.l1": { fa: "<b>Cloudflare (ابر نارنجی) فقط مسیرِ ورودی را پنهان می‌کند</b>، نه خروجی. مسیر واقعی این است: کلاینت → Cloudflare → <b>سرورِ تو</b> → سایت مقصد. درخواست به PornHub از <b>IP سرورِ خودت</b> بیرون می‌رود، نه از IP کلودفلر. پس CDN فقط کمک می‌کند که «IP سرورت از داخل ایران بسته نباشد»، اما «اینکه سایت مقصد IP سرورت را بپذیرد» را عوض نمی‌کند.", en: "<b>Cloudflare (orange cloud) only hides the inbound path</b>, not the outbound. The real path is: client → Cloudflare → <b>your server</b> → destination site. The request to PornHub leaves from <b>your own server IP</b>, not Cloudflare's. So the CDN only helps so “your server IP isn't blocked from inside Iran” — it doesn't change “whether the destination site accepts your server IP”." },
    "dm.t4.l2": { fa: "<b>سایت‌هایی مثل PornHub / Xvideos / بعضی استریم‌ها</b> رنج IP دیتاسنترها را بلاک می‌کنند و چند کشور را هم به‌خاطر قوانین تأیید سن جئوبلاک می‌کنند (آلمان، فرانسه، چند ایالت آمریکا). اگر IP/کشورِ سرورت در لیست بلاکِ آن سایت باشد، با <b>هیچ</b> کانفیگی (Reality، دامنه، CDN) باز نمی‌شود، چون همه از همان IP سرور خارج می‌شوند.", en: "<b>Sites like PornHub / Xvideos / some streams</b> block datacenter IP ranges and geo-block several countries over age-verification laws (Germany, France, some US states). If your server's IP/country is on that site's block list, it won't open with <b>any</b> config (Reality, domain, CDN), because they all exit from the same server IP." },
    "dm.t4.p2": { fa: "<b>تستِ قطعی (روی خودِ سرور):</b>", en: "<b>Definitive test (on the server itself):</b>" },
    "dm.t4.p3": { fa: "اگر همین دستور روی سرور <code>403</code> / ریدایرکت به صفحهٔ «در کشور شما در دسترس نیست» داد، یعنی مشکل از IP سرور است و ربطی به کانفیگ ندارد.", en: "If that command on the server returns <code>403</code> / a redirect to a “not available in your country” page, the problem is the server IP and has nothing to do with the config." },
    "dm.t4.p4": { fa: "<b>راه‌حل‌ها:</b>", en: "<b>Solutions:</b>" },
    "dm.t4.sl1": { fa: "<b>کانال آن کانفیگ را روی WARP بگذار</b> (نه «سریع/مستقیم»). خروجی به IP کلودفلر WARP عوض می‌شود؛ گاهی جواب می‌دهد (ولی PornHub خیلی از IPهای WARP را هم بلاک می‌کند).", en: "<b>Set that config's channel to WARP</b> (not “Fast/Direct”). The exit changes to a Cloudflare WARP IP; sometimes it works (but PornHub also blocks many WARP IPs)." },
    "dm.t4.sl2": { fa: "<b>سروری در کشور/دیتاسنترِ بازتر</b> بگیر (IPهای residential یا کشورهایی که این سایت بلاک نکرده). مؤثرترین راه همین است.", en: "<b>Get a server in a more open country/datacenter</b> (residential IPs or countries the site doesn't block). This is the most effective route." },
    "dm.t4.sl3": { fa: "اگر فقط چند سایت خاص مدنظر است، می‌توان قانون routing گذاشت که همان دامنه‌ها از WARP بروند و بقیه مستقیم (سریع‌تر بماند).", en: "If only a few specific sites matter, you can add a routing rule so those domains go through WARP and the rest stay direct (faster)." },
    "dm.t4.sum": { fa: "خلاصه: کانفیگِ دامنه‌دار «فیلترشکنیِ سمتِ ورود» را حل می‌کند، نه «پذیرش IP سرورت توسط سایت مقصد» را.", en: "In short: a domain config solves “inbound censorship circumvention”, not “the destination site accepting your server IP”." },

    /* ---------- shared step-guide ---------- */
    "gd.enterlink":   { fa: "لینک کانفیگ رو وارد کن", en: "Enter the config link" },

    /* ---------- SERVER tab (steps) ---------- */
    "sv.s1t": { fa: "یک برنامهٔ SSH باز کن", en: "Open an SSH app" },
    "sv.s1d": { fa: "روی گوشی: اپ <b>Termius</b> رو نصب کن. روی ویندوز: <b>PowerShell</b> یا <b>PuTTY</b>.", en: "On phone: install <b>Termius</b>. On Windows: <b>PowerShell</b> or <b>PuTTY</b>." },
    "sv.s2t": { fa: "به سرورت وصل شو", en: "Connect to your server" },
    "sv.s2d": { fa: "با آی‌پی و رمز سرور وصل شو. توی ترمینال این رو بزن (آی‌پی خودت رو بذار):", en: "Connect with the server IP and password. Type this in the terminal (use your own IP):" },
    "sv.s2n": { fa: "رمز سرور رو هنگام خرید بهت می‌دن. موقع تایپ رمز چیزی نمایش داده نمی‌شه — طبیعیه.", en: "The server password is given to you at purchase. Nothing shows while typing it — that's normal." },
    "sv.s3t": { fa: "دستور نصب رو از تب «ساخت کانفیگ» بگیر", en: "Get the install command from the “Build config” tab" },
    "sv.s3d": { fa: "برگرد به تب اول، آی‌پی سرورت رو وارد کن، دکمه رو بزن و <b>«دستور نصب»</b> رو کپی کن.", en: "Go back to the first tab, enter your server IP, press the button, and copy the <b>install command</b>." },
    "sv.s4t": { fa: "دستور رو توی ترمینال سرور Paste کن", en: "Paste the command into the server terminal" },
    "sv.s4d": { fa: "نصب خودش انجام می‌شه. <b>اگه وسط کار اینترنتت قطع شد هم اشکالی نداره</b> — نصب پشت‌صحنه ادامه می‌ده.", en: "It installs itself. <b>If your internet drops mid-way, no problem</b> — the install keeps running in the background." },
    "sv.s4n": { fa: "📱 <b>روی موبایل:</b> اگه Ctrl+V کار نکرد، روی ترمینال نگه‌دار (long-press) و از منو <b>Paste</b> رو بزن.", en: "📱 <b>On mobile:</b> if Ctrl+V doesn't work, long-press the terminal and choose <b>Paste</b> from the menu." },
    "sv.s5t": { fa: "۲ تا ۵ دقیقه صبر کن، بعد وضعیت رو چک کن", en: "Wait 2–5 minutes, then check the status" },
    "sv.s5d": { fa: "اگه نوشت Xray در حال اجراست ✅ تمومه. لینک‌های کانفیگ همون‌هایی هستن که توی تب اول گرفتی.", en: "If it says Xray is running ✅ you're done. The config links are the ones you got in the first tab." },
    "sv.min": { fa: "حداقل سرور: ۱ هسته CPU، ۵۱۲ مگ رم، اوبونتو ۲۲ یا ۲۴. لوکیشن خارج از ایران.", en: "Minimum server: 1 CPU core, 512 MB RAM, Ubuntu 22 or 24. Location outside Iran." },
    "sv.termius": { fa: "دانلود Termius (اندروید) ↗", en: "Download Termius (Android) ↗" },
    "sv.buy.netlen": { fa: "🌐 Netlen (ترکیه)", en: "🌐 Netlen (Turkey)" },
    "sv.buy.netlen.f": { fa: "<li>✓ بدون احراز هویت</li><li>✓ پرداخت کریپتو</li><li>✗ انگلیسی</li>", en: "<li>✓ No KYC</li><li>✓ Crypto payment</li><li>✗ English UI</li>" },
    "sv.buy.any": { fa: "🌍 هر VPS خارج از ایران", en: "🌍 Any VPS outside Iran" },
    "sv.buy.any.f": { fa: "<li>✓ ترجیحاً پرداخت کریپتو / بدون KYC</li><li>✓ لوکیشن نزدیک (ترکیه/آلمان/امارات)</li><li>✓ آی‌پی تمیز و در-دسترس از ایران</li>", en: "<li>✓ Prefer crypto payment / no KYC</li><li>✓ Nearby location (Turkey/Germany/UAE)</li><li>✓ Clean IP reachable from Iran</li>" },
    "sv.buy.any.n": { fa: "هر ارائه‌دهنده‌ای که این شرایط رو داشته باشه مناسبه.", en: "Any provider that meets these criteria works." },

    /* ---------- ANDROID tab (steps) ---------- */
    "an.s1t": { fa: "اپ v2rayNG رو نصب کن", en: "Install the v2rayNG app" },
    "an.s1d": { fa: "رایگان و متن‌باز — از Reality پشتیبانی می‌کنه.", en: "Free and open-source — supports Reality." },
    "an.dl": { fa: "دانلود v2rayNG از گیت‌هاب ↗", en: "Download v2rayNG from GitHub ↗" },
    "an.alt": { fa: "جایگزین: NekoBox for Android.", en: "Alternative: NekoBox for Android." },
    "an.two": { fa: "دو راه داری:", en: "You have two ways:" },
    "an.copy": { fa: "• <b>کپی-پیست:</b> توی تب «ساخت کانفیگ» روی «کپی لینک» بزن، بعد توی v2rayNG: دکمهٔ <b>+</b> بالا ← <b>«Import config from Clipboard»</b>.", en: "• <b>Copy-paste:</b> in the “Build config” tab tap “Copy link”, then in v2rayNG: the <b>+</b> button ← <b>“Import config from Clipboard”</b>." },
    "an.qr": { fa: "• <b>QR:</b> توی v2rayNG: دکمهٔ <b>+</b> ← <b>«Scan QR code»</b> ← QR روی صفحه رو اسکن کن.", en: "• <b>QR:</b> in v2rayNG: the <b>+</b> button ← <b>“Scan QR code”</b> ← scan the QR on screen." },
    "an.s3t": { fa: "وصل شو", en: "Connect" },
    "an.s3d": { fa: "روی کانفیگ بزن تا انتخاب بشه، بعد دکمهٔ گرد پایین (▶) رو بزن. اولین بار اجازهٔ VPN می‌خواد — تأیید کن.", en: "Tap the config to select it, then press the round button at the bottom (▶). The first time it asks for VPN permission — approve it." },
    "an.s4t": { fa: "اگه «هر دو» رو ساخته بودی", en: "If you built “Both”" },
    "an.s4d": { fa: "همهٔ کانفیگ‌های تو از <b>WARP</b> عبور می‌کنند (تقریباً همه‌چیز باز). فقط لینکِ Subscription را در v2rayNG/Kv2m وارد کن و وصل شو — انتخابِ حالت لازم نیست.", en: "All your configs egress through <b>WARP</b> (almost everything open). Just import the subscription link into v2rayNG/Kv2m and connect — no mode to choose." },
    "an.share": { fa: "📤 می‌خوای کانفیگ رو به دوستت بدی؟ همون لینک یا QR رو بفرست — همه‌چیز خودکار وارد می‌شه.", en: "📤 Want to share the config with a friend? Just send the same link or QR — everything imports automatically." },

    /* ---------- PC tab (steps) ---------- */
    "pc.s1t": { fa: "اپ v2rayN رو دانلود کن", en: "Download the v2rayN app" },
    "pc.s1d": { fa: "برای ویندوز — از Reality پشتیبانی می‌کنه.", en: "For Windows — supports Reality." },
    "pc.dl": { fa: "دانلود v2rayN ↗", en: "Download v2rayN ↗" },
    "pc.alt": { fa: "جایگزین چندسکویی (ویندوز/مک/لینوکس): NekoRay.", en: "Cross-platform alternative (Windows/macOS/Linux): NekoRay." },
    "pc.s2d": { fa: "توی تب «ساخت کانفیگ» روی «کپی لینک» بزن. بعد توی v2rayN از منوی بالا: <b>Servers ← Import bulk URL from clipboard</b> (یا Ctrl+V داخل لیست سرورها).", en: "In the “Build config” tab tap “Copy link”. Then in v2rayN from the top menu: <b>Servers ← Import bulk URL from clipboard</b> (or Ctrl+V inside the server list)." },
    "pc.s3t": { fa: "روشن کن", en: "Turn it on" },
    "pc.s3d": { fa: "روی کانفیگ دابل‌کلیک کن تا فعال بشه. بعد پایین‌راست ویندوز روی آیکن v2rayN راست‌کلیک ← <b>System Proxy ← Set system proxy</b>.", en: "Double-click the config to activate it. Then right-click the v2rayN icon in the Windows tray ← <b>System Proxy ← Set system proxy</b>." },
    "pc.ios": { fa: "🍎 <b>آیفون/iOS:</b> از اپ‌های <b>Streisand</b> یا <b>V2Box</b> (رایگان) یا <b>Shadowrocket</b> (پولی) استفاده کن — لینک یا QR رو همون‌طوری Import کن.", en: "🍎 <b>iPhone/iOS:</b> use <b>Streisand</b> or <b>V2Box</b> (free) or <b>Shadowrocket</b> (paid) — import the link or QR the same way." },

    "tp.h.quota":     { fa: "حجم و انقضا", en: "Quota & expiry" },
    "tp.quota.1":     { fa: "سیستم هر ۱۰ دقیقه مصرف هر کاربر رو چک می‌کنه و اگه حجمش تموم شد یا منقضی شد، خودکار غیرفعالش می‌کنه.", en: "Every 10 minutes the system checks each user's usage and auto-disables them if their quota is used up or they've expired." },
    "tp.quota.2":     { fa: "برای فعال‌کردن دوباره: <span class=\"mono\">kian-v2ray reset نام</span> یا <span class=\"mono\">renew نام</span>.", en: "To re-enable: <span class=\"mono\">kian-v2ray reset name</span> or <span class=\"mono\">renew name</span>." },

    /* ---------- Roadmap / Vision section ---------- */
    "rm.eyebrow":   { fa: "نقشه‌ی راه", en: "Roadmap" },
    "rm.title":     { fa: "از یک نصب‌کننده، به یک پلتفرمِ کاملِ VPN", en: "From an installer to a full VPN platform" },
    "rm.sub":       { fa: "امروز ساده و رایگان نصب می‌کنی؛ و مسیر به یک اکوسیستمِ چندسرور با پنل و اپ رسیده — بیشترِ این‌ها حالا ساخته شده‌اند:", en: "Today it installs free and simple; and the path has reached a multi-server ecosystem with a panel and apps — most of these are now built:" },
    "rm.now":       { fa: "موجود", en: "Available" },
    "rm.soon":      { fa: "به‌زودی", en: "Coming soon" },
    "rm.ready":     { fa: "آماده", en: "Ready" },
    "rm.privacy.t": { fa: "حریمِ خصوصیِ واقعی", en: "Real privacy" },
    "rm.privacy.d": { fa: "کلیدهای خصوصی در مرورگرِ خودت ساخته می‌شوند و هرگز به سرور نمی‌رسند — مزیتی که قابلِ کپی نیست.", en: "Private keys are generated in your own browser and never reach a server — an advantage that can't be copied." },
    "rm.multi.t":   { fa: "مدیریتِ چندسرور", en: "Multi-server management" },
    "rm.multi.d":   { fa: "یک پنل، چندین VPS: سلامت، Failover، توزیعِ بار و مسیریابیِ جغرافیایی — به‌علاوه‌ی مهاجرت از Marzban/3X-UI.", en: "One panel, many VPS: health, failover, load balancing and geo-routing — plus migration from Marzban/3X-UI." },
    "rm.panel.t":   { fa: "پنلِ وبِ کامل", en: "Full web panel" },
    "rm.panel.d":   { fa: "FastAPI + JWT، آمارِ زنده، محدودیتِ IP/سرعت/HWID، غیرفعال‌سازیِ خودکار و اکشن‌های گروهی برای هر کاربر.", en: "FastAPI + JWT, live stats, IP/speed/HWID limits, auto-disable and bulk actions per user." },
    "rm.app.t":     { fa: "اپِ موبایلِ Flutter", en: "Flutter mobile app" },
    "rm.app.d":     { fa: "کلاینتِ چندسکویی برای اندروید و iOS — با انتشار در کافه‌بازار، مایکت، F-Droid و سپس گوگل‌پلی.", en: "Cross-platform client for Android and iOS — published on Cafe Bazaar, Myket, F-Droid and then Google Play." },
    "rm.proto.t":   { fa: "پروتکل‌های ضدسانسورِ جدید", en: "New anti-censorship protocols" },
    "rm.proto.d":   { fa: "Hysteria2، TUIC v5، WireGuard، Fragment/uTLS و خروجیِ Sing-box/Clash برای پایداریِ بیشتر در شرایطِ سخت.", en: "Hysteria2, TUIC v5, WireGuard, Fragment/uTLS and Sing-box/Clash export for more resilience under harsh conditions." },
    "rm.ops.t":     { fa: "پایش و اتوماسیون", en: "Monitoring & automation" },
    "rm.ops.d":     { fa: "بکاپِ خودکار (Telegram/S3/R2)، Audit Log، و داشبوردِ Prometheus + Grafana برای دیدِ کامل به سلامتِ سرویس.", en: "Automated backup (Telegram/S3/R2), an audit log, and a Prometheus + Grafana dashboard for full service-health visibility." },
    "rm.foot":      {
      fa: "می‌خواهی در ساختش سهیم باشی یا پیشنهاد بدهی؟ کدِ کامل و نقشه‌ی راه در <a href=\"https://github.com/kian-irani/kian_v2ray\" target=\"_blank\" rel=\"noopener\">گیت‌هاب</a> باز است.",
      en: "Want to help build it or suggest something? The full code and roadmap are open on <a href=\"https://github.com/kian-irani/kian_v2ray\" target=\"_blank\" rel=\"noopener\">GitHub</a>."
    },

    "foot.channel": { fa: "کانال", en: "Channel" },
    "foot.support": { fa: "پشتیبانی", en: "Support" },
    "foot.privacy": { fa: "حریم خصوصی", en: "Privacy" },
    "foot.terms":   { fa: "شرایط استفاده", en: "Terms" },
    "foot.tag":     { fa: "متن‌باز · بدون لاگ · کلید سمت کاربر", en: "Open-source · No logs · Client-side keys" }
  };

  var STORE_KEY = "kv2ray_lang";

  function apply(lang) {
    var html = document.documentElement;
    html.setAttribute("lang", lang);
    html.setAttribute("dir", lang === "fa" ? "rtl" : "ltr");

    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var e = DICT[el.getAttribute("data-i18n")];
      if (e && typeof e[lang] === "string") el.textContent = e[lang];
    });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      var e = DICT[el.getAttribute("data-i18n-html")];
      if (e && typeof e[lang] === "string") el.innerHTML = e[lang];
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      var e = DICT[el.getAttribute("data-i18n-ph")];
      if (e && typeof e[lang] === "string") el.setAttribute("placeholder", e[lang]);
    });
    document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      var e = DICT[el.getAttribute("data-i18n-title")];
      if (e && typeof e[lang] === "string") el.setAttribute("title", e[lang]);
    });

    var btn = document.getElementById("lang-toggle");
    if (btn) {
      // The button shows the language you can switch TO.
      btn.textContent = lang === "fa" ? "EN" : "FA";
      btn.setAttribute("aria-label", lang === "fa" ? "Switch to English" : "تغییر به فارسی");
    }
  }

  function init() {
    var lang;
    try { lang = localStorage.getItem(STORE_KEY); } catch (_) { lang = null; }
    if (lang !== "fa" && lang !== "en") lang = "en";  // English primary by default
    apply(lang);

    var btn = document.getElementById("lang-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var next = document.documentElement.getAttribute("lang") === "fa" ? "en" : "fa";
        apply(next);
        try { localStorage.setItem(STORE_KEY, next); } catch (_) { /* private mode */ }
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
