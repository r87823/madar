class MadarNotification {
  const MadarNotification({
    required this.name,
    required this.title,
    required this.message,
    required this.eventType,
    required this.entityType,
    required this.entityName,
    required this.isRead,
    required this.createdAt,
    required this.priority,
  });

  final String name;
  final String title;
  final String message;
  final String eventType;
  final String entityType;
  final String entityName;
  final bool isRead;
  final String createdAt;
  final String priority;

  factory MadarNotification.fromMap(Map<String, dynamic> map) {
    return MadarNotification(
      name: map['name']?.toString() ?? '',
      title: map['title']?.toString() ?? '',
      message: map['message']?.toString() ?? '',
      eventType: map['event_type']?.toString() ?? '',
      entityType: map['entity_type']?.toString() ?? '',
      entityName: map['entity_name']?.toString() ?? '',
      isRead: _bool(map['is_read']),
      createdAt: map['created_at']?.toString() ?? '',
      priority: map['priority']?.toString() ?? 'normal',
    );
  }
}

class NotificationList {
  const NotificationList({required this.items});

  final List<MadarNotification> items;

  factory NotificationList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _map(envelope['data']);
    final rows = data['items'];
    return NotificationList(
      items: rows is List
          ? rows
                .map((row) => MadarNotification.fromMap(_map(row)))
                .toList(growable: false)
          : const [],
    );
  }
}

class NotificationUnreadCount {
  const NotificationUnreadCount({required this.unreadCount});

  final int unreadCount;

  factory NotificationUnreadCount.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _map(envelope['data']);
    return NotificationUnreadCount(
      unreadCount: int.tryParse('${data['unread_count'] ?? 0}') ?? 0,
    );
  }
}

bool _bool(Object? value) {
  if (value is bool) return value;
  if (value is num) return value != 0;
  return value?.toString() == '1' || value?.toString().toLowerCase() == 'true';
}

Map<String, dynamic> _map(Object? value) {
  return value is Map
      ? value.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
}
