/* ==========================================================================
 *  KIAN V2Ray — منطق صفحه‌ی تعاملی  (همه‌چیز سمت مرورگر؛ هیچ داده‌ای ارسال نمی‌شود)
 *  این فایل کانفیگ Xray و users.json و payload را می‌سازد و دستور نصب را تولید می‌کند.
 *  خروجی دقیقاً با install.sh و scripts/watchdog.sh هماهنگ است.
 *  وابستگی‌ها (لوکال، بدون CDN):  vendor/nacl.min.js  +  vendor/qrcode.min.js
 * ======================================================================== */
'use strict';

const RAW_BASE = 'https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main';
const WARP_PORT = 40000;
const SUB_PORT = 8080;          // سرویس سبک Subscription روی سرور کاربر
const SS_METHOD = 'chacha20-ietf-poly1305';
const GIB = 1073741824;
const BASE_PORT = 8443;        // پورت‌ها از اینجا به‌صورت خودکار اضافه می‌شوند

// دامنه‌های استتار (SNI) — TLS 1.3 و معمولاً در ایران در دسترس‌اند (yahoo حذف شد)
const SNI_POOL = [
  // تست‌شده روی شبکهٔ ایران (TLS1.3، در دسترس) — مه ۲۰۲۶
  'www.icloud.com',
  'cloudflare.com',
  's3.amazonaws.com',
  'fonts.gstatic.com',
  'speedtest.net',
  'www.amazon.com',
];

