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
  };

  String t(String key) {
    final pair = _t[key];
    if (pair == null) return key;
    return lang == 'fa' ? pair[0] : pair[1];
  }

  TextDirection get dir => lang == 'fa' ? TextDirection.rtl : TextDirection.ltr;
  Locale get locale => Locale(lang);
}
