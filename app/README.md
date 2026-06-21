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

The repo ships the **custom** Android sources (VPN-specific): `android/` Gradle
config, `AndroidManifest.xml` (VpnService + perms), `MainActivity.kt` (the
`kv2m/vpn` MethodChannel) and `KianVpnService.kt` (the tun setup). The standard
generated boilerplate (the Gradle wrapper, launcher-icon PNGs, `local.properties`)
is produced once by Flutter:

```bash
cd app
flutter create . --platforms=android --org com.kianirani   # fills generated boilerplate (keeps our files)
flutter pub get
dart run flutter_launcher_icons                              # generate launcher icons from a logo
flutter build apk --release          # sideload / Cafe Bazaar / Myket / F-Droid
flutter build appbundle --release    # Google Play (AAB)
```

Target: SDK 35+ (Android 15), 64-bit + 32-bit ABIs, min SDK 23.

### The tunnel core

`KianVpnService.startTunnelCore()` is where the native tunnel (xray-core's
Android `.aar`) is wired in — it receives the tun fd + the per-server config
JSON that the Dart layer builds. Until the `.aar` is bundled it's a no-op, so
the project builds and the whole UI/flow works; only real packet forwarding
waits on the native core. This is the single remaining native-integration step.

## No-GMS design (6.4)

- No Firebase / AdMob / Google Maps / FCM.
- Push uses **SSE or the Telegram bot**, not FCM.
- QR scanning uses `mobile_scanner` (works without Play Services).
- Smart server selection is pure Dart TCP latency (no Google location).

## Release order (6.6)

GitHub Releases (APK) → Telegram beta → **Cafe Bazaar** → Myket → F-Droid →
Google Play (Open Testing → Production) → iOS (later).

See `KEYSTORE.md` before the first signed build.
