/* ==========================================================================
 *  KIAN V2Ray — منطق صفحه‌ی تعاملی  (همه‌چیز سمت مرورگر؛ هیچ داده‌ای ارسال نمی‌شود)
 *  این فایل کانفیگ Xray و users.json و payload را می‌سازد و دستور نصب را تولید می‌کند.
 *  خروجی دقیقاً با install.sh و scripts/watchdog.sh هماهنگ است.
 *  وابستگی‌ها (لوکال، بدون CDN):  vendor/nacl.min.js  +  vendor/qrcode.min.js
 * ======================================================================== */
'use strict';

const RAW_BASE = 'https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main';
const WARP_PORT = 40000;
// Only these geo-blocked services route through WARP (they reject Iranian /
// datacenter IPs). Everything else goes DIRECT at full server speed. Plain
// `domain:` rules — no geosite.dat dependency.
const WARP_DOMAINS = [
  'domain:openai.com', 'domain:chatgpt.com', 'domain:oaistatic.com',
  'domain:oaiusercontent.com', 'domain:anthropic.com', 'domain:claude.ai',
  'domain:gemini.google.com', 'domain:aistudio.google.com',
  'domain:makersuite.google.com', 'domain:ai.google.dev',
  'domain:generativelanguage.googleapis.com', 'domain:x.ai', 'domain:grok.com',
  'domain:perplexity.ai',
];
const SUB_PORTS = [80, 8888, 2086]; // سرویس Subscription روی چند پورت همزمان اجرا می‌شود — هر کدام از بیرون باز بود، همان کار می‌کند. کاربر کاری نمی‌کند.
// واسطهٔ Gist (Cloudflare Worker): سرور کاربر به این endpoint POST می‌زند تا secret gist
// ساخته/آپدیت شود. توکن گیت‌هاب فقط در env-var همان Worker (سمت ما) ذخیره است،
// هرگز در ریپوی پابلیک یا روی سرور کاربر دیده نمی‌شود.
const GIST_PROXY = 'https://kian-sub.kian-mhrv.workers.dev'; // Worker واسط — سرور کاربر اینجا POST می‌زند تا لینک HTTPS Gist بگیرد
const SS_METHOD = 'chacha20-ietf-poly1305';
const GIB = 1073741824;
const BASE_PORT = 8443;        // پورت‌ها از اینجا به‌صورت خودکار اضافه می‌شوند

// فاز ۳: پروتکل‌های TLS پشت دامنه (Caddy روی :443 → Xray داخلی). هر کدام یک path یکتا دارد.
// internalBase: پورت داخلی localhost که Caddy به آن reverse proxy می‌کند (از 20810 به بعد خودکار).
const TLS_PROTOS = {
  'vless-ws':   { proto: 'vless',  net: 'ws',          label: 'VLESS-WS',   note: 'پایدارترین برای عبور از DPI و CDN' },
  'vmess-ws':   { proto: 'vmess',  net: 'ws',          label: 'VMess-WS',   note: 'سازگاری بالا با کلاینت‌های قدیمی' },
  'vless-grpc': { proto: 'vless',  net: 'grpc',        label: 'VLESS-gRPC', note: 'مالتی‌پلکس، خوب روی شبکه‌های پرتاخیر' },
  'vmess-grpc': { proto: 'vmess',  net: 'grpc',        label: 'VMess-gRPC', note: 'gRPC با VMess' },
  'trojan-ws':  { proto: 'trojan', net: 'ws',          label: 'Trojan-WS',  note: 'شبیه ترافیک HTTPS معمولی' },
  'vless-httpupgrade': { proto: 'vless', net: 'httpupgrade', label: 'VLESS-HTTPUpgrade', note: 'سبک‌تر از WS، عبور خوب از پراکسی‌ها' },
  'vmess-httpupgrade': { proto: 'vmess', net: 'httpupgrade', label: 'VMess-HTTPUpgrade', note: 'HTTPUpgrade با VMess' },
  'vless-xhttp': { proto: 'vless', net: 'xhttp', label: 'VLESS-XHTTP', note: 'جدید — مقاوم‌ترین در برابر DPI، عالی روی CDN' },
};

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

