import 'dart:convert';
import 'dart:math';

import 'package:cryptography/cryptography.dart';
import 'package:http/http.dart' as http;

/// Client-side config generation (C8) — the SAME mechanism as the web page
/// (assets/js/app.js) and the desktop (kv2m/core.py):
///   * X25519 reality keypair generated ON THE DEVICE (never sent to a server),
///   * a base64 install payload identical in shape to the web one,
///   * the install command (export KIAN_PAYLOAD=... ; curl install.sh | bash),
///   * the per-user **Gist** subscription created via OUR Cloudflare Worker.
///
/// So a user created from the mobile app gets the same gist.githubusercontent.com
/// subscription links as one created from the web page.
class ConfigGen {
  static const rawBase =
      'https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main';
  static const gistProxy = 'https://kian-sub.kian-mhrv.workers.dev';
  // Default reality SNIs + ports (mirror the web defaults).
  static const _snis = [
    'www.speedtest.net', 'www.bing.com', 'www.microsoft.com'
  ];
  static const _ports = [443, 2083, 2087];
  static const _apiPort = 10085;
  static const _warpPort = 40000;

  final _rnd = Random.secure();

  String _randHex(int bytes) {
    final b = List<int>.generate(bytes, (_) => _rnd.nextInt(256));
    return b.map((x) => x.toRadixString(16).padLeft(2, '0')).join();
  }

  String _uuid() {
    final b = List<int>.generate(16, (_) => _rnd.nextInt(256));
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    final h = b.map((x) => x.toRadixString(16).padLeft(2, '0')).join();
    return '${h.substring(0, 8)}-${h.substring(8, 12)}-${h.substring(12, 16)}'
        '-${h.substring(16, 20)}-${h.substring(20)}';
  }

  String _b64url(List<int> bytes) =>
      base64Url.encode(bytes).replaceAll('=', '');

  /// Generate the reality X25519 keypair (private kept locally; only public +
  /// shortId travel to the server, exactly like the web).
  Future<(String priv, String pub, String shortId)> genReality() async {
    final algo = X25519();
    final kp = await algo.newKeyPair();
    final privBytes = await kp.extractPrivateKeyBytes();
    final pub = await kp.extractPublicKey();
    return (_b64url(privBytes), _b64url(pub.bytes), _randHex(4));
  }

  String _vlessLink(String uuid, String ip, int port, String sni, String pbk,
      String sid, String label) {
    final host = ip.contains(':') && !ip.startsWith('[') ? '[$ip]' : ip;
    final q = {
      'encryption': 'none', 'flow': 'xtls-rprx-vision', 'security': 'reality',
      'sni': sni, 'fp': 'chrome', 'pbk': pbk, 'sid': sid, 'type': 'tcp',
    }.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&');
    return 'vless://$uuid@$host:$port?$q#${Uri.encodeComponent(label)}';
  }

  /// Build everything for one install: returns the install command + the per-user
  /// links + the data needed to create the Gist subscriptions.
  Future<InstallBundle> build({
    required String serverIp,
    required String userPrefix,
    int count = 1,
  }) async {
    final (priv, pub, sid) = await genReality();
    final installId = _randHex(16);
    final users = <Map<String, dynamic>>[];
    final subItems = <String, String>{};      // subtoken -> base64 content
    final perUserLinks = <String, List<String>>{};

    for (var i = 0; i < count; i++) {
      final name = count == 1 ? userPrefix : '$userPrefix-${i + 1}';
      final uuid = _uuid();
      users.add({'id': uuid, 'email': name, 'active': true});
      final links = <String>[];
      for (var p = 0; p < _ports.length; p++) {
        links.add(_vlessLink(uuid, serverIp, _ports[p], _snis[p % _snis.length],
            pub, sid, 'KIAN-$name-${_ports[p]}'));
      }
      perUserLinks[name] = links;
      subItems[_randHex(16)] = base64.encode(utf8.encode(links.join('\n')));
    }

    final subTokens = <String, String>{};
    var idx = 0;
    for (final u in users) {
      subTokens[u['email'] as String] = subItems.keys.elementAt(idx++);
    }

    final config = _realityConfig(users, priv, sid);
    final payload = {
      'warp_needed': false,
      'server_ip': serverIp,
      'config_b64': base64.encode(utf8.encode(jsonEncode(config))),
      'users_b64': base64.encode(utf8.encode(jsonEncode({'users': users}))),
      'links': perUserLinks.values.expand((l) => l).toList(),
      'ports': _ports,
      'sub_port': [80, 8888, 2086],
      'sub_tokens': subTokens,
      'api_port': _apiPort,
      'reality_pbk': pub,
      'reality_sid': sid,
      'ss_password': '',
      'gist_proxy': gistProxy,
      'install_id': installId,
      'tls_domain': '',
    };
    final payloadB64 = base64.encode(utf8.encode(jsonEncode(payload)));
    final cmd = "export KIAN_PAYLOAD='$payloadB64'\n"
        "curl -fsSL $rawBase/install.sh -o /tmp/kian-v2ray.sh && "
        "bash /tmp/kian-v2ray.sh";
    return InstallBundle(
      installCommand: cmd,
      installId: installId,
      subItems: subItems,
      perUserLinks: perUserLinks,
    );
  }

