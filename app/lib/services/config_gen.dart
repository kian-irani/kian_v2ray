import 'dart:convert';
import 'dart:math';

import 'package:cryptography/cryptography.dart';
import 'package:http/http.dart' as http;

/// Client-side config generation (C8) — the SAME mechanism as the web page
/// (assets/js/app.js) and desktop (kv2m/core.py): X25519 reality keys made on
/// the device, a base64 install payload identical in shape to the web one, the
/// install command, and per-user **Gist** subscriptions via OUR Cloudflare
/// Worker. Now also supports WARP, Shadowsocks and domain TLS, matching the web.
class ConfigGen {
  static const rawBase =
      'https://raw.githubusercontent.com/KIAN-IRANI/kian_v2ray/main';
  static const gistProxy = 'https://kian-sub.kian-mhrv.workers.dev';
  static const ssMethod = 'chacha20-ietf-poly1305';
  static const _apiPort = 10085;
  static const _warpPort = 40000;
  static const _snis = ['www.speedtest.net', 'www.bing.com', 'www.microsoft.com'];
  static const _ports = [443, 2083, 2087];

  // Only these geo-blocked services are routed through WARP (they reject
  // Iranian/datacenter IPs). Everything else goes DIRECT at full server speed.
  // Plain `domain:` rules — no geosite.dat dependency, so Xray never fails to
  // start over a missing category.
  static const warpDomains = [
    'domain:openai.com', 'domain:chatgpt.com', 'domain:oaistatic.com',
    'domain:oaiusercontent.com', 'domain:anthropic.com', 'domain:claude.ai',
    'domain:gemini.google.com', 'domain:aistudio.google.com',
    'domain:makersuite.google.com', 'domain:ai.google.dev',
    'domain:generativelanguage.googleapis.com', 'domain:x.ai', 'domain:grok.com',
    'domain:perplexity.ai',
  ];

  // kind -> (proto, net, label) — mirrors TLS_PROTOS in app.js.
  static const Map<String, List<String>> tlsProtos = {
    'vless-ws': ['vless', 'ws', 'VLESS-WS'],
    'vmess-ws': ['vmess', 'ws', 'VMess-WS'],
    'vless-grpc': ['vless', 'grpc', 'VLESS-gRPC'],
    'vmess-grpc': ['vmess', 'grpc', 'VMess-gRPC'],
    'trojan-ws': ['trojan', 'ws', 'Trojan-WS'],
    'vless-httpupgrade': ['vless', 'httpupgrade', 'VLESS-HTTPUpgrade'],
    'vmess-httpupgrade': ['vmess', 'httpupgrade', 'VMess-HTTPUpgrade'],
    'vless-xhttp': ['vless', 'xhttp', 'VLESS-XHTTP'],
  };

  final _rnd = Random.secure();

  String _randHex(int bytes) => List<int>.generate(bytes, (_) => _rnd.nextInt(256))
      .map((x) => x.toRadixString(16).padLeft(2, '0')).join();

  String _uuid() {
    final b = List<int>.generate(16, (_) => _rnd.nextInt(256));
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    final h = b.map((x) => x.toRadixString(16).padLeft(2, '0')).join();
    return '${h.substring(0, 8)}-${h.substring(8, 12)}-${h.substring(12, 16)}'
        '-${h.substring(16, 20)}-${h.substring(20)}';
  }

  String _b64url(List<int> bytes) => base64Url.encode(bytes).replaceAll('=', '');
  String _b64(String s) => base64.encode(utf8.encode(s));
  String _host(String ip) =>
      ip.contains(':') && !ip.startsWith('[') ? '[$ip]' : ip;

  Future<(String priv, String pub, String shortId)> genReality() async {
    final kp = await X25519().newKeyPair();
    final priv = await kp.extractPrivateKeyBytes();
    final pub = await kp.extractPublicKey();
    return (_b64url(priv), _b64url(pub.bytes), _randHex(4));
  }

  // ---- link builders (match app.js) ----
  String _vlessReality(String uuid, String ip, int port, String sni, String pbk,
      String sid, String label) {
    final q = {
      'encryption': 'none', 'flow': 'xtls-rprx-vision', 'security': 'reality',
      'sni': sni, 'fp': 'chrome', 'pbk': pbk, 'sid': sid,
      // spiderX (Reality advanced 10.6): the path the client's probe "crawls"
      // on the fronting site so its fallback traffic looks like a real browser.
      'spx': '/', 'type': 'tcp',
    }.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&');
    return 'vless://$uuid@${_host(ip)}:$port?$q#${Uri.encodeComponent(label)}';
  }

