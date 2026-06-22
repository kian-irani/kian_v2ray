import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'i18n.dart';
import 'theme.dart';
import 'screens/home_screen.dart';
import 'services/cache.dart';

void main() => runApp(const KianApp());

class KianApp extends StatefulWidget {
  const KianApp({super.key});
  @override
  State<KianApp> createState() => _KianAppState();
}

class _KianAppState extends State<KianApp> {
  String _lang = 'en';           // English default (matches install + page)
  ThemeMode _mode = ThemeMode.system;
  final _cache = Cache();

  @override
  void initState() {
    super.initState();
    _restorePrefs();
  }

  Future<void> _restorePrefs() async {
    final (lang, _) = await _cache.loadPrefs();
    final settings = await _cache.loadSettings();
    if (!mounted) return;
    setState(() {
      _lang = lang;
      _mode = _modeFrom(settings['themeMode'] as String?);
    });
  }

  ThemeMode _modeFrom(String? m) => switch (m) {
        'dark' => ThemeMode.dark,
        'light' => ThemeMode.light,
        _ => ThemeMode.system,
      };

  void setThemeMode(String m) => setState(() => _mode = _modeFrom(m));

  void _toggleLang() {
    setState(() => _lang = _lang == 'fa' ? 'en' : 'fa');
    _cache.savePrefs(lang: _lang);
  }

  void _toggleTheme() =>
      setState(() => _mode = _mode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark);

  @override
  Widget build(BuildContext context) {
    final s = Strings(_lang);
    return MaterialApp(
      title: 'Kv2m',
      debugShowCheckedModeBanner: false,
      theme: KianTheme.light(),
      darkTheme: KianTheme.dark(),
      themeMode: _mode,
      locale: s.locale,
      supportedLocales: const [Locale('fa'), Locale('en')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      builder: (context, child) =>
          Directionality(textDirection: s.dir, child: child!),
      home: HomeScreen(
        strings: s,
        onToggleLang: _toggleLang,
        onToggleTheme: _toggleTheme,
        onThemeMode: setThemeMode,
      ),
    );
  }
}
