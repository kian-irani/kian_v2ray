import 'dart:async';
import 'dart:io';

import '../models/server_profile.dart';

/// Smart server selection (6.3): TCP-ping each server's host:port and pick the
/// lowest-latency reachable one. Pure Dart (dart:io), no platform channels, so
/// it is unit-testable on the VM.
class SmartSelection {
  final Duration timeout;
  const SmartSelection({this.timeout = const Duration(seconds: 2)});

  Future<int?> ping(String host, int port) async {
    final sw = Stopwatch()..start();
    try {
      final socket = await Socket.connect(host, port, timeout: timeout);
      sw.stop();
      socket.destroy();
      return sw.elapsedMilliseconds;
    } catch (_) {
      return null;
    }
  }

  /// Measure latency for every profile with a host/port; returns them sorted
  /// best-first (unreachable ones at the end with null latency).
  Future<List<ServerProfile>> rank(List<ServerProfile> servers) async {
    await Future.wait(servers.map((s) async {
      if (s.host != null && s.port != null) {
        s.latencyMs = await ping(_unbracket(s.host!), s.port!);
      }
    }));
    final ranked = [...servers];
    ranked.sort((a, b) {
      final la = a.latencyMs ?? 1 << 30;
      final lb = b.latencyMs ?? 1 << 30;
      return la.compareTo(lb);
    });
    return ranked;
  }

  Future<ServerProfile?> best(List<ServerProfile> servers) async {
    final ranked = await rank(servers);
    return ranked.isNotEmpty && ranked.first.latencyMs != null
        ? ranked.first
        : null;
  }

  String _unbracket(String host) =>
      host.startsWith('[') && host.endsWith(']')
          ? host.substring(1, host.length - 1)
          : host;
}
