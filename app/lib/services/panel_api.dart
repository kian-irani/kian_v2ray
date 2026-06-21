import 'dart:convert';

import 'package:http/http.dart' as http;

/// Dart client for the KIAN web panel REST API, so the mobile app can manage
/// users/stats in-app (no separate browser panel needed). Mirrors the desktop
/// panel_client.py: login + transparent token refresh + user CRUD + stats.
class PanelApi {
  final String baseUrl;
  String? _access;
  String? _refresh;

  PanelApi(String base) : baseUrl = base.replaceAll(RegExp(r'/$'), '');

  bool get isLoggedIn => _access != null;

  Uri _u(String path) => Uri.parse('$baseUrl$path');

  Future<http.Response> _send(String method, String path,
      {Map<String, dynamic>? body, bool auth = true, bool retry = false}) async {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (auth && _access != null) headers['Authorization'] = 'Bearer $_access';
    final req = http.Request(method, _u(path))..headers.addAll(headers);
    if (body != null) req.body = jsonEncode(body);
    final streamed = await req.send().timeout(const Duration(seconds: 20));
    final res = await http.Response.fromStream(streamed);
    if (res.statusCode == 401 && auth && _refresh != null && !retry) {
      if (await _doRefresh()) {
        return _send(method, path, body: body, auth: auth, retry: true);
      }
    }
    return res;
  }

  Future<bool> _doRefresh() async {
    final res = await _send('POST', '/auth/refresh',
        body: {'refresh_token': _refresh}, auth: false);
    if (res.statusCode != 200) return false;
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    _access = j['access_token'] as String?;
    _refresh = j['refresh_token'] as String?;
    return true;
  }

  /// Returns true on success. [totp] only needed if 2FA is enabled.
  Future<bool> login(String username, String password, {String? totp}) async {
    final body = {'username': username, 'password': password};
    if (totp != null && totp.isNotEmpty) body['totp'] = totp;
    final res = await _send('POST', '/auth/login', body: body, auth: false);
    if (res.statusCode != 200) return false;
    final j = jsonDecode(res.body) as Map<String, dynamic>;
    _access = j['access_token'] as String?;
    _refresh = j['refresh_token'] as String?;
    return true;
  }

  void logout() {
    _access = null;
    _refresh = null;
  }

  Future<List<Map<String, dynamic>>> users({String query = ''}) async {
    final q = query.isEmpty ? '' : '&q=${Uri.encodeComponent(query)}';
    final res = await _send('GET', '/api/users?limit=500$q');
    if (res.statusCode != 200) return [];
    return (jsonDecode(res.body) as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> stats() async {
    final res = await _send('GET', '/api/stats');
    return res.statusCode == 200
        ? jsonDecode(res.body) as Map<String, dynamic>
        : {};
  }

  Future<bool> addUser(String name,
      {int quotaGb = 0, int days = 0, int ipLimit = 0}) async {
    final body = <String, dynamic>{
      'name': name,
      'quota_bytes': quotaGb * 1073741824,
      'ip_limit': ipLimit,
    };
    if (days > 0) {
      body['expires_at'] =
          DateTime.now().millisecondsSinceEpoch ~/ 1000 + days * 86400;
    }
    final res = await _send('POST', '/api/users', body: body);
    return res.statusCode == 201 || res.statusCode == 200;
  }

  Future<bool> deleteUser(String name) async {
    final res = await _send('DELETE', '/api/users/${Uri.encodeComponent(name)}');
    return res.statusCode == 200;
  }

  Future<bool> setEnabled(String name, bool enabled) async {
    final res = await _send('PATCH', '/api/users/${Uri.encodeComponent(name)}',
        body: {'enabled': enabled});
    return res.statusCode == 200;
  }

  /// Sync the installer's real users into the panel db (bridge).
  Future<bool> sync() async {
    final res = await _send('POST', '/api/sync');
    return res.statusCode == 200;
  }
}
