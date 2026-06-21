import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../i18n.dart';
import '../models/server_profile.dart';
import '../services/cache.dart';
import '../services/selection.dart';
import '../services/vpn_service.dart';
import '../theme.dart';
import 'config_detail_screen.dart';
import 'history_screen.dart';
import 'manage_screen.dart';
import 'setup_screen.dart';

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
  final _cache = Cache();
  final _vpn = VpnController();
  final _selection = const SmartSelection();
  ServerProfile? _selected;
  String? _subUrl;
  bool _connected = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    final saved = await _cache.loadServers();
    final sel = await _cache.loadSelected();
    final sub = await _cache.loadSubUrl();
    final status = await _vpn.status();
    if (!mounted) return;
    setState(() {
      _servers.addAll(saved);
      ServerProfile? match;
      for (final s in _servers) {
        if (s.name == sel) {
          match = s;
          break;
        }
      }
      _selected = match ?? (_servers.isNotEmpty ? _servers.first : null);
      _subUrl = sub;
      _connected = status == 'connected';
    });
  }

  /// Reload the server list from cache (after setup auto-imports configs).
  Future<void> _reloadFromCache() async {
    final saved = await _cache.loadServers();
    final sel = await _cache.loadSelected();
    final sub = await _cache.loadSubUrl();
    if (!mounted) return;
    setState(() {
      _servers
        ..clear()
        ..addAll(saved);
      ServerProfile? match;
      for (final srv in _servers) {
        if (srv.name == sel) {
          match = srv;
          break;
        }
      }
      _selected = match ?? (_servers.isNotEmpty ? _servers.first : null);
      _subUrl = sub;
    });
  }

  void _importLink(String body) {
    final parsed = parseSubscription(body);
    if (parsed.isEmpty) return;
    setState(() {
      _servers.addAll(parsed);
      _selected ??= _servers.first;
    });
    _cache.saveServers(_servers);
  }

  Future<void> _toggleConnection() async {
    if (_selected == null || _busy) return;
    setState(() => _busy = true);
    try {
      if (_connected) {
        await _vpn.stop();
        if (mounted) setState(() => _connected = false);
      } else {
        final ok = await _vpn.start(_selected!);
        if (mounted) setState(() => _connected = ok);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _pickBest() async {
    if (_servers.isEmpty) return;
    final ranked = await _selection.rank(_servers);
    if (!mounted) return;
    setState(() {
      _servers
        ..clear()
        ..addAll(ranked);
      if (ranked.first.latencyMs != null) _selected = ranked.first;
    });
    _cache.saveServers(_servers);
  }

  void _select(ServerProfile s) {
    setState(() => _selected = s);
    _cache.saveSelected(s.name);
  }

  /// Copy every server's share URI (newline-separated) to the clipboard.
  Future<void> _copyAllConfigs() async {
    if (_servers.isEmpty) return;
    final all = _servers.map((s) => s.uri).join('\n');
    await Clipboard.setData(ClipboardData(text: all));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(widget.strings.t('copyall.done')),
          duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('app.title')),
        actions: [
          IconButton(
            tooltip: s.t('open.setup'),
            onPressed: () async {
              await Navigator.push(context, MaterialPageRoute(
                  builder: (_) => SetupScreen(strings: s)));
              // Setup may have auto-imported configs into the cache — reload.
              await _reloadFromCache();
            },
            icon: const Icon(Icons.rocket_launch_outlined),
          ),
          IconButton(
            tooltip: s.t('open.manage'),
            onPressed: () => Navigator.push(context, MaterialPageRoute(
                builder: (_) => ManageScreen(strings: s))),
            icon: const Icon(Icons.admin_panel_settings_outlined),
          ),
          IconButton(
            tooltip: s.t('hist.open'),
            onPressed: () => Navigator.push(context, MaterialPageRoute(
                builder: (_) => HistoryScreen(strings: s))),
            icon: const Icon(Icons.history_outlined),
          ),
          IconButton(
            tooltip: s.t('best.auto'),
            onPressed: _servers.isEmpty ? null : _pickBest,
            icon: const Icon(Icons.speed_outlined),
          ),
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
              busy: _busy,
              label: _busy
                  ? '…'
                  : (_connected ? s.t('connected') : s.t('disconnected')),
              onTap: _selected == null ? null : _toggleConnection,
            ),
            const SizedBox(height: 18),
            if (_subUrl != null && _subUrl!.isNotEmpty) ...[
              Card(
                color: const Color(0xFF0E1B33),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 10, 6, 10),
                  child: Row(
                    children: [
                      const Icon(Icons.link_outlined, color: KianTheme.accent, size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(s.t('sub.title'),
                                style: const TextStyle(
                                    color: KianTheme.accent, fontSize: 12,
                                    fontWeight: FontWeight.bold)),
                            Text(_subUrl!,
                                maxLines: 1, overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontFamily: 'monospace', fontSize: 11)),
                          ],
                        ),
                      ),
                      IconButton(
                        tooltip: s.t('sub.copy'),
                        icon: const Icon(Icons.copy_outlined, size: 20),
                        onPressed: () async {
                          await Clipboard.setData(ClipboardData(text: _subUrl!));
                          if (!context.mounted) return;
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(s.t('cfg.copied')),
                                duration: const Duration(seconds: 2)),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],
            Row(
              children: [
                Expanded(
                  child: Text(s.t('tab.servers'),
                      style: Theme.of(context).textTheme.titleMedium),
                ),
                if (_servers.isNotEmpty)
                  TextButton.icon(
                    onPressed: _copyAllConfigs,
                    icon: const Icon(Icons.copy_all_outlined, size: 18),
                    label: Text(s.t('copyall.title')),
                  ),
              ],
            ),
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
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                if (srv.latencyMs != null)
                                  Text('${srv.latencyMs} ms',
                                      style: const TextStyle(fontSize: 12)),
                                IconButton(
                                  tooltip: s.t('cfg.view'),
                                  icon: const Icon(Icons.qr_code_2_outlined),
                                  onPressed: () => Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => ConfigDetailScreen(
                                          strings: s, server: srv),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            onTap: () => _select(srv),
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
  final bool busy;
  final String label;
  final VoidCallback? onTap;
  const _ConnectButton({
    required this.connected,
    required this.label,
    this.busy = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: busy ? null : onTap,
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
            if (busy)
              const SizedBox(
                width: 48, height: 48,
                child: CircularProgressIndicator(color: Colors.white),
              )
            else
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
