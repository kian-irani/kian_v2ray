# Keystore & Signing — Kv2m app

> **If you lose the `.jks`, you can NEVER update the published app** — you'd
> have to republish as a new package. Treat the keystore like a master key.

## Create (once)

```bash
keytool -genkey -v -keystore kian-release.jks \
  -keyalg RSA -keysize 4096 -validity 10000 -alias kian
```

## Wire into Gradle

`android/key.properties` (git-ignored):

```
storeFile=../kian-release.jks
storePassword=********
keyAlias=kian
keyPassword=********
```

## Backups (mandatory — 3 copies)

Keep **three encrypted copies in three different places**, e.g.:

1. Encrypted password manager / vault.
2. An offline USB drive (encrypted), stored physically apart.
3. A private encrypted cloud bucket (R2/S3) — `gpg -c kian-release.jks`.

Never commit the keystore or `key.properties` to git.

## Reproducible builds (F-Droid)

Document the exact Flutter/Gradle versions and `flutter build apk --release`
flags so F-Droid can reproduce the binary. Avoid any non-deterministic asset
generation at build time.