  String _ssLink(String ip, int port, String pw, String label) {
    final userinfo = base64.encode(utf8.encode('$ssMethod:$pw'));
    return 'ss://$userinfo@${_host(ip)}:$port#${Uri.encodeComponent(label)}';
  }

  String _tlsLink(String kind, String uuid, String domain, String path, String label) {
    final proto = tlsProtos[kind]![0], net = tlsProtos[kind]![1];
    if (proto == 'vmess') {
      final v = {
        'v': '2', 'ps': label, 'add': domain, 'port': '443', 'id': uuid,
        'aid': '0', 'scy': 'auto',
        'net': net == 'httpupgrade' ? 'httpupgrade' : net, 'type': 'none',
        'host': domain, 'path': net == 'grpc' ? path.replaceFirst('/', '') : path,
        'tls': 'tls', 'sni': domain, 'alpn': '', 'fp': 'chrome',
      };
      return 'vmess://${base64.encode(utf8.encode(jsonEncode(v)))}';
    }
    final q = <String, String>{
      if (proto == 'vless') 'encryption': 'none',
      'security': 'tls', 'sni': domain, 'fp': 'chrome', 'type': net, 'host': domain,
    };
    if (net == 'ws' || net == 'httpupgrade') q['path'] = path;
    if (net == 'xhttp') { q['path'] = path; q['mode'] = 'auto'; }
    if (net == 'grpc') { q['serviceName'] = path.replaceFirst('/', ''); q['mode'] = 'gun'; }
    final qs = q.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&');
    final scheme = proto == 'trojan' ? 'trojan' : 'vless';
    return '$scheme://$uuid@$domain:443?$qs#${Uri.encodeComponent(label)}';
  }

  String _caddyfile(String domain, List<Map<String, dynamic>> tls) {
    final l = <String>['$domain {'];
    for (final t in tls) {
      final tag = t['tag'], port = t['intPort'], net = t['net'], path = t['path'] as String;
      if (net == 'grpc') {
        final svc = path.replaceFirst('/', '');
        l.addAll(['\t@$tag {', '\t\tpath /$svc/*', '\t}',
          '\thandle @$tag {', '\t\treverse_proxy h2c://127.0.0.1:$port', '\t}']);
      } else if (net == 'xhttp') {
        l.addAll(['\t@$tag {', '\t\tpath $path $path/*', '\t}',
          '\thandle @$tag {', '\t\treverse_proxy h2c://127.0.0.1:$port', '\t}']);
      } else {
        l.addAll(['\t@$tag {', '\t\tpath $path', '\t}',
          '\thandle @$tag {', '\t\treverse_proxy 127.0.0.1:$port', '\t}']);
      }
    }
    l.addAll(['\thandle {', '\t\trespond "It works!" 200', '\t}', '}']);
    return l.join('\n');
  }

