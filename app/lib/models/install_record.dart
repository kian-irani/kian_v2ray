/// One server install performed from the app's setup wizard. Kept as a history
/// so the user always has their subscription link + web-panel URL/credentials,
/// even long after the install ran.
class InstallRecord {
  final String serverIp;
  final String dateIso; // ISO-8601, stamped by the caller (no clock in models)
  final String? subUrl;
  final String? panelUrl;
  final String? panelUser;
  final String? panelPass;
  final List<String> protocols; // reality, warp, ss, tls, hysteria2, tuic
  final int userCount;

  InstallRecord({
    required this.serverIp,
    required this.dateIso,
    this.subUrl,
    this.panelUrl,
    this.panelUser,
    this.panelPass,
    this.protocols = const [],
    this.userCount = 1,
  });

  Map<String, dynamic> toJson() => {
        'serverIp': serverIp,
        'dateIso': dateIso,
        'subUrl': subUrl,
        'panelUrl': panelUrl,
        'panelUser': panelUser,
        'panelPass': panelPass,
        'protocols': protocols,
        'userCount': userCount,
      };

  factory InstallRecord.fromJson(Map<String, dynamic> j) => InstallRecord(
        serverIp: j['serverIp'] as String? ?? '?',
        dateIso: j['dateIso'] as String? ?? '',
        subUrl: j['subUrl'] as String?,
        panelUrl: j['panelUrl'] as String?,
        panelUser: j['panelUser'] as String?,
        panelPass: j['panelPass'] as String?,
        protocols:
            (j['protocols'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        userCount: (j['userCount'] as num?)?.toInt() ?? 1,
      );

  /// Short human date (YYYY-MM-DD HH:MM) from the stored ISO string.
  String get dateShort {
    if (dateIso.length >= 16) return dateIso.substring(0, 16).replaceFirst('T', ' ');
    return dateIso;
  }
}
