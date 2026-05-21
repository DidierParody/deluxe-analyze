class Influencer {
  const Influencer({
    required this.rank,
    required this.userId,
    required this.username,
    required this.score,
  });

  final int rank;
  final String userId;
  final String? username;
  final double score;

  String get displayName => username ?? userId;

  factory Influencer.fromJson(Map<String, dynamic> json) => Influencer(
        rank: json['rank'] as int,
        userId: json['user_id'] as String,
        username: json['username'] as String?,
        score: (json['score'] as num).toDouble(),
      );
}

class InfluencerRanking {
  const InfluencerRanking({required this.maxScore, required this.ranking});

  final double maxScore;
  final List<Influencer> ranking;

  factory InfluencerRanking.fromJson(Map<String, dynamic> json) =>
      InfluencerRanking(
        maxScore: (json['max_score'] as num).toDouble(),
        ranking: (json['ranking'] as List<dynamic>)
            .map((e) => Influencer.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