// Install console language follows the page language (same key as i18n.js).
// Default to English so an English visitor gets an English install.
function _installLang() {
  try {
    const l = localStorage.getItem('kv2ray_lang');
    return l === 'fa' ? 'fa' : 'en';
  } catch (_) { return 'en'; }
}

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
// IPv6 (phase 1.5): accept full/compressed forms incl. an embedded IPv4 tail.
function isIPv6(s) {
  s = String(s).trim();
  if (s.indexOf(':') === -1) return false;
  return /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|([0-9a-fA-F]{1,4}:){1,4}:((\d{1,3}\.){3}\d{1,3}))$/.test(s);
}
function isServerAddr(s) { return isIPv4(s) || isIPv6(s); }
// In a URI authority an IPv6 literal must be bracketed: [2001:db8::1]:443.
function hostForUri(ip) { return isIPv6(ip) ? `[${ip}]` : ip; }
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
  const tlsWantsWarp = !!(o.tls && o.tls.enabled && o.tls.domain && o.tls.channel === 'warp' && (o.tlsProfiles || []).length);
  const anyWarp = o.profiles.some(p => p.channel === 'warp') || tlsWantsWarp;

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
    sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'], routeOnly: true },
  });

  const apiPort = o.apiPort || 10085;
  const inbounds = [
    { listen: '127.0.0.1', port: apiPort, protocol: 'dokodemo-door', settings: { address: '127.0.0.1' }, tag: 'api' },
  ];
  o.profiles.forEach(p => inbounds.push(realityInbound(p)));

  // فاز ۳: inboundهای TLS (پشت Caddy روی :443). هر کدام روی localhost با یک path یکتا.
  const tlsItems = (o.tls && o.tls.enabled && o.tls.domain) ? (o.tlsProfiles || []) : [];
  tlsItems.forEach(t => {
    const stream = { network: t.net, security: 'none' };
    if (t.net === 'ws')          stream.wsSettings = { path: t.path };
    else if (t.net === 'grpc')   stream.grpcSettings = { serviceName: t.path.replace(/^\//, '') };
    else if (t.net === 'httpupgrade') stream.httpupgradeSettings = { path: t.path };
    else if (t.net === 'xhttp')  stream.xhttpSettings = { mode: 'auto', path: t.path };
    let settings;
    if (t.proto === 'vless')      settings = { clients: o.users.map(u => ({ id: u.id, email: u.email })), decryption: 'none' };
    else if (t.proto === 'vmess') settings = { clients: o.users.map(u => ({ id: u.id, email: u.email })) };
    else if (t.proto === 'trojan')settings = { clients: o.users.map(u => ({ password: u.id, email: u.email })) };
    inbounds.push({
      listen: '127.0.0.1', port: t.intPort, protocol: t.proto, tag: t.tag,
      settings, streamSettings: stream,
      sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'], routeOnly: true },
    });
  });
  if (o.ss.enabled) {
    inbounds.push({
      listen: '0.0.0.0',
      port: o.ss.port,
      protocol: 'shadowsocks',
      tag: 'shadowsocks',
      // chacha20-ietf-poly1305 = تک‌کاربره: method + password (نه clients[])
      settings: { method: SS_METHOD, password: o.ss.password, network: 'tcp,udp' },
      sniffing: { enabled: true, destOverride: ['http', 'tls', 'quic'], routeOnly: true },
    });
  }

  const outbounds = [{ tag: 'direct', protocol: 'freedom', settings: { domainStrategy: 'AsIs' } }];
  if (anyWarp) outbounds.push({ tag: 'warp', protocol: 'socks', settings: { servers: [{ address: '127.0.0.1', port: WARP_PORT }] } });
  outbounds.push({ tag: 'block', protocol: 'blackhole', settings: {} });

  // سرعت: همهٔ ترافیک پروکسی مستقیم می‌رود (سرعتِ کاملِ خطِ سرور، مثل Xray معمولی
  // و 3x-ui). فقط سرویس‌های مسدودِ منتخب (ابزارهای AI که IP ایران/دیتاسنتر را رد
  // می‌کنند) از WARP عبور می‌کنند.
  const allTags = o.profiles.map(p => p.tag);
  const tlsTags = tlsItems.map(t => t.tag);

  const rules = [
    { type: 'field', inboundTag: ['api'], outboundTag: 'api' },
    { type: 'field', ip: ['geoip:private'], outboundTag: 'block' },
  ];
  if (anyWarp)         rules.push({ type: 'field', domain: WARP_DOMAINS, outboundTag: 'warp' });
  if (allTags.length)  rules.push({ type: 'field', inboundTag: allTags, outboundTag: 'direct' });
  if (o.ss.enabled)    rules.push({ type: 'field', inboundTag: ['shadowsocks'], outboundTag: 'direct' });
  if (tlsTags.length)  rules.push({ type: 'field', inboundTag: tlsTags, outboundTag: 'direct' });

  return {
    log: { loglevel: 'warning', access: 'none', error: '/var/log/xray/error.log' },
    dns: { servers: ['1.1.1.1', '8.8.8.8'] },
    api: { tag: 'api', services: ['HandlerService', 'StatsService'] },
    stats: {},
    policy: {
      levels: { '0': { statsUserUplink: true, statsUserDownlink: true } },
      system: { statsInboundUplink: true, statsInboundDownlink: true },
    },
    inbounds,
    outbounds,
    routing: { domainStrategy: 'AsIs', rules },
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
    spx: '/',          // spiderX (Reality advanced 10.6): browser-like fallback probe path
    type: 'tcp',
  });
  return `vless://${uuid}@${hostForUri(ip)}:${port}?${q.toString()}#${encodeURIComponent(label)}`;
}
function ssLink({ ip, port, password, label }) {
  return `ss://${btoa(`${SS_METHOD}:${password}`)}@${hostForUri(ip)}:${port}#${encodeURIComponent(label)}`;
}

