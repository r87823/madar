class MadarOrderItem {
  const MadarOrderItem({
    required this.name,
    required this.orderName,
    required this.itemCode,
    required this.itemName,
    required this.qty,
    required this.unitPrice,
    required this.lineTotal,
    this.notes,
  });

  final String name;
  final String orderName;
  final String itemCode;
  final String itemName;
  final double qty;
  final double unitPrice;
  final double lineTotal;
  final String? notes;

  factory MadarOrderItem.fromMap(Map<String, dynamic> map) {
    return MadarOrderItem(
      name: map['name']?.toString() ?? '',
      orderName: map['order_name']?.toString() ?? '',
      itemCode: map['item_code']?.toString() ?? '',
      itemName: map['item_name']?.toString() ?? '',
      qty: _toDouble(map['qty']),
      unitPrice: _toDouble(map['unit_price']),
      lineTotal: _toDouble(map['line_total']),
      notes: map['notes']?.toString(),
    );
  }
}

class OrderItemList {
  const OrderItemList({
    required this.items,
    required this.subtotal,
    required this.itemsCount,
  });

  final List<MadarOrderItem> items;
  final double subtotal;
  final int itemsCount;

  factory OrderItemList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final order = map['order'] is Map
        ? (map['order'] as Map).map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(MadarOrderItem.fromMap)
              .toList(growable: false)
        : <MadarOrderItem>[];
    return OrderItemList(
      items: items,
      subtotal: _toDouble(order['subtotal']),
      itemsCount: _toInt(order['items_count']),
    );
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
