class ProductItem {
  const ProductItem({
    required this.itemCode,
    required this.itemName,
    required this.stockUom,
    required this.disabled,
    this.image,
    this.defaultPrice = 0,
  });

  final String itemCode;
  final String itemName;
  final String stockUom;
  final bool disabled;
  final String? image;
  final double defaultPrice;

  factory ProductItem.fromMap(Map<String, dynamic> map) {
    return ProductItem(
      itemCode: map['item_code']?.toString() ?? '',
      itemName: map['item_name']?.toString() ?? '',
      stockUom: map['stock_uom']?.toString() ?? '',
      disabled: map['disabled'] == 1 || map['disabled'] == true,
      image: map['image']?.toString(),
      defaultPrice: _toDouble(map['default_price']),
    );
  }
}

class ProductList {
  const ProductList({required this.items});

  final List<ProductItem> items;

  factory ProductList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(ProductItem.fromMap)
              .toList(growable: false)
        : <ProductItem>[];
    return ProductList(items: items);
  }
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
