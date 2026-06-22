import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../models/server_profile.dart';

/// A saved subscription source: a URL the app re-fetches to keep its server
/// list current (the configs behind a Gist/sub link can change — ports remap,
/// users get added). Auto-refresh keeps the app in sync without re-importing.
class SubSource {
  final String url;
  final String name;
  String? lastFetchIso; // ISO-8601 of the last successful refresh
  int lastCount; // how many servers it yielded last time

  SubSource({required this.url, this.name = '', this.lastFetchIso, this.lastCount = 0});

  Map<String, dynamic> toJson() =>
      {'url': url, 'name': name, 'lastFetchIso': lastFetchIso, 'lastCount': lastCount};

  factory SubSource.fromJson(Map<String, dynamic> j) => SubSource(
        url: j['url'] as String,
        name: (j['name'] as String?) ?? '',
        lastFetchIso: j['lastFetchIso'] as String?,
        lastCount: (j['lastCount'] as num?)?.toInt() ?? 0,
      );
}

/// Manages subscription sources + refreshing them. Servers imported from a sub
/// are tagged with their source URL so a refresh can replace exactly those.
class SubscriptionService {
  static const _kSources = 'kv2m.subSources';

  Future<List<SubSource>> loadSources() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_kSources);
    if (raw == null || raw.isEmpty) return [];
    return (jsonDecode(raw) as List)
        .map((e) => SubSource.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> _saveSources(List<SubSource> sources) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
        _kSources, jsonEncode(sources.map((s) => s.toJson()).toList()));
  }

  /// Register a subscription URL (idempotent on URL). Returns the source list.
  Future<List<SubSource>> addSource(String url, {String name = ''}) async {
    final clean = url.trim();
    final sources = await loadSources();
    if (!sources.any((s) => s.url == clean)) {
      sources.add(SubSource(url: clean, name: name));
      await _saveSources(sources);
    }
    return sources;
  }

  Future<void> removeSource(String url) async {
    final sources = await loadSources();
    sources.removeWhere((s) => s.url == url);
    await _saveSources(sources);
  }

  /// True when [text] looks like a subscription URL (vs a raw share link).
  static bool isSubUrl(String text) {
    final t = text.trim();
    return (t.startsWith('http://') || t.startsWith('https://')) &&
        !t.contains('\n');
  }

  /// Fetch one subscription URL and parse it into servers. Handles base64 or
  /// plain-text bodies (parseSubscription already does both). Returns [] on any
  /// network/parse failure (fails soft — never throws into the UI).
  Future<List<ServerProfile>> fetch(String url,
      {Duration timeout = const Duration(seconds: 20)}) async {
    try {
      final res = await http.get(Uri.parse(url)).timeout(timeout);
      if (res.statusCode != 200) return [];
      final servers = parseSubscription(res.body);
      // tag each with its source so refresh can replace just these
      return servers
          .map((s) => ServerProfile(
                name: s.name, uri: s.uri, host: s.host, port: s.port,
                protocol: s.protocol, latencyMs: s.latencyMs, source: url,
              ))
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Refresh every saved source and return the merged fresh server list. The
  /// caller merges this with manually-added servers (those have source == null).
  /// [nowIso] is passed in (no clock here) to stamp lastFetch.
  Future<List<ServerProfile>> refreshAll(String nowIso) async {
    final sources = await loadSources();
    final fresh = <ServerProfile>[];
    for (final src in sources) {
      final got = await fetch(src.url);
      if (got.isNotEmpty) {
        src.lastFetchIso = nowIso;
        src.lastCount = got.length;
        fresh.addAll(got);
      }
    }
    await _saveSources(sources);
    return fresh;
  }
}
