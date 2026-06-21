# Flutter / Kv2m ProGuard rules.
-keep class io.flutter.** { *; }
-keep class com.kianirani.kv2m.** { *; }
# Keep the VpnService entry points referenced from the manifest.
-keep class * extends android.net.VpnService { *; }
