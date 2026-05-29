/* ==========================================================================
 *  KIAN V2Ray — منطق صفحه‌ی تعاملی  (همه‌چیز سمت مرورگر؛ هیچ داده‌ای ارسال نمی‌شود)
 *  این فایل کانفیگ Xray و users.json و payload را می‌سازد و دستور نصب را تولید می‌کند.
 *  خروجی دقیقاً با install.sh و scripts/watchdog.sh هماهنگ است.
 *  وابستگی‌ها (لوکال، بدون CDN):  vendor/nacl.min.js  +  vendor/qrcode.min.js
 * ======================================================================== */
'use strict';

const RAW_BASE = 'https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main';
const WARP_PORT = 40000;
const SS_METHOD = 'chacha20-ietf-poly1305';
const GIB = 1073741824;

/* ----------------------------- helpers --------------------------------- */
const $  = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

function utf8ToB64(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = '';
  bytes.forEach(b => (bin += String.fromCharCode(b)));
  return btoa(bin);
}
function u8ToB64url(u8) {
  let bin = '';
  u8.forEach(b => (bin += String.fromCharCode(b)));
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function randHex(nBytes) {
  const u = new Uint8Array(nBytes);
  crypto.getRandomValues(u);
  return Array.from(u, b => b.toString(16).padStart(2, '0')).join('');
}
function genPassword(nBytes = 16) {
  const u = new Uint8Array(nBytes);
  crypto.getRandomValues(u);
  return u8ToB64url(u).slice(0, 22);
}
function isIPv4(s) {
  const parts = String(s).trim().split('.');
  if (parts.length !== 4) return false;
  return parts.every(p => /^\d{1,3}$/.test(p) && +p >= 0 && +p <= 255);
}
function reExpiry(days) {
  if (!days || days <= 0) return null;                 // دائمی
  return new Date(Date.now() + days * 86400000).toISOString();
}

/* ------------------------- key / id generation ------------------------- */
function genReality() {
  const kp = nacl.box.keyPair();                       // X25519 (سازگار با xray x25519)
  return {
    privateKey: u8ToB64url(kp.secretKey),
    publicKey:  u8ToB64url(kp.publicKey),
    shortId:    randHex(8),                             // 16 hex
  };
}

/* ----------------------------- Xray config ----------------------------- */
function buildConfig(o) {
  const wantDirect = o.mode === 'direct' || o.mode === 'both';
  const wantWarp   = o.mode === 'warp'   || o.mode === 'both';
  const clients = o.users.map(u => ({ id: u.id, email: u.email, flow: 'xtls-rprx-vision' }));

  const realityInbound = (tag, port) => ({
    listen: '0.0.0.0',
    port,
    protocol: 'vless',
    tag,
    settings: { clients: clients.map(c => ({ ...c })), decryption: 'none' },
    streamSettings: {
      network: 'tcp',
      security: 'reality',
      realitySettings: {
        show: false,
        dest: `${o.sni}:443`,
        xver: 0,
        serverNames: [o.sni],
        privateKey: o.reality.privateKey,
        shortIds: [o.reality.shortId],
      },
    },
    sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'] },
  });

  const inbounds = [
    { listen: '127.0.0.1', port: 10085, protocol: 'dokodemo-door', settings: { address: '127.0.0.1' }, tag: 'api' },
  ];
  if (wantDirect) inbounds.push(realityInbound('reality-direct', o.portDirect));
  if (wantWarp)   inbounds.push(realityInbound('reality-warp',   o.portWarp));
  if (o.ss.enabled) {
    inbounds.push({
      listen: '0.0.0.0',
      port: o.ss.port,
      protocol: 'shadowsocks',
      tag: 'shadowsocks',
      settings: {
        clients: [{ password: o.ss.password, email: 'ss-shared@kian', method: SS_METHOD }],
        network: 'tcp,udp',
      },
      sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'] },
    });
  }

  const outbounds = [{ tag: 'direct', protocol: 'freedom', settings: { domainStrategy: 'UseIP' } }];
  if (wantWarp) outbounds.push({ tag: 'warp', protocol: 'socks', settings: { servers: [{ address: '127.0.0.1', port: WARP_PORT }] } });
  outbounds.push({ tag: 'block', protocol: 'blackhole', settings: {} });

  const ssOut = o.mode === 'warp' ? 'warp' : 'direct';
  const rules = [
    { type: 'field', inboundTag: ['api'], outboundTag: 'api' },
    { type: 'field', ip: ['geoip:private'], outboundTag: 'block' },
  ];
  if (wantWarp)     rules.push({ type: 'field', inboundTag: ['reality-warp'],  outboundTag: 'warp' });
  if (wantDirect)   rules.push({ type: 'field', inboundTag: ['reality-direct'], outboundTag: 'direct' });
  if (o.ss.enabled) rules.push({ type: 'field', inboundTag: ['shadowsocks'],   outboundTag: ssOut });

  return {
    log: { loglevel: 'warning', access: '/var/log/xray/access.log', error: '/var/log/xray/error.log' },
    dns: { servers: ['1.1.1.1', '8.8.8.8'] },
    api: { tag: 'api', services: ['HandlerService', 'StatsService'] },
    stats: {},
    policy: {
      levels: { '0': { statsUserUplink: true, statsUserDownlink: true } },
      system: { statsInboundUplink: true, statsInboundDownlink: true },
    },
    inbounds,
    outbounds,
    routing: { domainStrategy: 'IPIfNonMatch', rules },
  };
}

/* ------------------------------- links --------------------------------- */
function vlessLink({ uuid, ip, port, sni, pubkey, shortId, label }) {
  const q = new URLSearchParams({
    encryption: 'none',
    flow: 'xtls-rprx-vision',
    security: 'reality',
    sni,
    fp: 'chrome',
    pbk: pubkey,
    sid: shortId,
    type: 'tcp',
  });
  return `vless://${uuid}@${ip}:${port}?${q.toString()}#${encodeURIComponent(label)}`;
}
function ssLink({ ip, port, password, label }) {
  return `ss://${btoa(`${SS_METHOD}:${password}`)}@${ip}:${port}#${encodeURIComponent(label)}`;
}

/* --------------------------- read the form ----------------------------- */
function readForm() {
  const mode      = ($('input[name="mode"]:checked') || {}).value || 'both';
  const ssEnabled = $('#ss-enabled').checked;
  return {
    serverIp:  $('#server-ip').value.trim(),
    sni:       ($('#sni').value === '__custom__' ? $('#sni-custom').value.trim() : $('#sni').value).trim(),
    mode,
    portDirect: parseInt($('#port-direct').value, 10) || 8443,
    portWarp:   parseInt($('#port-warp').value, 10)   || 8444,
    numUsers:   Math.min(50, Math.max(1, parseInt($('#num-users').value, 10) || 1)),
    prefix:    ($('#user-prefix').value.trim() || 'user').replace(/[^a-zA-Z0-9_-]/g, ''),
    quotaGb:   parseInt($('#quota').value, 10),        // 0 = نامحدود
    days:      parseInt($('#days').value, 10),         // 0 = دائمی
    ss: {
      enabled: ssEnabled,
      port: parseInt($('#ss-port').value, 10) || 8388,
      password: '',
    },
  };
}

/* ------------------------------ generate ------------------------------- */
function generate(f) {
  const reality = genReality();
  if (f.ss.enabled) f.ss.password = genPassword();

  const wantDirect = f.mode === 'direct' || f.mode === 'both';
  const wantWarp   = f.mode === 'warp'   || f.mode === 'both';

  const users = [];
  for (let i = 1; i <= f.numUsers; i++) {
    users.push({
      id: crypto.randomUUID(),
      email: `${f.prefix}-${i}@kian`,
      quota_bytes: f.quotaGb > 0 ? f.quotaGb * GIB : 0,
      used_bytes: 0,
      expires_at: reExpiry(f.days),
      active: true,
      note: '',
    });
  }

  const config = buildConfig({ ...f, reality, users });

  const links = [];
  const perUser = users.map(u => {
    const local = u.email.split('@')[0];
    const out = { email: u.email, local, direct: null, warp: null };
    if (wantDirect) {
      out.direct = vlessLink({
        uuid: u.id, ip: f.serverIp, port: f.portDirect, sni: f.sni,
        pubkey: reality.publicKey, shortId: reality.shortId, label: `KIAN · ${local} · Direct`,
      });
      links.push(out.direct);
    }
    if (wantWarp) {
      out.warp = vlessLink({
        uuid: u.id, ip: f.serverIp, port: f.portWarp, sni: f.sni,
        pubkey: reality.publicKey, shortId: reality.shortId, label: `KIAN · ${local} · WARP`,
      });
      links.push(out.warp);
    }
    return out;
  });

  let ssOut = null;
  if (f.ss.enabled) {
    ssOut = ssLink({ ip: f.serverIp, port: f.ss.port, password: f.ss.password, label: 'KIAN · Shadowsocks' });
    links.push(ssOut);
  }

  const ports = [];
  if (wantDirect) ports.push(f.portDirect);
  if (wantWarp)   ports.push(f.portWarp);
  if (f.ss.enabled) ports.push(f.ss.port);

  const payload = {
    warp_needed: wantWarp,
    server_ip: f.serverIp,
    config_b64: utf8ToB64(JSON.stringify(config)),
    users_b64:  utf8ToB64(JSON.stringify({ users })),
    links,
    ports,
  };
  const payloadB64 = utf8ToB64(JSON.stringify(payload));

  const installCmd =
    `export KIAN_PAYLOAD='${payloadB64}'\n` +
    `curl -fsSL ${RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh`;

  return { f, reality, users, perUser, ssOut, ports, config, payloadB64, installCmd };
}

/* ------------------------------ rendering ------------------------------ */
function qr(el, text) {
  el.innerHTML = '';
  try {
    new QRCode(el, { text, width: 150, height: 150, colorDark: '#0b1016', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.L });
  } catch (e) { el.textContent = 'QR ?'; }
}

function copyBtn(label, getText) {
  const b = document.createElement('button');
  b.className = 'copy';
  b.type = 'button';
  b.innerHTML = `<span>${label}</span>`;
  b.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(getText());
    } catch (e) {
      const ta = document.createElement('textarea');
      ta.value = getText(); document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (_) {}
      ta.remove();
    }
    const prev = b.innerHTML;
    b.classList.add('ok');
    b.innerHTML = '<span>کپی شد ✓</span>';
    setTimeout(() => { b.innerHTML = prev; b.classList.remove('ok'); }, 1400);
  });
  return b;
}

