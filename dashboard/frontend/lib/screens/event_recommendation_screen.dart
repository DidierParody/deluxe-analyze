import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../api/dashboard_api.dart';
import '../models/event_recommendation.dart';
import '../models/user_summary.dart';
import '../theme/app_colors.dart';
import '../widgets/loading_state.dart';
import '../widgets/ranked_card.dart';
import '../widgets/user_picker.dart';

class EventRecommendationScreen extends StatefulWidget {
  const EventRecommendationScreen({super.key});
  @override
  State<EventRecommendationScreen> createState() => _EventRecommendationScreenState();
}

class _EventRecommendationScreenState extends State<EventRecommendationScreen> {
  UserSummary? _user = const UserSummary(id: 'csv:87', username: 'Raúl');
  Future<EventRecommendationList>? _future;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    if (_user == null) return;
    setState(() {
      _future = DashboardApi().eventRecommendations(_user!.id, limit: 5);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(icon: const Icon(Icons.arrow_back), onPressed: () => context.pop()),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('¿Qué evento le invito?', style: TextStyle(fontSize: 16)),
            Text('Basado en sus amigos', style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
        children: [
          UserPicker(
            selected: _user,
            onChanged: (u) { setState(() => _user = u); _load(); },
          ),
          const SizedBox(height: 16),
          if (_future == null)
            const LoadingState()
          else
            FutureBuilder<EventRecommendationList>(
              future: _future,
              builder: (_, snap) {
                if (snap.connectionState != ConnectionState.done) return const LoadingState();
                if (snap.hasError) return ErrorState(message: 'Error: ${snap.error}', onRetry: _load);
                final d = snap.data!;
                if (d.recommendations.isEmpty) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Text('Sin recomendaciones para este cliente.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppColors.textMuted)),
                  );
                }
                final maxScore = d.recommendations.first.score;
                return Column(children: [
                  const Padding(
                    padding: EdgeInsets.only(bottom: 10, top: 4),
                    child: Align(
                      alignment: Alignment.centerLeft,
                      child: Text('TOP EVENTOS PARA INVITAR',
                          style: TextStyle(color: AppColors.textFaint, fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 1)),
                    ),
                  ),
                  ...d.recommendations.map((r) => RankedCard(
                        rank: r.rank,
                        title: r.displayName,
                        subtitle: Text.rich(TextSpan(children: [
                          TextSpan(
                            text: '${r.friendsAttended}',
                            style: const TextStyle(color: AppColors.emerald400, fontWeight: FontWeight.bold),
                          ),
                          const TextSpan(text: ' amigos suyos ya fueron · score '),
                          TextSpan(text: r.score.toStringAsFixed(0)),
                        ])),
                        progress: maxScore == 0 ? 0 : r.score / maxScore,
                      )),
                ]);
              },
            ),
        ],
      ),
    );
  }
}
