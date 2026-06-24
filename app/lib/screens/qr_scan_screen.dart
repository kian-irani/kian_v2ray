import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../i18n.dart';
import '../theme.dart';

/// QR code scanner screen — returns the scanned text to the caller via
/// [Navigator.pop]. Used from the home screen import dialog so the user
/// can scan a vless:// or subscription link instead of typing it.
class QrScanScreen extends StatefulWidget {
  final Strings strings;
  const QrScanScreen({super.key, required this.strings});

  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen> {
  final _ctrl = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
  );
  bool _popped = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_popped) return;
    final value = capture.barcodes.firstOrNull?.rawValue;
    if (value == null || value.isEmpty) return;
    _popped = true;
    Navigator.pop(context, value);
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.strings;
    return Scaffold(
      appBar: AppBar(
        title: Text(s.t('import.qr')),
        actions: [
          IconButton(
            icon: ValueListenableBuilder(
              valueListenable: _ctrl.torchState,
              builder: (_, state, __) => Icon(
                state == TorchState.on ? Icons.flash_on : Icons.flash_off,
              ),
            ),
            onPressed: _ctrl.toggleTorch,
          ),
        ],
      ),
      body: Stack(
        children: [
          MobileScanner(controller: _ctrl, onDetect: _onDetect),
          // Overlay: شفاف با یه کادر مربعی برای راهنمایی کاربر
          CustomPaint(
            size: MediaQuery.of(context).size,
            painter: _ScanOverlay(),
          ),
          Positioned(
            bottom: 40,
            left: 0, right: 0,
            child: Text(
              s.t('import.qr.hint'),
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.white70, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

class _ScanOverlay extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final side = size.width * 0.65;
    final cx = size.width / 2, cy = size.height / 2;
    final rect = Rect.fromCenter(center: Offset(cx, cy), width: side, height: side);
    final paint = Paint()..color = Colors.black45;
    // shade outside the scan window
    canvas.drawPath(
      Path.combine(PathOperation.difference,
          Path()..addRect(Offset.zero & size),
          Path()..addRRect(RRect.fromRectAndRadius(rect, const Radius.circular(12)))),
      paint,
    );
    // corner markers
    final corner = Paint()
      ..color = KianTheme.accent
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
    const len = 24.0;
    for (final dx in [-1, 1]) {
      for (final dy in [-1, 1]) {
        final ox = cx + dx * side / 2;
        final oy = cy + dy * side / 2;
        canvas.drawLine(Offset(ox, oy), Offset(ox - dx * len, oy), corner);
        canvas.drawLine(Offset(ox, oy), Offset(ox, oy - dy * len), corner);
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
