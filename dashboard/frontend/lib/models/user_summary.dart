class UserSummary {
  const UserSummary({required this.id, this.username});

  final String id;
  final String? username;

  factory UserSummary.fromJson(Map<String, dynamic> json) => UserSummary(
        id: json['id'] as String,
        username: json['username'] as String?,
      );

  String get displayName => username ?? id;

  String get initial =>
      (username != null && username!.isNotEmpty)
          ? username!.substring(0, 1).toUpperCase()
          : '?';
}
