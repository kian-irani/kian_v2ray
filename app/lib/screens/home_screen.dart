import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../i18n.dart';
import '../models/app_settings.dart';
import '../models/server_profile.dart';
import '../services/cache.dart';
import '../services/selection.dart';
import '../services/subscription.dart';
import '../services/vpn_service.dart';
import '../theme.dart';
import '../widgets/help_card.dart';
import 'config_detail_screen.dart';
import 'history_screen.dart';
import 'manage_screen.dart';
import 'settings_screen.dart';
import 'setup_screen.dart';

class HomeScreen extends StatefulWidget {
  final Strings strings;
  final VoidCallback onToggleLang;
  final VoidCallback onToggleTheme;
  final ValueChanged<String> onThemeMode;
  const HomeScreen({
    super.key,
    required this.strings,
    required this.onToggleLang,
    required this.onToggleTheme,
    required this.onThemeMode,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final List<ServerProfile> _servers = [];
  final _cache = Cache();
  late final VpnController _vpn;
  final _selection = const SmartSelection();
  final _subs = SubscriptionService();
  ServerProfile? _selected;
  String? _subUrl;
  bool _connected = false;
  bool _busy = false;
  bool _refreshing = false;

  @override
  void initState() {
    super.initState();
    _vpn = VpnController(onStats: () {
      if (mounted) setState(() {}); // refresh live up/down + duration
    });
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
    // Auto-refresh subscriptions on launch (silent — won't disrupt if offline).
    final sources = await _subs.loadSources();
    if (sources.isNotEmpty) _refreshSubs(silent: true);
    // Deep-link: if the app was opened by tapping a share link / sub URL, import it.
    final link = await _vpn.initialLink();
    if (link != null && link.isNotEmpty) await _importLink(link);
  }

  /// Re-fetch all subscription sources and merge with manually-added servers.
  Future<void> _refreshSubs({bool silent = false}) async {
    if (_refreshing) return;
    setState(() => _refreshing = true);
    try {
      final fresh = await _subs.refreshAll(DateTime.now().toIso8601String());
      if (!mounted) return;
      if (fresh.isEmpty && !silent) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(widget.strings.t('sub.refresh.none')),
              duration: const Duration(seconds: 2)),
        );
        return;
      }
      // keep manual servers (source == null), replace all sub-sourced ones
      final manual = _servers.where((s) => s.source == null).toList();
      final selName = _selected?.name;
      setState(() {
        _servers
          ..clear()
          ..addAll(manual)
          ..addAll(fresh);
        ServerProfile? match;
        for (final s in _servers) {
          if (s.name == selName) { match = s; break; }
        }
        _selected = match ?? (_servers.isNotEmpty ? _servers.first : null);
      });
      await _cache.saveServers(_servers);
      if (!silent && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${widget.strings.t('sub.refresh.done')} (${fresh.length})'),
              duration: const Duration(seconds: 2)),
        );
      }
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  /// Reload the server list from cache (after setup auto-imports configs).
  Future<void> _reloadFromCache() async {
    final saved = await _cache.loadServers();
    final sel = await _cache.loadSelected();
    final sub = await _cache.loadSubUrl();
    // Register the install's sub link as a refreshable source so future configs
    // (port remaps, added users) auto-update — connects the wizard to refresh.
    if (sub != null && sub.isNotEmpty) await _subs.addSource(sub);
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

  Future<void> _importLink(String body) async {
    final text = body.trim();
    if (text.isEmpty) return;
    // A subscription URL → register it as a source and fetch it (keeps updating
    // automatically on future launches / manual refresh). Otherwise treat the
    // text as raw share link(s) / base64 and add once.
    if (SubscriptionService.isSubUrl(text)) {
      await _subs.addSource(text);
      await _refreshSubs();
      return;
    }
    final parsed = parseSubscription(text);
    if (parsed.isEmpty) return;
    setState(() {
      _servers.addAll(parsed);
      _selected ??= _servers.first;
    });
    _cache.saveServers(_servers);
  }

  Future<void> _toggleConnection() async {
    if (_selected == null || _busy) return;
    // Honesty guard: if this build has no native tunnel core, connecting would
    // route all traffic into a dead tunnel and kill the user's internet. Don't.
    if (!_connected) {
      final hasCore = await _vpn.coreAvailable();
      if (!hasCore) {
        if (mounted) await _showNoCoreDialog();
        return;
      }
    }
    setState(() => _busy = true);
    try {
      if (_connected) {
        await _vpn.stop();
        if (mounted) setState(() => _connected = false);
      } else {
        final cfg = AppSettings.fromJson(await _cache.loadSettings());
        final ok = await _vpn.start(_selected!,
            proxyOnly: cfg.proxyOnly, bypassSubnets: cfg.bypassSubnets());
        if (mounted) setState(() => _connected = ok);
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  /// Explain (honestly) that this build can't tunnel on-device yet, and offer
  /// the real path: copy the config and import it into v2rayNG.
  Future<void> _showNoCoreDialog() async {
    final s = widget.strings;
    await showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(s.t('nocore.title')),
        content: Text(s.t('nocore.body')),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(s.t('cancel')),
          ),
          if (_selected != null)
            FilledButton.icon(
              onPressed: () async {
                await Clipboard.setData(ClipboardData(text: _selected!.uri));
                if (!context.mounted) return;
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(s.t('cfg.copied')),
                      duration: const Duration(seconds: 2)),
                );
              },
              icon: const Icon(Icons.copy_outlined, size: 18),
              label: Text(s.t('cfg.copy')),
            ),
        ],
      ),
    );
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

  /// Helpful empty state with icon + two clear actions (design review).
  Widget _emptyServers(Strings s) => Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_outlined, size: 64, color: Color(0xFF3A4A66)),
              const SizedBox(height: 14),
              Text(s.t('servers.empty'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 15)),
              const SizedBox(height: 6),
              Text(s.t('servers.empty.d'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12, color: Color(0xFF8AA0C0))),
              const SizedBox(height: 16),
              Wrap(
                spacing: 10, runSpacing: 10, alignment: WrapAlignment.center,
                children: [
                  OutlinedButton.icon(
                    onPressed: () => _showImport(context, s),
                    icon: const Icon(Icons.add, size: 18),
                    label: Text(s.t('import.title')),
                  ),
                  FilledButton.icon(
                    onPressed: () async {
                      await Navigator.push(context, MaterialPageRoute(
                          builder: (_) => SetupScreen(strings: s)));
                      await _reloadFromCache();
                    },
                    icon: const Icon(Icons.rocket_launch_outlined, size: 18),
                    label: Text(s.t('open.setup')),
                  ),
                ],
              ),
            ],
          ),
        ),
      );

  /// Rename a server (config management, 9.11). Updates the cache.
  Future<void> _renameServer(ServerProfile srv) async {
    final s = widget.strings;
    final ctrl = TextEditingController(text: srv.name);
    final newName = await showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(s.t('cfg.rename')),
        content: TextField(
          controller: ctrl, autofocus: true,
          decoration: InputDecoration(labelText: s.t('cfg.name')),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text(s.t('cancel'))),
          FilledButton(
            onPressed: () => Navigator.pop(context, ctrl.text.trim()),
            child: Text(s.t('cfg.save')),
          ),
        ],
      ),
    );
    if (newName == null || newName.isEmpty) return;
    final idx = _servers.indexOf(srv);
    if (idx < 0) return;
    final renamed = ServerProfile(
      name: newName, uri: srv.uri, host: srv.host, port: srv.port,
      protocol: srv.protocol, latencyMs: srv.latencyMs, source: srv.source,
    );
    setState(() {
      _servers[idx] = renamed;
      if (_selected == srv) _selected = renamed;
    });
    await _cache.saveServers(_servers);
  }

  /// Delete a server with an undo snackbar (config management, 9.11).
  Future<void> _deleteServer(ServerProfile srv) async {
    final s = widget.strings;
    final idx = _servers.indexOf(srv);
    if (idx < 0) return;
    setState(() {
      _servers.removeAt(idx);
      if (_selected == srv) _selected = _servers.isNotEmpty ? _servers.first : null;
    });
    await _cache.saveServers(_servers);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(s.t('cfg.deleted')),
        duration: const Duration(seconds: 4),
        action: SnackBarAction(
          label: s.t('cfg.undo'),
          onPressed: () async {
            setState(() => _servers.insert(idx.clamp(0, _servers.length), srv));
            await _cache.saveServers(_servers);
          },
        ),
      ),
    );
  }

  /// Live up/down speed + session duration while connected (parity feature).
  Widget _statsRow(Strings s) {
    Widget cell(IconData ic, String label, String val) => Expanded(
          child: Column(
            children: [
              Icon(ic, size: 18, color: KianTheme.accent),
              const SizedBox(height: 4),
              Text(val, style: const TextStyle(
                  fontFamily: 'monospace', fontWeight: FontWeight.bold, fontSize: 13)),
              Text(label, style: const TextStyle(fontSize: 10, color: Color(0xFF8AA0C0))),
            ],
          ),
        );
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF0E1B33),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(children: [
        cell(Icons.south_outlined, s.t('stats.down'), '${_fmtSpeed(_vpn.downloadSpeed)}/s'),
        cell(Icons.north_outlined, s.t('stats.up'), '${_fmtSpeed(_vpn.uploadSpeed)}/s'),
        cell(Icons.timer_outlined, s.t('stats.time'), _vpn.duration),
      ]),
    );
  }

  String _fmtSpeed(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / 1024 / 1024).toStringAsFixed(1)} MB';
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
          IconButton(
            tooltip: s.t('sub.refresh'),
            onPressed: _refreshing ? null : () => _refreshSubs(),
            icon: _refreshing
                ? const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.refresh_outlined),
          ),
          IconButton(
            tooltip: s.t('settings.open'),
            onPressed: () => Navigator.push(context, MaterialPageRoute(
                builder: (_) => SettingsScreen(
                  strings: s,
                  onToggleLang: widget.onToggleLang,
                  onThemeMode: widget.onThemeMode,
                ))),
            icon: const Icon(Icons.settings_outlined),
          ),
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
            if (_connected) ...[
              const SizedBox(height: 12),
              _statsRow(s),
            ],
            const SizedBox(height: 14),
            HelpCard(title: s.t('help.title'), body: s.t('help.home'),
                initiallyExpanded: _servers.isEmpty),
            const SizedBox(height: 14),
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
                  ? _emptyServers(s)
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
                                PopupMenuButton<String>(
                                  tooltip: s.t('cfg.more'),
                                  icon: const Icon(Icons.more_vert),
                                  onSelected: (v) {
                                    if (v == 'rename') _renameServer(srv);
                                    if (v == 'delete') _deleteServer(srv);
                                  },
                                  itemBuilder: (_) => [
                                    PopupMenuItem(value: 'rename',
                                        child: Text(s.t('cfg.rename'))),
                                    PopupMenuItem(value: 'delete',
                                        child: Text(s.t('cfg.delete'))),
                                  ],
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
