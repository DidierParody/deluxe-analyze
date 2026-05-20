class Broker {
  const Broker({
    required this.rank,
    required this.userId,
    required this.username,
    required this.betweennessScore,
  });

  final int rank;
  final String userId;
  final String username;
  final double betweennessScore;

  factory Broker.fromJson(Map<String, dynamic> json) => Broker(
        rank: json['rank'] as int,
        userId: json['user_id'] as String,
        username: (json['username'] ?? json['user_id'] ?? '') as String,
        betweennessScore: (json['betweenness_score'] as num).toDouble(),
      );
}

class BrokerRanking {
  const BrokerRanking({required this.ranking});

  final List<Broker> ranking;

  factory BrokerRanking.fromJson(Map<String, dynamic> json) => BrokerRanking(
        ranking: (json['ranking'] as List<dynamic>)
            .map((e) => Broker.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
