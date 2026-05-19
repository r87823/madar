import '../orders/order_models.dart';

enum PaymentMethod {
  cash,
  card,
  transfer,
  online,
  unknown;

  String get apiValue {
    switch (this) {
      case PaymentMethod.cash:
        return 'cash';
      case PaymentMethod.card:
        return 'card';
      case PaymentMethod.transfer:
        return 'transfer';
      case PaymentMethod.online:
        return 'online';
      case PaymentMethod.unknown:
        return '';
    }
  }

  String get arabicLabel {
    switch (this) {
      case PaymentMethod.cash:
        return 'نقد';
      case PaymentMethod.card:
        return 'بطاقة';
      case PaymentMethod.transfer:
        return 'تحويل';
      case PaymentMethod.online:
        return 'إلكتروني';
      case PaymentMethod.unknown:
        return 'غير معروف';
    }
  }

  static PaymentMethod fromString(String? value) {
    switch (value) {
      case 'cash':
        return PaymentMethod.cash;
      case 'card':
        return PaymentMethod.card;
      case 'transfer':
        return PaymentMethod.transfer;
      case 'online':
        return PaymentMethod.online;
      default:
        return PaymentMethod.unknown;
    }
  }
}

enum PaymentCollectionContext {
  branch,
  delivery,
  admin,
  unknown;

  String get arabicLabel {
    switch (this) {
      case PaymentCollectionContext.branch:
        return 'الفرع';
      case PaymentCollectionContext.delivery:
        return 'التوصيل';
      case PaymentCollectionContext.admin:
        return 'الإدارة';
      case PaymentCollectionContext.unknown:
        return 'غير معروف';
    }
  }

  static PaymentCollectionContext fromString(String? value) {
    switch (value) {
      case 'branch':
        return PaymentCollectionContext.branch;
      case 'delivery':
        return PaymentCollectionContext.delivery;
      case 'admin':
        return PaymentCollectionContext.admin;
      default:
        return PaymentCollectionContext.unknown;
    }
  }
}

class MadarPayment {
  const MadarPayment({
    required this.name,
    required this.madarOrder,
    required this.amount,
    required this.paymentMethod,
    required this.paymentStatus,
    required this.collectionContext,
    this.collectedByUser,
    this.collectedAt,
    this.referenceNo,
    this.notes,
    this.isCancelled = false,
    this.cancellationReason,
  });

  final String name;
  final String madarOrder;
  final double amount;
  final PaymentMethod paymentMethod;
  final String paymentStatus;
  final PaymentCollectionContext collectionContext;
  final String? collectedByUser;
  final String? collectedAt;
  final String? referenceNo;
  final String? notes;
  final bool isCancelled;
  final String? cancellationReason;

  factory MadarPayment.fromMap(Map<String, dynamic> map) {
    return MadarPayment(
      name: map['name']?.toString() ?? '',
      madarOrder: map['madar_order']?.toString() ?? '',
      amount: _toDouble(map['amount']),
      paymentMethod: PaymentMethod.fromString(
        map['payment_method']?.toString(),
      ),
      paymentStatus: map['payment_status']?.toString() ?? '',
      collectionContext: PaymentCollectionContext.fromString(
        map['collection_context']?.toString(),
      ),
      collectedByUser: map['collected_by_user']?.toString(),
      collectedAt: map['collected_at']?.toString(),
      referenceNo: map['reference_no']?.toString(),
      notes: map['notes']?.toString(),
      isCancelled: map['is_cancelled'] == true || map['is_cancelled'] == 1,
      cancellationReason: map['cancellation_reason']?.toString(),
    );
  }

  factory MadarPayment.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return MadarPayment.fromMap(map);
  }
}

class PaymentList {
  const PaymentList({required this.items});

  final List<MadarPayment> items;

  factory PaymentList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(MadarPayment.fromMap)
              .toList(growable: false)
        : <MadarPayment>[];
    return PaymentList(items: items);
  }
}

class PaymentCollectionResult {
  const PaymentCollectionResult({required this.payment, this.order});

  final MadarPayment payment;
  final MadarOrder? order;

  factory PaymentCollectionResult.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final orderData = map['order'];
    return PaymentCollectionResult(
      payment: MadarPayment.fromMap(map),
      order: orderData is Map
          ? MadarOrder.fromMap(
              orderData.map((key, value) => MapEntry('$key', value)),
            )
          : null,
    );
  }
}

double _toDouble(Object? value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
