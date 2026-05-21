import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class RankedCard extends StatelessWidget {
  const RankedCard({
    super.key,
    required this.rank,
    required this.title,
    required this.subtitle,
    required this.progress,
  });

  final int rank;
  final String title;
  final Widget subtitle;
  final double progress; // 0..1

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: Stack(
        children: [
          Positioned(
            top: 0, right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: AppColors.grayDark.withOpacity(0.30),
                border: Border.all(color: Colors.white.withOpacity(0.06)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text('#$rank',
                  style: const TextStyle(color: AppColors.grayLight, fontWeight: FontWeight.bold, fontSize: 10)),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.only(right: 36),
                child: Text(title,
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
              ),
              const SizedBox(height: 4),
              DefaultTextStyle.merge(
                style: const TextStyle(color: AppColors.textMuted, fontSize: 11.5),
                child: subtitle,
              ),
              const SizedBox(height: 8),
              SizedBox(
                height: 6,
                child: Stack(
                  children: [
                    Container(decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.04),
                      borderRadius: BorderRadius.circular(3),
                    )),
                    FractionallySizedBox(
                      widthFactor: progress.clamp(0.05, 1.0),
                      child: Container(decoration: BoxDecoration(
                        gradient: AppColors.barGradient,
                        borderRadius: BorderRadius.circular(3),
                      )),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
