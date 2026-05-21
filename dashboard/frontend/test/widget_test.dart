import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:deluxe_dashboard/theme/app_theme.dart';

void main() {
  testWidgets('AppTheme dark builds without throwing', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.dark(),
        home: const Scaffold(body: SizedBox.shrink()),
      ),
    );
    expect(find.byType(Scaffold), findsOneWidget);
  });
}
