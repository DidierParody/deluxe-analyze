import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'screens/brokers_screen.dart';
import 'screens/communities_screen.dart';
import 'screens/event_recommendation_screen.dart';
import 'screens/home_screen.dart';
import 'screens/influencers_screen.dart';
import 'screens/promo_reach_screen.dart';
import 'theme/app_theme.dart';

class DeluxeDashboardApp extends StatelessWidget {
  const DeluxeDashboardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Deluxe Insights',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      routerConfig: _router,
    );
  }
}

final _router = GoRouter(
  routes: [
    GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
    GoRoute(path: '/promo-reach', builder: (_, __) => const PromoReachScreen()),
    GoRoute(path: '/influencers', builder: (_, __) => const InfluencersScreen()),
    GoRoute(path: '/events', builder: (_, __) => const EventRecommendationScreen()),
    GoRoute(path: '/communities', builder: (_, __) => const CommunitiesScreen()),
    GoRoute(path: '/brokers', builder: (_, __) => const BrokersScreen()),
  ],
);
