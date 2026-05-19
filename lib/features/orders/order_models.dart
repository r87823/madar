enum OrderStatus {
  draft,
  submitted,
  cancelled,
  unknown;

  String get arabicLabel {
    switch (this) {
      case OrderStatus.draft:
        return 'مسودة';
      case OrderStatus.submitted:
        return 'تم الإرسال';
      case OrderStatus.cancelled:
        return 'ملغي';
      case OrderStatus.unknown:
        return 'غير معروف';
    }
  }

  static OrderStatus fromString(String? value) {
    switch (value) {
      case 'draft':
        return OrderStatus.draft;
      case 'submitted':
        return OrderStatus.submitted;
      case 'cancelled':
        return OrderStatus.cancelled;
      default:
        return OrderStatus.unknown;
    }
  }
}

class MadarOrder {
  const MadarOrder({
    required this.name,
    required this.customerName,
    required this.customerPhone,
    required this.status,
    this.branch,
    this.assignedBranch,
    this.createdByUser,
    this.notes,
    this.subtotal = 0,
    this.itemsCount = 0,
    this.submittedAt,
    this.cancelledAt,
  });

  final String name;
  final String customerName;
  final String customerPhone;
  final OrderStatus status;
  final String? branch;
  final String? assignedBranch;
  final String? createdByUser;
  final String? notes;
  final double subtotal;
  final int itemsCount;
  final String? submittedAt;
  final String? cancelledAt;

  factory MadarOrder.fromMap(Map<String, dynamic> map) {
    return MadarOrder(
      name: map['name']?.toString() ?? '',
      customerName: map['customer_name']?.toString() ?? '',
      customerPhone: map['customer_phone']?.toString() ?? '',
      status: OrderStatus.fromString(map['order_status']?.toString()),
      branch: map['branch']?.toString(),
      assignedBranch: map['assigned_branch']?.toString(),
      createdByUser: map['created_by_user']?.toString(),
      notes: map['notes']?.toString(),
      subtotal: _toDouble(map['subtotal']),
      itemsCount: _toInt(map['items_count']),
      submittedAt: map['submitted_at']?.toString(),
      cancelledAt: map['cancelled_at']?.toString(),
    );
  }

  factory MadarOrder.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return MadarOrder.fromMap(map);
  }
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}

int _toInt(Object? value) {
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

class OrderList {
  const OrderList({required this.items});

  final List<MadarOrder> items;

  factory OrderList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(MadarOrder.fromMap)
              .toList(growable: false)
        : <MadarOrder>[];
    return OrderList(items: items);
  }
}
