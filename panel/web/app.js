/* KIAN V2Ray panel — dashboard logic (vanilla, dependency-free).
 * Talks to panel.main (FastAPI). Tokens in localStorage; auto-refresh on 401. */
(function () {
  "use strict";
  var API = (window.KIAN_API || "").replace(/\/$/, "");   // same-origin by default
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var state = { access: null, refresh: null, users: [], lang: "en", view: "users" };

  /* ----------------------------- i18n ----------------------------- */
  var T = {
    "login.title": ["ورود به پنل KIAN", "Sign in to KIAN Panel"],
    "login.user": ["نام کاربری", "Username"], "login.pass": ["رمز عبور", "Password"],
    "login.btn": ["ورود", "Sign in"], "logout": ["خروج", "Logout"],
    "sys.load": ["بار", "Load"], "sys.mem": ["رم", "RAM"],
    "stat.total": ["کل کاربران", "Total users"], "stat.active": ["فعال", "Active"],
    "stat.traffic": ["مصرف کل", "Total traffic"],
    "tab.users": ["کاربران", "Users"], "tab.audit": ["گزارش ممیزی", "Audit log"],
    "tab.chart": ["نمودار مصرف", "Usage chart"], "tab.nodes": ["سرورها", "Nodes"],
    "tab.settings": ["تنظیمات", "Settings"],
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
    "f.routing.default": ["پیش‌فرض سرور", "Server default"], "f.routing.global": ["سراسری", "Global"],
    "f.routing.lan": ["عبور از LAN", "Bypass LAN"], "f.routing.iran": ["عبور از ایران", "Bypass Iran"],
    "f.routing.both": ["LAN + ایران", "LAN + Iran"],
    "cancel": ["انصراف", "Cancel"], "save": ["ذخیره", "Save"],
    "enable": ["فعال", "On"], "disable": ["غیرفعال", "Off"],
    "del.confirm": ["این کاربر حذف شود؟", "Delete this user?"],
    "err.login": ["نام کاربری یا رمز اشتباه است", "Wrong username or password"]
  };
  function t(k) { return (T[k] || [k, k])[state.lang === "fa" ? 0 : 1]; }
  function applyLang() {
    var fa = state.lang === "fa";
    document.documentElement.lang = state.lang;
    document.documentElement.dir = fa ? "rtl" : "ltr";
    $$("[data-i18n]").forEach(function (el) { el.textContent = t(el.getAttribute("data-i18n")); });
    $$("[data-i18n-ph]").forEach(function (el) { el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph"))); });
    var b = $("#lang-toggle"); if (b) b.textContent = fa ? "EN" : "FA";
  }

  /* ----------------------------- api ----------------------------- */
  function save() {
    try { localStorage.setItem("kp_tok", JSON.stringify({ a: state.access, r: state.refresh })); } catch (e) {}
  }
  function load() {
    try { var o = JSON.parse(localStorage.getItem("kp_tok") || "{}"); state.access = o.a; state.refresh = o.r; } catch (e) {}
  }
  async function api(path, opts, retry) {
    opts = opts || {};
    opts.headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
    if (state.access) opts.headers.Authorization = "Bearer " + state.access;
    var res = await fetch(API + path, opts);
    if (res.status === 401 && state.refresh && !retry) {
      if (await doRefresh()) return api(path, opts, true);
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

  /* ----------------------------- auth ----------------------------- */
  $("#login-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    $("#lg-err").textContent = "";
    try {
      var r = await fetch(API + "/auth/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: $("#lg-user").value, password: $("#lg-pass").value })
      });
      if (!r.ok) throw new Error("bad");
      var j = await r.json(); state.access = j.access_token; state.refresh = j.refresh_token; save();
      showApp();
    } catch (err) { $("#lg-err").textContent = t("err.login"); }
  });
  $("#logout").addEventListener("click", function () {
    state.access = state.refresh = null; save();
    $("#app").classList.add("hidden"); $("#login").classList.remove("hidden");
  });

  /* ----------------------------- rendering ----------------------------- */
  function fmtGB(bytes) { return (bytes / 1073741824).toFixed(2); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); }

  async function refreshStats() {
    try {
      var s = await api("/api/stats");
      $("#s-total").textContent = s.total_users;
      $("#s-active").textContent = s.active_users;
      $("#s-traffic").innerHTML = fmtGB(s.total_used_bytes) + "<small> GB</small>";
    } catch (e) {}
  }
  async function refreshSystem() {
    try {
      var s = await api("/api/system");
      $("#sys-load").textContent = s.loadavg ? s.loadavg[0].toFixed(2) : "—";
      $("#sys-mem").textContent = (s.mem_used_pct != null ? s.mem_used_pct + "%" : "—");
    } catch (e) {}
  }
  function usageBar(u) {
    var pct = u.quota_bytes > 0 ? Math.min(100, u.used_bytes / u.quota_bytes * 100) : 0;
    var q = u.quota_bytes > 0 ? fmtGB(u.quota_bytes) + " GB" : "∞";
    return '<div>' + fmtGB(u.used_bytes) + ' / ' + q + '</div>' +
      '<div class="bar"><i style="width:' + pct + '%"></i></div>';
  }
  async function refreshUsers() {
    var q = $("#search").value.trim();
    try {
      state.users = await api("/api/users?limit=500" + (q ? "&q=" + encodeURIComponent(q) : ""));
    } catch (e) { return; }
    var body = $("#users-body");
    if (!state.users.length) { body.innerHTML = '<tr><td colspan="7" class="muted" style="text-align:center;padding:24px">—</td></tr>'; return; }
    body.innerHTML = state.users.map(function (u) {
      var lim = (u.ip_limit ? ("IP " + u.ip_limit) : "—") + (u.speed_kbps ? (" · " + u.speed_kbps + "KB/s") : "");
      return '<tr data-name="' + esc(u.name) + '">' +
        '<td><input type="checkbox" class="rowchk" aria-label="select"></td>' +
        '<td><b>' + esc(u.name) + '</b></td>' +
        '<td class="hide mono muted">' + esc(String(u.uuid).slice(0, 8)) + '…</td>' +
        '<td>' + usageBar(u) + '</td>' +
        '<td class="hide muted">' + esc(lim) + '</td>' +
        '<td><span class="tag ' + (u.enabled ? "on" : "off") + '">' + (u.enabled ? t("enable") : t("disable")) + '</span></td>' +
        '<td><div class="row-actions">' +
          '<a class="btn sm ghost act-sub" title="config" aria-label="config" target="_blank" href="sub.html?name=' + encodeURIComponent(u.name) + '"><svg class="icon" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg></a>' +
          '<button class="btn sm ghost act-toggle" title="toggle" aria-label="toggle"><svg class="icon" viewBox="0 0 24 24"><path d="M12 2v10M18.4 6.6a9 9 0 1 1-12.8 0"/></svg></button>' +
          '<button class="btn sm ghost act-edit" aria-label="edit"><svg class="icon" viewBox="0 0 24 24"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg></button>' +
          '<button class="btn sm danger act-del" aria-label="delete"><svg class="icon" viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg></button>' +
        '</div></td></tr>';
    }).join("");
  }
  async function refreshAudit() {
    try {
      var d = await api("/api/audit?limit=100");
      $("#audit-body").innerHTML = (d.entries || []).map(function (a) {
        var dt = new Date(a.ts * 1000).toISOString().replace("T", " ").slice(0, 19);
        return '<tr><td class="mono muted">' + dt + '</td><td>' + esc(a.actor) + '</td><td><b>' + esc(a.action) + '</b></td><td>' + esc(a.target || "—") + '</td><td class="hide mono muted">' + esc(a.ip || "—") + '</td></tr>';
      }).join("") || '<tr><td colspan="5" class="muted" style="text-align:center;padding:20px">—</td></tr>';
    } catch (e) {}
  }
  async function refreshNodes() {
    try {
      var d = await api("/api/nodes");
      var nodes = d.nodes || [];
      $("#nodes-body").innerHTML = nodes.length ? nodes.map(function (n) {
        return '<tr data-name="' + esc(n.name) + '">' +
          '<td><b>' + esc(n.name) + '</b></td>' +
          '<td class="hide mono muted">' + esc(n.address) + ':' + esc(n.api_port) + '</td>' +
          '<td>' + esc(n.geo || '—') + '</td>' +
          '<td>' + (n.load != null ? Number(n.load).toFixed(2) : '—') + '</td>' +
          '<td><span class="tag ' + (n.alive ? 'on' : 'off') + '">' + (n.alive ? t('nd.alive') : t('nd.down')) + '</span></td>' +
          '<td><button class="btn sm danger act-ndel" aria-label="delete"><svg class="icon" viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/></svg></button></td>' +
          '</tr>';
      }).join("") : '<tr><td colspan="6" class="muted" style="text-align:center;padding:24px">—</td></tr>';
      // route/failover summary
      var r = await api("/api/route");
      var alerts = (r.alerts || []).map(function (a) { return a.name; });
      $("#nodes-route").innerHTML = t('nd.route') + ': ' +
        '<b>' + esc(r.chosen || '—') + '</b>' +
        (r.failover && r.failover.length ? ' · failover: ' + r.failover.map(esc).join(' → ') : '') +
        (alerts.length ? ' · ⚠ bandwidth: ' + alerts.map(esc).join(', ') : '');
    } catch (e) {}
  }

  var _2faMode = "setup"; // setup | enable | disable
  async function refreshSettings() {
    try {
      var st = await api("/auth/2fa/status");
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
    ctx.clearRect(0, 0, c.width, c.height);
    var top = state.users.slice().sort(function (a, b) { return b.used_bytes - a.used_bytes; }).slice(0, 10);
    var max = Math.max.apply(null, top.map(function (u) { return u.used_bytes; }).concat([1]));
    var bw = c.width / (top.length || 1), pad = 10;
    top.forEach(function (u, i) {
      var h = (u.used_bytes / max) * (c.height - 34);
      var x = i * bw + pad, y = c.height - h - 20;
      ctx.fillStyle = "#22C55E"; ctx.fillRect(x, y, bw - pad * 2, h);
      ctx.fillStyle = "#94A3B8"; ctx.font = "11px Vazirmatn,sans-serif"; ctx.textAlign = "center";
      ctx.fillText(String(u.name).slice(0, 8), x + (bw - pad * 2) / 2, c.height - 6);
      ctx.fillText(fmtGB(u.used_bytes), x + (bw - pad * 2) / 2, y - 4);
    });
  }

  /* ----------------------------- events ----------------------------- */
  $("#users-body").addEventListener("click", async function (e) {
    var tr = e.target.closest("tr"); if (!tr) return;
    var name = tr.getAttribute("data-name");
    var u = state.users.filter(function (x) { return x.name === name; })[0];
    if (e.target.closest(".act-toggle")) {
      await api("/api/users/" + encodeURIComponent(name), { method: "PATCH", body: JSON.stringify({ enabled: !u.enabled }) });
      refreshUsers(); refreshStats();
    } else if (e.target.closest(".act-edit")) {
      openModal(u);
    } else if (e.target.closest(".act-del")) {
      if (confirm(t("del.confirm"))) { await api("/api/users/" + encodeURIComponent(name), { method: "DELETE" }); refreshUsers(); refreshStats(); }
    }
  });
  $("#chk-all").addEventListener("change", function (e) {
    $$(".rowchk").forEach(function (c) { c.checked = e.target.checked; });
  });
  $("#bulk-apply").addEventListener("click", async function () {
    var action = $("#bulk-action").value; if (!action) return;
    var names = $$("#users-body tr").filter(function (tr) { return $(".rowchk", tr) && $(".rowchk", tr).checked; })
      .map(function (tr) { return tr.getAttribute("data-name"); });
    if (!names.length) return;
    if (action === "delete" && !confirm(t("del.confirm"))) return;
    await api("/api/users/bulk", { method: "POST", body: JSON.stringify({ action: action, names: names }) });
    refreshUsers(); refreshStats();
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
      $("#view-settings").classList.toggle("hidden", state.view !== "settings");
      if (state.view === "audit") refreshAudit();
      if (state.view === "chart") drawChart();
      if (state.view === "nodes") refreshNodes();
      if (state.view === "settings") refreshSettings();
    });
  });

  $("#nd-add").addEventListener("click", async function () {
    var body = {
      name: $("#nd-name").value.trim(), address: $("#nd-addr").value.trim(),
      token: $("#nd-token").value.trim() || "changeme",
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
    $("#modal").classList.remove("hidden");
  }
  $("#new-user").addEventListener("click", function () { openModal(null); });
  $("#modal-cancel").addEventListener("click", function () { $("#modal").classList.add("hidden"); });
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
    try { localStorage.setItem("kp_lang", state.lang); } catch (e) {}
    applyLang(); refreshUsers();
  });

  function debounce(fn, ms) { var tmr; return function () { clearTimeout(tmr); tmr = setTimeout(fn, ms); }; }

  /* ----------------------------- boot ----------------------------- */
  function showApp() {
    $("#login").classList.add("hidden"); $("#app").classList.remove("hidden");
    refreshStats(); refreshUsers(); refreshSystem();
    clearInterval(window._kpTick);
    window._kpTick = setInterval(function () { refreshStats(); refreshSystem(); }, 5000);
  }
  function boot() {
    try { state.lang = localStorage.getItem("kp_lang") || "en"; } catch (e) {}
    applyLang(); load();
    if (state.access) { showApp(); refreshStats().catch(function () {}); }
  }
  boot();
})();
