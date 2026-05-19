class ErpSyncOrder {
  const ErpSyncOrder({
    required this.name,
    required this.customerName,
    required this.subtotal,
    required this.orderStatus,
    required this.erpSyncStatus,
    this.erpSyncError,
    this.erpSalesOrder,
    this.approvedAt,
    this.approvedBy,
  });

  final String name;
  final String customerName;
  final double subtotal;
  final String orderStatus;
  final String erpSyncStatus;
  final String? erpSyncError;
  final String? erpSalesOrder;
  final String? approvedAt;
  final String? approvedBy;

  bool get canRetry => erpSyncStatus == 'pending' || erpSyncStatus == 'failed';

  String get statusLabel {
    switch (erpSyncStatus) {
      case 'synced':
        return 'تمت المزامنة';
      case 'failed':
        return 'فشلت المزامنة';
      case 'pending':
      default:
        return 'بانتظار المزامنة';
    }
  }

  factory ErpSyncOrder.fromMap(Map<String, dynamic> map) {
    return ErpSyncOrder(
      name: map['name']?.toString() ?? '',
      customerName: map['customer_name']?.toString() ?? '',
      subtotal: _toDouble(map['subtotal']),
      orderStatus: map['order_status']?.toString() ?? '',
      erpSyncStatus: map['erp_sync_status']?.toString() ?? 'pending',
      erpSyncError: _nullableString(map['erp_sync_error']),
      erpSalesOrder: _nullableString(map['erp_sales_order']),
      approvedAt: _nullableString(map['approved_at']),
      approvedBy: _nullableString(map['approved_by']),
    );
  }

  factory ErpSyncOrder.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return ErpSyncOrder.fromMap(map);
  }
}

class ErpSyncOrderList {
  const ErpSyncOrderList({required this.items});

  final List<ErpSyncOrder> items;

  factory ErpSyncOrderList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(ErpSyncOrder.fromMap)
              .toList(growable: false)
        : <ErpSyncOrder>[];
    return ErpSyncOrderList(items: items);
  }
}

String? _nullableString(Object? value) {
  final text = value?.toString();
  if (text == null || text.isEmpty || text == 'null') return null;
  return text;
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
