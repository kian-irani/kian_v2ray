import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_v2ray/flutter_v2ray.dart';

import '../models/server_profile.dart';

/// Real on-device tunnel via the bundled flutter_v2ray core (Xray). This makes
/// Kv2m connect by itself — no v2rayNG needed. The plugin ships the native core
/// and its own VpnService, so [coreAvailable] is true on a real device and
/// false on dev/desktop (where the platform channel is absent) — keeping the
/// home screen's "don't fake a connection" guard honest.
class VpnController {
  VpnController({void Function()? onStats}) {
    _v2ray = FlutterV2ray(onStatusChanged: (status) {
      // status: state, duration, uploadSpeed, downloadSpeed, upload, download.
      _state = status.state;
      _duration = status.duration;
      _upSpeed = status.uploadSpeed;
      _downSpeed = status.downloadSpeed;
      onStats?.call();
    });
  }

  // Our own MainActivity channel for native extras the plugin doesn't cover
  // (deep-link import). Separate from flutter_v2ray's internal channels.
  static const _extras = MethodChannel('kv2m/vpn');

  late final FlutterV2ray _v2ray;
  String _state = 'DISCONNECTED';
  bool _initialized = false;

  // Live stats from the last status event (shown on the home screen).
  String _duration = '00:00:00';
  int _upSpeed = 0;
  int _downSpeed = 0;
  String get duration => _duration;
  int get uploadSpeed => _upSpeed;
  int get downloadSpeed => _downSpeed;

  /// True when the native core is present (real device). Returns false on
  /// dev/desktop so the UI stays honest instead of black-holing traffic.
  Future<bool> coreAvailable() async {
    try {
      await _ensureInit();
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> _ensureInit() async {
    if (_initialized) return;
    await _v2ray.initializeV2Ray();
    _initialized = true;
  }

  /// Ask the OS for VPN consent (first connect). Returns true if granted.
  Future<bool> prepare() async {
    try {
      await _ensureInit();
      return await _v2ray.requestPermission();
    } catch (_) {
      return false;
    }
  }

  /// Start the real tunnel for [server] (parses its share URI into a full Xray
  /// config and runs it through the bundled core). Honors user settings:
  /// [proxyOnly] (no system TUN) and [bypassSubnets] (routing mode). Returns
  /// true if it started.
  ///
  /// [antiDpi] injects TLS-ClientHello fragmentation into the outbound stream
  /// settings — helps bypass DPI boxes that inspect the first TCP segment.
  Future<bool> start(
    ServerProfile server, {
    bool proxyOnly = false,
    List<String>? bypassSubnets,
    List<String>? blockedApps,
    bool antiDpi = true,
  }) async {
    try {
      await _ensureInit();
      if (!await _v2ray.requestPermission()) return false;
      final parser = FlutterV2ray.parseFromURL(server.uri);
      final rawCfg = parser.getFullConfiguration();
      final cfg = antiDpi ? _injectAntiDpi(rawCfg) : rawCfg;
      _v2ray.startV2Ray(
        remark: parser.remark.isNotEmpty ? parser.remark : server.name,
        config: cfg,
        proxyOnly: proxyOnly,
        bypassSubnets: bypassSubnets,
        blockedApps: (blockedApps != null && blockedApps.isNotEmpty) ? blockedApps : null,
      );
      return true;
    } catch (e) {
      debugPrint('VpnController.start failed: $e');
      return false;
    }
  }

  /// Inject TLS-Hello fragmentation into the proxy outbound(s).
  ///
  /// How Xray fragment actually works (same wiring v2rayNG / Hiddify use): the
  /// real proxy outbound dials its TCP socket THROUGH a `freedom` outbound whose
  /// `settings.fragment` splits the TLS ClientHello across several TCP segments.
  /// We do that by:
  ///   1. adding a `fragment` freedom outbound (packets=tlshello), and
  ///   2. pointing each TCP proxy outbound's `sockopt.dialerProxy` at it.
  /// Without step 2 the fragment outbound is dead weight — which is the bug this
  /// replaces. Effective against Iranian ISP-level DPI that fingerprints the
  /// first packet of the handshake.
  String _injectAntiDpi(String configJson) {
    try {
      final cfg = json.decode(configJson) as Map<String, dynamic>;
      final outbounds = cfg['outbounds'];
      if (outbounds is! List) return configJson;

      var wiredAny = false;
      for (final ob in outbounds) {
        if (ob is! Map<String, dynamic>) continue;
        final tag = ob['tag'] as String? ?? '';
        if (tag == 'fragment') continue; // never chain the fragment to itself
        final proto = ob['protocol'] as String? ?? '';
        // Only the real proxy outbounds carry the handshake we want to fragment.
        if (proto == 'freedom' || proto == 'blackhole' || proto == 'dns') continue;

        final stream = (ob['streamSettings'] as Map<String, dynamic>?) ?? {};
        final net = stream['network'] as String? ?? 'tcp';
        if (net != 'tcp' && net != 'raw') continue; // fragment is TCP/raw only

        // Dial this outbound's TCP socket through the fragment outbound.
        final sockopt = (stream['sockopt'] as Map<String, dynamic>?) ?? {};
        sockopt['dialerProxy'] = 'fragment';
        stream['sockopt'] = sockopt;
        ob['streamSettings'] = stream;
        wiredAny = true;
      }

      // Nothing TCP to fragment (e.g. a pure UDP outbound) → leave config as-is.
      if (!wiredAny) return configJson;

      final hasFragment = outbounds.any((o) => o is Map && o['tag'] == 'fragment');
      if (!hasFragment) {
        outbounds.add({
          'protocol': 'freedom',
          'tag': 'fragment',
          'settings': {
            'domainStrategy': 'UseIP',
            'fragment': {'packets': 'tlshello', 'length': '100-200', 'interval': '10-20'},
          },
          'streamSettings': {'sockopt': {'tcpNoDelay': true}},
        });
      }

      return json.encode(cfg);
    } catch (e) {
      debugPrint('_injectAntiDpi failed, using original config: $e');
      return configJson;
    }
  }

  Future<void> stop() async {
    try {
      _v2ray.stopV2Ray();
    } catch (_) {
      // no-op on dev/desktop
    }
  }

  /// Measured real latency through the selected server's config (ms), or -1.
  Future<int> serverDelay(ServerProfile server) async {
    try {
      await _ensureInit();
      final cfg = FlutterV2ray.parseFromURL(server.uri).getFullConfiguration();
      return await _v2ray.getServerDelay(config: cfg);
    } catch (_) {
      return -1;
    }
  }

  /// "connected" | "disconnected"
  Future<String> status() async =>
      _state.toUpperCase() == 'CONNECTED' ? 'connected' : 'disconnected';

  /// Pending deep-link the app was opened with (a share link / sub URL), or null.
  /// Consumed once by the native side (9.9 — one-tap import).
  Future<String?> initialLink() async {
    try {
      return await _extras.invokeMethod<String>('initialLink');
    } on PlatformException {
      return null;
    } on MissingPluginException {
      return null;
    }
  }
}