  /// Build the whole install for one server.
  Future<InstallBundle> build({
    required String serverIp,
    required String userPrefix,
    int count = 1,
    bool warp = false,
    bool ss = false,
    int ssPort = 8388,
    String? tlsDomain,
    List<String> tlsProtoKinds = const [],
    List<String> extraProtocols = const [],
    List<String> snis = const [],   // override the default Reality SNIs (page parity)
    String lang = 'en',             // install console language (matches app UI)
  }) async {
    // Use caller-supplied SNIs when given (custom SNI), else the built-in set.
    final activeSnis = snis.where((s) => s.trim().isNotEmpty).toList();
    final useSnis = activeSnis.isEmpty ? _snis : activeSnis;
    final (priv, pub, sid) = await genReality();
    final installId = _randHex(16);
    final channel = warp ? 'warp' : 'direct';
    final ssPassword = ss ? _b64url(List<int>.generate(16, (_) => _rnd.nextInt(256))).substring(0, 22) : '';

    // TLS profiles (internal localhost ports behind Caddy)
    final tlsEnabled = tlsDomain != null && tlsDomain.isNotEmpty && tlsProtoKinds.isNotEmpty;
    final dom = tlsDomain ?? '';   // non-null for the link/caddyfile builders
    final tls = <Map<String, dynamic>>[];
    if (tlsEnabled) {
      final safeStart = [20810, (ss ? ssPort : 0) + 100, _ports.reduce(max) + 100].reduce(max);
      var ip2 = safeStart;
      final rnd = _randHex(3);
      for (var i = 0; i < tlsProtoKinds.length; i++) {
        final kind = tlsProtoKinds[i];
        if (!tlsProtos.containsKey(kind)) continue;
        final net = tlsProtos[kind]![1];
        tls.add({'kind': kind, 'tag': 'tls-$kind', 'intPort': ip2++, 'net': net,
          'proto': tlsProtos[kind]![0], 'path': '/$rnd$i${net == 'grpc' ? 'grpc' : ''}'});
      }
    }

    final users = <Map<String, dynamic>>[];
    final subItems = <String, String>{};
    final subTokens = <String, String>{};
    final perUserLinks = <String, List<String>>{};
    final allLinks = <String>[];

    for (var i = 0; i < count; i++) {
      final name = count == 1 ? userPrefix : '$userPrefix-${i + 1}';
      final uuid = _uuid();
      users.add({'id': uuid, 'email': name, 'active': true});
      final links = <String>[];
      for (var p = 0; p < _ports.length; p++) {
        links.add(_vlessReality(uuid, serverIp, _ports[p], useSnis[p % useSnis.length],
            pub, sid, 'KIAN-$name-${_ports[p]}'));
      }
      for (final t in tls) {
        links.add(_tlsLink(t['kind'] as String, uuid, dom, t['path'] as String,
            'KIAN-$name-${tlsProtos[t['kind']]![2]}'));
      }
      if (ss) links.add(_ssLink(serverIp, ssPort, ssPassword, 'KIAN-$name-SS'));
      perUserLinks[name] = links;
      allLinks.addAll(links);
      final token = _randHex(16);
      subTokens[name] = token;
      subItems[token] = _b64(links.join('\n'));
    }

    final config = _buildConfig(users, priv, sid, channel, ss, ssPort,
        ssPassword, tls, warp, useSnis);
    final payload = {
      'warp_needed': warp,
      'server_ip': serverIp,
      'config_b64': _b64(jsonEncode(config)),
      'users_b64': _b64(jsonEncode({'users': users})),
      'links': allLinks,
      'ports': [..._ports, if (ss) ssPort],
      'api_port': _apiPort,
      'sub_port': [80, 8888, 2086],
      'sub_tokens': subTokens,
      'reality_pbk': pub,
      'reality_sid': sid,
      'ss_password': ssPassword,
      'gist_proxy': gistProxy,
      'install_id': installId,
      'tls_domain': tlsEnabled ? dom : '',
      'caddyfile_b64': tlsEnabled ? _b64(_caddyfile(dom, tls)) : '',
      'extra_protocols': extraProtocols,   // Hysteria2/TUIC روی sing-box
      'lang': lang,                        // install console language
    };
    final cmd = "export KIAN_PAYLOAD='${_b64(jsonEncode(payload))}'\n"
        "export KIAN_LANG='$lang'\n"
        "curl -fsSL $rawBase/install.sh -o /tmp/kian-v2ray.sh && "
        "bash /tmp/kian-v2ray.sh";
    return InstallBundle(installCommand: cmd, installId: installId,
        subItems: subItems, perUserLinks: perUserLinks);
  }

