class ReportDefinition {
  const ReportDefinition({
    required this.key,
    required this.title,
    required this.method,
    required this.filterKeys,
  });

  final String key;
  final String title;
  final String method;
  final List<String> filterKeys;
}

class ReportDefinitions {
  static const all = [
    ReportDefinition(
      key: 'orders',
      title: 'تقرير الطلبات',
      method: 'madar.api.reports.get_orders_report',
      filterKeys: [
        'date_from',
        'date_to',
        'order_status',
        'branch',
        'delivery_status',
        'production_status',
        'payment_status',
      ],
    ),
    ReportDefinition(
      key: 'payments',
      title: 'تقرير المدفوعات',
      method: 'madar.api.reports.get_payments_report',
      filterKeys: [
        'date_from',
        'date_to',
        'payment_method',
        'payment_status',
        'collection_context',
        'collected_by_user',
      ],
    ),
    ReportDefinition(
      key: 'production',
      title: 'تقرير الإنتاج',
      method: 'madar.api.reports.get_production_report',
      filterKeys: [
        'date_from',
        'date_to',
        'production_center',
        'production_department',
        'status',
      ],
    ),
    ReportDefinition(
      key: 'delivery',
      title: 'تقرير التوصيل',
      method: 'madar.api.reports.get_delivery_report',
      filterKeys: [
        'date_from',
        'date_to',
        'batch_type',
        'status',
        'driver_user',
        'destination_branch',
      ],
    ),
    ReportDefinition(
      key: 'cashbox',
      title: 'تقرير الصناديق',
      method: 'madar.api.reports.get_cashbox_report',
      filterKeys: ['date_from', 'date_to', 'status', 'user'],
    ),
    ReportDefinition(
      key: 'erp_sync_errors',
      title: 'تقرير أخطاء ERP',
      method: 'madar.api.reports.get_erp_sync_errors_report',
      filterKeys: ['entity_type', 'status', 'date_from', 'date_to'],
    ),
  ];
}

class ReportResult {
  const ReportResult({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.filters,
    required this.summary,
  });

  final List<Map<String, dynamic>> items;
  final int total;
  final int page;
  final int pageSize;
  final Map<String, dynamic> filters;
  final ReportSummary summary;

  factory ReportResult.fromEnvelope(Map<String, dynamic> envelope) {
    final data = _map(envelope['data']);
    final rawItems = data['items'];
    return ReportResult(
      items: rawItems is List
          ? rawItems.map((item) => _map(item)).toList(growable: false)
          : const [],
      total: _toInt(data['total']),
      page: _toInt(data['page'], fallback: 1),
      pageSize: _toInt(data['page_size'], fallback: 20),
      filters: _map(data['filters']),
      summary: ReportSummary.fromMap(_map(data['summary'])),
    );
  }
}

class ReportSummary {
  const ReportSummary({required this.count, required this.totalAmount});

  final int count;
  final double totalAmount;

  factory ReportSummary.fromMap(Map<String, dynamic> map) {
    return ReportSummary(
      count: _toInt(map['count']),
      totalAmount: _toDouble(map['total_amount']),
    );
  }
}

String reportFilterLabel(String key) {
  switch (key) {
    case 'date_from':
      return 'من تاريخ';
    case 'date_to':
      return 'إلى تاريخ';
    case 'order_status':
      return 'حالة الطلب';
    case 'branch':
      return 'الفرع';
    case 'delivery_status':
      return 'حالة التوصيل';
    case 'production_status':
      return 'حالة الإنتاج';
    case 'payment_status':
      return 'حالة الدفع';
    case 'payment_method':
      return 'طريقة الدفع';
    case 'collection_context':
      return 'سياق التحصيل';
    case 'collected_by_user':
      return 'المحصّل';
    case 'production_center':
      return 'مركز الإنتاج';
    case 'production_department':
      return 'قسم الإنتاج';
    case 'batch_type':
      return 'نوع الدفعة';
    case 'driver_user':
      return 'السائق';
    case 'destination_branch':
      return 'فرع الوجهة';
    case 'entity_type':
      return 'نوع السجل';
    case 'status':
      return 'الحالة';
    case 'user':
      return 'المستخدم';
    default:
      return key;
  }
}

Map<String, dynamic> _map(Object? value) {
  return value is Map
      ? value.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
}

int _toInt(Object? value, {int fallback = 0}) {
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
