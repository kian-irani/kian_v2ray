import 'package:flutter/material.dart';

import '../i18n.dart';
import '../models/server_profile.dart';
import '../services/cache.dart';
import '../services/config_gen.dart';
import '../services/ssh_installer.dart';
import '../theme.dart';

/// Setup wizard (C7): the app generates the config (client-side keys + the same
/// Gist subscription as the web), SSHes into the server, and runs the install —
/// the whole flow, no terminal needed.
class SetupScreen extends StatefulWidget {
  final Strings strings;
  const SetupScreen({super.key, required this.strings});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final _ip = TextEditingController();
  final _sshPort = TextEditingController(text: '22');
  final _sshUser = TextEditingController(text: 'root');
  final _sshPass = TextEditingController();
  final _username = TextEditingController(text: 'ali');
  final _tlsDomain = TextEditingController();

  bool _warp = false;
  bool _ss = false;
  bool _tls = false;
  bool _hy2 = false;
  bool _tuic = false;
  bool _busy = false;
  final _log = <String>[];
  String? _subUrl;
  int _imported = 0;

  void _say(String s) => setState(() => _log.add(s));

  /// Turn the generated per-user links into ServerProfiles for the home list.
  /// Names come from the link label (#KIAN-<name>-<port>) when present.
  List<ServerProfile> _profilesFromBundle(InstallBundle bundle) {
    final out = <ServerProfile>[];
    for (final links in bundle.perUserLinks.values) {
      for (final link in links) {
        String? name;
        final frag = Uri.tryParse(link)?.fragment;
        if (frag != null && frag.isNotEmpty) name = Uri.decodeComponent(frag);
        out.add(ServerProfile.fromUri(link, name: name));
      }
    }
    return out;
  }

