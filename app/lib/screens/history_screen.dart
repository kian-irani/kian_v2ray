import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../i18n.dart';
import '../models/install_record.dart';
import '../services/cache.dart';
import '../theme.dart';

/// Install history (C-feedback): every server install the user ran from the app,
/// with its subscription link + web-panel URL/credentials, always recoverable.
class HistoryScreen extends StatefulWidget {
  final Strings strings;
  const HistoryScreen({super.key, required this.strings});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _cache = Cache();
  List<InstallRecord> _records = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final r = await _cache.loadInstallHistory();
    if (!mounted) return;
    setState(() { _records = r; _loading = false; });
  }

  Future<void> _delete(int index) async {
    setState(() => _records.removeAt(index));
    await _cache.saveInstallHistory(_records);
  }

  Future<void> _copy(String text, String label) async {
    await Clipboard.setData(ClipboardData(text: text));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(label), duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return Scaffold(
      appBar: AppBar(title: Text(s.t('hist.title'))),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _records.isEmpty
              ? _empty(s)
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _records.length,
                  itemBuilder: (_, i) => _RecordCard(
                    strings: s,
                    record: _records[i],
                    onCopy: _copy,
                    onDelete: () => _confirmDelete(s, i),
                  ),
                ),
    );
  }

  Widget _empty(Strings s) => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.history_toggle_off_outlined,
                  size: 64, color: Color(0xFF3A4A66)),
              const SizedBox(height: 14),
              Text(s.t('hist.empty'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 15)),
              const SizedBox(height: 6),
              Text(s.t('hist.empty.d'),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12, color: Color(0xFF8AA0C0))),
            ],
          ),
        ),
      );

  Future<void> _confirmDelete(Strings s, int index) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(s.t('hist.delete')),
        content: Text(s.t('hist.delete.confirm')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(s.t('cancel'))),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: const Color(0xFFDC2626)),
            onPressed: () => Navigator.pop(context, true),
            child: Text(s.t('hist.delete')),
          ),
        ],
      ),
    );
    if (ok == true) _delete(index);
  }
}

class _RecordCard extends StatefulWidget {
  final Strings strings;
  final InstallRecord record;
  final Future<void> Function(String text, String label) onCopy;
  final VoidCallback onDelete;
  const _RecordCard({
    required this.strings,
    required this.record,
    required this.onCopy,
    required this.onDelete,
  });

  @override
  State<_RecordCard> createState() => _RecordCardState();
}

class _RecordCardState extends State<_RecordCard> {
  bool _showPass = false;

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    final r = widget.record;
    return Card(
      color: const Color(0xFF0E1B33),
      margin: const EdgeInsets.only(bottom: 14),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.dns_outlined, size: 20, color: KianTheme.accent),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(r.serverIp,
                      style: const TextStyle(
                          fontFamily: 'monospace',
                          fontWeight: FontWeight.bold,
                          fontSize: 15)),
                ),
                IconButton(
                  tooltip: s.t('hist.delete'),
                  icon: const Icon(Icons.delete_outline, size: 20, color: Color(0xFFEF6B6B)),
                  onPressed: widget.onDelete,
                ),
              ],
            ),
            Text('${r.dateShort} · ${r.userCount} ${s.t('hist.users')}',
                style: const TextStyle(fontSize: 11, color: Color(0xFF8AA0C0))),
            if (r.protocols.isNotEmpty) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 6, runSpacing: 6,
                children: r.protocols
                    .map((p) => Chip(
                          label: Text(p, style: const TextStyle(fontSize: 11)),
                          backgroundColor: const Color(0xFF13203A),
                          side: const BorderSide(color: Color(0xFF223052)),
                          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          visualDensity: VisualDensity.compact,
                        ))
                    .toList(),
              ),
            ],
            if (r.subUrl != null) ...[
              const Divider(height: 22),
              _copyRow(s.t('hist.sub'), r.subUrl!, () => widget.onCopy(r.subUrl!, s.t('cfg.copied')),
                  prominent: true),
            ],
            if (r.panelUrl != null) ...[
              const SizedBox(height: 10),
              _copyRow(s.t('hist.panel'), r.panelUrl!, () => widget.onCopy(r.panelUrl!, s.t('cfg.copied'))),
            ],
            if (r.panelUser != null) ...[
              const SizedBox(height: 10),
              _credRow(s.t('hist.user'), r.panelUser!, () => widget.onCopy(r.panelUser!, s.t('cfg.copied'))),
            ],
            if (r.panelPass != null) ...[
              const SizedBox(height: 10),
              _credRow(
                s.t('hist.pass'),
                _showPass ? r.panelPass! : '••••••••',
                () => widget.onCopy(r.panelPass!, s.t('cfg.copied')),
                leading: IconButton(
                  tooltip: _showPass ? s.t('hist.hide') : s.t('hist.show'),
                  icon: Icon(_showPass ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                      size: 18),
                  onPressed: () => setState(() => _showPass = !_showPass),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // A label + value + prominent copy button (used for the subscription link).
  Widget _copyRow(String label, String value, VoidCallback onCopy, {bool prominent = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: prominent ? KianTheme.accent : const Color(0xFF8AA0C0))),
        const SizedBox(height: 4),
        Row(
          children: [
            Expanded(
              child: Text(value,
                  maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontFamily: 'monospace', fontSize: 11)),
            ),
            prominent
                ? FilledButton.icon(
                    onPressed: onCopy,
                    icon: const Icon(Icons.copy_outlined, size: 16),
                    label: Text(widget.strings.t('cfg.copy')),
                    style: FilledButton.styleFrom(
                        visualDensity: VisualDensity.compact,
                        padding: const EdgeInsets.symmetric(horizontal: 12)),
                  )
                : IconButton(
                    icon: const Icon(Icons.copy_outlined, size: 18),
                    onPressed: onCopy,
                  ),
          ],
        ),
      ],
    );
  }

  // A credential row (user/pass): optional leading (reveal) + value + copy.
  Widget _credRow(String label, String value, VoidCallback onCopy, {Widget? leading}) {
    return Row(
      children: [
        SizedBox(
          width: 64,
          child: Text(label, style: const TextStyle(fontSize: 11, color: Color(0xFF8AA0C0))),
        ),
        Expanded(
          child: Text(value,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
        ),
        if (leading != null) leading,
        IconButton(
          icon: const Icon(Icons.copy_outlined, size: 18),
          onPressed: onCopy,
        ),
      ],
    );
  }
}
