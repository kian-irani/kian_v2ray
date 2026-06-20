import 'package:flutter/material.dart';

/// KIAN brand theme — dark-first (matches the panel: deep navy + connected
/// green), with a light variant. Stored choice is applied at boot (3.4 / 6.x).
class KianTheme {
  static const Color navy = Color(0xFF0F172A);
  static const Color primary = Color(0xFF1E3A5F);
  static const Color accent = Color(0xFF22C55E); // "connected" green
  static const Color danger = Color(0xFFDC2626);

  static ThemeData dark() {
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: navy,
      colorScheme: base.colorScheme.copyWith(
        primary: accent,
        secondary: primary,
        surface: const Color(0xFF111C33),
        error: danger,
      ),
      cardTheme: CardThemeData(
        color: Colors.white.withValues(alpha: 0.04),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(backgroundColor: accent, foregroundColor: navy),
      ),
    );
  }

  static ThemeData light() {
    final base = ThemeData.light(useMaterial3: true);
    return base.copyWith(
      colorScheme: base.colorScheme.copyWith(primary: primary, secondary: accent, error: danger),
    );
  }
}
