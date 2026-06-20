/* KIAN V2Ray — bilingual (FA ↔ EN) layer for the landing page.
 * Loaded after app.js and intentionally independent of it: it only swaps the
 * textContent / innerHTML of [data-i18n] / [data-i18n-html] elements and flips
 * <html lang|dir>, so it can never break the interactive config generator.
 * Persian is the in-HTML default; English comes from this dictionary. */
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
