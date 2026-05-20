enum PaymentSyncMethod {
  cash,
  card,
  transfer,
  online,
  unknown;

  String get arabicLabel {
    switch (this) {
      case PaymentSyncMethod.cash:
        return 'نقد';
      case PaymentSyncMethod.card:
        return 'بطاقة';
      case PaymentSyncMethod.transfer:
        return 'تحويل';
      case PaymentSyncMethod.online:
        return 'إلكتروني';
      case PaymentSyncMethod.unknown:
        return 'غير معروف';
    }
  }

  static PaymentSyncMethod fromString(String? value) {
    switch (value) {
      case 'cash':
        return PaymentSyncMethod.cash;
      case 'card':
        return PaymentSyncMethod.card;
      case 'transfer':
        return PaymentSyncMethod.transfer;
      case 'online':
        return PaymentSyncMethod.online;
      default:
        return PaymentSyncMethod.unknown;
    }
  }
}

class PaymentSyncItem {
  const PaymentSyncItem({
    required this.name,
    required this.madarOrder,
    required this.customerName,
    required this.amount,
    required this.paymentMethod,
    required this.erpSyncStatus,
    this.erpSyncError,
    this.erpPaymentEntry,
    this.erpSalesOrder,
    this.referenceNo,
  });

  final String name;
  final String madarOrder;
  final String customerName;
  final double amount;
  final PaymentSyncMethod paymentMethod;
  final String erpSyncStatus;
  final String? erpSyncError;
  final String? erpPaymentEntry;
  final String? erpSalesOrder;
  final String? referenceNo;

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

  factory PaymentSyncItem.fromMap(Map<String, dynamic> map) {
    return PaymentSyncItem(
      name: map['name']?.toString() ?? '',
      madarOrder: map['madar_order']?.toString() ?? '',
      customerName: map['customer_name']?.toString() ?? '',
      amount: _toDouble(map['amount']),
      paymentMethod: PaymentSyncMethod.fromString(
        map['payment_method']?.toString(),
      ),
      erpSyncStatus: map['erp_sync_status']?.toString() ?? 'pending',
      erpSyncError: _nullableString(map['erp_sync_error']),
      erpPaymentEntry: _nullableString(map['erp_payment_entry']),
      erpSalesOrder: _nullableString(map['erp_sales_order']),
      referenceNo: _nullableString(map['reference_no']),
    );
  }

  factory PaymentSyncItem.fromEnvelope(Map<String, dynamic> envelope) {
    return PaymentSyncItem.fromMap(_dataMap(envelope));
  }
}

class PaymentSyncItemList {
  const PaymentSyncItemList({required this.items});

  final List<PaymentSyncItem> items;

  factory PaymentSyncItemList.fromEnvelope(Map<String, dynamic> envelope) {
    final rawItems = _dataMap(envelope)['items'];
    return PaymentSyncItemList(
      items: rawItems is List
          ? rawItems
                .whereType<Map>()
                .map(
                  (item) => item.map((key, value) => MapEntry('$key', value)),
                )
                .map(PaymentSyncItem.fromMap)
                .toList(growable: false)
          : const [],
    );
  }
}

Map<String, dynamic> _dataMap(Map<String, dynamic> envelope) {
  final data = envelope['data'];
  return data is Map
      ? data.map((key, value) => MapEntry('$key', value))
      : <String, dynamic>{};
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
