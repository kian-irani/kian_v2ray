import 'package:flutter/material.dart';
import 'package:installed_apps/app_info.dart';
import 'package:installed_apps/installed_apps.dart';

import '../i18n.dart';
import '../models/app_settings.dart';
import '../services/cache.dart';
import '../theme.dart';

/// Per-app proxy / split-tunnel picker (9.2). Choose which installed apps
/// BYPASS the VPN (go direct, not tunneled). Empty selection = every app is
/// tunneled (default). Stored in AppSettings.perAppProxy and applied at connect
/// time directly as flutter_v2ray's `blockedApps` (the bypass list — see
/// VpnController.start). Parity with v2rayNG/Hiddify split-tunnel.
class PerAppScreen extends StatefulWidget {
  final Strings strings;
  const PerAppScreen({super.key, required this.strings});

  @override
  State<PerAppScreen> createState() => _PerAppScreenState();
}

class _PerAppScreenState extends State<PerAppScreen> {
  final _cache = Cache();
  List<AppInfo> _apps = [];
  final Set<String> _selected = {};
  bool _loading = true;
  String _query = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final settings = AppSettings.fromJson(await _cache.loadSettings());
    _selected.addAll(settings.perAppProxy);
    List<AppInfo> apps = [];
    try {
      apps = await InstalledApps.getInstalledApps(true, true); // exclude system, with icons
      apps.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    } catch (_) {
      apps = [];
    }
    if (!mounted) return;
    setState(() { _apps = apps; _loading = false; });
  }

  Future<void> _save() async {
    final raw = await _cache.loadSettings();
    final s = AppSettings.fromJson(raw);
    s.perAppProxy = _selected.toList();
    await _cache.saveSettings(s.toJson());
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    final filtered = _query.isEmpty
        ? _apps
        : _apps.where((a) => a.name.toLowerCase().contains(_query.toLowerCase())).toList();
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('perapp.title')),
        actions: [
          if (_selected.isNotEmpty)
            TextButton(
              onPressed: () { setState(_selected.clear); _save(); },
              child: Text(s.t('perapp.clear')),
            ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(
                    _selected.isEmpty ? s.t('perapp.all') : s.t('perapp.some'),
                    style: const TextStyle(fontSize: 12, color: Color(0xFF8AA0C0)),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  child: TextField(
                    decoration: InputDecoration(
                      prefixIcon: const Icon(Icons.search),
                      hintText: s.t('perapp.search'),
                      isDense: true,
                    ),
                    onChanged: (v) => setState(() => _query = v),
                  ),
                ),
                Expanded(
                  child: _apps.isEmpty
                      ? Center(child: Text(s.t('perapp.none')))
                      : ListView.builder(
                          itemCount: filtered.length,
                          itemBuilder: (_, i) {
                            final a = filtered[i];
                            final on = _selected.contains(a.packageName);
                            return CheckboxListTile(
                              value: on,
                              activeColor: KianTheme.accent,
                              secondary: a.icon != null
                                  ? Image.memory(a.icon!, width: 32, height: 32)
                                  : const Icon(Icons.android),
                              title: Text(a.name),
                              subtitle: Text(a.packageName,
                                  style: const TextStyle(fontSize: 11),
                                  maxLines: 1, overflow: TextOverflow.ellipsis),
                              onChanged: (v) {
                                setState(() {
                                  if (v == true) {
                                    _selected.add(a.packageName);
                                  } else {
                                    _selected.remove(a.packageName);
                                  }
                                });
                                _save();
                              },
                            );
                          },
                        ),
                ),
              ],
            ),
    );
  }
}
