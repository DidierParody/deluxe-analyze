import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../api/dashboard_api.dart';
import '../models/broker.dart';
import '../theme/app_colors.dart';
import '../widgets/insight_box.dart';
import '../widgets/loading_state.dart';
import '../widgets/lollipop_chart.dart';

class BrokersScreen extends StatefulWidget {
  const BrokersScreen({super.key});
  @override
  State<BrokersScreen> createState() => _BrokersScreenState();
}

class _BrokersScreenState extends State<BrokersScreen> {
  late Future<BrokerRanking> _future = DashboardApi().brokers(limit: 10);
  void _reload() => setState(() => _future = DashboardApi().brokers(limit: 10));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Brokers sociales', style: TextStyle(fontSize: 16)),
            Text('Conectan grupos distintos',
                style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
          ],
        ),
      ),
      body: FutureBuilder<BrokerRanking>(
        future: _future,
        builder: (_, snap) {
          if (snap.connectionState != ConnectionState.done) return const LoadingState();
          if (snap.hasError) return ErrorState(message: 'Error: ${snap.error}', onRetry: _reload);
          final d = snap.data!;
          final maxV = d.ranking.isEmpty ? 0.0 : d.ranking.first.betweennessScore;
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
            children: [
              const InsightBox(
                child: Text.rich(TextSpan(children: [
                  TextSpan(text: 'Estos clientes '),
                  TextSpan(
                    text: 'conectan comunidades',
                    style: TextStyle(color: AppColors.emerald400, fontWeight: FontWeight.bold),
                  ),
                  TextSpan(text: ' que de otra forma no se mezclarían. Palanca para marketing cruzado.'),
                ])),
              ),
              const SizedBox(height: 14),
              LollipopChart(
                maxValue: maxV,
                entries: d.ranking
                    .map((b) => LollipopEntry(label: b.username.isEmpty ? b.userId : b.username, value: b.betweennessScore))
                    .toList(),
              ),
            ],
          );
        },
      ),
    );
  }
}
