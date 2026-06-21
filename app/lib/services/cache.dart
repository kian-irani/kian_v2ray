import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/server_profile.dart';

/// Offline mode (6.3): persist the server list + last-known stats so the app
/// shows useful information without a network connection. Backed by
/// shared_preferences (a tiny key/value store), so it survives restarts.
class Cache {
  static const _kServers = 'kv2m.servers';
  static const _kSelected = 'kv2m.selected';
  static const _kStats = 'kv2m.lastStats';
  static const _kLang = 'kv2m.lang';
  static const _kTheme = 'kv2m.theme';
  static const _kSubUrl = 'kv2m.subUrl';

  Future<void> saveServers(List<ServerProfile> servers) async {
    final prefs = await SharedPreferences.getInstance();
    final json = jsonEncode(servers.map((s) => s.toJson()).toList());
    await prefs.setString(_kServers, json);
  }

  Future<List<ServerProfile>> loadServers() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_kServers);
    if (raw == null || raw.isEmpty) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list
        .map((e) => ServerProfile.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> saveSelected(String? name) async {
    final prefs = await SharedPreferences.getInstance();
    if (name == null) {
      await prefs.remove(_kSelected);
    } else {
      await prefs.setString(_kSelected, name);
    }
  }

  Future<String?> loadSelected() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kSelected);
  }

  /// Cache last successfully fetched stats; shown with an "(offline)" badge
  /// when the network is unavailable.
  Future<void> saveStats(Map<String, dynamic> stats) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kStats, jsonEncode(stats));
  }

  Future<Map<String, dynamic>?> loadStats() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_kStats);
    return raw == null ? null : jsonDecode(raw) as Map<String, dynamic>;
  }

  /// The subscription URL (Gist) produced at install time, so the user can copy
  /// or refresh it later — managed from the home screen.
  Future<void> saveSubUrl(String? url) async {
    final prefs = await SharedPreferences.getInstance();
    if (url == null || url.isEmpty) {
      await prefs.remove(_kSubUrl);
    } else {
      await prefs.setString(_kSubUrl, url);
    }
  }

  Future<String?> loadSubUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kSubUrl);
  }

  Future<void> savePrefs({String? lang, String? theme}) async {
    final prefs = await SharedPreferences.getInstance();
    if (lang != null) await prefs.setString(_kLang, lang);
    if (theme != null) await prefs.setString(_kTheme, theme);
  }

  Future<(String lang, String theme)> loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    return (prefs.getString(_kLang) ?? 'fa', prefs.getString(_kTheme) ?? 'dark');
  }
}