/* لینک‌های TLS (پشت دامنه، روی :443) */
function tlsVlessLink({ uuid, domain, net, path, label }) {
  const q = new URLSearchParams({ encryption: 'none', security: 'tls', sni: domain, fp: 'chrome', type: net, host: domain });
  if (net === 'ws' || net === 'httpupgrade') q.set('path', path);
  if (net === 'xhttp') { q.set('path', path); q.set('mode', 'auto'); }
  if (net === 'grpc') { q.set('serviceName', path.replace(/^\//, '')); q.set('mode', 'gun'); }
  return `vless://${uuid}@${domain}:443?${q.toString()}#${encodeURIComponent(label)}`;
}
function tlsTrojanLink({ uuid, domain, net, path, label }) {
  const q = new URLSearchParams({ security: 'tls', sni: domain, fp: 'chrome', type: net, host: domain });
  if (net === 'ws' || net === 'httpupgrade') q.set('path', path);
  if (net === 'grpc') { q.set('serviceName', path.replace(/^\//, '')); q.set('mode', 'gun'); }
  return `trojan://${uuid}@${domain}:443?${q.toString()}#${encodeURIComponent(label)}`;
}
function tlsVmessLink({ uuid, domain, net, path, label }) {
  // VMess = JSON بیس64شده (فرمت v2rayN)
  const v = {
    v: '2', ps: label, add: domain, port: '443', id: uuid, aid: '0', scy: 'auto',
    net: net === 'httpupgrade' ? 'httpupgrade' : net, type: 'none',
    host: domain, path: (net === 'grpc' ? path.replace(/^\//, '') : path),
    tls: 'tls', sni: domain, alpn: '', fp: 'chrome',
  };
  if (net === 'grpc') { v.path = path.replace(/^\//, ''); }
  return 'vmess://' + btoa(unescape(encodeURIComponent(JSON.stringify(v))));
}
function tlsLink(item, user, domain) {
  const base = { uuid: user.id, domain, net: TLS_PROTOS[item.kind].net, path: item.path, label: item.label };
  const proto = TLS_PROTOS[item.kind].proto;
  if (proto === 'vmess')  return tlsVmessLink(base);
  if (proto === 'trojan') return tlsTrojanLink(base);
  return tlsVlessLink(base);
}
function isDomain(d) {
  return typeof d === 'string' && /^(?=.{4,253}$)([a-z0-9](-?[a-z0-9])*\.)+[a-z]{2,}$/.test(d);
}
function tlsWantsWarp(f, tlsProfiles) {
  return !!(f.tls && f.tls.enabled && f.tls.channel === 'warp' && tlsProfiles && tlsProfiles.length);
}
// Caddyfile: TLS واقعی روی :443، path-based reverse_proxy به Xray داخلی
function buildCaddyfile(domain, tlsProfiles) {
  const lines = [];
  lines.push(`${domain} {`);

  tlsProfiles.forEach(t => {
    if (t.net === 'grpc') {
      const svc = t.path.replace(/^\//, '');
      lines.push(`\t@${t.tag} {`);
      lines.push(`\t\tpath /${svc}/*`);
      lines.push(`\t}`);
      lines.push(`\thandle @${t.tag} {`);
      lines.push(`\t\treverse_proxy h2c://127.0.0.1:${t.intPort}`);
      lines.push(`\t}`);
    } else if (t.net === 'xhttp') {
      // XHTTP uses a path PREFIX (sub-requests under it); proxy with h2c so
      // both HTTP/1.1 and H2 streams reach Xray.
      lines.push(`\t@${t.tag} {`);
      lines.push(`\t\tpath ${t.path} ${t.path}/*`);
      lines.push(`\t}`);
      lines.push(`\thandle @${t.tag} {`);
      lines.push(`\t\treverse_proxy h2c://127.0.0.1:${t.intPort}`);
      lines.push(`\t}`);
    } else {
      lines.push(`\t@${t.tag} {`);
      lines.push(`\t\tpath ${t.path}`);
      lines.push(`\t}`);
      lines.push(`\thandle @${t.tag} {`);
      lines.push(`\t\treverse_proxy 127.0.0.1:${t.intPort}`);
      lines.push(`\t}`);
    }
  });
  // صفحهٔ طعمه برای بقیهٔ مسیرها (شبیه یک سایت معمولی)
  lines.push(`\thandle {`);
  lines.push(`\t\trespond "It works!" 200`);
  lines.push(`\t}`);
  lines.push(`}`);
  return lines.join('\n');
}

/* --------------------------- read the form ----------------------------- */
function readForm() {
  // حالتِ اتصال حذف شد — همیشه از WARP عبور می‌کند (غیرقابل‌انتخاب).
  const mode      = 'warp';
  const hasDomain = !!($('#tls-enabled')?.checked && $('#tls-domain')?.value.trim());
  const ssEnabled = hasDomain ? ($('#ss-enabled') && $('#ss-enabled').checked) : true;
  const sniMode   = ($('#sni-mode') && $('#sni-mode').value) || 'auto';   // auto | manual
  const manualSni = ($('#sni').value === '__custom__' ? $('#sni-custom').value.trim() : $('#sni').value).trim();
  const sniCount  = parseInt(($('#sni-count') && $('#sni-count').value) || '2', 10);
  return {
    serverIp:  $('#server-ip').value.trim(),
    mode,
    sniMode,
    manualSni,
    sniCount:  Math.max(1, Math.min(5, sniCount || 2)),
    basePort:  parseInt(($('#base-port') && $('#base-port').value), 10) || 0,   // 0 = خودکار (پول معروف)
    numUsers:  Math.min(50, Math.max(1, parseInt($('#num-users').value, 10) || 1)),
    prefix:   ($('#user-prefix').value.trim()).replace(/[^a-zA-Z0-9_-]/g, ''),
    quotaGb:  parseInt($('#quota').value, 10),        // 0 = نامحدود
    days:     parseInt($('#days').value, 10),         // 0 = دائمی
    panelUser: (($('#panel-user') && $('#panel-user').value.trim()) || 'admin').replace(/[^a-zA-Z0-9_-]/g, '') || 'admin',
    panelPass: ($('#panel-pass') && $('#panel-pass').value) || '',
    ss: {
      enabled: ssEnabled,
      port: parseInt(($('#ss-port') && $('#ss-port').value) || '8388', 10) || 8388,
      password: '',
    },
    tls: {
      enabled: !!($('#tls-enabled') && $('#tls-enabled').checked),
      domain: ($('#tls-domain') && $('#tls-domain').value.trim().toLowerCase()) || '',
      channel: 'warp',   // همیشه از WARP — حالتِ مستقیم حذف شد
      protos: $$('input[name="tls-proto"]:checked').map(el => el.value),
    },
    // پروتکل‌های اضافه روی sing-box (بدون دامنه: خودکار همه؛ با دامنه: انتخابِ کاربر)
    extraProtocols: hasDomain
      ? $$('input[name="extra-proto"]:checked').map(el => el.value)
      : ['hysteria2', 'tuic'],
  };
}

/* ------------------------------ generate ------------------------------- */
async function generate(f) {
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
  // اگر کاربر basePort سفارشی نزده، اول از پورت‌های "تقریباً همیشه باز" استفاده می‌کنیم
  // (مثل 443، 2083، 8080، 2096 — تقریباً همهٔ پروایدرها باز می‌گذارند).
  // اگر TLS فعال است، 443 و 80 برای Caddy رزرو می‌شوند.
  const profiles = [];
  const userBasePort = f.basePort;  // 0 = خودکار
  const tlsReserves443 = !!(f.tls && f.tls.enabled && isDomain(f.tls.domain) && f.tls.protos.length);
  const wellKnownOpen = [443, 2083, 2087, 2096, 8080, 2052, 2086];
  const reservedByTls = tlsReserves443 ? [443, 80] : [];
  // اگر کاربر basePort سفارشی داده، فقط همان را استفاده کن (رفتار قدیمی)
  // وگرنه، اول پورت‌های معروف بازنشده، بعد از 8443 ادامه بده
  let portPool;
  if (userBasePort && userBasePort >= 1 && userBasePort <= 65500) {
    portPool = [];
    for (let p = userBasePort; p < userBasePort + 50; p++) portPool.push(p);
  } else {
    portPool = wellKnownOpen.filter(p => !reservedByTls.includes(p));
    for (let p = 8443; p < 8493; p++) portPool.push(p);
  }
  // پورت‌های ممنوع: ss و WARP و رزروشده توسط TLS
  const banned = new Set([WARP_PORT, ...reservedByTls]);
  if (f.ss.enabled) banned.add(f.ss.port);
  let portIdx = 0;
  const nextPort = () => {
    while (portIdx < portPool.length && banned.has(portPool[portIdx])) portIdx++;
    if (portIdx >= portPool.length) throw new Error('پورت کافی پیدا نشد — basePort را عوض کن');
    return portPool[portIdx++];
  };
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

  // فاز ۳: پروفایل‌های TLS (پشت دامنه). هر پروتکل یک پورت داخلی و path یکتا.
  const tlsEnabled = f.tls.enabled && isDomain(f.tls.domain) && f.tls.protos.length > 0;
  const tlsProfiles = [];
  if (tlsEnabled) {
    // پورت داخلی TLS باید همیشه بعد از همهٔ پورت‌های reality و ss باشد تا تداخل نداشته باشد
    const realityMax = profiles.length ? Math.max(...profiles.map(p => p.port)) : (f.basePort || BASE_PORT);
    const ssMax = f.ss.enabled ? f.ss.port : 0;
    const safeStart = Math.max(20810, realityMax + 100, ssMax + 100);
    let ip2 = safeStart;
    const rnd = Math.random().toString(36).slice(2, 8);
    f.tls.protos.forEach((kind, i) => {
      if (!TLS_PROTOS[kind]) return;
      const net = TLS_PROTOS[kind].net;
      const path = `/${rnd}${i}${net === 'grpc' ? 'grpc' : ''}`;
      tlsProfiles.push({ kind, tag: `tls-${kind}`, intPort: ip2++, net, proto: TLS_PROTOS[kind].proto, path });
    });
  }

  // پورت API تصادفی (مشکل ۰.۱): جلوگیری از تداخل با 3x-ui/Marzban که روی 10085 + network=host هستند
  // و همچنین جلوگیری از تداخل با پورت‌های داخلی TLS (20810+) که روی localhost هستند
  const usedPorts = profiles.map(p => p.port);
  if (f.ss.enabled) usedPorts.push(f.ss.port);
  tlsProfiles.forEach(t => usedPorts.push(t.intPort));
  usedPorts.push(40000);  // WARP port
  let apiPort;
  do { apiPort = 20000 + Math.floor(Math.random() * 30000); } while (usedPorts.includes(apiPort));

  const config = buildConfig({ profiles, reality, users, ss: f.ss, apiPort,
    tls: f.tls, tlsProfiles });

  // لینک‌ها: برای هر کاربر، یک لینک به‌ازای هر پروفایل + یک لینک Subscription
  const links = [];
  const subTokens = {};   // email → token (به payload می‌رود تا سرور فایل sub را بسازد)
  const perUser = users.map(u => {
    const local = u.email.split('@')[0];
    const items = profiles.map(p => {
      const link = vlessLink({
        uuid: u.id, ip: f.serverIp, port: p.port, sni: p.sni,
        pubkey: reality.publicKey, shortId: reality.shortId,
        label: `${local}-reality-${p.port}`,
      });
      links.push(link);
      return { channel: p.channel, sni: p.sni, port: p.port, link };
    });
    // فاز ۳: لینک‌های TLS این کاربر
    const tlsLinks = tlsProfiles.map(t => {
      const label = `${local}-${TLS_PROTOS[t.kind].label.toLowerCase()}-443`;
      const link = tlsLink({ kind: t.kind, path: t.path, label }, u, f.tls.domain);
      links.push(link);
      return { kind: t.kind, label: TLS_PROTOS[t.kind].label, note: TLS_PROTOS[t.kind].note, link };
    });
    // توکن Subscription تصادفی (مثل UUID — همان‌جا در مرورگر ساخته می‌شود)
    const token = randHex(16);
    subTokens[u.email] = token;
    // محتوای sub این کاربر: لینک‌های Reality + TLS + SS مشترک (در ادامه اضافه می‌شود)
    const userLinks = [];
    items.forEach(it => userLinks.push(it.link));
    tlsLinks.forEach(t => userLinks.push(t.link));
    return { email: u.email, local, items, tlsLinks, subToken: token, userLinks };
  });

  let ssOut = null;
  if (f.ss.enabled) {
    // SS link is shared (same port/password) but labeled per-user so the
    // per-user subscription grep (#<name>-) picks it up: <name>-shadowsocks-<port>
    perUser.forEach(pu => {
      const ssLnk = ssLink({ ip: f.serverIp, port: f.ss.port, password: f.ss.password,
        label: `${pu.local}-shadowsocks-${f.ss.port}` });
      pu.userLinks.push(ssLnk);
      links.push(ssLnk);
    });
    ssOut = ssLink({ ip: f.serverIp, port: f.ss.port, password: f.ss.password, label: 'shadowsocks' });
  }

  // install_id یکتا برای این نصب (مرورگر می‌سازد، سرور همان را استفاده می‌کند → URL Gist یکسان می‌ماند)
  const installId = randHex(16);

  const ports = profiles.map(p => p.port);
  if (f.ss.enabled) ports.push(f.ss.port);

  const payload = {
    warp_needed: channels.includes('warp') || tlsWantsWarp(f, tlsProfiles),
    server_ip: f.serverIp,
    config_b64: utf8ToB64(JSON.stringify(config)),
    users_b64:  utf8ToB64(JSON.stringify({ users })),
    links,
    ports,
    api_port: apiPort,
    sub_port: SUB_PORTS,
    sub_tokens: subTokens,
    reality_pbk: reality.publicKey,   // کلید عمومی (راز نیست) — سرور لینک‌ها را از config نهایی می‌سازد
    reality_sid: reality.shortId,
    ss_password: f.ss.enabled ? f.ss.password : '',
    gist_proxy: GIST_PROXY,            // endpoint Worker: سرور POST می‌زند، Worker با توکن خصوصی gist می‌سازد
    install_id: installId,             // همان شناسه‌ای که مرورگر استفاده کرده تا URL Gist‌ها یکی بمانند
    tls_domain: tlsProfiles.length ? f.tls.domain : '',
    caddyfile_b64: tlsProfiles.length ? utf8ToB64(buildCaddyfile(f.tls.domain, tlsProfiles)) : '',
    extra_protocols: f.extraProtocols || [],   // Hysteria2/TUIC روی sing-box (انتخابِ کاربر)
    panel_admin_user: f.panelUser || 'admin',  // نام کاربری پنل مدیریت
    panel_admin_pass: f.panelPass || '',        // رمز پنل (خالی = تصادفی روی سرور)
    lang: _installLang(),                       // install console language = page language
  };
  const payloadB64 = utf8ToB64(JSON.stringify(payload));

  const installCmd =
    `export KIAN_PAYLOAD='${payloadB64}'\n` +
    `export KIAN_LANG='${_installLang()}'\n` +
    `curl -fsSL ${RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh`;

  // ساخت gist‌ها همین الان (مرورگر → Worker) تا لینک HTTPS Subscription به کاربر داده شود.
  // وقتی سرور بعداً نصب شود، با همان install_id و subTokenها به Worker POST می‌زند →
  // همان gist‌ها آپدیت می‌شوند (gist_id ثابت → URL یکسان می‌ماند).
  const items = {};
  perUser.forEach(pu => {
    const content = pu.userLinks.join('\n');
    items[pu.subToken] = utf8ToB64(content);   // base64 (فرمت v2rayNG)
  });
  let gistUrls = {};
  try {
    const resp = await fetch(GIST_PROXY + '/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ install_id: installId, items }),
    });
    const data = await resp.json();
    if (data && data.ok && data.urls) gistUrls = data.urls;
  } catch (e) {
    console.warn('gist proxy unreachable:', e);
  }
  perUser.forEach(pu => { pu.subUrl = gistUrls[pu.subToken] || ''; });

  return { f, reality, users, perUser, ssOut, ports, profiles, sniList, config, payloadB64, installCmd, gistOk: Object.keys(gistUrls).length > 0 };
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
  const titleSpan = document.createElement('span');
  titleSpan.className = 'linkrow-title';
  titleSpan.textContent = title;
  head.appendChild(titleSpan);
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
  const isNoSni = false;   // حالتِ بدون-SNI/سریع حذف شد
  const modeLabel  = 'WARP';
  const quotaLabel = out.f.quotaGb > 0 ? `${out.f.quotaGb}GB` : 'نامحدود';
  const daysLabel  = out.f.days > 0 ? `${out.f.days} روز` : 'دائمی';
  const linksPerUser = out.profiles.length;
  if (isNoSni) {
    step3.innerHTML = `<div class="panel-title">۳) کانفیگ بدون SNI (Shadowsocks)</div>
      <div class="risk">⚠️ این کانفیگ <b>استتار TLS ندارد</b>. ساده و سریع است، ولی چون شبیه ترافیک معمولی نیست،
      ممکن است به‌مرور شناسایی شود و <b>آی‌پی سرورت فیلتر شود</b>. توصیه: این حالت را <b>فقط برای خودت</b> استفاده کن، نه پخش عمومی.
      اگر آی‌پی فیلتر شد، یک سرور/آی‌پی دیگر بگیر یا از حالت «سریع + WARP» (با SNI) استفاده کن.</div>`;
  } else {
    step3.innerHTML = `<div class="panel-title">۳) لینک Subscription کاربرها (${out.users.length} کاربر)</div>
      <p class="muted small">برای هر کاربر <b>یک لینک Subscription</b> ساخته شد که همهٔ کانفیگ‌ها (SNIها و کانال‌های مختلف) را خودکار از سرور می‌آورد.</p>
      <div class="sub-port-note">⚠️ <b>خیلی مهم:</b> لینک Subscription روی <b>پورت ۸۰</b> سرورت کار می‌کند. این پورت باید روی سرورت <b>کاملاً خالی باشد</b> (نباید Caddy/Nginx/Apache یا وب‌سرور دیگری رویش باشد). اگر پورت ۸۰ اشغال باشد، نصب‌کننده یک پورت دیگر انتخاب می‌کند ولی ممکن است پروایدرت آن را از بیرون باز نگذارد. پورت ۸۰ استاندارد است و تقریباً همیشه از بیرون باز است.</div>
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
      if (u.subUrl) {
        // حالت موفق: همان لینک HTTPS که سرور هم خواهد داد
        const subHead = document.createElement('div');
        subHead.className = 'sub-head';
        subHead.innerHTML = '⭐ <b>لینک Subscription (HTTPS — یک‌بار برای همیشه)</b>';
        card.appendChild(subHead);
        card.appendChild(linkRow('این را در v2rayNG → Subscription وارد کن', u.subUrl));
        const hint = document.createElement('div');
        hint.className = 'sub-hint';
        hint.innerHTML = 'این لینک <b>روی همهٔ پروایدرها</b> و فایروال‌ها کار می‌کند. سرور بعد از نصب همین لینک را آپدیت می‌کند، پس همیشه به‌روز می‌ماند.';
        card.appendChild(hint);
      } else {
        // حالت ناموفق (Worker در دسترس نبود): کانفیگ‌های تکی به‌عنوان پشتیبان
        const warn = document.createElement('div');
        warn.className = 'sub-hint warn';
        warn.innerHTML = '⚠️ ساخت لینک Subscription موفق نبود (احتمالاً به اینترنت نیاز است). کانفیگ‌های تکی پایین را در v2rayNG وارد کن، یا بعد از نصب روی سرورت بزن: <code class="mono">kian-v2ray sub ' + u.local + '</code>';
        card.appendChild(warn);
        const sep = document.createElement('div');
        sep.className = 'config-sep';
        sep.textContent = 'کانفیگ‌های تکی (پشتیبان):';
        card.appendChild(sep);
        u.items.forEach(it => {
          card.appendChild(linkRow(`WARP · ${it.sni}`, it.link));
        });
        if (u.tlsLinks && u.tlsLinks.length) {
          const tlsSep = document.createElement('div');
          tlsSep.className = 'config-sep';
          tlsSep.textContent = 'کانفیگ‌های دامنه‌دار (TLS — روی :443):';
          card.appendChild(tlsSep);
          u.tlsLinks.forEach(t => card.appendChild(linkRow(`${t.label} — ${t.note}`, t.link)));
        }
      }
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

  // ---- مرحله ۴: پنل مدیریت وب ----
  const panelUrl = `http://${out.f.serverIp}:8443/app`;
  const step4 = document.createElement('div');
  step4.className = 'panel reveal';
  step4.innerHTML = `<div class="panel-title">۴) پنل مدیریت وب</div>
    <p class="muted">بعد از اتمام نصب، داشبورد مدیریت از این آدرس در دسترس است (ممکن است ۳-۵ دقیقه طول بکشد):</p>`;
  step4.appendChild(linkRow('آدرس پنل مدیریت', panelUrl));
  const credNote = document.createElement('div');
  credNote.className = 'callout';
  const pUser = out.f.panelUser || 'admin';
  const pPass = out.f.panelPass;
  credNote.innerHTML = pPass
    ? `🔑 <b>اطلاعات ورود:</b> نام کاربری <code class="mono">${pUser}</code> · رمز عبور: همانی که وارد کردید`
    : `🔑 <b>نام کاربری:</b> <code class="mono">${pUser}</code> · <b>رمز عبور:</b> تصادفی — بعد از نصب در ترمینال نمایش داده می‌شود، یا دستور <code class="mono">kian-panel.sh url</code> بزن`;
  step4.appendChild(credNote);
  box.appendChild(step4);

  $$('.reveal', box).forEach((el, i) => { el.style.animationDelay = `${i * 90}ms`; });
  box.classList.remove('hidden');
  if (typeof box.scrollIntoView === 'function') {
    try { box.scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) {}
  }
}

/* ------------------------------- wiring -------------------------------- */
function syncVisibility() {
  // حالتِ اتصال حذف شد — همیشه WARP. (دیگر noSni/سریع نداریم)
  const sniMode = ($('#sni-mode') && $('#sni-mode').value) || 'auto';
  const isManual = sniMode === 'manual';
  $('#field-sni-count').classList.toggle('hidden', isManual);
  $('#field-sni').classList.toggle('hidden', !isManual);
  $('#field-sni-custom').classList.toggle('hidden', !(isManual && $('#sni').value === '__custom__'));
  const ssEnabledChk = $('#ss-enabled');
  const fieldSsPort = $('#field-ss-port');
  if (ssEnabledChk && fieldSsPort) fieldSsPort.classList.toggle('hidden', !ssEnabledChk.checked);
  const tlsEn = $('#tls-enabled');
  const tlsOpts = $('#tls-options');
  if (tlsEn && tlsOpts) tlsOpts.hidden = !tlsEn.checked;
  // وقتی TLS فعال است، هشدار فیلتر IP پنهان می‌شود (چون TLS این مشکل را حل می‌کند)
  // ولی اگر TLS غیر است، هشدار همیشه دیده می‌شود
  const ipWarn = $('#ip-blacklist-warn');
  if (ipWarn) ipWarn.classList.toggle('hidden', !!(tlsEn && tlsEn.checked));
  // پروتکل‌های بدون دامنه (Shadowsocks/Hy2/TUIC): خودکار فعال — نیازی به چک‌باکس نیست
  const hasDomainSync = !!(tlsEn && tlsEn.checked && $('#tls-domain') && $('#tls-domain').value.trim());
  const nodomainNote = $('#nodomain-proto-note');
  const domainManual = $('#domain-proto-manual');
  if (nodomainNote) nodomainNote.classList.toggle('hidden', hasDomainSync);
  if (domainManual) domainManual.classList.toggle('hidden', !hasDomainSync);
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
      resync: { name: false, gb: false, days: false },
      protocols: { name: false, gb: false, days: false },
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
    else if (a === 'resync') cmd = `kian-v2ray resync`;
    else if (a === 'protocols') cmd = `kian-v2ray protocols enable`;
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

  // دکمه‌های کپی استاتیک (data-copy)
  $$('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-copy');
      const el = document.getElementById(targetId);
      if (!el) return;
      const txt = el.textContent.trim();
      const fallback = () => {
        const ta = document.createElement('textarea');
        ta.value = txt; document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).catch(fallback);
      } else { fallback(); }
      const old = btn.textContent;
      btn.textContent = '✓ کپی شد';
      setTimeout(() => { btn.textContent = old; }, 1500);
    });
  });

  $$('input[name="mode"]').forEach(r => r.addEventListener('change', syncVisibility));
  const ssChk = $('#ss-enabled');
  if (ssChk) ssChk.addEventListener('change', syncVisibility);
  const tlsEn2 = $('#tls-enabled');
  if (tlsEn2) tlsEn2.addEventListener('change', syncVisibility);
  $('#sni-mode') && $('#sni-mode').addEventListener('change', syncVisibility);
  $('#sni') && $('#sni').addEventListener('change', syncVisibility);

  // وقتی دامنهٔ TLS معتبر وارد شد، همهٔ پروتکل‌ها خودکار فعال می‌شوند
  const tlsDomainEl = $('#tls-domain');
  if (tlsDomainEl) {
    tlsDomainEl.addEventListener('input', () => {
      const v = tlsDomainEl.value.trim().toLowerCase();
      const note = $('#tls-auto-note');
      if (isDomain(v)) {
        $$('input[name="tls-proto"]').forEach(cb => { cb.checked = true; });
        if (note) note.hidden = false;
      } else {
        if (note) note.hidden = true;
      }
      syncVisibility();
    });
  }

  syncVisibility();

  $('#gen-form').addEventListener('submit', e => {
    e.preventDefault();
    const f = readForm();
    const err = $('#form-error');
    err.textContent = '';

    if (!isServerAddr(f.serverIp)) { err.textContent = 'آی‌پی سرور معتبر نیست (نمونه: 203.0.113.10 یا 2001:db8::1).'; $('#server-ip').focus(); return; }
    if (!f.prefix) { err.textContent = 'یک نام کاربر (انگلیسی) وارد کن — این نام لینک‌های هر کاربر را از هم جدا می‌کند.'; $('#user-prefix').focus(); return; }
    if (f.tls && f.tls.enabled) {
      if (!isDomain(f.tls.domain)) { err.textContent = 'دامنهٔ TLS معتبر نیست (نمونه: vpn.example.com). یک رکورد A این دامنه باید به IP سرورت اشاره کند.'; $('#tls-domain').focus(); return; }
      // اگر دامنه وارد شده ولی هیچ پروتکلی انتخاب نشده، همه را خودکار فعال کن
      if (!f.tls.protos.length) {
        $$('input[name="tls-proto"]').forEach(cb => { cb.checked = true; });
        f.tls.protos = $$('input[name="tls-proto"]:checked').map(el => el.value);
      }
    }
    if (f.sniMode === 'manual' && !f.manualSni) { err.textContent = 'یک دامنهٔ استتار (SNI) انتخاب یا وارد کن.'; return; }
    if (f.basePort < 0 || f.basePort > 65500) { err.textContent = 'پورت پایه نامعتبر است؛ خالی بگذار یا عددی بین 1 تا 65500 بده.'; return; }
    if (f.ss.enabled && (f.ss.port < 1 || f.ss.port > 65535)) { err.textContent = 'پورت Shadowsocks نامعتبر است.'; return; }

    const btn = $('#gen-btn');
    btn.disabled = true;
    btn.classList.add('busy');
    // اجازه بده UI یک frame رفرش شود، بعد محاسبه‌ی سنگین (QR ها)
    requestAnimationFrame(async () => {
      try {
        const out = await generate(f);
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
