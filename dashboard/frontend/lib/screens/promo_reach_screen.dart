import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../api/dashboard_api.dart';
import '../models/promo_reach.dart';
import '../models/user_summary.dart';
import '../theme/app_colors.dart';
import '../widgets/funnel_chart.dart';
import '../widgets/insight_box.dart';
import '../widgets/kpi_card.dart';
import '../widgets/loading_state.dart';
import '../widgets/user_picker.dart';

class PromoReachScreen extends StatefulWidget {
  const PromoReachScreen({super.key});
  @override
  State<PromoReachScreen> createState() => _PromoReachScreenState();
}

class _PromoReachScreenState extends State<PromoReachScreen> {
  UserSummary? _user = const UserSummary(id: 'csv:87', username: 'Raúl');
  Future<PromoReach>? _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    if (_user == null) return;
    setState(() => _future = DashboardApi().promoReach(_user!.id));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Alcance de promoción', style: TextStyle(fontSize: 16)),
            Text('Hasta dónde llega la red',
                style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        children: [
          UserPicker(
            selected: _user,
            onChanged: (u) {
              setState(() => _user = u);
              _load();
            },
          ),
          const SizedBox(height: 16),
          if (_future == null)
            const LoadingState()
          else
            FutureBuilder<PromoReach>(
              future: _future,
              builder: (_, snap) {
                if (snap.connectionState != ConnectionState.done) return const LoadingState();
                if (snap.hasError) {
                  return ErrorState(message: 'Error: ${snap.error}', onRetry: _load);
                }
                final d = snap.data!;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    KpiCard(
                      label: 'Alcance total',
                      value: '${d.totalReach}',
                      suffix: 'de ${d.totalUsers} clientes',
                      context: '${d.reachPercentage.toStringAsFixed(0)} % de tu base alcanzable en 3 saltos',
                    ),
                    const SizedBox(height: 14),
                    const _SectionTitle('Desglose por saltos'),
                    FunnelChart(hops: d.byHop),
                    const SizedBox(height: 14),
                    InsightBox(
                      emoji: '💡',
                      child: Text.rich(TextSpan(children: [
                        TextSpan(
                          text: d.username ?? d.userId,
                          style: const TextStyle(color: AppColors.emerald400, fontWeight: FontWeight.bold),
                        ),
                        const TextSpan(text: ' es una palanca de marketing fuerte: una promoción suya llega a '),
                        TextSpan(
                          text: '${d.totalReach} personas',
                          style: const TextStyle(color: AppColors.emerald400, fontWeight: FontWeight.bold),
                        ),
                        const TextSpan(text: ' a través de su red.'),
                      ])),
                    ),
                    const SizedBox(height: 14),
                    FilledButton(
                      style: FilledButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: AppColors.emerald500,
                      ),
                      onPressed: () {},
                      child: Text('Lanzar promoción a ${d.username ?? d.userId} →'),
                    ),
                  ],
                );
              },
            ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10, top: 8),
        child: Text(text.toUpperCase(),
            style: const TextStyle(color: AppColors.textFaint, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 1)),
      );
}
