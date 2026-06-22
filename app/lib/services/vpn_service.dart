import 'package:flutter/foundation.dart';
import 'package:flutter_v2ray/flutter_v2ray.dart';

import '../models/server_profile.dart';

/// Real on-device tunnel via the bundled flutter_v2ray core (Xray). This makes
/// Kv2m connect by itself — no v2rayNG needed. The plugin ships the native core
/// and its own VpnService, so [coreAvailable] is true on a real device and
/// false on dev/desktop (where the platform channel is absent) — keeping the
/// home screen's "don't fake a connection" guard honest.
class VpnController {
  VpnController() {
    _v2ray = FlutterV2ray(onStatusChanged: (status) {
      // status.state is e.g. "CONNECTED" | "DISCONNECTED" | "CONNECTING".
      _state = status.state;
    });
  }

  late final FlutterV2ray _v2ray;
  String _state = 'DISCONNECTED';
  bool _initialized = false;

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
  Future<bool> start(
    ServerProfile server, {
    bool proxyOnly = false,
    List<String>? bypassSubnets,
  }) async {
    try {
      await _ensureInit();
      if (!await _v2ray.requestPermission()) return false;
      final parser = FlutterV2ray.parseFromURL(server.uri);
      _v2ray.startV2Ray(
        remark: parser.remark.isNotEmpty ? parser.remark : server.name,
        config: parser.getFullConfiguration(),
        proxyOnly: proxyOnly,
        bypassSubnets: bypassSubnets,
      );
      return true;
    } catch (e) {
      debugPrint('VpnController.start failed: $e');
      return false;
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
}
