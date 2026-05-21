import 'package:flutter/material.dart';

import '../models/promo_reach.dart';
import '../theme/app_colors.dart';

class FunnelChart extends StatelessWidget {
  const FunnelChart({super.key, required this.hops});
  final List<HopBucket> hops;

  @override
  Widget build(BuildContext context) {
    final maxCount = hops.fold<int>(0, (m, h) => h.count > m ? h.count : m);
    return Column(
      children: hops.map((h) {
        final pct = maxCount == 0 ? 0.0 : h.count / maxCount;
        final gradient = switch (h.hop) {
          1 => AppColors.hop1Gradient,
          2 => AppColors.hop2Gradient,
          _ => AppColors.hop3Gradient,
        };
        return Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.04),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white.withOpacity(0.04)),
            ),
            child: Row(
              children: [
                SizedBox(
                  width: 56,
                  child: Text(
                    '${h.hop} salto${h.hop > 1 ? 's' : ''}',
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                Expanded(
                  child: SizedBox(
                    height: 28,
                    child: LayoutBuilder(
                      builder: (_, c) => Stack(
                        children: [
                          Container(
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(6),
                            ),
                          ),
                          FractionallySizedBox(
                            widthFactor: pct.clamp(0.05, 1.0),
                            child: Container(
                              decoration: BoxDecoration(
                                gradient: gradient,
                                borderRadius: BorderRadius.circular(6),
                              ),
                              padding: const EdgeInsets.symmetric(horizontal: 10),
                              alignment: Alignment.centerLeft,
                              child: Text(
                                '${h.count}',
                                style: const TextStyle(
                                  color: Color(0xFF052E1D),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}
