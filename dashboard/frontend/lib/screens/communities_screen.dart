import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../api/dashboard_api.dart';
import '../models/community.dart';
import '../theme/app_colors.dart';
import '../widgets/insight_box.dart';
import '../widgets/loading_state.dart';
import '../widgets/treemap_chart.dart';

class CommunitiesScreen extends StatefulWidget {
  const CommunitiesScreen({super.key});
  @override
  State<CommunitiesScreen> createState() => _CommunitiesScreenState();
}

class _CommunitiesScreenState extends State<CommunitiesScreen> {
  late Future<CommunitiesOverview> _future = DashboardApi().communities(minSize: 5);
  void _reload() => setState(() => _future = DashboardApi().communities(minSize: 5));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Grupos sociales', style: TextStyle(fontSize: 16)),
            Text('Detección con Louvain', style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
          ],
        ),
      ),
      body: FutureBuilder<CommunitiesOverview>(
        future: _future,
        builder: (_, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingState();
          if (snap.hasError) return ErrorState(message: 'Error: ${snap.error}', onRetry: _reload);
          final d = snap.data!;
          final tiles = d.dominantCommunities.take(3).map((c) =>
              CommunityTile(label: 'Grupo ${c.communityId}', size: c.size)).toList();
          if (d.nichesCount > 0) {
            tiles.add(CommunityTile(
              label: '+${d.nichesCount} nichos',
              size: d.nichesTotalMembers,
              isNiche: true,
            ));
          }
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
            children: [
              InsightBox(
                child: Text.rich(TextSpan(children: [
                  const TextSpan(text: 'Tu base se divide en '),
                  TextSpan(
                    text: '${d.dominantCommunities.length} grupos dominantes',
                    style: const TextStyle(color: AppColors.emerald400, fontWeight: FontWeight.bold),
                  ),
                  TextSpan(text: ' + ${d.nichesCount} nichos pequeños.'),
                ])),
              ),
              const SizedBox(height: 14),
              TreemapChart(tiles: tiles),
              const SizedBox(height: 14),
              if (d.dominantCommunities.isNotEmpty)
                InsightBox(
                  emoji: '🎯',
                  child: Text.rich(TextSpan(children: [
                    const TextSpan(text: 'El '),
                    TextSpan(
                      text: 'Grupo ${d.dominantCommunities.first.communityId}',
                      style: const TextStyle(color: AppColors.emerald400, fontWeight: FontWeight.bold),
                    ),
                    TextSpan(text: ' (${d.dominantCommunities.first.size} personas) es tu mejor target para eventos masivos.'),
                  ])),
                ),
            ],
          );
        },
      ),
    );
  }
}