  Map<String, dynamic> _buildConfig(
      List<Map<String, dynamic>> users, String priv, String sid, String channel,
      bool ss, int ssPort, String ssPw, List<Map<String, dynamic>> tls, bool warp,
      List<String> snis) {
    // routeOnly: sniff the domain for ROUTING only — never override the
    // connection's destination. Avoids a second DNS resolution per request and
    // keeps UDP/QUIC (gaming) intact. The big latency/packet-loss fix.
    final sniff = {'enabled': true, 'destOverride': ['http', 'tls', 'quic'], 'routeOnly': true};
    final realityClients = users
        .map((u) => {'id': u['id'], 'email': u['email'], 'flow': 'xtls-rprx-vision'})
        .toList();
    final inbounds = <Map<String, dynamic>>[
      {'listen': '127.0.0.1', 'port': _apiPort, 'protocol': 'dokodemo-door',
        'settings': {'address': '127.0.0.1'}, 'tag': 'api'},
    ];
    final realityTags = <String>[];
    for (var i = 0; i < _ports.length; i++) {
      final tag = 'reality-$channel-${i + 1}';
      realityTags.add(tag);
      final sni = snis[i % snis.length];
      inbounds.add({'tag': tag, 'protocol': 'vless', 'port': _ports[i],
        'settings': {'clients': realityClients, 'decryption': 'none'},
        'streamSettings': {'network': 'tcp', 'security': 'reality',
          // dest is REQUIRED by xray-core 26.x — without it the REALITY inbound
          // fails to build and xray never starts (see install.sh sanitizer).
          'realitySettings': {'dest': '$sni:443', 'privateKey': priv,
            'shortIds': [sid], 'serverNames': [sni]}},
        'sniffing': sniff});
    }
    // TLS inbounds (behind Caddy, on localhost)
    final tlsTags = <String>[];
    for (final t in tls) {
      tlsTags.add(t['tag'] as String);
      final net = t['net'] as String, proto = t['proto'] as String, path = t['path'] as String;
      final stream = <String, dynamic>{'network': net, 'security': 'none'};
      if (net == 'ws') stream['wsSettings'] = {'path': path};
      else if (net == 'grpc') stream['grpcSettings'] = {'serviceName': path.replaceFirst('/', '')};
      else if (net == 'httpupgrade') stream['httpupgradeSettings'] = {'path': path};
      else if (net == 'xhttp') stream['xhttpSettings'] = {'mode': 'auto', 'path': path};
      Map<String, dynamic> settings;
      if (proto == 'trojan') {
        settings = {'clients': users.map((u) => {'password': u['id'], 'email': u['email']}).toList()};
      } else {
        settings = {'clients': users.map((u) => {'id': u['id'], 'email': u['email']}).toList(),
          if (proto == 'vless') 'decryption': 'none'};
      }
      inbounds.add({'listen': '127.0.0.1', 'port': t['intPort'], 'protocol': proto,
        'tag': t['tag'], 'settings': settings, 'streamSettings': stream, 'sniffing': sniff});
    }
    if (ss) {
      inbounds.add({'listen': '0.0.0.0', 'port': ssPort, 'protocol': 'shadowsocks',
        'tag': 'shadowsocks',
        'settings': {'method': ssMethod, 'password': ssPw, 'network': 'tcp,udp'},
        'sniffing': sniff});
    }

    // Speed: general traffic goes DIRECT (full server line, like plain Xray /
    // 3x-ui). Only the curated geo-blocked services above are sent through
    // WARP — so browsing/streaming/downloads run at native speed while
    // ChatGPT/Claude/Gemini still work from a blocked server IP.
    final anyWarp = warp;
    final outbounds = <Map<String, dynamic>>[
      {'tag': 'direct', 'protocol': 'freedom', 'settings': {'domainStrategy': 'AsIs'}},
    ];
    if (anyWarp) {
      outbounds.add({'tag': 'warp', 'protocol': 'socks',
        'settings': {'servers': [{'address': '127.0.0.1', 'port': _warpPort}]}});
    }
    outbounds.add({'tag': 'block', 'protocol': 'blackhole', 'settings': {}});

    final rules = <Map<String, dynamic>>[
      {'type': 'field', 'inboundTag': ['api'], 'outboundTag': 'api'},
      {'type': 'field', 'ip': ['geoip:private'], 'outboundTag': 'block'},
      if (anyWarp) {'type': 'field', 'domain': warpDomains, 'outboundTag': 'warp'},
      {'type': 'field', 'inboundTag': realityTags, 'outboundTag': 'direct'},
    ];
    if (tlsTags.isNotEmpty) {
      rules.add({'type': 'field', 'inboundTag': tlsTags, 'outboundTag': 'direct'});
    }
    if (ss) rules.add({'type': 'field', 'inboundTag': ['shadowsocks'], 'outboundTag': 'direct'});

    return {
      // access log off: a per-connection file write on the bind-mounted log
      // dir adds latency/jitter under load (3x-ui ships it off). Usage stats
      // come from the Xray stats API, not this log, so quotas keep working.
      'log': {'loglevel': 'warning', 'access': 'none',
        'error': '/var/log/xray/error.log'},
      'dns': {'servers': ['1.1.1.1', '8.8.8.8']},
      'api': {'tag': 'api', 'services': ['HandlerService', 'StatsService']},
      'stats': {},
      'policy': {'levels': {'0': {'statsUserUplink': true, 'statsUserDownlink': true}},
        'system': {'statsInboundUplink': true, 'statsInboundDownlink': true}},
      'inbounds': inbounds,
      'outbounds': outbounds,
      'routing': {'domainStrategy': 'AsIs', 'rules': rules},
    };
  }

  Future<Map<String, String>> createGistSubs(
      String installId, Map<String, String> subItems) async {
    try {
      final res = await http.post(Uri.parse('$gistProxy/sync'),
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
  final Map<String, String> subItems;
  final Map<String, List<String>> perUserLinks;
  InstallBundle({required this.installCommand, required this.installId,
    required this.subItems, required this.perUserLinks});
}
