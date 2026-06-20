import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'i18n.dart';
import 'theme.dart';
import 'screens/home_screen.dart';

void main() => runApp(const KianApp());

class KianApp extends StatefulWidget {
  const KianApp({super.key});
  @override
  State<KianApp> createState() => _KianAppState();
}

class _KianAppState extends State<KianApp> {
  String _lang = 'fa';
  ThemeMode _mode = ThemeMode.dark;

  void _toggleLang() => setState(() => _lang = _lang == 'fa' ? 'en' : 'fa');
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
      ),
    );
  }
}
