import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../api/dashboard_api.dart';
import '../models/influencer.dart';
import '../theme/app_colors.dart';
import '../widgets/horizontal_bar_chart.dart';
import '../widgets/insight_box.dart';
import '../widgets/loading_state.dart';

class InfluencersScreen extends StatefulWidget {
  const InfluencersScreen({super.key});
  @override
  State<InfluencersScreen> createState() => _InfluencersScreenState();
}

class _InfluencersScreenState extends State<InfluencersScreen> {
  late Future<InfluencerRanking> _future = DashboardApi().influencers(limit: 10);

  void _reload() => setState(() => _future = DashboardApi().influencers(limit: 10));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Clientes más influyentes', style: TextStyle(fontSize: 16)),
            Text('Por PageRank en CONOCE_A',
                style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
          ],
        ),
      ),
      body: FutureBuilder<InfluencerRanking>(
        future: _future,
        builder: (_, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingState();
          if (snap.hasError) {
            return ErrorState(message: 'Error: ${snap.error}', onRetry: _reload);
          }
          final d = snap.data!;
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
            children: [
              const InsightBox(
                child: Text(
                  'Estos clientes son el corazón de tu red.\nCuando vienen, otros vienen con ellos.',
                ),
              ),
              const SizedBox(height: 14),
              HorizontalBarChart(
                maxValue: d.maxScore,
                entries: d.ranking
                    .map((i) => BarEntry(
                          label: i.displayName,
                          value: i.score,
                          valueLabel: i.score.toStringAsFixed(2),
                        ))
                    .toList(),
              ),
            ],
          );
        },
      ),
    );
  }
}
