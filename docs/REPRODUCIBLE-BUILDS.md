# Reproducible Builds

KIAN's release artifacts are built by **public CI from a tagged commit** — anyone
can rebuild the exact same inputs and compare. This documents how, so the builds
are auditable (and to support an eventual F-Droid submission).

## What is pinned

| Artifact | Toolchain pin | Source of truth |
|----------|---------------|-----------------|
| Installer / scripts | `XRAY_VERSION`, `SINGBOX_VERSION` | [`VERSION`](../VERSION) |
| Android app (Kv2m) | Flutter `3.24.5`, Java `17`, AGP/Gradle `8.7` | [`.github/workflows/build-app.yml`](../.github/workflows/build-app.yml) |
| Desktop (Kv2m) | Python `3.11`, PyInstaller, pinned `PySide6-Essentials` | [`.github/workflows/build-kv2m.yml`](../.github/workflows/build-kv2m.yml) |
| Panel image | `python:3.12-slim` + pinned `panel/requirements.txt` | [`Dockerfile`](../Dockerfile) |

## Rebuild the Android APK yourself

```bash
git clone https://github.com/kian-irani/kian_v2ray
cd kian_v2ray && git checkout app-v<VERSION>     # the exact release tag
cd app
flutter --version          # must be 3.24.5 (fvm use 3.24.5)
flutter pub get
flutter build apk --release --split-per-abi
# compare build/app/outputs/flutter-apk/*.apk against the GitHub release assets
```

Diff the APKs with `diffoscope` (signing block aside, the contents should match
for the same tag + toolchain):

```bash
diffoscope your-build.apk released.apk
```

## Rebuild the desktop / installer

- **Desktop:** the `build-kv2m.yml` steps are plain `pyinstaller` invocations —
  run the same command locally with the pinned deps.
- **Installer:** `install.sh` is the artifact; there is no compile step. Verify it
  by checksum against the tagged file:
  `sha256sum install.sh` and compare to the tag.

## Determinism caveats

- APK signing uses a key that is **not** in the repo (see [`KEYSTORE.md`](../app/KEYSTORE.md)),
  so the signing block differs — strip it before comparing.
- PyInstaller embeds a timestamp; use `SOURCE_DATE_EPOCH` for byte-identical
  desktop builds if needed.
- Native cores (Xray `.aar`, sing-box) are pulled at pinned versions; their own
  reproducibility is upstream's responsibility.

## Verifying a release without rebuilding

Every release is tied to a tag and a CI run. Check the **Actions** tab → the run
for that tag shows the full build log and the commit it built from.
