import 'package:flutter/material.dart';

import '../i18n.dart';
import '../services/panel_api.dart';
import '../theme.dart';

/// In-app server management (the web-panel sections, native — no browser).
/// Connect to a deployed KIAN panel, then manage users + see stats.
class ManageScreen extends StatefulWidget {
  final Strings strings;
  const ManageScreen({super.key, required this.strings});

  @override
  State<ManageScreen> createState() => _ManageScreenState();
}

class _ManageScreenState extends State<ManageScreen> {
  final _url = TextEditingController(text: 'http://');
  final _user = TextEditingController(text: 'admin');
  final _pass = TextEditingController();
  PanelApi? _api;
  bool _busy = false;
  String? _error;
  List<Map<String, dynamic>> _users = [];
  Map<String, dynamic> _stats = {};

  Future<void> _connect() async {
    setState(() { _busy = true; _error = null; });
    final api = PanelApi(_url.text.trim());
    final ok = await api.login(_user.text.trim(), _pass.text);
    if (!mounted) return;
    if (!ok) {
      setState(() { _busy = false; _error = 'login failed'; });
      return;
    }
    _api = api;
    await _refresh();
  }

  Future<void> _refresh() async {
    if (_api == null) return;
    setState(() => _busy = true);
    await _api!.sync();
    final u = await _api!.users();
    final s = await _api!.stats();
    if (!mounted) return;
    setState(() { _users = u; _stats = s; _busy = false; });
  }

  Future<void> _addUser() async {
    final ctrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(widget.strings.t('mg.add')),
        content: TextField(controller: ctrl,
            decoration: const InputDecoration(hintText: 'name')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false),
              child: Text(widget.strings.t('cancel'))),
          FilledButton(onPressed: () => Navigator.pop(context, true),
              child: Text(widget.strings.t('mg.add'))),
        ],
      ),
    );
    if (ok == true && ctrl.text.trim().isNotEmpty) {
      await _api!.addUser(ctrl.text.trim());
      await _refresh();
    }
  }

  String _gb(num b) => (b / 1073741824).toStringAsFixed(1);

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('mg.title')),
        actions: [
          if (_api != null)
            IconButton(onPressed: _busy ? null : _refresh,
                icon: const Icon(Icons.refresh)),
        ],
      ),
      body: _api == null ? _connectForm(s) : _dashboard(s),
      floatingActionButton: _api == null
          ? null
          : FloatingActionButton(onPressed: _addUser, child: const Icon(Icons.add)),
    );
  }

  Widget _connectForm(Strings s) {
    return Padding(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(s.t('mg.connect'), style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          TextField(controller: _url,
              decoration: InputDecoration(labelText: s.t('mg.url'),
                  hintText: 'http://1.2.3.4:8443')),
          const SizedBox(height: 10),
          TextField(controller: _user,
              decoration: InputDecoration(labelText: s.t('login.user'))),
          const SizedBox(height: 10),
          TextField(controller: _pass, obscureText: true,
              decoration: InputDecoration(labelText: s.t('login.pass'))),
          const SizedBox(height: 8),
          if (_error != null)
            Text(_error!, style: const TextStyle(color: KianTheme.danger)),
          const SizedBox(height: 12),
          FilledButton(onPressed: _busy ? null : _connect,
              child: Text(_busy ? '…' : s.t('mg.connectbtn'))),
        ],
      ),
    );
  }

  Widget _dashboard(Strings s) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          Row(children: [
            _statCard(s.t('stat.total'), '${_stats['total_users'] ?? '—'}'),
            _statCard(s.t('stat.active'), '${_stats['active_users'] ?? '—'}'),
            _statCard(s.t('stat.traffic'),
                '${_gb((_stats['total_used_bytes'] ?? 0) as num)} GB'),
          ]),
          const SizedBox(height: 12),
          ..._users.map((u) => Card(
                child: ListTile(
                  leading: Icon(
                    (u['enabled'] == 1) ? Icons.check_circle : Icons.block,
                    color: (u['enabled'] == 1) ? KianTheme.accent : KianTheme.danger,
                  ),
                  title: Text('${u['name']}'),
                  subtitle: Text(
                      '${_gb((u['used_bytes'] ?? 0) as num)} GB'
                      '${(u['ip_limit'] ?? 0) != 0 ? " · IP ${u['ip_limit']}" : ""}'),
                  trailing: PopupMenuButton<String>(
                    onSelected: (v) async {
                      if (v == 'toggle') {
                        await _api!.setEnabled('${u['name']}', u['enabled'] != 1);
                      } else if (v == 'delete') {
                        await _api!.deleteUser('${u['name']}');
                      }
                      await _refresh();
                    },
                    itemBuilder: (_) => [
                      PopupMenuItem(value: 'toggle', child: Text(s.t('mg.toggle'))),
                      PopupMenuItem(value: 'delete', child: Text(s.t('mg.delete'))),
                    ],
                  ),
                ),
              )),
        ],
      ),
    );
  }

  Widget _statCard(String label, String value) => Expanded(
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(children: [
              Text(value, style: const TextStyle(
                  fontSize: 20, fontWeight: FontWeight.bold)),
              Text(label, style: const TextStyle(
                  fontSize: 12, color: KianTheme.accent)),
            ]),
          ),
        ),
      );

  @override
  void dispose() {
    _url.dispose();
    _user.dispose();
    _pass.dispose();
    super.dispose();
  }
}
