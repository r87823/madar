class ProductionCenter {
  const ProductionCenter({
    required this.name,
    required this.centerName,
    required this.centerCode,
    required this.isActive,
  });

  final String name;
  final String centerName;
  final String centerCode;
  final bool isActive;

  factory ProductionCenter.fromMap(Map<String, dynamic> map) {
    return ProductionCenter(
      name: map['name']?.toString() ?? '',
      centerName: map['center_name']?.toString() ?? '',
      centerCode: map['center_code']?.toString() ?? '',
      isActive: _toBool(map['is_active']),
    );
  }
}

class ProductionDepartment {
  const ProductionDepartment({
    required this.name,
    required this.departmentName,
    required this.departmentCode,
    required this.productionCenter,
    required this.isActive,
  });

  final String name;
  final String departmentName;
  final String departmentCode;
  final String productionCenter;
  final bool isActive;

  factory ProductionDepartment.fromMap(Map<String, dynamic> map) {
    return ProductionDepartment(
      name: map['name']?.toString() ?? '',
      departmentName: map['department_name']?.toString() ?? '',
      departmentCode: map['department_code']?.toString() ?? '',
      productionCenter: map['production_center']?.toString() ?? '',
      isActive: _toBool(map['is_active']),
    );
  }
}

class ProductionMapping {
  const ProductionMapping({
    required this.name,
    required this.itemCode,
    required this.itemName,
    required this.productionCenter,
    required this.productionDepartment,
    required this.isActive,
  });

  final String name;
  final String itemCode;
  final String itemName;
  final String productionCenter;
  final String productionDepartment;
  final bool isActive;

  factory ProductionMapping.fromMap(Map<String, dynamic> map) {
    return ProductionMapping(
      name: map['name']?.toString() ?? '',
      itemCode: map['item_code']?.toString() ?? '',
      itemName: map['item_name']?.toString() ?? '',
      productionCenter: map['production_center']?.toString() ?? '',
      productionDepartment: map['production_department']?.toString() ?? '',
      isActive: _toBool(map['is_active']),
    );
  }

  factory ProductionMapping.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return ProductionMapping.fromMap(map);
  }
}

class ProductionCenterList {
  const ProductionCenterList({required this.items});

  final List<ProductionCenter> items;

  factory ProductionCenterList.fromEnvelope(Map<String, dynamic> envelope) {
    return ProductionCenterList(
      items: _items(
        envelope,
      ).map(ProductionCenter.fromMap).toList(growable: false),
    );
  }
}

class ProductionDepartmentList {
  const ProductionDepartmentList({required this.items});

  final List<ProductionDepartment> items;

  factory ProductionDepartmentList.fromEnvelope(Map<String, dynamic> envelope) {
    return ProductionDepartmentList(
      items: _items(
        envelope,
      ).map(ProductionDepartment.fromMap).toList(growable: false),
    );
  }
}

class ProductionMappingList {
  const ProductionMappingList({required this.items});

  final List<ProductionMapping> items;

  factory ProductionMappingList.fromEnvelope(Map<String, dynamic> envelope) {
    return ProductionMappingList(
      items: _items(
        envelope,
      ).map(ProductionMapping.fromMap).toList(growable: false),
    );
  }
}

class OrderDepartmentMappingValidation {
  const OrderDepartmentMappingValidation({
    required this.orderName,
    required this.isValid,
    required this.missingItemCodes,
    required this.mappedItemCodes,
  });

  final String orderName;
  final bool isValid;
  final List<String> missingItemCodes;
  final List<String> mappedItemCodes;

  factory OrderDepartmentMappingValidation.fromEnvelope(
    Map<String, dynamic> envelope,
  ) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return OrderDepartmentMappingValidation(
      orderName: map['order_name']?.toString() ?? '',
      isValid: map['is_valid'] == true,
      missingItemCodes: _strings(map['missing_item_codes']),
      mappedItemCodes: _strings(map['mapped_item_codes']),
    );
  }
}

List<Map<String, dynamic>> _items(Map<String, dynamic> envelope) {
  final data = envelope['data'];
  final map = data is Map
      ? data.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
  final rawItems = map['items'];
  return rawItems is List
      ? rawItems
            .whereType<Map>()
            .map((item) => item.map((key, value) => MapEntry('$key', value)))
            .toList(growable: false)
      : <Map<String, dynamic>>[];
}

List<String> _strings(Object? value) {
  return value is List
      ? value.map((item) => item.toString()).toList(growable: false)
      : const [];
}

bool _toBool(Object? value) {
  return value == true || value == 1 || value?.toString() == '1';
}
