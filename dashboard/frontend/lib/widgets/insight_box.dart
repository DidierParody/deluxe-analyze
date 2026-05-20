import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class InsightBox extends StatelessWidget {
  const InsightBox({super.key, required this.child, this.emoji});

  final Widget child;
  final String? emoji;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(8),
        border: const Border(
          left: BorderSide(color: AppColors.emerald500, width: 3),
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (emoji != null) ...[
            Text(emoji!, style: const TextStyle(fontSize: 14)),
            const SizedBox(width: 8),
          ],
          Expanded(
            child: DefaultTextStyle.merge(
              style: const TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
                height: 1.5,
              ),
              child: child,
            ),
          ),
        ],
      ),
    );
  }
}