  Future<void> _run() async {
    setState(() { _busy = true; _log.clear(); _subUrl = null; });
    final ssh = SshInstaller();
    try {
      _say('• ساختِ کانفیگ و کلید (روی همین دستگاه)…');
      final gen = ConfigGen();
      final bundle = await gen.build(
        serverIp: _ip.text.trim(),
        userPrefix: _username.text.trim().isEmpty ? 'user' : _username.text.trim(),
        warp: _warp,
        ss: _ss,
        tlsDomain: _tls ? _tlsDomain.text.trim() : null,
        tlsProtoKinds: _tls ? const ['vless-ws', 'vmess-ws', 'trojan-ws'] : const [],
        extraProtocols: [if (_hy2) 'hysteria2', if (_tuic) 'tuic'],
      );

      _say('• ساختِ لینکِ Subscription روی Gist…');
      final urls = await gen.createGistSubs(bundle.installId, bundle.subItems);
      final firstUrl = urls.values.isNotEmpty ? urls.values.first : null;

      _say('• اتصالِ SSH به ${_ip.text.trim()}…');
      final err = await ssh.connect(
        host: _ip.text.trim(),
        port: int.tryParse(_sshPort.text.trim()) ?? 22,
        user: _sshUser.text.trim().isEmpty ? 'root' : _sshUser.text.trim(),
        password: _sshPass.text,
      );
      if (err != null) { _say('✘ اتصال نشد: $err'); return; }
      _say('✔ متصل شد. در حالِ نصب (۲–۵ دقیقه)…');

      final (code, out) = await ssh.runInstall(bundle.installCommand);
      _say(out.trim().split('\n').take(8).join('\n'));
      if (code == 0) {
        _say('✅ نصب کامل شد.');
        // Auto-import the generated configs into the app's server list so the
        // user doesn't have to copy the sub link by hand (the #1 complaint).
        final imported = _profilesFromBundle(bundle);
        if (imported.isNotEmpty) {
          final cache = Cache();
          final existing = await cache.loadServers();
          existing.addAll(imported);
          await cache.saveServers(existing);
          await cache.saveSelected(imported.first.name);
          _say('✅ ${imported.length} کانفیگ به اپ اضافه شد — در صفحهٔ خانه ببین.');
        }
        setState(() { _subUrl = firstUrl; _imported = imported.length; });
      } else {
        _say('⚠️ کدِ خروجی $code — لاگ را ببین.');
      }
    } catch (e) {
      _say('✘ خطا: $e');
    } finally {
      ssh.close();
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return Scaffold(
      appBar: AppBar(title: Text(s.t('setup.title'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(s.t('setup.desc'), style: const TextStyle(color: KianTheme.accent)),
          const SizedBox(height: 12),
          _field(_ip, s.t('setup.ip'), hint: '185.x.x.x'),
          Row(children: [
            Expanded(flex: 2, child: _field(_sshPort, s.t('setup.sshport'))),
            const SizedBox(width: 10),
            Expanded(flex: 3, child: _field(_sshUser, s.t('setup.sshuser'))),
          ]),
          _field(_sshPass, s.t('setup.sshpass'), obscure: true),
          _field(_username, s.t('setup.username')),
          const SizedBox(height: 4),
          SwitchListTile(
            value: _warp, onChanged: (v) => setState(() => _warp = v),
            title: Text(s.t('setup.warp')), subtitle: Text(s.t('setup.warp.d')),
            contentPadding: EdgeInsets.zero,
          ),
          SwitchListTile(
            value: _ss, onChanged: (v) => setState(() => _ss = v),
            title: Text(s.t('setup.ss')), subtitle: Text(s.t('setup.ss.d')),
            contentPadding: EdgeInsets.zero,
          ),
          SwitchListTile(
            value: _tls, onChanged: (v) => setState(() => _tls = v),
            title: Text(s.t('setup.tls')), subtitle: Text(s.t('setup.tls.d')),
            contentPadding: EdgeInsets.zero,
          ),
          if (_tls)
            _field(_tlsDomain, s.t('setup.tlsdomain'), hint: 'vpn.example.com'),
          const Divider(height: 24),
          Text(s.t('setup.extra'),
              style: const TextStyle(color: KianTheme.accent, fontWeight: FontWeight.bold)),
          Text(s.t('setup.extra.d'), style: const TextStyle(fontSize: 12)),
          SwitchListTile(
            value: _hy2, onChanged: (v) => setState(() => _hy2 = v),
            title: Text(s.t('setup.hy2')), subtitle: Text(s.t('setup.hy2.d')),
            contentPadding: EdgeInsets.zero,
          ),
          SwitchListTile(
            value: _tuic, onChanged: (v) => setState(() => _tuic = v),
            title: Text(s.t('setup.tuic')), subtitle: Text(s.t('setup.tuic.d')),
            contentPadding: EdgeInsets.zero,
          ),
          const SizedBox(height: 14),
          FilledButton.icon(
            onPressed: _busy ? null : _run,
            icon: _busy
                ? const SizedBox(width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.rocket_launch_outlined),
            label: Text(_busy ? '…' : s.t('setup.install')),
          ),
          const SizedBox(height: 14),
          if (_log.isNotEmpty)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF0B1426),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(_log.join('\n'),
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
            ),
          if (_subUrl != null) ...[
            const SizedBox(height: 14),
            Text(s.t('setup.sublink'),
                style: const TextStyle(color: KianTheme.accent)),
            SelectableText(_subUrl!,
                style: const TextStyle(fontFamily: 'monospace')),
          ],
          if (_imported > 0) ...[
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => Navigator.pop(context, true),
              icon: const Icon(Icons.home_outlined),
              label: Text(s.t('setup.gohome')),
            ),
          ],
        ],
      ),
    );
  }

  Widget _field(TextEditingController c, String label,
      {String? hint, bool obscure = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: TextField(
        controller: c,
        obscureText: obscure,
        decoration: InputDecoration(labelText: label, hintText: hint),
      ),
    );
  }

  @override
  void dispose() {
    _ip.dispose();
    _sshPort.dispose();
    _sshUser.dispose();
    _sshPass.dispose();
    _username.dispose();
    _tlsDomain.dispose();
    super.dispose();
  }
}
