class FollowupDashboardSummary {
  const FollowupDashboardSummary({required this.cards, required this.alerts});

  final List<FollowupDashboardCard> cards;
  final List<FollowupDashboardAlert> alerts;

  factory FollowupDashboardSummary.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _map(envelope['data']);
    final cards = data['cards'];
    final alerts = data['alerts'];
    return FollowupDashboardSummary(
      cards: cards is List
          ? cards
                .map((row) => FollowupDashboardCard.fromMap(_map(row)))
                .toList(growable: false)
          : const [],
      alerts: alerts is List
          ? alerts
                .map((row) => FollowupDashboardAlert.fromMap(_map(row)))
                .toList(growable: false)
          : const [],
    );
  }
}

class FollowupDashboardCard {
  const FollowupDashboardCard({
    required this.key,
    required this.title,
    required this.value,
    required this.subtitle,
    required this.priority,
    required this.routeKey,
    required this.routeParams,
  });

  final String key;
  final Object value;
  final String title;
  final String subtitle;
  final String priority;
  final String routeKey;
  final Map<String, String> routeParams;

  String get valueText => value.toString();
  bool get isHighPriority => priority == 'high';

  factory FollowupDashboardCard.fromMap(Map<String, dynamic> map) {
    return FollowupDashboardCard(
      key: map['key']?.toString() ?? '',
      title: map['title']?.toString() ?? '',
      value: map['value'] ?? 0,
      subtitle: map['subtitle']?.toString() ?? '',
      priority: map['priority']?.toString() ?? 'normal',
      routeKey: map['route_key']?.toString() ?? 'none',
      routeParams: _stringMap(map['route_params']),
    );
  }
}

class FollowupDashboardAlert {
  const FollowupDashboardAlert({
    required this.key,
    required this.title,
    required this.message,
    required this.priority,
    required this.routeKey,
    required this.routeParams,
  });

  final String key;
  final String title;
  final String message;
  final String priority;
  final String routeKey;
  final Map<String, String> routeParams;

  factory FollowupDashboardAlert.fromMap(Map<String, dynamic> map) {
    return FollowupDashboardAlert(
      key: map['key']?.toString() ?? '',
      title: map['title']?.toString() ?? '',
      message: map['message']?.toString() ?? '',
      priority: map['priority']?.toString() ?? 'normal',
      routeKey: map['route_key']?.toString() ?? 'none',
      routeParams: _stringMap(map['route_params']),
    );
  }
}

Map<String, dynamic> _map(Object? value) {
  return value is Map
      ? value.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
}

Map<String, String> _stringMap(Object? value) {
  final source = _map(value);
  return source.map((key, value) => MapEntry(key, value?.toString() ?? ''));
}
