class SettingsList {
  const SettingsList({required this.items});

  final List<MadarSetting> items;

  factory SettingsList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _map(envelope['data']);
    final raw = data['items'];
    return SettingsList(
      items: raw is List
          ? raw
                .map((item) => MadarSetting.fromMap(_map(item)))
                .toList(growable: false)
          : const [],
    );
  }
}

class MadarSetting {
  const MadarSetting({
    required this.settingKey,
    required this.value,
    required this.valueType,
    required this.category,
    required this.labelAr,
    required this.descriptionAr,
    required this.isEditable,
  });

  final String settingKey;
  final Object? value;
  final String valueType;
  final String category;
  final String labelAr;
  final String descriptionAr;
  final bool isEditable;

  factory MadarSetting.fromMap(Map<String, dynamic> map) {
    return MadarSetting(
      settingKey: map['setting_key']?.toString() ?? '',
      value: map['value'],
      valueType: map['value_type']?.toString() ?? 'string',
      category: map['category']?.toString() ?? 'general',
      labelAr: map['label_ar']?.toString() ?? '',
      descriptionAr: map['description_ar']?.toString() ?? '',
      isEditable: map['is_editable'] == true || map['is_editable'] == 1,
    );
  }

  bool get boolValue => value == true || value?.toString() == 'true';
  int get intValue => value is num
      ? (value as num).toInt()
      : int.tryParse(value?.toString() ?? '') ?? 0;
  List<String> get stringListValue => value is List
      ? (value as List).map((item) => item.toString()).toList(growable: false)
      : const [];
}

String settingsCategoryLabel(String category) {
  switch (category) {
    case 'general':
      return 'إعدادات عامة';
    case 'attendance':
      return 'إعدادات الحضور';
    case 'orders':
      return 'إعدادات الطلبات';
    case 'payments':
      return 'إعدادات المدفوعات';
    case 'cashbox':
      return 'إعدادات الصندوق';
    case 'erp':
      return 'إعدادات المزامنة';
    case 'notifications':
      return 'إعدادات الإشعارات';
    default:
      return category;
  }
}

Map<String, dynamic> _map(Object? value) {
  return value is Map
      ? value.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
}
