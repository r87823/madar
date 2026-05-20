class ErpSyncOrder {
  const ErpSyncOrder({
    required this.name,
    required this.customerName,
    required this.subtotal,
    required this.orderStatus,
    this.deliveryStatus,
    required this.erpSyncStatus,
    this.erpSyncError,
    this.erpSalesOrder,
    this.erpSalesOrderDocstatus,
    this.erpSalesInvoice,
    this.erpInvoiceSyncStatus,
    this.erpInvoiceSyncError,
    this.erpInvoiceCreatedAt,
    this.approvedAt,
    this.approvedBy,
  });

  final String name;
  final String customerName;
  final double subtotal;
  final String orderStatus;
  final String? deliveryStatus;
  final String erpSyncStatus;
  final String? erpSyncError;
  final String? erpSalesOrder;
  final int? erpSalesOrderDocstatus;
  final String? erpSalesInvoice;
  final String? erpInvoiceSyncStatus;
  final String? erpInvoiceSyncError;
  final String? erpInvoiceCreatedAt;
  final String? approvedAt;
  final String? approvedBy;

  bool get canRetry => erpSyncStatus == 'pending' || erpSyncStatus == 'failed';
  bool get canSubmitSalesOrder =>
      (erpSalesOrder?.isNotEmpty ?? false) && erpSalesOrderDocstatus != 1;
  bool get canRetryInvoice =>
      erpInvoiceSyncStatus == 'pending' || erpInvoiceSyncStatus == 'failed';

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

  String get salesOrderStatusLabel {
    return erpSalesOrderDocstatus == 1
        ? 'أمر بيع معتمد في ERP'
        : 'أمر بيع مسودة';
  }

  String get invoiceStatusLabel {
    switch (erpInvoiceSyncStatus) {
      case 'synced':
        return 'تم إنشاء الفاتورة';
      case 'failed':
        return 'فشل إنشاء الفاتورة';
      case 'pending':
      default:
        return 'بانتظار إنشاء الفاتورة';
    }
  }

  factory ErpSyncOrder.fromMap(Map<String, dynamic> map) {
    return ErpSyncOrder(
      name: map['name']?.toString() ?? '',
      customerName: map['customer_name']?.toString() ?? '',
      subtotal: _toDouble(map['subtotal']),
      orderStatus: map['order_status']?.toString() ?? '',
      deliveryStatus: _nullableString(map['delivery_status']),
      erpSyncStatus: map['erp_sync_status']?.toString() ?? 'pending',
      erpSyncError: _nullableString(map['erp_sync_error']),
      erpSalesOrder: _nullableString(map['erp_sales_order']),
      erpSalesOrderDocstatus: _toIntOrNull(map['erp_sales_order_docstatus']),
      erpSalesInvoice: _nullableString(map['erp_sales_invoice']),
      erpInvoiceSyncStatus:
          _nullableString(map['erp_invoice_sync_status']) ?? 'pending',
      erpInvoiceSyncError: _nullableString(map['erp_invoice_sync_error']),
      erpInvoiceCreatedAt: _nullableString(map['erp_invoice_created_at']),
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

int? _toIntOrNull(Object? value) {
  if (value == null || value.toString().isEmpty || value.toString() == 'null') {
    return null;
  }
  if (value is num) return value.toInt();
  return int.tryParse(value.toString());
}
