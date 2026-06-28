/* KIAN V2Ray panel — dashboard logic (vanilla, dependency-free).
 * Talks to panel.main (FastAPI). Tokens in sessionStorage (fallback: memory).
 * FIX v2: CSP-safe, API auto-detect, TOTP field, error resilience. */
(function () {
  "use strict";

  /* ── API base URL ──────────────────────────────────────────────────────── *
   * اولویت: 1) window.KIAN_API (اگه توسط سرور inject شده)
   *          2) /api/config endpoint (همان origin)
   *          3) same-origin (empty string)
   * ---------------------------------------------------------------------- */
  var API = (window.KIAN_API || "").replace(/\/$/, "");
  var _apiReady = false;

  function _initAPI() {
    if (API || _apiReady) return Promise.resolve();
    return fetch("/api/config")
      .then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (cfg) {
        if (cfg && cfg.api_base) API = cfg.api_base.replace(/\/$/, "");
        _apiReady = true;
      })
      .catch(function () { _apiReady = true; });
  }

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var state = { access: null, refresh: null, users: [], lang: "en", view: "users", mode: "simple" };

  /* ── i18n ──────────────────────────────────────────────────────────────── */
  var T = {
    "login.title": ["ورود به پنل KIAN", "Sign in to KIAN Panel"],
    "login.user": ["نام کاربری", "Username"], "login.pass": ["رمز عبور", "Password"],
    "login.totp": ["کد ۲FA", "2FA Code"],
    "login.btn": ["ورود", "Sign in"], "logout": ["خروج", "Logout"],
    "copy.sub": ["کپی لینک ساب‌سکرایب", "Copy sub link"],
    "copy.cfg": ["کپی کانفیگ", "Copy config links"],
    "copy.ok": ["کپی شد ✓", "Copied ✓"],
    "cfg.qr": ["نمایش QR", "Show QR"],
    "cfg.modal.title": ["کانفیگ‌های کاربر", "User configs"],
    "cfg.loading": ["در حال بارگذاری…", "Loading…"],
    "cfg.none": ["کانفیگی یافت نشد", "No configs found"],
    "copyall.btn": ["کپی همه کانفیگ‌ها", "Copy all configs"],
    "copyall.ok": ["کانفیگ کپی شد ✓", "configs copied ✓"],
    "detail.open": ["نمایش جزئیات، کانفیگ و لینک", "Show detail, configs & link"],
    "sys.load": ["بار", "Load"], "sys.mem": ["رم", "RAM"],
    "stat.total": ["کل کاربران", "Total users"], "stat.active": ["فعال", "Active"],
    "stat.traffic": ["مصرف کل", "Total traffic"],
    "tab.users": ["کاربران", "Users"], "tab.audit": ["گزارش ممیزی", "Audit log"],
    "tab.chart": ["نمودار مصرف", "Usage chart"], "tab.nodes": ["سرورها", "Nodes"],
    "tab.settings": ["تنظیمات", "Settings"], "tab.xray": ["کانفیگ Xray", "Xray config"],
    "mode.simple": ["ساده", "Simple"], "mode.advanced": ["پیشرفته", "Advanced"],
    "xray.title": ["کانفیگ زندهٔ Xray", "Live Xray config"],
    "xray.reload": ["بارگذاری مجدد", "Reload"], "xray.format": ["مرتب‌سازی JSON", "Format JSON"],
    "xray.apply": ["اعمال و ری‌استارت", "Apply & restart"],
    "xray.note": ["قبل از اعمال یک بکاپ گرفته می‌شود؛ اگر Xray با کانفیگِ جدید بالا نیاید، خودکار به نسخهٔ قبل برمی‌گردد.",
      "A backup is taken before applying; if Xray fails to start with the new config it auto-rolls back."],
    "xray.badjson": ["JSON نامعتبر", "Invalid JSON"],
    "xray.needio": ["کانفیگ باید inbounds و outbounds داشته باشد.", "Config must have inbounds and outbounds."],
    "xray.confirm": ["این کانفیگ اعمال و Xray ری‌استارت شود؟", "Apply this config and restart Xray?"],
    "xray.applied": ["اعمال شد — Xray ری‌استارت شد", "Applied — Xray restarted"],
    "xray.rejected": ["رد شد (کانفیگِ قبلی حفظ شد)", "Rejected (previous config kept)"],
    "xray.loadfail": ["بارگذاری کانفیگ ناموفق", "Failed to load config"],
    "set.2fa": ["احراز هویت دومرحله‌ای (2FA)", "Two-factor auth (2FA)"],
    "set.2fa.d": ["با اپ Google Authenticator / Aegis یک لایه امنیتی اضافه کن.", "Add a security layer with Google Authenticator / Aegis."],
    "set.2fa.code": ["کد ۶ رقمی اپ:", "6-digit app code:"],
    "set.pw": ["تغییر رمز عبور", "Change password"],
    "set.rotate": ["چرخش کلید JWT", "Rotate JWT key"],
    "set.2fa.on": ["✅ فعال است", "✅ Enabled"], "set.2fa.off": ["غیرفعال", "Disabled"],
    "set.2fa.setup": ["راه‌اندازی 2FA", "Set up 2FA"], "set.2fa.enable": ["فعال‌سازی", "Enable"],
    "set.2fa.disable": ["غیرفعال‌سازی", "Disable"],
    "set.scan": ["این secret را در اپ اضافه کن:", "Add this secret in your app:"],
    "nd.name": ["نام", "name"], "nd.addr": ["آدرس", "address"], "nd.geo": ["کشور", "geo"],
    "nd.token": ["token", "token"], "nd.add": ["افزودن سرور", "Add node"],
    "nd.load": ["بار", "Load"], "nd.alive": ["زنده", "Alive"], "nd.down": ["خاموش", "Down"],
    "nd.route": ["مسیریابی", "Routing"],
    "search.ph": ["جستجوی نام…", "Search name…"],
    "bulk.none": ["اقدام گروهی…", "Bulk action…"], "bulk.enable": ["فعال‌سازی", "Enable"],
    "bulk.disable": ["غیرفعال", "Disable"], "bulk.delete": ["حذف", "Delete"],
    "bulk.apply": ["اعمال", "Apply"], "user.new": ["کاربر جدید", "New user"],
    "th.name": ["نام", "Name"], "th.usage": ["مصرف", "Usage"], "th.limits": ["محدودیت", "Limits"],
    "th.status": ["وضعیت", "Status"], "th.actions": ["اقدام", "Actions"],
    "th.time": ["زمان", "Time"], "th.actor": ["کاربر", "Actor"], "th.action": ["عملیات", "Action"],
    "th.target": ["هدف", "Target"], "loading": ["در حال بارگذاری…", "Loading…"],
    "chart.title": ["پرمصرف‌ترین کاربران (گیگابایت)", "Top users by traffic (GB)"],
    "modal.new": ["کاربر جدید", "New user"], "modal.edit": ["ویرایش کاربر", "Edit user"],
    "f.name": ["نام (انگلیسی)", "Name (English)"], "f.quota": ["حجم (GB — ۰ نامحدود)", "Quota (GB — 0 unlimited)"],
    "f.days": ["اعتبار (روز — ۰ دائمی)", "Validity (days — 0 forever)"],
    "f.iplimit": ["سقف IP همزمان", "Concurrent IP limit"],
    "f.speed": ["سقف سرعت (KB/s — ۰ نامحدود)", "Speed cap (KB/s — 0 unlimited)"],
    "f.routing": ["مسیریابی", "Routing"], "f.dns": ["DNS سفارشی (اختیاری)", "Custom DNS (optional)"],
    "f.filter": ["نوع کانفیگ‌های این کاربر", "This user's config types"],
    "f.filter.all": ["همه (دامنه‌دار + بدون دامنه)", "All (domain + no-domain)"],
    "f.filter.domain": ["فقط دامنه‌دار (TLS)", "Domain only (TLS)"],
    "f.filter.nodomain": ["فقط بدون دامنه (Reality/SS/Hy2/TUIC)", "No-domain only (Reality/SS/Hy2/TUIC)"],
    "f.reset": ["ریستِ دوره‌ای حجم", "Periodic traffic reset"],
    "f.reset.none": ["بدون ریست (سقف کل)", "No reset (lifetime cap)"],
    "f.reset.daily": ["روزانه", "Daily"], "f.reset.weekly": ["هفتگی", "Weekly"],
    "f.reset.monthly": ["ماهانه", "Monthly"],
    "f.routing.default": ["پیش‌فرض سرور", "Server default"], "f.routing.global": ["سراسری", "Global"],
    "f.routing.lan": ["عبور از LAN", "Bypass LAN"], "f.routing.iran": ["عبور از ایران", "Bypass Iran"],
    "f.routing.both": ["LAN + ایران", "LAN + Iran"],
    "cancel": ["انصراف", "Cancel"], "save": ["ذخیره", "Save"],
    "enable": ["فعال", "On"], "disable": ["غیرفعال", "Off"],
    "del.confirm": ["این کاربر حذف شود؟", "Delete this user?"],
    "err.login": ["نام کاربری یا رمز اشتباه است", "Wrong username or password"],
    "err.2fa": ["کد ۲FA اشتباه است", "Invalid 2FA code"],
    "state.loading": ["در حال بارگذاری…", "Loading…"],
    "state.retry": ["تلاش دوباره", "Retry"],
    "state.err": ["بارگذاری ناموفق بود — اتصال را بررسی کنید.", "Couldn't load — check your connection."],
    "empty.users": ["هنوز کاربری نیست. «کاربر جدید» را بزنید تا اولین کاربر ساخته شود.",
      "No users yet. Click “New user” to create the first one."],
    "empty.audit": ["هیچ رویدادی ثبت نشده است.", "No audit events recorded yet."],
    "empty.nodes": ["سروری اضافه نشده. یک نودِ خروجی اضافه کنید.", "No nodes added. Add an outbound node."]
  };
  function t(k) { return (T[k] || [k, k])[state.lang === "fa" ? 0 : 1]; }
  function applyLang() {
    var fa = state.lang === "fa";
    document.documentElement.lang = state.lang;
    document.documentElement.dir = fa ? "rtl" : "ltr";
    $$("[data-i18n]").forEach(function (el) { el.textContent = t(el.getAttribute("data-i18n")); });
    $$("[data-i18n-ph]").forEach(function (el) { el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph"))); });
    var b = $("#lang-toggle"); if (b) b.textContent = fa ? "EN" : "FA";
    if (typeof applyMode === "function") applyMode();  // keep the mode button label in sync
  }

  /* ── storage (sessionStorage با fallback به memory) ────────────────────── *
   * از localStorage صرف نظر شد تا در private mode و بعضی مرورگرها
   * SecurityError نگیریم. sessionStorage هم try/catch داره.
   * ---------------------------------------------------------------------- */
  var _mem = {};
  function _sset(k, v) {
    try { sessionStorage.setItem(k, v); } catch (e) { _mem[k] = v; }
  }
  function _sget(k) {
    try { return sessionStorage.getItem(k); } catch (e) { return _mem[k] || null; }
  }

  function save() {
    _sset("kp_tok", JSON.stringify({ a: state.access, r: state.refresh }));
  }
  function load() {
    try {
      var o = JSON.parse(_sget("kp_tok") || "{}");
      state.access = o.a || null;
      state.refresh = o.r || null;
    } catch (e) { state.access = state.refresh = null; }
  }

  /* ── api ───────────────────────────────────────────────────────────────── */
  async function api(path, opts, retry) {
    opts = opts || {};
    opts.headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    if (state.access) opts.headers.Authorization = "Bearer " + state.access;
    var res = await fetch(API + path, opts);
    if (res.status === 401 && state.refresh && !retry) {
      if (await doRefresh()) return api(path, opts, true);
      /* توکن refresh هم expire شده → برگرد به login */
      _logout();
      return;
    }
    if (!res.ok) throw new Error("HTTP " + res.status);
    var ct = res.headers.get("content-type") || "";
    return ct.indexOf("application/json") >= 0 ? res.json() : res.text();
  }
  async function doRefresh() {
    try {
      var r = await fetch(API + "/auth/refresh", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: state.refresh })
      });
      if (!r.ok) return false;
      var j = await r.json(); state.access = j.access_token; state.refresh = j.refresh_token; save(); return true;
    } catch (e) { return false; }
  }

  /* ── auth ──────────────────────────────────────────────────────────────── */
  var _need2fa = false;

  $("#login-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    $("#lg-err").textContent = "";
    var body = { username: $("#lg-user").value, password: $("#lg-pass").value };
    var totpVal = $("#lg-totp") ? $("#lg-totp").value.trim() : "";
    if (totpVal) body.totp = totpVal;

    try {
      var r = await fetch(API + "/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      /* اگه backend کد ۴۰۱ با پیام "2FA" برگردوند، فیلد TOTP رو نشون بده */
      if (r.status === 401) {
        var errJson = {};
        try { errJson = await r.json(); } catch (_) {}
        var detail = (errJson.detail || "").toLowerCase();
        if (detail.indexOf("2fa") >= 0 || detail.indexOf("totp") >= 0) {
          _need2fa = true;
          var tf = $("#totp-field");
          if (tf) { tf.classList.remove("hidden"); $("#lg-totp").focus(); }
          $("#lg-err").textContent = t("err.2fa");
          return;
        }
        throw new Error("bad");
      }
      if (!r.ok) throw new Error("bad");
      var j = await r.json();
      state.access = j.access_token; state.refresh = j.refresh_token; save();
      _need2fa = false;
      if ($("#totp-field")) $("#totp-field").classList.add("hidden");
      showApp();
    } catch (err) {
      $("#lg-err").textContent = t("err.login");
    }
  });

  function _logout() {
    state.access = state.refresh = null; save();
    clearInterval(window._kpTick);
    $("#app").classList.add("hidden"); $("#login").classList.remove("hidden");
  }
  $("#logout").addEventListener("click", _logout);

  /* ── rendering ─────────────────────────────────────────────────────────── */
  function fmtGB(bytes) { return (bytes / 1073741824).toFixed(2); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c];
    });
  }

  async function refreshStats() {
    try {
      var s = await api("/api/stats");
      if (!s) return;
      $("#s-total").textContent = s.total_users;
      $("#s-active").textContent = s.active_users;
      $("#s-traffic").innerHTML = fmtGB(s.total_used_bytes) + "<small> GB</small>";
    } catch (e) {}
  }
  async function refreshSystem() {
    try {
      var s = await api("/api/system");
      if (!s) return;
      $("#sys-load").textContent = s.loadavg ? s.loadavg[0].toFixed(2) : "—";
      $("#sys-mem").textContent = (s.mem_used_pct != null ? s.mem_used_pct + "%" : "—");
    } catch (e) {}
  }
  /* Consistent full-width state row (loading / empty / error) for tables.
   * kind: "loading" | "empty" | "error". retry: optional view name to reload. */
  function stateRow(colspan, kind, msg, retry) {
    var icon = {
      loading: "<div class=\"spin\" role=\"status\" aria-label=\"loading\"></div>",
      empty: "<svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M3 7h18M3 12h18M3 17h10\"/></svg>",
      error: "<svg class=\"icon\" viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 8v5M12 16h.01\"/></svg>"
    }[kind] || "";
    var btn = retry
      ? "<button class=\"btn sm act-retry\" data-retry=\"" + esc(retry) + "\">" + t("state.retry") + "</button>"
      : "";
    return "<tr><td colspan=\"" + colspan + "\"><div class=\"state " + kind + "\">" +
      icon + "<div class=\"state-msg\">" + esc(msg) + "</div>" + btn + "</div></td></tr>";
  }
  function usageBar(u) {
    var pct = u.quota_bytes > 0 ? Math.min(100, u.used_bytes / u.quota_bytes * 100) : 0;
    var q = u.quota_bytes > 0 ? fmtGB(u.quota_bytes) + " GB" : "∞";
    return "<div>" + fmtGB(u.used_bytes) + " / " + q + "</div>" +
      "<div class=\"bar\"><i style=\"width:" + pct + "%\"></i></div>";
  }
  async function refreshUsers() {
    var q = $("#search").value.trim();
    var body = $("#users-body");
    try {
      state.users = await api("/api/users?limit=500" + (q ? "&q=" + encodeURIComponent(q) : ""));
      if (!state.users) state.users = [];
    } catch (e) {
      state.users = [];
      body.innerHTML = stateRow(7, "error", t("state.err"), "users");
      return;
    }
    if (!state.users.length) {
      body.innerHTML = stateRow(7, "empty", q ? "—" : t("empty.users"), null);
      return;
    }
    body.innerHTML = state.users.map(function (u) {
      var lim = (u.ip_limit ? ("IP " + u.ip_limit) : "—") + (u.speed_kbps ? (" · " + u.speed_kbps + "KB/s") : "");
      return "<tr data-name=\"" + esc(u.name) + "\">" +
        "<td><input type=\"checkbox\" class=\"rowchk\" aria-label=\"select\"></td>" +
        "<td><button class=\"btn sm ghost act-detail\" style=\"font-weight:700;padding:4px 8px\" title=\"" + t("detail.open") + "\">" + esc(u.name) + "</button></td>" +
        "<td class=\"hide mono muted\">" + esc(String(u.uuid).slice(0, 8)) + "…</td>" +
        "<td>" + usageBar(u) + "</td>" +
        "<td class=\"hide muted\">" + esc(lim) + "</td>" +
        "<td><span class=\"tag " + (u.enabled ? "on" : "off") + "\">" + (u.enabled ? t("enable") : t("disable")) + "</span></td>" +
        "<td><div class=\"row-actions\">" +
          "<button class=\"btn sm ghost act-copy-sub\" title=\"" + t("copy.sub") + "\" aria-label=\"copy sub\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1\"/></svg></button>" +
          "<button class=\"btn sm ghost act-copy-cfg\" title=\"" + t("copy.cfg") + "\" aria-label=\"copy config\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><rect x=\"9\" y=\"9\" width=\"13\" height=\"13\" rx=\"2\" ry=\"2\"/><path d=\"M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1\"/></svg></button>" +
          "<button class=\"btn sm ghost act-qr\" title=\"" + t("cfg.qr") + "\" aria-label=\"qr\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><rect x=\"3\" y=\"3\" width=\"7\" height=\"7\"/><rect x=\"14\" y=\"3\" width=\"7\" height=\"7\"/><rect x=\"3\" y=\"14\" width=\"7\" height=\"7\"/><path d=\"M14 14h3v3M17 21v-3M21 14v3M21 21h-3M21 17h-3\"/></svg></button>" +
          "<a class=\"btn sm ghost act-sub\" title=\"sub page\" aria-label=\"sub page\" target=\"_blank\" href=\"sub.html?name=" + encodeURIComponent(u.name) + "\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14 21 3\"/></svg></button>" +
          "<button class=\"btn sm ghost act-toggle\" title=\"toggle\" aria-label=\"toggle\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M12 2v10M18.4 6.6a9 9 0 1 1-12.8 0\"/></svg></button>" +
          "<button class=\"btn sm ghost act-edit\" aria-label=\"edit\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z\"/></svg></button>" +
          "<button class=\"btn sm danger act-del\" aria-label=\"delete\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6\"/></svg></button>" +
        "</div></td></tr>";
    }).join("");
  }
  async function refreshAudit() {
    var body = $("#audit-body");
    try {
      var d = await api("/api/audit?limit=100");
      if (!d) { body.innerHTML = stateRow(5, "error", t("state.err"), "audit"); return; }
      body.innerHTML = (d.entries || []).map(function (a) {
        var dt = new Date(a.ts * 1000).toISOString().replace("T", " ").slice(0, 19);
        return "<tr><td class=\"mono muted\">" + dt + "</td><td>" + esc(a.actor) + "</td><td><b>" + esc(a.action) + "</b></td><td>" + esc(a.target || "—") + "</td><td class=\"hide mono muted\">" + esc(a.ip || "—") + "</td></tr>";
      }).join("") || stateRow(5, "empty", t("empty.audit"), null);
    } catch (e) { body.innerHTML = stateRow(5, "error", t("state.err"), "audit"); }
  }
  async function refreshNodes() {
    var body = $("#nodes-body");
    try {
      var d = await api("/api/nodes");
      if (!d) { body.innerHTML = stateRow(6, "error", t("state.err"), "nodes"); return; }
      var nodes = d.nodes || [];
      body.innerHTML = nodes.length ? nodes.map(function (n) {
        return "<tr data-name=\"" + esc(n.name) + "\">" +
          "<td><b>" + esc(n.name) + "</b></td>" +
          "<td class=\"hide mono muted\">" + esc(n.address) + ":" + esc(n.api_port) + "</td>" +
          "<td>" + esc(n.geo || "—") + "</td>" +
          "<td>" + (n.load != null ? Number(n.load).toFixed(2) : "—") + "</td>" +
          "<td><span class=\"tag " + (n.alive ? "on" : "off") + "\">" + (n.alive ? t("nd.alive") : t("nd.down")) + "</span></td>" +
          "<td><button class=\"btn sm danger act-ndel\" aria-label=\"delete\"><svg class=\"icon\" viewBox=\"0 0 24 24\"><path d=\"M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6\"/></svg></button></td>" +
          "</tr>";
      }).join("") : stateRow(6, "empty", t("empty.nodes"), null);
      var r = await api("/api/route");
      if (!r) return;
      var alerts = (r.alerts || []).map(function (a) { return a.name; });
      $("#nodes-route").innerHTML = t("nd.route") + ": " +
        "<b>" + esc(r.chosen || "—") + "</b>" +
        (r.failover && r.failover.length ? " · failover: " + r.failover.map(esc).join(" → ") : "") +
        (alerts.length ? " · ⚠ bandwidth: " + alerts.map(esc).join(", ") : "");
    } catch (e) { body.innerHTML = stateRow(6, "error", t("state.err"), "nodes"); }
  }

  var _2faMode = "setup";
  async function refreshSettings() {
    try {
      var st = await api("/auth/2fa/status");
      if (!st) return;
      var enabled = !!st.enabled;
      $("#twofa-state").textContent = enabled ? t("set.2fa.on") : t("set.2fa.off");
      $("#twofa-setup").classList.add("hidden");
      _2faMode = enabled ? "disable" : "setup";
      $("#twofa-btn").textContent = enabled ? t("set.2fa.disable") : t("set.2fa.setup");
      $("#twofa-btn").classList.toggle("danger", enabled);
    } catch (e) {}
  }
  $("#twofa-btn").addEventListener("click", async function () {
    try {
      if (_2faMode === "setup") {
        var r = await api("/auth/2fa/setup", { method: "POST" });
        if (!r) return;
        $("#twofa-secret").textContent = t("set.scan") + " " + r.secret;
        $("#twofa-setup").classList.remove("hidden");
        _2faMode = "enable";
        $("#twofa-btn").textContent = t("set.2fa.enable");
      } else if (_2faMode === "enable") {
        var code = $("#twofa-code").value.trim();
        if (code.length !== 6) return;
        await api("/auth/2fa/enable", { method: "POST", body: JSON.stringify({ code: code }) });
        refreshSettings();
      } else if (_2faMode === "disable") {
        await api("/auth/2fa/disable", { method: "POST" });
        refreshSettings();
      }
    } catch (e) { $("#twofa-state").textContent = "خطا / error: " + e.message; }
  });
  $("#pw-btn").addEventListener("click", async function () {
    var oldp = prompt("رمز فعلی / current password:"); if (!oldp) return;
    var newp = prompt("رمز جدید (حداقل ۸) / new password (min 8):"); if (!newp) return;
    try {
      await api("/auth/password", { method: "POST", body: JSON.stringify({ old_password: oldp, new_password: newp }) });
      alert("✅");
    } catch (e) { alert("خطا / error: " + e.message); }
  });
  $("#rotate-btn").addEventListener("click", async function () {
    if (!confirm("همه توکن‌ها باطل می‌شوند / all tokens will be invalidated. ادامه؟")) return;
    try { await api("/api/keys/rotate", { method: "POST" }); alert("✅"); } catch (e) { alert("error: " + e.message); }
  });

  function drawChart() {
    var c = $("#chart"), ctx = c.getContext("2d");
    /* canvas width رو از DOM بگیر نه attribute تا responsive باشه */
    var W = c.offsetWidth || c.width, H = c.offsetHeight || c.height;
    c.width = W; c.height = H;
    ctx.clearRect(0, 0, W, H);
    var top = state.users.slice().sort(function (a, b) { return b.used_bytes - a.used_bytes; }).slice(0, 10);
    if (!top.length) return;
    var max = Math.max.apply(null, top.map(function (u) { return u.used_bytes; }).concat([1]));
    var bw = W / top.length, pad = 10;
    top.forEach(function (u, i) {
      var h = (u.used_bytes / max) * (H - 34);
      var x = i * bw + pad, y = H - h - 20;
      ctx.fillStyle = "#22C55E"; ctx.fillRect(x, y, bw - pad * 2, h);
      ctx.fillStyle = "#94A3B8"; ctx.font = "11px Vazirmatn,system-ui,sans-serif"; ctx.textAlign = "center";
      ctx.fillText(String(u.name).slice(0, 8), x + (bw - pad * 2) / 2, H - 6);
      ctx.fillText(fmtGB(u.used_bytes), x + (bw - pad * 2) / 2, y - 4);
    });
  }

  /* ── events ────────────────────────────────────────────────────────────── */
  /* ── copy helpers ─────────────────────────────────────────────────────────── */
  function _flashBtn(btn, text) {
    var orig = btn.innerHTML;
    btn.textContent = text;
    setTimeout(function () { btn.innerHTML = orig; }, 1800);
  }
  function _copyText(text, btn) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () {
        if (btn) _flashBtn(btn, t("copy.ok"));
      }).catch(function () { _legacyCopy(text, btn); });
    } else { _legacyCopy(text, btn); }
  }
  function _legacyCopy(text, btn) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.focus(); ta.select();
    try { document.execCommand("copy"); if (btn) _flashBtn(btn, t("copy.ok")); } catch (_) {}
    document.body.removeChild(ta);
  }

  /* ── user config / QR modal ────────────────────────────────────────────── */
  var _cfgModal = null;
  function _buildCfgModal() {
    if (_cfgModal) return;
    _cfgModal = document.createElement("div");
    _cfgModal.id = "cfg-modal";
    _cfgModal.className = "scrim hidden";
    _cfgModal.innerHTML = [
      '<div class="modal" style="max-width:520px">',
        '<h3 id="cfg-modal-title"></h3>',
        '<div id="cfg-modal-body" style="font-size:13px;word-break:break-all;max-height:360px;overflow:auto"></div>',
        '<div id="cfg-modal-qr" style="text-align:center;margin:12px 0"></div>',
        '<div class="modal-actions">',
          '<button class="btn ghost" id="cfg-modal-copy-all">' + t("copy.cfg") + '</button>',
          '<button class="btn" id="cfg-modal-close">' + t("cancel") + '</button>',
        '</div>',
      '</div>'
    ].join('');
    document.body.appendChild(_cfgModal);
    _cfgModal.addEventListener("click", function (e) {
      if (e.target === _cfgModal) _cfgModal.classList.add("hidden");
    });
    document.getElementById("cfg-modal-close").addEventListener("click", function () {
      _cfgModal.classList.add("hidden");
    });
  }

  function _fmtTs(ts) {
    if (!ts) return "∞";
    try { return new Date(ts * 1000).toISOString().slice(0, 10); } catch (e) { return "—"; }
  }

  /// Full per-user detail: usage, expiry, status, sub link, every config + QR.
  async function _showCfgModal(name) {
    _buildCfgModal();
    document.getElementById("cfg-modal-title").textContent = t("cfg.modal.title") + ": " + name;
    var body = document.getElementById("cfg-modal-body");
    var qrdiv = document.getElementById("cfg-modal-qr");
    body.textContent = t("cfg.loading"); qrdiv.innerHTML = "";
    _cfgModal.classList.remove("hidden");

    // Usage / expiry / status header (from the already-loaded user row, no extra call).
    var u = state.users.filter(function (x) { return x.name === name; })[0];
    var headHtml = "";
    if (u) {
      var pct = u.quota_bytes > 0 ? Math.min(100, u.used_bytes / u.quota_bytes * 100) : 0;
      var q = u.quota_bytes > 0 ? fmtGB(u.quota_bytes) + " GB" : "∞";
      var subUrl = window.location.origin + window.location.pathname.replace(/\/[^/]*$/, "/sub.html") + "?name=" + encodeURIComponent(name);
      headHtml =
        '<div style="margin-bottom:12px;padding:10px;background:#0b1426;border-radius:10px">' +
          '<div style="display:flex;gap:16px;flex-wrap:wrap;font-size:13px">' +
            '<span>' + t("th.usage") + ': <b>' + fmtGB(u.used_bytes) + ' / ' + q + '</b></span>' +
            '<span>' + t("f.days") + ': <b>' + _fmtTs(u.expires_at) + '</b></span>' +
            '<span>' + t("th.status") + ': <b>' + (u.enabled ? t("enable") : t("disable")) + '</b></span>' +
          '</div>' +
          '<div class="bar" style="margin-top:8px"><i style="width:' + pct + '%"></i></div>' +
          '<div style="display:flex;gap:8px;align-items:center;margin-top:10px">' +
            '<span style="flex:1;font-family:ui-monospace,monospace;font-size:11px;word-break:break-all">' + esc(subUrl) + '</span>' +
            '<button class="btn sm" id="cfg-modal-copy-sub">' + t("copy.sub") + '</button>' +
          '</div>' +
        '</div>';
    }

    try {
      var data = await api("/api/users/" + encodeURIComponent(name) + "/links");
      if (!data || !data.links || !data.links.length) {
        body.innerHTML = headHtml + '<div class="muted" style="padding:8px">' + t("cfg.none") + '</div>';
        var sb0 = document.getElementById("cfg-modal-copy-sub");
        if (sb0 && u) sb0.onclick = function () {
          _copyText(window.location.origin + window.location.pathname.replace(/\/[^/]*$/, "/sub.html") + "?name=" + encodeURIComponent(name), sb0);
        };
        return;
      }
      body.innerHTML = headHtml;
      data.links.forEach(function (l) {
        var row = document.createElement('div');
        row.style.cssText = 'margin:6px 0;padding:8px;background:#0b1426;border-radius:8px;display:flex;gap:8px;align-items:flex-start';
        var span = document.createElement('span');
        span.style.cssText = 'flex:1;font-family:ui-monospace,monospace;font-size:11px';
        span.textContent = l;
        var btn = document.createElement('button');
        btn.className = 'btn sm ghost';
        btn.title = 'copy';
        btn.textContent = '⎘';
        btn.addEventListener('click', function () {
          var b = btn;
          if (navigator.clipboard) {
            navigator.clipboard.writeText(l).then(function () { b.textContent = '✓'; setTimeout(function () { b.textContent = '⎘'; }, 1500); });
          } else {
            var ta = document.createElement('textarea'); ta.value = l; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
            b.textContent = '✓'; setTimeout(function () { b.textContent = '⎘'; }, 1500);
          }
        });
        row.appendChild(span);
        row.appendChild(btn);
        body.appendChild(row);
      });
      /* QR برای اولین لینک */
      if (data.links[0] && window.QRCode) {
        qrdiv.innerHTML = '<canvas id="_kqr"></canvas>';
        new QRCode(document.getElementById("_kqr"), { text: data.links[0], width: 180, height: 180, correctLevel: QRCode.CorrectLevel.M });
      }
      var allLinks = data.links.join('\n');
      document.getElementById("cfg-modal-copy-all").onclick = function () {
        _copyText(allLinks, document.getElementById("cfg-modal-copy-all"));
      };
      var sb = document.getElementById("cfg-modal-copy-sub");
      if (sb) sb.onclick = function () {
        _copyText(window.location.origin + window.location.pathname.replace(/\/[^/]*$/, "/sub.html") + "?name=" + encodeURIComponent(name), sb);
      };
    } catch (e) {
      body.innerHTML = headHtml + '<div class="muted" style="padding:8px">Error: ' + esc(e.message) + '</div>';
    }
  }

  /* lazy-load qrcode.js برای QR در مدال */
  (function () {
    var s = document.createElement("script");
    s.src = "/app/vendor/qrcode.min.js";
    document.head.appendChild(s);
  })();

  $("#users-body").addEventListener("click", async function (e) {
    var tr = e.target.closest("tr"); if (!tr) return;
    var name = tr.getAttribute("data-name");
    if (!name) return;
    var u = state.users.filter(function (x) { return x.name === name; })[0];
    if (e.target.closest(".act-detail")) {
      _showCfgModal(name);
    } else if (e.target.closest(".act-copy-sub")) {
      var subUrl = window.location.origin + window.location.pathname.replace(/\/[^/]*$/, "/sub.html") + "?name=" + encodeURIComponent(name);
      _copyText(subUrl, e.target.closest(".act-copy-sub"));
    } else if (e.target.closest(".act-copy-cfg")) {
      var btn = e.target.closest(".act-copy-cfg");
      try {
        var data = await api("/api/users/" + encodeURIComponent(name) + "/links");
        if (data && data.links && data.links.length) {
          _copyText(data.links.join('\n'), btn);
        } else { _flashBtn(btn, t("cfg.none")); }
      } catch (_) { _flashBtn(btn, "error"); }
    } else if (e.target.closest(".act-qr")) {
      _showCfgModal(name);
    } else if (e.target.closest(".act-toggle") && u) {
      await api("/api/users/" + encodeURIComponent(name), { method: "PATCH", body: JSON.stringify({ enabled: !u.enabled }) });
      refreshUsers(); refreshStats();
    } else if (e.target.closest(".act-edit") && u) {
      openModal(u);
    } else if (e.target.closest(".act-del")) {
      if (confirm(t("del.confirm"))) {
        await api("/api/users/" + encodeURIComponent(name), { method: "DELETE" });
        refreshUsers(); refreshStats();
      }
    }
  });
  $("#chk-all").addEventListener("change", function (e) {
    $$(".rowchk").forEach(function (c) { c.checked = e.target.checked; });
  });
  $("#bulk-apply").addEventListener("click", async function () {
    var action = $("#bulk-action").value; if (!action) return;
    var names = $$("#users-body tr")
      .filter(function (tr) { return $(".rowchk", tr) && $(".rowchk", tr).checked; })
      .map(function (tr) { return tr.getAttribute("data-name"); });
    if (!names.length) return;
    if (action === "delete" && !confirm(t("del.confirm"))) return;
    await api("/api/users/bulk", { method: "POST", body: JSON.stringify({ action: action, names: names }) });
    refreshUsers(); refreshStats();
  });
  $("#copy-all-cfg").addEventListener("click", async function () {
    var btn = this;
    try {
      var d = await api("/api/links");
      if (d && d.links && d.links.length) {
        _copyText(d.links.join("\n"), null);
        _flashBtn(btn, d.links.length + " " + t("copyall.ok"));
      } else {
        _flashBtn(btn, t("cfg.none"));
      }
    } catch (e) { _flashBtn(btn, "error"); }
  });
  $("#search").addEventListener("input", debounce(refreshUsers, 300));
  $("#export").addEventListener("click", async function () {
    try {
      var r = await fetch(API + "/api/export?fmt=csv", { headers: { Authorization: "Bearer " + state.access } });
      var blob = await r.blob(), url = URL.createObjectURL(blob), a = document.createElement("a");
      a.href = url; a.download = "users.csv"; a.click(); URL.revokeObjectURL(url);
    } catch (e) {}
  });
  $$(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      $$(".tab").forEach(function (x) { x.classList.remove("active"); });
      tab.classList.add("active");
      state.view = tab.getAttribute("data-view");
      $("#view-users").classList.toggle("hidden", state.view !== "users");
      $("#view-audit").classList.toggle("hidden", state.view !== "audit");
      $("#view-chart").classList.toggle("hidden", state.view !== "chart");
      $("#view-nodes").classList.toggle("hidden", state.view !== "nodes");
      $("#view-xray").classList.toggle("hidden", state.view !== "xray");
      $("#view-settings").classList.toggle("hidden", state.view !== "settings");
      if (state.view === "audit") refreshAudit();
      if (state.view === "chart") { setTimeout(drawChart, 50); }
      if (state.view === "nodes") refreshNodes();
      if (state.view === "xray") loadXray();
      if (state.view === "settings") refreshSettings();
    });
  });

  // Retry buttons inside error state rows re-run the matching loader.
  var _retry = { users: refreshUsers, audit: refreshAudit, nodes: refreshNodes };
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".act-retry");
    if (!b) return;
    var fn = _retry[b.getAttribute("data-retry")];
    if (fn) {
      var td = b.closest("td"), host = b.closest("tbody");
      var cs = td ? (td.getAttribute("colspan") || 6) : 6;
      if (host) host.innerHTML = stateRow(cs, "loading", t("state.loading"), null);
      fn();
    }
  });

  // ---- Simple / Advanced mode -------------------------------------------- //
  // Simple = everyday essentials (Users + Settings). Advanced = everything,
  // including the live Xray config editor. Persisted across sessions.
  function applyMode() {
    var adv = state.mode === "advanced";
    $$(".tab.adv").forEach(function (x) { x.classList.toggle("hidden", !adv); });
    var btn = $("#mode-toggle");
    if (btn) btn.querySelector("span").textContent = adv ? t("mode.advanced") : t("mode.simple");
    // If a now-hidden advanced tab was active, fall back to Users.
    if (!adv && ["nodes", "audit", "chart", "xray"].indexOf(state.view) >= 0) {
      var u = document.querySelector('.tab[data-view="users"]');
      if (u) u.click();
    }
  }
  // null-safe binder: a missing element (e.g. an index.html older than this
  // app.js) must NEVER throw here, or it would abort the rest of init and leave
  // later buttons (new-user, nodes…) unwired.
  function on(sel, ev, fn) { var el = $(sel); if (el) el.addEventListener(ev, fn); }
  on("#mode-toggle", "click", function () {
    state.mode = state.mode === "advanced" ? "simple" : "advanced";
    try { localStorage.setItem("kian_mode", state.mode); } catch (e) {}
    applyMode();
  });

  // ---- Xray config editor (advanced) ------------------------------------- //
  async function loadXray() {
    var ed = $("#xray-editor"); if (!ed) return;
    $("#xray-err").textContent = ""; $("#xray-ok").textContent = "";
    try {
      var d = await api("/api/xray");
      ed.value = JSON.stringify(d.config || {}, null, 2);
      $("#xray-counts").textContent = "in " + (d.inbounds || 0) + " · out " + (d.outbounds || 0);
    } catch (e) {
      $("#xray-err").textContent = (t("xray.loadfail") || "Failed to load config") + " — " + e.message;
    }
  }
  on("#xray-reload", "click", loadXray);
  on("#xray-format", "click", function () {
    $("#xray-err").textContent = "";
    try {
      $("#xray-editor").value = JSON.stringify(JSON.parse($("#xray-editor").value), null, 2);
    } catch (e) { $("#xray-err").textContent = (t("xray.badjson") || "Invalid JSON") + ": " + e.message; }
  });
  on("#xray-apply", "click", async function () {
    $("#xray-err").textContent = ""; $("#xray-ok").textContent = "";
    var cfg;
    try { cfg = JSON.parse($("#xray-editor").value); }
    catch (e) { $("#xray-err").textContent = (t("xray.badjson") || "Invalid JSON") + ": " + e.message; return; }
    if (!cfg || !cfg.inbounds || !cfg.outbounds) {
      $("#xray-err").textContent = t("xray.needio") || "Config must have inbounds and outbounds.";
      return;
    }
    if (!confirm(t("xray.confirm") || "Apply this config and restart Xray?")) return;
    var btn = $("#xray-apply"); btn.disabled = true;
    try {
      var r = await api("/api/xray", { method: "POST", body: JSON.stringify({ config: cfg }) });
      $("#xray-ok").textContent = (t("xray.applied") || "Applied — Xray restarted") +
        (r.output ? " ✅" : "");
      loadXray();
    } catch (e) {
      $("#xray-err").textContent = (t("xray.rejected") || "Rejected (previous config kept)") + " — " + e.message;
    } finally { btn.disabled = false; }
  });

  $("#nd-add").addEventListener("click", async function () {
    var tokenVal = $("#nd-token").value.trim();
    if (!tokenVal) {
      alert(t("nd.token.required") || "Node token is required — generate a random one and save it.");
      $("#nd-token").focus();
      return;
    }
    var body = {
      name: $("#nd-name").value.trim(), address: $("#nd-addr").value.trim(),
      token: tokenVal,
      geo: $("#nd-geo").value.trim() || null
    };
    if (!body.name || !body.address) return;
    try {
      await api("/api/nodes", { method: "POST", body: JSON.stringify(body) });
      $("#nd-name").value = $("#nd-addr").value = $("#nd-geo").value = $("#nd-token").value = "";
      refreshNodes();
    } catch (e) {}
  });
  $("#nodes-body").addEventListener("click", async function (e) {
    if (!e.target.closest(".act-ndel")) return;
    var tr = e.target.closest("tr"), name = tr.getAttribute("data-name");
    if (!confirm(t("del.confirm"))) return;
    try { await api("/api/nodes/" + encodeURIComponent(name), { method: "DELETE" }); refreshNodes(); } catch (e) {}
  });

  /* modal */
  function openModal(u) {
    $("#modal-err").textContent = "";
    $("#modal-title").textContent = u ? t("modal.edit") : t("modal.new");
    $("#user-form").dataset.edit = u ? u.name : "";
    $("#f-name").value = u ? u.name : ""; $("#f-name").disabled = !!u;
    $("#f-quota").value = u ? Math.round(u.quota_bytes / 1073741824) : 0;
    $("#f-days").value = 0;
    $("#f-iplimit").value = u ? u.ip_limit : 0;
    $("#f-speed").value = u ? u.speed_kbps : 0;
    $("#f-routing").value = (u && u.routing) ? u.routing : "";
    $("#f-dns").value = (u && u.dns) ? u.dns : "";
    if ($("#f-filter")) $("#f-filter").value = (u && u.sub_filter) ? u.sub_filter : "all";
    if ($("#f-reset")) $("#f-reset").value = (u && u.reset_strategy) ? u.reset_strategy : "none";
    $("#modal").classList.remove("hidden");
  }
  $("#new-user").addEventListener("click", function () { openModal(null); });
  $("#modal-cancel").addEventListener("click", function () { $("#modal").classList.add("hidden"); });
  /* بستن مدال با کلیک روی scrim */
  $("#modal").addEventListener("click", function (e) {
    if (e.target === $("#modal")) $("#modal").classList.add("hidden");
  });
  $("#user-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    var edit = $("#user-form").dataset.edit;
    var payload = {
      quota_bytes: Math.max(0, +$("#f-quota").value) * 1073741824,
      ip_limit: Math.max(0, +$("#f-iplimit").value),
      speed_kbps: Math.max(0, +$("#f-speed").value)
    };
    var routing = $("#f-routing").value;
    if (routing) payload.routing = routing;
    var dns = $("#f-dns").value.trim();
    if (dns) payload.dns = dns;
    var days = Math.max(0, +$("#f-days").value);
    if (days > 0) payload.expires_at = Math.floor(Date.now() / 1000) + days * 86400;
    var filt = $("#f-filter") ? $("#f-filter").value : "all";
    if (filt) payload.sub_filter = filt;   // per-user config selection
    var reset = $("#f-reset") ? $("#f-reset").value : "none";
    payload.reset_strategy = reset;        // FR-S1 periodic quota reset
    try {
      if (edit) {
        await api("/api/users/" + encodeURIComponent(edit), { method: "PATCH", body: JSON.stringify(payload) });
      } else {
        payload.name = $("#f-name").value;
        await api("/api/users", { method: "POST", body: JSON.stringify(payload) });
      }
      $("#modal").classList.add("hidden"); refreshUsers(); refreshStats();
    } catch (err) { $("#modal-err").textContent = "HTTP " + err.message; }
  });

  $("#lang-toggle").addEventListener("click", function () {
    state.lang = state.lang === "fa" ? "en" : "fa";
    _sset("kp_lang", state.lang);
    applyLang(); refreshUsers();
  });

  function debounce(fn, ms) { var tmr; return function () { clearTimeout(tmr); tmr = setTimeout(fn, ms); }; }

  /* ── boot ──────────────────────────────────────────────────────────────── */
  function showApp() {
    $("#login").classList.add("hidden"); $("#app").classList.remove("hidden");
    try { state.mode = localStorage.getItem("kian_mode") || "simple"; } catch (e) {}
    applyMode();
    refreshStats(); refreshUsers(); refreshSystem();
    clearInterval(window._kpTick);
    window._kpTick = setInterval(function () { refreshStats(); refreshSystem(); }, 5000);
  }

  async function boot() {
    try { state.lang = _sget("kp_lang") || "en"; } catch (e) {}
    applyLang();
    /* اول API base رو resolve کن، بعد بقیه */
    await _initAPI();
    load();
    if (state.access) {
      /* یه ping سریع بزن ببین توکن هنوز معتبره */
      try {
        await api("/api/stats");
        showApp();
      } catch (e) {
        /* اگه refresh هم کار نکرد، به login برگرد */
        _logout();
      }
    }
    /* اگه access نیست، login form از قبل visible هست */
  }
  boot();
})();
