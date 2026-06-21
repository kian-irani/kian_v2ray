/* KIAN — web-panel setup helper for the landing page.
 * Independent of app.js/i18n.js: reads the admin user/pass (and the server IP
 * already entered in the generator) and produces the one-line command the user
 * runs on the server to deploy the web panel, plus the resulting URL. */
(function () {
  "use strict";
  var $ = function (s) { return document.querySelector(s); };
  var btn = $("#panel-gen");
  if (!btn) return;

  function esc(s) { return String(s).replace(/"/g, '\\"'); }

  btn.addEventListener("click", function () {
    var ipEl = $("#server-ip");
    var ip = (ipEl && ipEl.value.trim()) || "<server-ip>";
    var user = ($("#panel-user").value.trim()) || "admin";
    var pass = $("#panel-pass").value.trim() || "CHANGE-ME-strong";
    // The CLI is installed by the installer; this enables the panel with the
    // chosen admin credentials and prints the URL on the server too.
    var cmd = 'KIAN_ADMIN_USER=' + user + ' KIAN_ADMIN_PASSWORD="' + esc(pass) +
              '" kian-v2ray panel enable';
    $("#panel-cmd").textContent = cmd;
    $("#panel-url").textContent = "http://" + ip + ":8443/app";
    $("#panel-out").hidden = false;
  });
})();
