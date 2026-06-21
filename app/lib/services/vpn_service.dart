import 'package:flutter/services.dart';

import '../models/server_profile.dart';

/// Dart side of the native VPN bridge (Android: [KianVpnService] over the
/// `kv2m/vpn` MethodChannel). On platforms without the channel, calls degrade
/// gracefully so the UI stays usable for development.
class VpnController {
  static const _channel = MethodChannel('kv2m/vpn');

  /// True if this build bundles a real native tunnel core. When false, the app
  /// can generate/manage configs but cannot tunnel traffic on-device — importing
  /// the subscription into v2rayNG is the way to actually connect. On dev/desktop
  /// (no channel) we report false so the UI stays honest.
  Future<bool> coreAvailable() async {
    try {
      return await _channel.invokeMethod<bool>('coreAvailable') ?? false;
    } on PlatformException {
      return false;
    } on MissingPluginException {
      return false;
    }
  }

  /// Ask the OS for VPN consent (first connect). Returns true if granted.
  Future<bool> prepare() async {
    try {
      return await _channel.invokeMethod<bool>('prepare') ?? false;
    } on PlatformException {
      return false;
    } on MissingPluginException {
      return true; // dev/desktop: pretend granted
    }
  }

  /// Start the tunnel for [server]. The config JSON is what the native core
  /// consumes (here we pass the share URI; the core expands it).
  Future<bool> start(ServerProfile server) async {
    final ok = await prepare();
    if (!ok) return false;
    try {
      return await _channel.invokeMethod<bool>('start', {
            'config': server.uri,
          }) ??
          false;
    } on MissingPluginException {
      return true;
    }
  }

  Future<void> stop() async {
    try {
      await _channel.invokeMethod('stop');
    } on MissingPluginException {
      // no-op on dev/desktop
    }
  }

  /// "connected" | "disconnected"
  Future<String> status() async {
    try {
      return await _channel.invokeMethod<String>('status') ?? 'disconnected';
    } on MissingPluginException {
      return 'disconnected';
    }
  }
}
