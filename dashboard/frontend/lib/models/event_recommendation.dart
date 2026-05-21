class EventRecommendation {
  const EventRecommendation({
    required this.rank,
    required this.eventId,
    required this.eventName,
    required this.score,
    required this.friendsAttended,
  });

  final int rank;
  final String eventId;
  final String? eventName;
  final double score;
  final int friendsAttended;

  String get displayName => eventName ?? eventId;

  factory EventRecommendation.fromJson(Map<String, dynamic> json) =>
      EventRecommendation(
        rank: json['rank'] as int,
        eventId: json['event_id'] as String,
        eventName: json['event_name'] as String?,
        score: (json['score'] as num).toDouble(),
        friendsAttended: json['friends_attended'] as int,
      );
}

class EventRecommendationList {
  const EventRecommendationList({
    required this.userId,
    required this.username,
    required this.recommendations,
  });

  final String userId;
  final String? username;
  final List<EventRecommendation> recommendations;

  factory EventRecommendationList.fromJson(Map<String, dynamic> json) =>
      EventRecommendationList(
        userId: json['user_id'] as String,
        username: json['username'] as String?,
        recommendations: (json['recommendations'] as List<dynamic>)
            .map((e) =>
                EventRecommendation.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
