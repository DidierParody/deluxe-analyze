import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class HorizontalBarChart extends StatelessWidget {
  const HorizontalBarChart({super.key, required this.entries, required this.maxValue});

  final List<BarEntry> entries;
  final double maxValue;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: entries.asMap().entries.map((e) {
        final pct = maxValue == 0 ? 0.0 : (e.value.value / maxValue).clamp(0.05, 1.0);
        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Row(
            children: [
              SizedBox(
                width: 18,
                child: Text('${e.key + 1}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: AppColors.textDim, fontWeight: FontWeight.w700, fontSize: 11)),
              ),
              const SizedBox(width: 6),
              SizedBox(
                width: 92,
                child: Text(e.value.label,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: SizedBox(
                  height: 22,
                  child: Stack(
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.04),
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                      FractionallySizedBox(
                        widthFactor: pct,
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: AppColors.barGradient,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          padding: const EdgeInsets.only(right: 6),
                          alignment: Alignment.centerRight,
                          child: Text(
                            e.value.valueLabel ?? e.value.value.toStringAsFixed(2),
                            style: const TextStyle(
                              color: Color(0xFF052E1D),
                              fontWeight: FontWeight.bold,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

class BarEntry {
  const BarEntry({required this.label, required this.value, this.valueLabel});
  final String label;
  final double value;
  final String? valueLabel;
}
