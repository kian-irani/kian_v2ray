import 'package:flutter/material.dart';

import '../theme.dart';

/// A consistent, collapsible bilingual help card used on every screen so guidance
/// is complete everywhere (user request). Collapsed by default to stay out of the
/// way; tap to expand. Pure presentation — pass already-localized title/body.
class HelpCard extends StatefulWidget {
  final String title;
  final String body;
  final bool initiallyExpanded;
  const HelpCard({
    super.key,
    required this.title,
    required this.body,
    this.initiallyExpanded = false,
  });

  @override
  State<HelpCard> createState() => _HelpCardState();
}

class _HelpCardState extends State<HelpCard> {
  late bool _open = widget.initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFF0E1B33),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => setState(() => _open = !_open),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.help_outline, size: 18, color: KianTheme.accent),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(widget.title,
                        style: const TextStyle(
                            color: KianTheme.accent, fontWeight: FontWeight.bold)),
                  ),
                  Icon(_open ? Icons.expand_less : Icons.expand_more,
                      size: 20, color: const Color(0xFF8AA0C0)),
                ],
              ),
              AnimatedCrossFade(
                duration: const Duration(milliseconds: 200),
                crossFadeState:
                    _open ? CrossFadeState.showSecond : CrossFadeState.showFirst,
                firstChild: const SizedBox(width: double.infinity),
                secondChild: Padding(
                  padding: const EdgeInsets.only(top: 10),
                  child: Text(widget.body,
                      style: const TextStyle(fontSize: 12.5, height: 1.55)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
