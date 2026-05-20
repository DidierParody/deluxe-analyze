import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class FeatureCard extends StatelessWidget {
  const FeatureCard({
    super.key,
    required this.icon,
    required this.title,
    required this.description,
    required this.onTap,
    this.hero = false,
    this.iconBg,
    this.iconColor,
  });

  final String icon;
  final String title;
  final String description;
  final VoidCallback onTap;
  final bool hero;
  final Color? iconBg;
  final Color? iconColor;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: hero ? AppColors.heroSoftGradient : null,
          color: hero ? null : Colors.white.withOpacity(0.04),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: hero
                ? AppColors.emerald500.withOpacity(0.28)
                : Colors.white.withOpacity(0.06),
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: hero ? AppColors.heroGradient : null,
                color: hero ? null : (iconBg ?? Colors.white.withOpacity(0.04)),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Text(
                icon,
                style: TextStyle(
                  fontSize: 22,
                  color: hero ? Colors.white : (iconColor ?? AppColors.textPrimary),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    description,
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 11.5,
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.textDim, size: 18),
          ],
        ),
      ),
    );
  }
}