// انتخاب n دامنهٔ متمایز و تصادفی از لیست بالا
function pickSNIs(n) {
  const pool = SNI_POOL.slice();
  for (let i = pool.length - 1; i > 0; i--) {       // Fisher–Yates
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  return pool.slice(0, Math.max(1, Math.min(n, pool.length)));
}

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
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');}
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
// o.profiles: [{ tag, port, sni, channel:'direct'|'warp' }]
function buildConfig(o) {
  const clients = o.users.map(u => ({ id: u.id, email: u.email, flow: 'xtls-rprx-vision' }));
  const anyWarp = o.profiles.some(p => p.channel === 'warp');

  const realityInbound = (p) => ({
    listen: '0.0.0.0',
    port: p.port,
    protocol: 'vless',
    tag: p.tag,
    settings: { clients: clients.map(c => ({ ...c })), decryption: 'none' },
    streamSettings: {
      network: 'tcp',
      security: 'reality',
      realitySettings: {
        show: false,
        dest: `${p.sni}:443`,
        xver: 0,
        serverNames: [p.sni],
        privateKey: o.reality.privateKey,
        shortIds: [o.reality.shortId],
      },
    },
    sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'] },
  });

  const apiPort = o.apiPort || 10085;
  const inbounds = [
    { listen: '127.0.0.1', port: apiPort, protocol: 'dokodemo-door', settings: { address: '127.0.0.1' }, tag: 'api' },
  ];
  o.profiles.forEach(p => inbounds.push(realityInbound(p)));
  if (o.ss.enabled) {
    inbounds.push({
      listen: '0.0.0.0',
      port: o.ss.port,
      protocol: 'shadowsocks',
      tag: 'shadowsocks',
      // chacha20-ietf-poly1305 = تک‌کاربره: method + password (نه clients[])
      settings: { method: SS_METHOD, password: o.ss.password, network: 'tcp,udp' },
      sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'] },
    });
  }

  const outbounds = [{ tag: 'direct', protocol: 'freedom', settings: { domainStrategy: 'UseIP' } }];
  if (anyWarp) outbounds.push({ tag: 'warp', protocol: 'socks', settings: { servers: [{ address: '127.0.0.1', port: WARP_PORT }] } });
  outbounds.push({ tag: 'block', protocol: 'blackhole', settings: {} });

  const directTags = o.profiles.filter(p => p.channel === 'direct').map(p => p.tag);
  const warpTags   = o.profiles.filter(p => p.channel === 'warp').map(p => p.tag);
  // اگر خروجی warp وجود نداشته باشد، Shadowsocks باید از direct برود
  const ssOut = (directTags.length || !anyWarp) ? 'direct' : 'warp';

  const rules = [
    { type: 'field', inboundTag: ['api'], outboundTag: 'api' },
    { type: 'field', ip: ['geoip:private'], outboundTag: 'block' },
  ];
  if (warpTags.length)   rules.push({ type: 'field', inboundTag: warpTags,   outboundTag: 'warp' });
  if (directTags.length) rules.push({ type: 'field', inboundTag: directTags, outboundTag: 'direct' });
  if (o.ss.enabled)      rules.push({ type: 'field', inboundTag: ['shadowsocks'], outboundTag: ssOut });

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
  const sniMode   = ($('#sni-mode') && $('#sni-mode').value) || 'auto';   // auto | manual
  const manualSni = ($('#sni').value === '__custom__' ? $('#sni-custom').value.trim() : $('#sni').value).trim();
  const sniCount  = parseInt(($('#sni-count') && $('#sni-count').value) || '2', 10);
  return {
    serverIp:  $('#server-ip').value.trim(),
    mode,
    sniMode,
    manualSni,
    sniCount:  Math.max(1, Math.min(5, sniCount || 2)),
    basePort:  Math.max(1, Math.min(65535, parseInt(($('#base-port') && $('#base-port').value) || BASE_PORT, 10) || BASE_PORT)),
    numUsers:  Math.min(50, Math.max(1, parseInt($('#num-users').value, 10) || 1)),
    prefix:   ($('#user-prefix').value.trim() || 'user').replace(/[^a-zA-Z0-9_-]/g, ''),
    quotaGb:  parseInt($('#quota').value, 10),        // 0 = نامحدود
    days:     parseInt($('#days').value, 10),         // 0 = دائمی
    ss: {
      enabled: ssEnabled,
      port: parseInt($('#ss-port').value, 10) || 8388,
      password: '',
    },
  };
}

const CH_LABEL = { direct: 'سریع', warp: 'WARP' };

/* ------------------------------ generate ------------------------------- */
function generate(f) {
  const reality = genReality();
  if (f.mode === 'nosni') f.ss.enabled = true;       // بدون SNI = فقط Shadowsocks
  if (f.ss.enabled) f.ss.password = genPassword();

  // کانال‌های Reality بر اساس حالت (nosni هیچ کانال Reality ندارد)
  const channels = f.mode === 'both' ? ['direct', 'warp']
                 : f.mode === 'nosni' ? []
                 : [f.mode];

  // لیست SNI فقط وقتی Reality داریم
  const sniList = channels.length === 0 ? []
                : (f.sniMode === 'manual' && f.manualSni) ? [f.manualSni]
                : pickSNIs(f.sniCount);

  // ساخت پروفایل‌ها: برای هر (کانال × SNI) یک inbound با پورت خودکار
  const profiles = [];
  let port = f.basePort || BASE_PORT;
  const nextPort = () => { while (f.ss.enabled && port === f.ss.port) port++; return port++; };
  channels.forEach(ch => {
    sniList.forEach((sni, i) => {
      profiles.push({ tag: `reality-${ch}-${i + 1}`, port: nextPort(), sni, channel: ch });
    });
  });

  // کاربرها
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

  // پورت API تصادفی (مشکل ۰.۱): جلوگیری از تداخل با 3x-ui/Marzban که روی 10085 + network=host هستند
  const usedPorts = profiles.map(p => p.port);
  if (f.ss.enabled) usedPorts.push(f.ss.port);
  let apiPort;
  do { apiPort = 20000 + Math.floor(Math.random() * 30000); } while (usedPorts.includes(apiPort));

  const config = buildConfig({ profiles, reality, users, ss: f.ss, apiPort });

  // لینک‌ها: برای هر کاربر، یک لینک به‌ازای هر پروفایل + یک لینک Subscription
  const links = [];
  const subTokens = {};   // email → token (به payload می‌رود تا سرور فایل sub را بسازد)
  const perUser = users.map(u => {
    const local = u.email.split('@')[0];
    const items = profiles.map(p => {
      const link = vlessLink({
        uuid: u.id, ip: f.serverIp, port: p.port, sni: p.sni,
        pubkey: reality.publicKey, shortId: reality.shortId,
        label: `KIAN-${local}-${CH_LABEL[p.channel]}-${p.sni}`,
      });
      links.push(link);
      return { channel: p.channel, sni: p.sni, port: p.port, link };
    });
    // توکن Subscription تصادفی (مثل UUID — همان‌جا در مرورگر ساخته می‌شود)
    const token = randHex(16);
    subTokens[u.email] = token;
    const subUrl = `http://${f.serverIp}:${SUB_PORT}/sub/${token}`;
    return { email: u.email, local, items, subUrl };
  });

  let ssOut = null;
  if (f.ss.enabled) {
    ssOut = ssLink({ ip: f.serverIp, port: f.ss.port, password: f.ss.password, label: 'KIAN-Shadowsocks' });
    links.push(ssOut);
  }

  const ports = profiles.map(p => p.port);
  if (f.ss.enabled) ports.push(f.ss.port);

  const payload = {
    warp_needed: channels.includes('warp'),
    server_ip: f.serverIp,
    config_b64: utf8ToB64(JSON.stringify(config)),
    users_b64:  utf8ToB64(JSON.stringify({ users })),
    links,
    ports,
    api_port: apiPort,
    sub_port: SUB_PORT,
    sub_tokens: subTokens,
  };
  const payloadB64 = utf8ToB64(JSON.stringify(payload));

  const installCmd =
    `export KIAN_PAYLOAD='${payloadB64}'\n` +
    `curl -fsSL ${RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh`;

  return { f, reality, users, perUser, ssOut, ports, profiles, sniList, config, payloadB64, installCmd };
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
  const isNoSni = out.f.mode === 'nosni';
  const modeLabel  = { direct: 'سریع', warp: 'WARP', both: 'سریع + WARP', nosni: 'بدون SNI' }[out.f.mode];
  const quotaLabel = out.f.quotaGb > 0 ? `${out.f.quotaGb}GB` : 'نامحدود';
  const daysLabel  = out.f.days > 0 ? `${out.f.days} روز` : 'دائمی';
  const linksPerUser = out.profiles.length;
  if (isNoSni) {
    step3.innerHTML = `<div class="panel-title">۳) کانفیگ بدون SNI (Shadowsocks)</div>
      <div class="risk">⚠️ این کانفیگ <b>استتار TLS ندارد</b>. ساده و سریع است، ولی چون شبیه ترافیک معمولی نیست،
      ممکن است به‌مرور شناسایی شود و <b>آی‌پی سرورت فیلتر شود</b>. توصیه: این حالت را <b>فقط برای خودت</b> استفاده کن، نه پخش عمومی.
      اگر آی‌پی فیلتر شد، یک سرور/آی‌پی دیگر بگیر یا از حالت «سریع + WARP» (با SNI) استفاده کن.</div>`;
  } else {
    step3.innerHTML = `<div class="panel-title">۳) کانفیگ کاربرها (${out.users.length} کاربر × ${linksPerUser} لینک)</div>
      <p class="muted small">برای هر کاربر چند لینک با SNI و پورت‌های مختلف ساخته شد. توی اپ همه را وارد کن و <b>هرکدام وصل شد همان را استفاده کن</b> (بقیه پشتیبان‌اند).</p>
      <div class="badges">
        <span class="badge">${modeLabel}</span>
        <span class="badge">حجم: ${quotaLabel}</span>
        <span class="badge">اعتبار: ${daysLabel}</span>
        <span class="badge">${out.sniList.length} دامنه (SNI)</span>
      </div>`;
  }
  if (out.profiles.length) {
    out.perUser.forEach(u => {
      const card = document.createElement('div');
      card.className = 'usercard';
      card.innerHTML = `<div class="usercard-title">👤 ${u.local}</div>`;
      // لینک Subscription (توصیه‌شده): یک لینک که همهٔ کانفیگ‌ها را می‌آورد و خودکار آپدیت می‌شود
      if (u.subUrl) {
        const subRow = linkRow('⭐ لینک Subscription (این یکی را در v2rayNG بزن — همه کانفیگ‌ها خودکار می‌آیند)', u.subUrl);
        card.appendChild(subRow);
        const hint = document.createElement('div');
        hint.className = 'sub-hint';
        hint.textContent = 'به‌جای افزودن تک‌تک کانفیگ‌های زیر، فقط همین لینک را در بخش Subscription کلاینت وارد کن.';
        card.appendChild(hint);
      }
      u.items.forEach(it => {
        const tag = it.channel === 'warp' ? 'WARP — همه‌چیز باز' : 'سریع — Direct';
        card.appendChild(linkRow(`${tag} · ${it.sni} · پورت ${it.port}`, it.link));
      });
      step3.appendChild(card);
    });
  }
  if (out.ssOut) {
    const card = document.createElement('div');
    card.className = 'usercard';
    card.innerHTML = `<div class="usercard-title">🧩 Shadowsocks${isNoSni ? '' : ' (مشترک)'}</div>`;
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
  const noSni = mode === 'nosni';
  const sniBlock = $('#sni-block');
  if (sniBlock) sniBlock.classList.toggle('hidden', noSni);   // در حالت بدون SNI کل بخش SNI پنهان

  const sniMode = ($('#sni-mode') && $('#sni-mode').value) || 'auto';
  const isManual = sniMode === 'manual';
  $('#field-sni-count').classList.toggle('hidden', noSni || isManual);
  $('#field-sni').classList.toggle('hidden', noSni || !isManual);
  $('#field-sni-custom').classList.toggle('hidden', noSni || !(isManual && $('#sni').value === '__custom__'));
  $('#field-ss-port').classList.toggle('hidden', !$('#ss-enabled').checked);
}

function initTabs() {
  const tabs = $$('#tabs .tab');
  const panels = $$('.panel-tab');
  function switchTab(name) {
    tabs.forEach(x => x.classList.toggle('active', x.dataset.tab === name));
    panels.forEach(p => p.classList.toggle('active', p.dataset.panel === name));
    try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (e) {}
  }
  tabs.forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));
  // کارت‌های راهنما (بار اول / قبلاً نصب کردم / لینک کاربر)
  $$('.guide-card').forEach(c => c.addEventListener('click', () => {
    const go = c.dataset.go;
    if (go === 'gen-stay') {  // «بار اولمه» — همین‌جا بمان، فقط به فرم اسکرول کن
      try { $('#gen-form')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
      return;
    }
    switchTab(go);
    // اگر مقصد «مدیریت» است، عملیات مناسب را بر اساس آیکون کارت از پیش انتخاب کن
    const sel = $('#mg-action');
    if (go === 'manage' && sel) {
      const ic = c.querySelector('.guide-ic')?.textContent || '';
      sel.value = ic.includes('🔗') ? 'sub' : ic.includes('❌') ? 'uninstall' : 'add';
      sel.dispatchEvent(new Event('change'));
    }
  }));
}

function initStepper() {
  const input = $('#num-users');
  $$('.step-btn').forEach(b => b.addEventListener('click', () => {
    const step = parseInt(b.dataset.step, 10) || 0;
    let v = (parseInt(input.value, 10) || 1) + step;
    v = Math.min(50, Math.max(1, v));
    input.value = v;
  }));
}

function initAdvanced() {
  const tg = $('#adv-toggle');
  const body = $('#adv-body');
  tg.addEventListener('click', () => {
    const open = body.classList.toggle('hidden') === false;
    tg.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
}

function initCopyTrc20() {
  const btn = $('#copy-trc20');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const txt = $('#trc20').textContent.trim();
    try { await navigator.clipboard.writeText(txt); }
    catch (e) {
      const ta = document.createElement('textarea');
      ta.value = txt; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (_) {}
      ta.remove();
    }
    const prev = btn.innerHTML;
    btn.classList.add('ok'); btn.innerHTML = '<span>کپی شد ✓</span>';
    setTimeout(() => { btn.innerHTML = prev; btn.classList.remove('ok'); }, 1400);
  });
}

function initManage() {
  const action = $('#mg-action');
  if (!action) return;
  const nameEl = $('#mg-name'), gbEl = $('#mg-gb'), daysEl = $('#mg-days'), out = $('#mg-out');
  const nameF = $('#mg-name-f'), gbF = $('#mg-gb-f'), daysF = $('#mg-days-f');

  function recompute() {
    const a = action.value;
    const name = (nameEl.value.trim() || '<نام>').replace(/[^a-zA-Z0-9_<>-]/g, '');
    const gb = Math.max(0, parseInt(gbEl.value, 10) || 0);
    const days = Math.max(0, parseInt(daysEl.value, 10) || 0);

    // نمایش فیلدهای مرتبط با هر عملیات
    const need = {
      add:    { name: true,  gb: true,  days: true },
      remove: { name: true,  gb: false, days: false },
      renew:  { name: true,  gb: false, days: true },
      reset:  { name: true,  gb: true,  days: false },
      configs:{ name: true,  gb: false, days: false },
      sub:    { name: true,  gb: false, days: false },
      status: { name: false, gb: false, days: false },
      users:  { name: false, gb: false, days: false },
      update: { name: false, gb: false, days: false },
      uninstall: { name: false, gb: false, days: false },
    }[a] || { name: false, gb: false, days: false };
    nameF.classList.toggle('hidden', !need.name);
    gbF.classList.toggle('hidden', !need.gb);
    daysF.classList.toggle('hidden', !need.days);

    let cmd = '';
    if (a === 'add')      cmd = `kian-v2ray add ${name} ${gb} ${days} && kian-v2ray sub ${name}`;
    else if (a === 'remove') cmd = `kian-v2ray remove ${name}`;
    else if (a === 'renew')  cmd = `kian-v2ray renew ${name} ${days}`;
    else if (a === 'reset')  cmd = `kian-v2ray reset ${name} ${gb}`;
    else if (a === 'configs')cmd = `kian-v2ray configs ${name}`;
    else if (a === 'sub')    cmd = `kian-v2ray sub ${name}`;
    else if (a === 'status') cmd = `kian-v2ray status`;
    else if (a === 'users')  cmd = `kian-v2ray users`;
    else if (a === 'update') cmd = `kian-v2ray update`;
    else if (a === 'uninstall') cmd = `kian-v2ray uninstall`;
    out.textContent = cmd;
  }

  [action, nameEl, gbEl, daysEl].forEach(el => {
    el.addEventListener('input', recompute);
    el.addEventListener('change', recompute);
  });
  recompute();

  const row = $('#mg-copy-row');
  if (row) row.appendChild(copyBtn('کپی دستور', () => out.textContent));
}

function init() {
  initTabs();
  initStepper();
  initAdvanced();
  initCopyTrc20();
  initManage();

  $$('input[name="mode"]').forEach(r => r.addEventListener('change', syncVisibility));
  $('#ss-enabled').addEventListener('change', syncVisibility);
  $('#sni-mode') && $('#sni-mode').addEventListener('change', syncVisibility);
  $('#sni') && $('#sni').addEventListener('change', syncVisibility);
  syncVisibility();

  $('#gen-form').addEventListener('submit', e => {
    e.preventDefault();
    const f = readForm();
    const err = $('#form-error');
    err.textContent = '';

    if (!isIPv4(f.serverIp)) { err.textContent = 'آی‌پی سرور معتبر نیست (نمونه: 203.0.113.10).'; $('#server-ip').focus(); return; }
    if (f.sniMode === 'manual' && !f.manualSni) { err.textContent = 'یک دامنهٔ استتار (SNI) انتخاب یا وارد کن.'; return; }
    if (f.basePort > 65500) { err.textContent = 'پورت پایه خیلی بالاست؛ عددی کمتر (مثلاً 8443 یا 9443) انتخاب کن.'; return; }
    if (f.ss.enabled && (f.ss.port < 1 || f.ss.port > 65535)) { err.textContent = 'پورت Shadowsocks نامعتبر است.'; return; }

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
