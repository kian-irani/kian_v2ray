import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:kv2m/models/server_profile.dart';

void main() {
  group('ServerProfile.fromUri', () {
    test('parses vless host and port', () {
      final p = ServerProfile.fromUri('vless://uuid@1.2.3.4:443?type=tcp#DE');
      expect(p.protocol, 'vless');
      expect(p.host, '1.2.3.4');
      expect(p.port, 443);
    });

    test('parses bracketed IPv6 host', () {
      final p = ServerProfile.fromUri('vless://uuid@[2001:db8::1]:8443#v6');
      expect(p.host, '[2001:db8::1]');
      expect(p.port, 8443);
    });
  });

  group('parseSubscription', () {
    test('decodes base64 bundle of links', () {
      final raw = 'vless://u@1.1.1.1:443#A\nss://x@2.2.2.2:8388#B';
      final b64 = base64.encode(utf8.encode(raw));
      final list = parseSubscription(b64);
      expect(list.length, 2);
      expect(list[0].host, '1.1.1.1');
      expect(list[1].protocol, 'ss');
    });

    test('handles plain text (non-base64) too', () {
      final list = parseSubscription('vless://u@9.9.9.9:443#X');
      expect(list.length, 1);
      expect(list[0].port, 443);
    });
  });
}
