# Kv2m — Mobile App (Flutter, phase 6)

The mobile member of the **Kv2m** family (same brand as the Kv2m desktop app),
a privacy-first VPN client. **Android-first and deliberately GMS-free** so it
ships on Cafe Bazaar, Myket and F-Droid (not just Google Play).

## Structure

```
app/
├── pubspec.yaml
├── lib/
│   ├── main.dart                 # MaterialApp, RTL/LTR, dark/light toggle
│   ├── theme.dart                # KIAN dark-glass theme (navy + green)
│   ├── i18n.dart                 # FA/EN strings + direction
│   ├── models/server_profile.dart# share-link + subscription parsing
│   ├── services/selection.dart   # smart server selection (TCP latency)
│   └── screens/home_screen.dart  # connect button + server list + import
├── test/                         # dart unit tests (parsing, selection)
├── fastlane/metadata/android/    # store listings (fa-IR + en-US)
├── KEYSTORE.md                   # signing + 3-backup policy
└── PRIVACY-fa.md                 # Persian privacy policy (market requirement)
```

## Build

```bash
cd app
flutter pub get
flutter build apk --release          # sideload / Cafe Bazaar / Myket / F-Droid
flutter build appbundle --release    # Google Play (AAB)
```

Target: SDK 35+ (Android 15), 64-bit ABIs, min SDK 23.

## No-GMS design (6.4)

- No Firebase / AdMob / Google Maps / FCM.
- Push uses **SSE or the Telegram bot**, not FCM.
- QR scanning uses `mobile_scanner` (works without Play Services).
- Smart server selection is pure Dart TCP latency (no Google location).

## Release order (6.6)

GitHub Releases (APK) → Telegram beta → **Cafe Bazaar** → Myket → F-Droid →
Google Play (Open Testing → Production) → iOS (later).

See `KEYSTORE.md` before the first signed build.
