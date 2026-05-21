import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class LollipopChart extends StatelessWidget {
  const LollipopChart({super.key, required this.entries, required this.maxValue});
  final List<LollipopEntry> entries;
  final double maxValue;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: entries.asMap().entries.map((e) {
        final pct = maxValue == 0 ? 0.0 : (e.value.value / maxValue).clamp(0.05, 1.0);
        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(
            children: [
              SizedBox(width: 18, child: Text('${e.key + 1}', textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textDim, fontWeight: FontWeight.w700, fontSize: 11))),
              const SizedBox(width: 6),
              SizedBox(width: 84, child: Text(e.value.label,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500))),
              const SizedBox(width: 6),
              Expanded(
                child: SizedBox(
                  height: 16,
                  child: LayoutBuilder(
                    builder: (_, c) => Stack(
                      clipBehavior: Clip.none,
                      children: [
                        Positioned(
                          top: 7, left: 0,
                          right: c.maxWidth * (1 - pct),
                          child: Container(height: 2, color: AppColors.grayMid.withOpacity(0.25)),
                        ),
                        Positioned(
                          left: c.maxWidth * pct - 6, top: 2,
                          child: Container(
                            width: 12, height: 12,
                            decoration: BoxDecoration(
                              gradient: AppColors.kpiGradient,
                              borderRadius: BorderRadius.circular(6),
                              boxShadow: [
                                BoxShadow(
                                  color: AppColors.emerald500.withOpacity(0.2),
                                  spreadRadius: 3,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 6),
              SizedBox(
                width: 42,
                child: Text(
                  e.value.value.toStringAsFixed(0),
                  textAlign: TextAlign.right,
                  style: const TextStyle(color: AppColors.emerald300, fontWeight: FontWeight.bold, fontSize: 11),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

class LollipopEntry {
  const LollipopEntry({required this.label, required this.value});
  final String label;
  final double value;
}
