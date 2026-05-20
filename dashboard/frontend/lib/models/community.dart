class DominantCommunity {
  const DominantCommunity({
    required this.communityId,
    required this.size,
    required this.sampleUsers,
  });

  final int communityId;
  final int size;
  final List<String> sampleUsers;

  factory DominantCommunity.fromJson(Map<String, dynamic> json) =>
      DominantCommunity(
        communityId: json['community_id'] as int,
        size: json['size'] as int,
        sampleUsers: (json['sample_users'] as List<dynamic>)
            .map((e) => e as String)
            .toList(),
      );
}

class CommunitiesOverview {
  const CommunitiesOverview({
    required this.totalCommunities,
    required this.dominantCommunities,
    required this.nichesCount,
    required this.nichesTotalMembers,
  });

  final int totalCommunities;
  final List<DominantCommunity> dominantCommunities;
  final int nichesCount;
  final int nichesTotalMembers;

  factory CommunitiesOverview.fromJson(Map<String, dynamic> json) =>
      CommunitiesOverview(
        totalCommunities: json['total_communities'] as int,
        dominantCommunities: (json['dominant_communities'] as List<dynamic>)
            .map((e) => DominantCommunity.fromJson(e as Map<String, dynamic>))
            .toList(),
        nichesCount: json['niches_count'] as int,
        nichesTotalMembers: json['niches_total_members'] as int,
      );
}
