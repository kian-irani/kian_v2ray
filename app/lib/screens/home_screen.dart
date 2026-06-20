import 'package:flutter/material.dart';

import '../i18n.dart';
import '../models/server_profile.dart';
import '../theme.dart';

class HomeScreen extends StatefulWidget {
  final Strings strings;
  final VoidCallback onToggleLang;
  final VoidCallback onToggleTheme;
  const HomeScreen({
    super.key,
    required this.strings,
    required this.onToggleLang,
    required this.onToggleTheme,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final List<ServerProfile> _servers = [];
  ServerProfile? _selected;
  bool _connected = false;

  void _importLink(String body) {
    final parsed = parseSubscription(body);
    if (parsed.isEmpty) return;
    setState(() {
      _servers.addAll(parsed);
      _selected ??= _servers.first;
    });
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('app.title')),
        actions: [
          IconButton(onPressed: widget.onToggleTheme, icon: const Icon(Icons.brightness_6_outlined)),
          TextButton(onPressed: widget.onToggleLang, child: Text(s.lang == 'fa' ? 'EN' : 'FA')),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _ConnectButton(
              connected: _connected,
              label: _connected ? s.t('connected') : s.t('disconnected'),
              onTap: _selected == null ? null : () => setState(() => _connected = !_connected),
            ),
            const SizedBox(height: 22),
            Text(s.t('tab.servers'), style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Expanded(
              child: _servers.isEmpty
                  ? Center(child: Text(s.t('servers.empty')))
                  : ListView.builder(
                      itemCount: _servers.length,
                      itemBuilder: (_, i) {
                        final srv = _servers[i];
                        final sel = srv == _selected;
                        return Card(
                          child: ListTile(
                            leading: Icon(sel ? Icons.check_circle : Icons.circle_outlined,
                                color: sel ? KianTheme.accent : null),
                            title: Text(srv.name),
                            subtitle: Text('${srv.protocol ?? '?'} · ${srv.host ?? ''}'),
                            trailing: srv.latencyMs != null ? Text('${srv.latencyMs} ms') : null,
                            onTap: () => setState(() => _selected = srv),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showImport(context, s),
        icon: const Icon(Icons.add),
        label: Text(s.t('import.title')),
      ),
    );
  }

  void _showImport(BuildContext context, Strings s) {
    final controller = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom + 18,
          left: 18, right: 18, top: 18,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(s.t('import.link'), style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            TextField(
              controller: controller,
              decoration: const InputDecoration(hintText: 'https://…/sub  or  vless://…'),
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () {
                _importLink(controller.text);
                Navigator.pop(context);
              },
              child: Text(s.t('import.title')),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConnectButton extends StatelessWidget {
  final bool connected;
  final String label;
  final VoidCallback? onTap;
  const _ConnectButton({required this.connected, required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        height: 160,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          gradient: LinearGradient(
            colors: connected
                ? [KianTheme.accent, const Color(0xFF16A34A)]
                : [KianTheme.primary, KianTheme.navy],
          ),
        ),
        alignment: Alignment.center,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(connected ? Icons.shield : Icons.shield_outlined, size: 48,
                color: connected ? KianTheme.navy : Colors.white),
            const SizedBox(height: 8),
            Text(label, style: TextStyle(
                fontWeight: FontWeight.bold,
                color: connected ? KianTheme.navy : Colors.white)),
          ],
        ),
      ),
    );
  }
}
