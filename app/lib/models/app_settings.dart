/// Central app settings (parity with v2rayNG / Hiddify settings screens).
/// Persisted as a JSON map via Cache.loadSettings/saveSettings.
class AppSettings {
  String themeMode; // 'system' | 'dark' | 'light'
  String routing;   // 'global' | 'bypass-lan' | 'bypass-iran' | 'bypass-both'
  bool killSwitch;  // block traffic if the tunnel drops
  bool autoConnect; // connect on app launch to the last server
  bool proxyOnly;   // proxy mode instead of full VPN/TUN
  bool autoRefreshSubs; // refresh subscriptions on launch
  bool antiDpi;     // inject TLS-Hello fragmentation to defeat DPI (Fragment)
  String remoteDns; // DNS for proxied queries
  String directDns; // DNS for direct queries
  List<String> perAppProxy; // package names EXCLUDED from VPN (bypass); [] = all apps tunneled

  AppSettings({
    this.themeMode = 'system',
    this.routing = 'bypass-lan',
    this.killSwitch = false,
    this.autoConnect = false,
    this.proxyOnly = false,
    this.autoRefreshSubs = true,
    this.antiDpi = true,
    this.remoteDns = '1.1.1.1',
    this.directDns = '8.8.8.8',
    this.perAppProxy = const [],
  });

  Map<String, dynamic> toJson() => {
        'themeMode': themeMode,
        'routing': routing,
        'killSwitch': killSwitch,
        'autoConnect': autoConnect,
        'proxyOnly': proxyOnly,
        'autoRefreshSubs': autoRefreshSubs,
        'antiDpi': antiDpi,
        'remoteDns': remoteDns,
        'directDns': directDns,
        'perAppProxy': perAppProxy,
      };

  factory AppSettings.fromJson(Map<String, dynamic> j) => AppSettings(
        themeMode: j['themeMode'] as String? ?? 'system',
        routing: j['routing'] as String? ?? 'bypass-lan',
        killSwitch: j['killSwitch'] as bool? ?? false,
        autoConnect: j['autoConnect'] as bool? ?? false,
        proxyOnly: j['proxyOnly'] as bool? ?? false,
        autoRefreshSubs: j['autoRefreshSubs'] as bool? ?? true,
        antiDpi: j['antiDpi'] as bool? ?? true,
        remoteDns: j['remoteDns'] as String? ?? '1.1.1.1',
        directDns: j['directDns'] as String? ?? '8.8.8.8',
        perAppProxy:
            (j['perAppProxy'] as List?)?.map((e) => e.toString()).toList() ?? const [],
      );

  /// Private/LAN subnets to bypass (passed to flutter_v2ray as bypassSubnets).
  static const _lan = [
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '127.0.0.0/8',
    '169.254.0.0/16', '224.0.0.0/4', 'fc00::/7', '::1/128',
  ];

  /// The bypassSubnets list for the current routing mode (null = route all).
  List<String>? bypassSubnets() {
    switch (routing) {
      case 'bypass-lan':
      case 'bypass-both':
        return List<String>.from(_lan);
      default:
        return null;
    }
  }

  /// Whether Iran traffic should route direct (handled via routing rules in the
  /// generated config; the flag is surfaced here for the connect path).
  bool get bypassIran => routing == 'bypass-iran' || routing == 'bypass-both';
}
