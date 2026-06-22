import 'package:flutter/material.dart';

import '../i18n.dart';
import '../models/app_settings.dart';
import '../services/cache.dart';
import '../theme.dart';
import 'per_app_screen.dart';

/// Central settings (parity with v2rayNG / Hiddify): theme, language, routing,
/// kill-switch, auto-connect, proxy-only, DNS, subscription auto-refresh.
class SettingsScreen extends StatefulWidget {
  final Strings strings;
  final VoidCallback onToggleLang;
  final ValueChanged<String> onThemeMode; // 'system'|'dark'|'light'
  const SettingsScreen({
    super.key,
    required this.strings,
    required this.onToggleLang,
    required this.onThemeMode,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _cache = Cache();
  AppSettings _s = AppSettings();
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final raw = await _cache.loadSettings();
    if (!mounted) return;
    setState(() {
      _s = AppSettings.fromJson(raw);
      _loading = false;
    });
  }

  Future<void> _save() async => _cache.saveSettings(_s.toJson());

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(s.t('settings.title'))),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    return Scaffold(
      appBar: AppBar(title: Text(s.t('settings.title'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _section(s.t('settings.appearance')),
          _segment(
            s.t('settings.theme'),
            current: _s.themeMode,
            options: {
              'system': s.t('settings.theme.system'),
              'dark': s.t('settings.theme.dark'),
              'light': s.t('settings.theme.light'),
            },
            onPick: (v) {
              setState(() => _s.themeMode = v);
              widget.onThemeMode(v);
              _save();
            },
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(s.t('settings.language')),
            trailing: OutlinedButton(
              onPressed: widget.onToggleLang,
              child: Text(s.lang == 'fa' ? 'English' : 'فارسی'),
            ),
          ),

          _section(s.t('settings.routing')),
          _segment(
            s.t('settings.routing.mode'),
            current: _s.routing,
            options: {
              'global': s.t('settings.routing.global'),
              'bypass-lan': s.t('settings.routing.lan'),
              'bypass-iran': s.t('settings.routing.iran'),
              'bypass-both': s.t('settings.routing.both'),
            },
            onPick: (v) { setState(() => _s.routing = v); _save(); },
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _s.proxyOnly,
            onChanged: (v) { setState(() => _s.proxyOnly = v); _save(); },
            title: Text(s.t('settings.proxyonly')),
            subtitle: Text(s.t('settings.proxyonly.d')),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.apps_outlined),
            title: Text(s.t('settings.perapp')),
            subtitle: Text(s.t('settings.perapp.d')),
            trailing: Row(mainAxisSize: MainAxisSize.min, children: [
              if (_s.perAppProxy.isNotEmpty)
                Text('${_s.perAppProxy.length}',
                    style: const TextStyle(color: KianTheme.accent)),
              const Icon(Icons.chevron_right),
            ]),
            onTap: () async {
              await Navigator.push(context, MaterialPageRoute(
                  builder: (_) => PerAppScreen(strings: widget.strings)));
              await _load(); // refresh count after returning
            },
          ),

          _section(s.t('settings.dns')),
          _dnsField(s.t('settings.dns.remote'), _s.remoteDns,
              (v) { _s.remoteDns = v; _save(); }),
          _dnsField(s.t('settings.dns.direct'), _s.directDns,
              (v) { _s.directDns = v; _save(); }),

          _section(s.t('settings.connection')),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _s.killSwitch,
            onChanged: (v) { setState(() => _s.killSwitch = v); _save(); },
            title: Text(s.t('settings.killswitch')),
            subtitle: Text(s.t('settings.killswitch.d')),
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _s.autoConnect,
            onChanged: (v) { setState(() => _s.autoConnect = v); _save(); },
            title: Text(s.t('settings.autoconnect')),
            subtitle: Text(s.t('settings.autoconnect.d')),
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _s.autoRefreshSubs,
            onChanged: (v) { setState(() => _s.autoRefreshSubs = v); _save(); },
            title: Text(s.t('settings.autorefresh')),
            subtitle: Text(s.t('settings.autorefresh.d')),
          ),

          const SizedBox(height: 16),
          _helpCard(s),
        ],
      ),
    );
  }

  Widget _section(String title) => Padding(
        padding: const EdgeInsets.fromLTRB(0, 16, 0, 8),
        child: Text(title,
            style: const TextStyle(
                color: KianTheme.accent, fontWeight: FontWeight.bold, fontSize: 13)),
      );

  Widget _segment(String label,
      {required String current,
      required Map<String, String> options,
      required ValueChanged<String> onPick}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Text(label, style: const TextStyle(fontSize: 13)),
        ),
        Wrap(
          spacing: 8, runSpacing: 8,
          children: options.entries.map((e) {
            final on = e.key == current;
            return ChoiceChip(
              label: Text(e.value, style: const TextStyle(fontSize: 12)),
              selected: on,
              showCheckmark: false,
              selectedColor: KianTheme.accent.withOpacity(0.25),
              onSelected: (_) => onPick(e.key),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _dnsField(String label, String value, ValueChanged<String> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: TextFormField(
        initialValue: value,
        decoration: InputDecoration(labelText: label),
        keyboardType: TextInputType.url,
        onChanged: onChanged,
      ),
    );
  }

  Widget _helpCard(Strings s) => Card(
        color: const Color(0xFF0E1B33),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                const Icon(Icons.help_outline, size: 18, color: KianTheme.accent),
                const SizedBox(width: 8),
                Text(s.t('settings.help'),
                    style: const TextStyle(color: KianTheme.accent, fontWeight: FontWeight.bold)),
              ]),
              const SizedBox(height: 8),
              Text(s.t('settings.help.body'), style: const TextStyle(fontSize: 12)),
            ],
          ),
        ),
      );
}
