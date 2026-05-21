class HopBucket {
  const HopBucket({required this.hop, required this.count});
  final int hop;
  final int count;

  factory HopBucket.fromJson(Map<String, dynamic> json) => HopBucket(
        hop: json['hop'] as int,
        count: json['count'] as int,
      );
}

class PromoReach {
  const PromoReach({
    required this.userId,
    required this.username,
    required this.totalReach,
    required this.totalUsers,
    required this.reachPercentage,
    required this.byHop,
  });

  final String userId;
  final String? username;
  final int totalReach;
  final int totalUsers;
  final double reachPercentage;
  final List<HopBucket> byHop;

  factory PromoReach.fromJson(Map<String, dynamic> json) => PromoReach(
        userId: json['user_id'] as String,
        username: json['username'] as String?,
        totalReach: json['total_reach'] as int,
        totalUsers: json['total_users'] as int,
        reachPercentage: (json['reach_percentage'] as num).toDouble(),
        byHop: (json['by_hop'] as List<dynamic>)
            .map((e) => HopBucket.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
