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
  };

  String t(String key) {
    final pair = _t[key];
    if (pair == null) return key;
    return lang == 'fa' ? pair[0] : pair[1];
  }

  TextDirection get dir => lang == 'fa' ? TextDirection.rtl : TextDirection.ltr;
  Locale get locale => Locale(lang);
}
