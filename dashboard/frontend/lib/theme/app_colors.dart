import 'package:flutter/material.dart';

/// Centralized palette extracted from `dashboard/mockups/index.html`.
class AppColors {
  AppColors._();

  // Backgrounds
  static const Color backgroundBase = Color(0xFF050605);
  static const Color backgroundTop = Color(0xFF0D1410);
  static const Color surface = Color(0xFF0C100E);
  static Color surfaceVariant = Colors.white.withOpacity(0.04);
  static Color borderSubtle = Colors.white.withOpacity(0.06);

  // Brand emerald scale
  static const Color emerald300 = Color(0xFF6EE7B7);
  static const Color emerald400 = Color(0xFF34D399);
  static const Color emerald500 = Color(0xFF10B981);
  static const Color emerald600 = Color(0xFF059669);
  static const Color emerald700 = Color(0xFF047857);
  static const Color emerald800 = Color(0xFF065F46);
  static const Color emerald900 = Color(0xFF064E3B);

  // Accent grays
  static const Color grayLight = Color(0xFFD1D5DB);
  static const Color grayMid = Color(0xFF9CA3AF);
  static const Color grayDark = Color(0xFF4B5563);
  static const Color graySlate = Color(0xFF374151);
  static const Color grayDeep = Color(0xFF1F2937);

  // Text
  static const Color textPrimary = Color(0xFFE8E8E8);
  static const Color textSecondary = Color(0xFFCBD5D1);
  static const Color textMuted = Color(0xFF888888);
  static const Color textFaint = Color(0xFF666666);
  static const Color textDim = Color(0xFF555555);

  // Insight bold
  static const Color insightBold = emerald400;

  // Gradients
  static const LinearGradient kpiGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [emerald400, emerald300],
  );

  static const LinearGradient heroGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [emerald500, emerald700],
  );

  static const LinearGradient heroSoftGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0x2410B981), Color(0x1A064E3B)],
  );

  static const LinearGradient barGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [emerald600, emerald400],
  );

  static const LinearGradient hop1Gradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [emerald400, emerald300],
  );
  static const LinearGradient hop2Gradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [emerald500, emerald400],
  );
  static const LinearGradient hop3Gradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [emerald700, emerald600],
  );

  static const RadialGradient pageGradient = RadialGradient(
    center: Alignment.topCenter,
    radius: 1.2,
    colors: [backgroundTop, backgroundBase],
    stops: [0.0, 0.6],
  );
}
