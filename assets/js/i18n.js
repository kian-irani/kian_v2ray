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
    "m.act.update": { fa: "⬆️ آپدیت به آخرین نسخه (حفظ کاربران)", en: "⬆️ Update to latest (keeps users)" },
    "m.act.uninst": { fa: "❌ حذف کامل نصب از سرور", en: "❌ Fully uninstall from the server" },
    "m.name.l":     { fa: "نام کاربر (انگلیسی — مثل ali یا user-2)", en: "User name (English — e.g. ali or user-2)" },
    "m.name.h":     { fa: "همان نامی که موقع ساخت گذاشتی، یا یک نام جدید برای کاربر تازه.", en: "The name you set when creating it, or a new name for a new user." },
    "m.gb.l":       { fa: "حجم (گیگ — ۰ یعنی نامحدود)", en: "Quota (GB — 0 means unlimited)" },
    "m.days.l":     { fa: "مدت (روز — ۰ یعنی دائمی)", en: "Duration (days — 0 means permanent)" },
    "m.run.l":      { fa: "👇 این دستور را در ترمینال سرور بزن:", en: "👇 Run this command in the server terminal:" },

    /* ---------- ABOUT headings ---------- */
    "ab.roadmap":   { fa: "🗺️ نقشهٔ راه", en: "🗺️ Roadmap" },
    "ab.kv2m":      { fa: "🛠️ نرم‌افزار Kv2m (جدید)", en: "🛠️ Kv2m app (new)" },
    "ab.channels":  { fa: "👤 کانال‌ها و ارتباط", en: "👤 Channels & contact" },
    "ab.donate":    { fa: "💝 حمایت (اختیاری)", en: "💝 Support (optional)" },
    "ab.builtwith": { fa: "🙏 ساخته‌شده با استفاده از", en: "🙏 Built with" },

    /* ---------- TIPS tab (deep prose) ---------- */
    "tp.h.diff":      { fa: "فرق «سریع» و «WARP» چیه؟", en: "What's the difference between “Fast” and “WARP”?" },
    "tp.diff.1":      { fa: "<b>سریع (Direct):</b> ترافیک مستقیم از سرورت می‌ره بیرون. سریع‌ترینه، ولی بعضی سایت‌ها رو ممکنه پروایدرِ سرور بسته باشه.", en: "<b>Fast (Direct):</b> traffic leaves directly from your server. Fastest, but the server's provider may have blocked some sites." },
    "tp.diff.2":      { fa: "<b>WARP:</b> ترافیک از WARP کلودفلر رد می‌شه و تقریباً همه‌چیز باز می‌شه، فقط کمی کندتره.", en: "<b>WARP:</b> traffic goes through Cloudflare WARP and almost everything opens, just a bit slower." },
    "tp.diff.3":      { fa: "پیشنهاد: حالت <b>«هر دو»</b> رو بساز و هرکدوم بهتر جواب داد استفاده کن.", en: "Tip: build the <b>“Both”</b> mode and use whichever works better." },
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
    "tp.h.quota":     { fa: "حجم و انقضا", en: "Quota & expiry" },
    "tp.quota.1":     { fa: "سیستم هر ۱۰ دقیقه مصرف هر کاربر رو چک می‌کنه و اگه حجمش تموم شد یا منقضی شد، خودکار غیرفعالش می‌کنه.", en: "Every 10 minutes the system checks each user's usage and auto-disables them if their quota is used up or they've expired." },
    "tp.quota.2":     { fa: "برای فعال‌کردن دوباره: <span class=\"mono\">kian-v2ray reset نام</span> یا <span class=\"mono\">renew نام</span>.", en: "To re-enable: <span class=\"mono\">kian-v2ray reset name</span> or <span class=\"mono\">renew name</span>." },

    /* ---------- Roadmap / Vision section ---------- */
    "rm.eyebrow":   { fa: "نقشه‌ی راه", en: "Roadmap" },
    "rm.title":     { fa: "از یک نصب‌کننده، به یک پلتفرمِ کاملِ VPN", en: "From an installer to a full VPN platform" },
    "rm.sub":       { fa: "امروز ساده و رایگان نصب می‌کنی؛ مسیر، یک اکوسیستمِ چندسرور با پنل و اپ موبایل است. این‌ها در دست ساخت‌اند:", en: "Today it installs free and simple; the path is a multi-server ecosystem with a panel and a mobile app. These are in progress:" },
    "rm.now":       { fa: "موجود", en: "Available" },
    "rm.soon":      { fa: "به‌زودی", en: "Coming soon" },
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
    if (lang !== "fa" && lang !== "en") lang = "fa";
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
