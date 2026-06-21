import 'package:flutter/widgets.dart';

/// Tiny FA/EN dictionary + direction handling for the mobile client.
/// RTL for Persian, LTR for English — matches the web surfaces.
class Strings {
  final String lang; // 'fa' | 'en'
  const Strings(this.lang);

  static const Map<String, List<String>> _t = {
    // key: [fa, en]
    'app.title': ['Kv2m', 'Kv2m'],
    'tab.home': ['خانه', 'Home'],
    'tab.servers': ['سرورها', 'Servers'],
    'tab.settings': ['تنظیمات', 'Settings'],
    'connect': ['اتصال', 'Connect'],
    'disconnect': ['قطع', 'Disconnect'],
    'connected': ['متصل', 'Connected'],
    'disconnected': ['قطع', 'Disconnected'],
    'import.title': ['افزودن سرور', 'Add server'],
    'import.link': ['از روی لینک Subscription', 'From subscription link'],
    'import.qr': ['اسکن QR', 'Scan QR'],
    'import.manual': ['دستی', 'Manual'],
    'servers.empty': ['هنوز سروری اضافه نکرده‌ای', 'No servers yet'],
    'best.auto': ['انتخاب خودکار بهترین سرور', 'Auto-pick best server'],
    'offline.note': ['آخرین وضعیت (آفلاین)', 'Last state (offline)'],
    'cancel': ['انصراف', 'Cancel'],
    'login.user': ['نام کاربری', 'Username'],
    'login.pass': ['رمز عبور', 'Password'],
    'stat.total': ['کل کاربران', 'Total'],
    'stat.active': ['فعال', 'Active'],
    'stat.traffic': ['مصرف', 'Traffic'],
    'mg.title': ['مدیریت سرور', 'Server management'],
    'mg.connect': ['به پنلِ سرورت وصل شو', 'Connect to your server panel'],
    'mg.url': ['آدرس پنل', 'Panel URL'],
    'mg.connectbtn': ['اتصال', 'Connect'],
    'mg.add': ['افزودن کاربر', 'Add user'],
    'mg.toggle': ['فعال/غیرفعال', 'Enable/Disable'],
    'mg.delete': ['حذف', 'Delete'],
    'open.manage': ['مدیریت سرور', 'Manage server'],
    'open.setup': ['نصب روی سرور', 'Set up server'],
    'setup.title': ['نصب روی سرور', 'Set up server'],
    'setup.desc': ['اپ خودش به سرورت SSH می‌زند، کانفیگ می‌سازد و نصب می‌کند — بدون ترمینال.', 'The app SSHes into your server, builds the config and installs — no terminal.'],
    'setup.ip': ['آی‌پی سرور', 'Server IP'],
    'setup.sshport': ['پورت SSH', 'SSH port'],
    'setup.sshuser': ['کاربر SSH', 'SSH user'],
    'setup.sshpass': ['رمز SSH', 'SSH password'],
    'setup.username': ['نام کاربر (برای کانفیگ)', 'User name (for the config)'],
    'setup.install': ['ساخت و نصب', 'Build & install'],
    'setup.sublink': ['لینک Subscription (روی Gist):', 'Subscription link (on Gist):'],
    'setup.warp': ['WARP (همه‌چیز باز)', 'WARP (everything open)'],
    'setup.warp.d': ['ترافیک از WARP کلودفلر رد می‌شود؛ کمی کندتر.', 'Routes via Cloudflare WARP; a bit slower.'],
    'setup.ss': ['Shadowsocks (پشتیبان)', 'Shadowsocks (backup)'],
    'setup.ss.d': ['یک پروتکل ساده‌ی پشتیبان اضافه می‌کند.', 'Adds a simple backup protocol.'],
    'setup.tls': ['دامنه + TLS (پیشرفته)', 'Domain + TLS (advanced)'],
    'setup.tls.d': ['VLESS/VMess/Trojan روی WS پشت Caddy — نیاز به دامنه دارد.', 'VLESS/VMess/Trojan over WS behind Caddy — needs a domain.'],
    'setup.tlsdomain': ['دامنه (رکورد A به IP سرور)', 'Domain (A record to server IP)'],
    'setup.extra': ['پروتکل‌های اضافه (UDP)', 'Extra protocols (UDP)'],
    'setup.extra.d': ['روی sing-box کنارِ Xray؛ نیازمندِ بازبودنِ پورت UDP. به Subscription اضافه می‌شوند.', 'On sing-box next to Xray; needs UDP open. Added to your subscription.'],
    'setup.hy2': ['Hysteria2', 'Hysteria2'],
    'setup.hy2.d': ['سریع روی شبکهٔ پُرافت، عبورِ عالی از DPI.', 'Fast on lossy networks; great DPI evasion.'],
    'setup.tuic': ['TUIC v5', 'TUIC v5'],
    'setup.tuic.d': ['QUIC، 0-RTT، کنترلِ ازدحام BBR.', 'QUIC, 0-RTT, BBR congestion control.'],
    'setup.gohome': ['بازگشت به خانه و دیدنِ کانفیگ‌ها', 'Back to home & view configs'],
    'cfg.view': ['نمایشِ کانفیگ (QR)', 'View config (QR)'],
    'cfg.uri': ['لینکِ کانفیگ', 'Config link'],
    'cfg.copy': ['کپیِ لینک', 'Copy link'],
    'cfg.copied': ['کپی شد', 'Copied'],
    'cfg.port': ['پورت', 'port'],
    'sub.title': ['لینکِ Subscription', 'Subscription link'],
    'sub.copy': ['کپیِ لینکِ Subscription', 'Copy subscription link'],
    'setup.panel': ['راه‌اندازیِ پنلِ وب', 'Deploy web panel'],
    'setup.panel.d': ['پنلِ مدیریتِ کاربر/آمار را روی سرور نصب می‌کند و آدرس+رمز می‌دهد.', 'Installs the user/stats admin panel on the server and gives URL+password.'],
    'setup.paneluser': ['کاربرِ پنل', 'Panel user'],
    'setup.panelpass': ['رمزِ پنل (خالی = تصادفی)', 'Panel pass (empty = random)'],
    'setup.panelinfo': ['دسترسیِ پنلِ وب:', 'Web panel access:'],
  };

  String t(String key) {
    final pair = _t[key];
    if (pair == null) return key;
    return lang == 'fa' ? pair[0] : pair[1];
  }

  TextDirection get dir => lang == 'fa' ? TextDirection.rtl : TextDirection.ltr;
  Locale get locale => Locale(lang);
}
