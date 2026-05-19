class WorkOrder {
  const WorkOrder({
    required this.name,
    required this.madarOrder,
    required this.productionCenter,
    required this.productionDepartment,
    required this.status,
    this.acceptedAt,
    this.startedAt,
    this.readyAt,
    this.delayedAt,
    this.delayReason,
    this.createdFromOrderAt,
    this.items = const [],
  });

  final String name;
  final String madarOrder;
  final String productionCenter;
  final String productionDepartment;
  final String status;
  final String? acceptedAt;
  final String? startedAt;
  final String? readyAt;
  final String? delayedAt;
  final String? delayReason;
  final String? createdFromOrderAt;
  final List<WorkOrderItem> items;

  String get statusLabel {
    return switch (status) {
      'pending' => 'بانتظار القبول',
      'accepted' => 'مقبول',
      'in_production' => 'قيد الإنتاج',
      'ready' => 'جاهز',
      'delayed' => 'متأخر',
      _ => status,
    };
  }

  factory WorkOrder.fromMap(Map<String, dynamic> map) {
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(WorkOrderItem.fromMap)
              .toList(growable: false)
        : <WorkOrderItem>[];
    return WorkOrder(
      name: map['name']?.toString() ?? '',
      madarOrder: map['madar_order']?.toString() ?? '',
      productionCenter: map['production_center']?.toString() ?? '',
      productionDepartment: map['production_department']?.toString() ?? '',
      status: map['status']?.toString() ?? '',
      acceptedAt: map['accepted_at']?.toString(),
      startedAt: map['started_at']?.toString(),
      readyAt: map['ready_at']?.toString(),
      delayedAt: map['delayed_at']?.toString(),
      delayReason: map['delay_reason']?.toString(),
      createdFromOrderAt: map['created_from_order_at']?.toString(),
      items: items,
    );
  }

  factory WorkOrder.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return WorkOrder.fromMap(map);
  }
}

class WorkOrderItem {
  const WorkOrderItem({
    required this.name,
    required this.workOrder,
    required this.madarOrderItem,
    required this.itemCode,
    required this.itemName,
    required this.qty,
    this.notes,
  });

  final String name;
  final String workOrder;
  final String madarOrderItem;
  final String itemCode;
  final String itemName;
  final double qty;
  final String? notes;

  factory WorkOrderItem.fromMap(Map<String, dynamic> map) {
    return WorkOrderItem(
      name: map['name']?.toString() ?? '',
      workOrder: map['work_order']?.toString() ?? '',
      madarOrderItem: map['madar_order_item']?.toString() ?? '',
      itemCode: map['item_code']?.toString() ?? '',
      itemName: map['item_name']?.toString() ?? '',
      qty: _toDouble(map['qty']),
      notes: map['notes']?.toString(),
    );
  }
}

class WorkOrderList {
  const WorkOrderList({required this.items});

  final List<WorkOrder> items;

  factory WorkOrderList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(WorkOrder.fromMap)
              .toList(growable: false)
        : <WorkOrder>[];
    return WorkOrderList(items: items);
  }
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