  /// Full Xray config, matching assets/js/app.js buildConfig() for the
  /// reality-direct case: api inbound + stats/policy (per-user quota tracking),
  /// sniffing, routing (api->api, geoip:private->block, reality->direct), and
  /// the block outbound. (WARP/SS/TLS options are generated by the web/desktop;
  /// the mobile generator covers the default Reality install.)
  Map<String, dynamic> _realityConfig(
      List<Map<String, dynamic>> users, String priv, String sid) {
    final clients = users
        .map((u) => {'id': u['id'], 'email': u['email'], 'flow': 'xtls-rprx-vision'})
        .toList();
    final sniff = {'enabled': true, 'destOverride': ['http', 'tls', 'quic']};

    final inbounds = <Map<String, dynamic>>[
      // stats/handler API (required so the watchdog can read per-user usage)
      {
        'listen': '127.0.0.1', 'port': _apiPort, 'protocol': 'dokodemo-door',
        'settings': {'address': '127.0.0.1'}, 'tag': 'api',
      },
    ];
    final realityTags = <String>[];
    for (var i = 0; i < _ports.length; i++) {
      final tag = 'reality-direct-${i + 1}';
      realityTags.add(tag);
      inbounds.add({
        'tag': tag, 'protocol': 'vless', 'port': _ports[i],
        'settings': {'clients': clients, 'decryption': 'none'},
        'streamSettings': {
          'network': 'tcp', 'security': 'reality',
          'realitySettings': {
            'privateKey': priv, 'shortIds': [sid],
            'serverNames': [_snis[i % _snis.length]],
          },
        },
        'sniffing': sniff,
      });
    }

    return {
      'log': {
        'loglevel': 'warning',
        'access': '/var/log/xray/access.log',
        'error': '/var/log/xray/error.log',
      },
      'dns': {'servers': ['1.1.1.1', '8.8.8.8']},
      'api': {'tag': 'api', 'services': ['HandlerService', 'StatsService']},
      'stats': {},
      'policy': {
        'levels': {'0': {'statsUserUplink': true, 'statsUserDownlink': true}},
        'system': {'statsInboundUplink': true, 'statsInboundDownlink': true},
      },
      'inbounds': inbounds,
      'outbounds': [
        {'tag': 'direct', 'protocol': 'freedom', 'settings': {'domainStrategy': 'UseIP'}},
        {'tag': 'block', 'protocol': 'blackhole', 'settings': {}},
      ],
      'routing': {
        'rules': [
          {'type': 'field', 'inboundTag': ['api'], 'outboundTag': 'api'},
          {'type': 'field', 'ip': ['geoip:private'], 'outboundTag': 'block'},
          {'type': 'field', 'inboundTag': realityTags, 'outboundTag': 'direct'},
        ],
      },
    };
  }

  /// Create the per-user Gist subscriptions via OUR Worker (same as the web).
  /// Returns { subtoken: httpsUrl }.
  Future<Map<String, String>> createGistSubs(
      String installId, Map<String, String> subItems) async {
    try {
      final res = await http.post(
        Uri.parse('$gistProxy/sync'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'install_id': installId, 'items': subItems}),
      ).timeout(const Duration(seconds: 25));
      if (res.statusCode != 200) return {};
      final j = jsonDecode(res.body) as Map<String, dynamic>;
      return (j['urls'] as Map?)?.cast<String, String>() ?? {};
    } catch (_) {
      return {};
    }
  }
}

class InstallBundle {
  final String installCommand;
  final String installId;
  final Map<String, String> subItems;       // subtoken -> base64 content
  final Map<String, List<String>> perUserLinks;
  InstallBundle({
    required this.installCommand,
    required this.installId,
    required this.subItems,
    required this.perUserLinks,
  });
}
