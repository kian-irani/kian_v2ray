import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../i18n.dart';
import '../models/server_profile.dart';
import '../theme.dart';

/// Shows one config in full: a scannable QR, the full share URI, copy button,
/// and its protocol/host/port. Closes the "app shows nothing" gap — the user can
/// see every config and move it to any other client.
class ConfigDetailScreen extends StatelessWidget {
  final Strings strings;
  final ServerProfile server;
  const ConfigDetailScreen(
      {super.key, required this.strings, required this.server});

  @override
  Widget build(BuildContext context) {
    final s = strings;
    return Scaffold(
      appBar: AppBar(title: Text(server.name)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
              ),
              child: QrImageView(
                data: server.uri,
                version: QrVersions.auto,
                size: 230,
                backgroundColor: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (server.protocol != null) _chip(server.protocol!.toUpperCase()),
              if (server.host != null) _chip(server.host!),
              if (server.port != null) _chip('${s.t('cfg.port')} ${server.port}'),
            ],
          ),
          const SizedBox(height: 18),
          Text(s.t('cfg.uri'),
              style: const TextStyle(color: KianTheme.accent, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFF0B1426),
              borderRadius: BorderRadius.circular(10),
            ),
            child: SelectableText(server.uri,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: server.uri));
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(s.t('cfg.copied')), duration: const Duration(seconds: 2)),
                );
              }
            },
            icon: const Icon(Icons.copy_outlined),
            label: Text(s.t('cfg.copy')),
          ),
        ],
      ),
    );
  }

  Widget _chip(String label) => Chip(
        label: Text(label, style: const TextStyle(fontSize: 12)),
        backgroundColor: const Color(0xFF13203A),
        side: const BorderSide(color: Color(0xFF223052)),
      );
}