function linkRow(title, link) {
  const wrap = document.createElement('div');
  wrap.className = 'linkrow';
  const head = document.createElement('div');
  head.className = 'linkrow-head';
  head.innerHTML = `<span class="linkrow-title">${title}</span>`;
  head.appendChild(copyBtn('کپی لینک', () => link));
  const code = document.createElement('div');
  code.className = 'linkrow-code mono';
  code.textContent = link;
  const qrbox = document.createElement('div');
  qrbox.className = 'qr';
  qr(qrbox, link);
  wrap.append(head, code, qrbox);
  return wrap;
}

function render(out) {
  const box = $('#result');
  box.innerHTML = '';

  const warn = document.createElement('div');
  warn.className = 'panel warn reveal';
  warn.innerHTML = `
    <div class="panel-title">⚠️ مهم — قبل از بستن این صفحه بخوان</div>
    <ul class="tips">
      <li>کلیدها همین‌الان و فقط در همین صفحه ساخته شدند. اگر صفحه را ببندی <b>قابل بازیابی نیستند</b>.</li>
      <li>اول دستور نصب (بخش ۱) را روی سرور اجرا کن، بعد لینک‌های کاربر (بخش ۳) را ذخیره/پخش کن.</li>
      <li>هر بار «ساخت کانفیگ» بزنی، کلیدهای کاملاً جدید ساخته می‌شود و لینک‌های قبلی باطل می‌شوند.</li>
    </ul>`;
  box.appendChild(warn);

  const step1 = document.createElement('div');
  step1.className = 'panel reveal';
  step1.innerHTML = `<div class="panel-title">۱) این دستور را در ترمینالِ سرور (SSH) اجرا کن</div>
    <p class="muted">یک‌بار کپی کن و در ترمینال paste کن. نصب در پس‌زمینه اجرا می‌شود؛ <b>حتی اگر SSH قطع شد ادامه پیدا می‌کند</b>.</p>`;
  const term = document.createElement('div');
  term.className = 'terminal';
  term.innerHTML = `<div class="term-bar"><i></i><i></i><i></i><span>root@server:~#</span></div>`;
  const termBody = document.createElement('pre');
  termBody.className = 'term-body mono';
  termBody.textContent = out.installCmd;
  term.appendChild(termBody);
  const termActions = document.createElement('div');
  termActions.className = 'row';
  termActions.appendChild(copyBtn('کپی دستور نصب', () => out.installCmd));
  step1.append(term, termActions);
  box.appendChild(step1);

  const step2 = document.createElement('div');
  step2.className = 'panel reveal';
  step2.innerHTML = `<div class="panel-title">۲) بعد از ۲ تا ۵ دقیقه، وضعیت را چک کن</div>
    <p class="muted">می‌توانی SSH را ببندی و دوباره وصل شوی. این دستور وضعیت نصب و سرویس را نشان می‌دهد:</p>`;
  const cmd2 = document.createElement('div');
  cmd2.className = 'cmdline mono';
  cmd2.textContent = 'bash /tmp/kian-v2ray.sh status';
  const a2 = document.createElement('div');
  a2.className = 'row';
  a2.appendChild(copyBtn('کپی', () => 'bash /tmp/kian-v2ray.sh status'));
  const note2 = document.createElement('p');
  note2.className = 'muted small';
  note2.innerHTML = 'بعد از پایان نصب، این دستورها هم در دسترس‌اند: <span class="mono">kian-v2ray status</span> · <span class="mono">kian-v2ray configs</span> · <span class="mono">kian-v2ray users</span>';
  step2.append(cmd2, a2, note2);
  box.appendChild(step2);

  const step3 = document.createElement('div');
  step3.className = 'panel reveal';
  const modeLabel  = { direct: 'فقط مستقیم', warp: 'فقط WARP', both: 'مستقیم + WARP' }[out.f.mode];
  const quotaLabel = out.f.quotaGb > 0 ? `${out.f.quotaGb}GB` : 'نامحدود';
  const daysLabel  = out.f.days > 0 ? `${out.f.days} روز` : 'دائمی';
  step3.innerHTML = `<div class="panel-title">۳) کانفیگ کاربرها (${out.users.length} کاربر)</div>
    <div class="badges">
      <span class="badge">${modeLabel}</span>
      <span class="badge">حجم: ${quotaLabel}</span>
      <span class="badge">اعتبار: ${daysLabel}</span>
      <span class="badge">SNI: ${out.f.sni}</span>
    </div>`;
  out.perUser.forEach(u => {
    const card = document.createElement('div');
    card.className = 'usercard';
    card.innerHTML = `<div class="usercard-title">👤 ${u.local}</div>`;
    if (u.direct) card.appendChild(linkRow('Reality مستقیم — سرعت بالا', u.direct));
    if (u.warp)   card.appendChild(linkRow('Reality + WARP — همه‌چیز باز', u.warp));
    step3.appendChild(card);
  });
  if (out.ssOut) {
    const card = document.createElement('div');
    card.className = 'usercard';
    card.innerHTML = `<div class="usercard-title">🧩 Shadowsocks (مشترک · بدون محدودیت حجمِ تک‌کاربره)</div>`;
    card.appendChild(linkRow('Shadowsocks', out.ssOut));
    step3.appendChild(card);
  }
  box.appendChild(step3);

  $$('.reveal', box).forEach((el, i) => { el.style.animationDelay = `${i * 90}ms`; });
  box.classList.remove('hidden');
  if (typeof box.scrollIntoView === 'function') {
    try { box.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
  }
}

/* ------------------------------- wiring -------------------------------- */
function syncVisibility() {
  const mode = ($('input[name="mode"]:checked') || {}).value || 'both';
  $('#field-port-direct').classList.toggle('hidden', !(mode === 'direct' || mode === 'both'));
  $('#field-port-warp').classList.toggle('hidden',   !(mode === 'warp'   || mode === 'both'));
  $('#field-ss-port').classList.toggle('hidden', !$('#ss-enabled').checked);
  $('#field-sni-custom').classList.toggle('hidden', $('#sni').value !== '__custom__');
}

function init() {
  $$('input[name="mode"]').forEach(r => r.addEventListener('change', syncVisibility));
  $('#ss-enabled').addEventListener('change', syncVisibility);
  $('#sni').addEventListener('change', syncVisibility);
  syncVisibility();

  $('#gen-form').addEventListener('submit', e => {
    e.preventDefault();
    const f = readForm();
    const err = $('#form-error');
    err.textContent = '';

    if (!isIPv4(f.serverIp)) { err.textContent = 'آی‌پی سرور معتبر نیست (نمونه: 203.0.113.10).'; $('#server-ip').focus(); return; }
    if (!f.sni)              { err.textContent = 'دامنه‌ی استتار (SNI) را انتخاب یا وارد کن.'; return; }
    if (f.mode !== 'warp'   && (f.portDirect < 1 || f.portDirect > 65535)) { err.textContent = 'پورت مستقیم نامعتبر است.'; return; }
    if (f.mode !== 'direct' && (f.portWarp   < 1 || f.portWarp   > 65535)) { err.textContent = 'پورت WARP نامعتبر است.'; return; }
    if (f.mode === 'both'   && f.portDirect === f.portWarp) { err.textContent = 'پورت مستقیم و WARP باید متفاوت باشند.'; return; }
    if (f.ss.enabled) {
      if (f.ss.port < 1 || f.ss.port > 65535) { err.textContent = 'پورت Shadowsocks نامعتبر است.'; return; }
      const clash = (f.mode !== 'warp' && f.ss.port === f.portDirect) || (f.mode !== 'direct' && f.ss.port === f.portWarp);
      if (clash) { err.textContent = 'پورت Shadowsocks با پورت‌های دیگر تداخل دارد.'; return; }
    }

    const btn = $('#gen-btn');
    btn.disabled = true;
    btn.classList.add('busy');
    // اجازه بده UI یک frame رفرش شود، بعد محاسبه‌ی سنگین (QR ها)
    requestAnimationFrame(() => {
      try {
        const out = generate(f);
        render(out);
      } catch (ex) {
        err.textContent = 'خطا در ساخت کانفیگ: ' + (ex && ex.message ? ex.message : ex);
        console.error(ex);
      } finally {
        btn.disabled = false;
        btn.classList.remove('busy');
      }
    });
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
