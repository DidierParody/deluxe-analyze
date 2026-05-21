import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class KpiCard extends StatelessWidget {
  const KpiCard({
    super.key,
    required this.label,
    required this.value,
    this.suffix,
    this.context,
  });

  final String label;
  final String value;
  final String? suffix;
  // ignore: avoid_field_initializers_in_const_classes
  final String? context;

  @override
  Widget build(BuildContext ctx) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: AppColors.heroSoftGradient,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.emerald500.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              color: AppColors.emerald300,
              fontSize: 11,
              letterSpacing: 1,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          ShaderMask(
            shaderCallback: (rect) => AppColors.kpiGradient.createShader(rect),
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 56,
                fontWeight: FontWeight.w800,
                color: Colors.white,
                height: 1,
              ),
            ),
          ),
          if (suffix != null)
            Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Text(
                suffix!,
                style: const TextStyle(color: AppColors.textPrimary, fontSize: 13),
              ),
            ),
          if (context != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                context!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }
}
