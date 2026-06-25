import 'dart:convert';

import 'package:dartssh2/dartssh2.dart';

/// SSH into the server from inside the app (C7) — connect, run the install
/// command produced by ConfigGen, and run management commands. So the mobile
/// app can do the whole thing (like the desktop Kv2m and the "run on server"
/// button), without the user opening a terminal.
class SshInstaller {
  SSHClient? _client;

  bool get connected => _client != null;

  /// Connect with a password (the common VPS case). Returns null on success,
  /// or an error message.
  Future<String?> connect({
    required String host,
    int port = 22,
    String user = 'root',
    required String password,
    Duration timeout = const Duration(seconds: 20),
  }) async {
    try {
      final socket = await SSHSocket.connect(host, port, timeout: timeout);
      final client = SSHClient(
        socket,
        username: user,
        onPasswordRequest: () => password,
      );
      await client.authenticated;
      _client = client;
      return null;
    } catch (e) {
      return e.toString();
    }
  }

  /// Run a command; returns (exitCode, combined stdout+stderr).
  Future<(int, String)> run(String command,
      {Duration timeout = const Duration(minutes: 5)}) async {
    final c = _client;
    if (c == null) return (255, 'not connected');
    try {
      final session = await c.execute(command);
      final out = StringBuffer();
      await session.stdout
          .cast<List<int>>()
          .transform(utf8.decoder)
          .forEach(out.write)
          .timeout(timeout);
      await session.stderr
          .cast<List<int>>()
          .transform(utf8.decoder)
          .forEach(out.write)
          .timeout(timeout);
      await session.done;
      return (session.exitCode ?? 0, out.toString());
    } catch (e) {
      return (1, 'error: $e');
    }
  }

  /// Run the full install command (multi-line: export KIAN_PAYLOAD=...; curl|bash).
  Future<(int, String)> runInstall(String installCommand) =>
      run(installCommand, timeout: const Duration(minutes: 8));

  /// Convenience wrappers around the management CLI.
  Future<(int, String)> status() => run('kian-v2ray status');
  Future<(int, String)> subLink(String name) =>
      run('kian-v2ray sub ${_q(name)}');
  Future<(int, String)> deployPanel(String adminUser, String adminPass) => run(
      'KIAN_ADMIN_USER=${_q(adminUser)} '
      'KIAN_ADMIN_PASSWORD=${_q(adminPass)} kian-v2ray panel enable');

  /// Update the whole server in place (Xray + scripts + panel + companion
  /// protocols + resync everyone's subscription) — no reinstall, users kept.
  Future<(int, String)> updateServer() =>
      run('kian-v2ray update', timeout: const Duration(minutes: 8));

  /// Regenerate every user's subscription so anyone holding a link auto-gets
  /// the current config set (after enabling a protocol / changing methods).
  Future<(int, String)> resync() =>
      run('kian-v2ray resync', timeout: const Duration(minutes: 3));

  String _q(String s) => "'${s.replaceAll("'", "'\\''")}'";

  void close() {
    _client?.close();
    _client = null;
  }
}
