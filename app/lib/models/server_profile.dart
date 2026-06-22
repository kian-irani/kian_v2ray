import 'dart:convert';

/// A saved VPN server/config the user imported (link, QR, manual, or panel).
class ServerProfile {
  final String name;
  final String uri; // full share link (vless://, ss://, ...)
  final String? host;
  final int? port;
  final String? protocol; // vless | vmess | trojan | shadowsocks | hysteria2 ...
  int? latencyMs; // measured by the smart-selection ping
  final String? source; // subscription URL this came from (null = manual)

  ServerProfile({
    required this.name,
    required this.uri,
    this.host,
    this.port,
    this.protocol,
    this.latencyMs,
    this.source,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'uri': uri,
        'host': host,
        'port': port,
        'protocol': protocol,
        'latencyMs': latencyMs,
        'source': source,
      };

  factory ServerProfile.fromJson(Map<String, dynamic> j) => ServerProfile(
        name: j['name'] as String,
        uri: j['uri'] as String,
        host: j['host'] as String?,
        port: j['port'] as int?,
        protocol: j['protocol'] as String?,
        latencyMs: j['latencyMs'] as int?,
        source: j['source'] as String?,
      );

  /// Best-effort parse of a share link into host/port/protocol.
  factory ServerProfile.fromUri(String uri, {String? name}) {
    final scheme = uri.contains('://') ? uri.split('://').first : 'unknown';
    String? host;
    int? port;
    final at = uri.indexOf('@');
    if (at != -1) {
      final tail = uri.substring(at + 1);
      final hostPort = tail.split(RegExp('[/?#]')).first;
      // handle bracketed IPv6: [::1]:443
      final m = RegExp(r'^(\[[^\]]+\]|[^:]+):(\d+)').firstMatch(hostPort);
      if (m != null) {
        host = m.group(1);
        port = int.tryParse(m.group(2)!);
      }
    }
    return ServerProfile(
      name: name ?? (host ?? scheme),
      uri: uri,
      host: host,
      port: port,
      protocol: scheme,
    );
  }
}

/// Parse a subscription payload (base64 of newline-separated links) into a list.
List<ServerProfile> parseSubscription(String body) {
  String decoded = body.trim();
  try {
    decoded = utf8.decode(base64.decode(_pad(decoded)));
  } catch (_) {
    // already plain text
  }
  return decoded
      .split(RegExp(r'\r?\n'))
      .map((l) => l.trim())
      .where((l) => l.contains('://'))
      .map((l) => ServerProfile.fromUri(l))
      .toList();
}

String _pad(String s) {
  final mod = s.length % 4;
  return mod == 0 ? s : s + '=' * (4 - mod);
}
