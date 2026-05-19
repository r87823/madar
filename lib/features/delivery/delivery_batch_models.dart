import '../orders/order_models.dart';

enum DeliveryBatchType {
  branchTransfer,
  customerDelivery,
  unknown;

  String get arabicLabel {
    switch (this) {
      case DeliveryBatchType.branchTransfer:
        return 'تحويل إلى الفرع';
      case DeliveryBatchType.customerDelivery:
        return 'توصيل للعميل';
      case DeliveryBatchType.unknown:
        return 'غير معروف';
    }
  }

  static DeliveryBatchType fromString(String? value) {
    switch (value) {
      case 'branch_transfer':
        return DeliveryBatchType.branchTransfer;
      case 'customer_delivery':
        return DeliveryBatchType.customerDelivery;
      default:
        return DeliveryBatchType.unknown;
    }
  }
}

enum DeliveryBatchStatus {
  draft,
  assigned,
  pickedUp,
  outForDelivery,
  completed,
  partiallyCompleted,
  returned,
  cancelled,
  unknown;

  String get arabicLabel {
    switch (this) {
      case DeliveryBatchStatus.draft:
        return 'مسودة';
      case DeliveryBatchStatus.assigned:
        return 'تم التعيين';
      case DeliveryBatchStatus.pickedUp:
        return 'تم استلام الدفعة';
      case DeliveryBatchStatus.outForDelivery:
        return 'خرجت للتوصيل';
      case DeliveryBatchStatus.completed:
        return 'مكتملة';
      case DeliveryBatchStatus.partiallyCompleted:
        return 'مكتملة جزئيًا';
      case DeliveryBatchStatus.returned:
        return 'مرتجعة';
      case DeliveryBatchStatus.cancelled:
        return 'ملغاة';
      case DeliveryBatchStatus.unknown:
        return 'غير معروف';
    }
  }

  static DeliveryBatchStatus fromString(String? value) {
    switch (value) {
      case 'draft':
        return DeliveryBatchStatus.draft;
      case 'assigned':
        return DeliveryBatchStatus.assigned;
      case 'picked_up':
        return DeliveryBatchStatus.pickedUp;
      case 'out_for_delivery':
        return DeliveryBatchStatus.outForDelivery;
      case 'completed':
        return DeliveryBatchStatus.completed;
      case 'partially_completed':
        return DeliveryBatchStatus.partiallyCompleted;
      case 'returned':
        return DeliveryBatchStatus.returned;
      case 'cancelled':
        return DeliveryBatchStatus.cancelled;
      default:
        return DeliveryBatchStatus.unknown;
    }
  }
}

class DeliveryBatch {
  const DeliveryBatch({
    required this.name,
    required this.batchNumber,
    required this.batchType,
    required this.status,
    this.destinationBranch,
    this.driverUser,
    this.createdByUser,
    this.pickedUpAt,
    this.outForDeliveryAt,
    this.deliveredAt,
    this.returnedAt,
    this.returnReason,
    this.orders = const [],
  });

  final String name;
  final String batchNumber;
  final DeliveryBatchType batchType;
  final DeliveryBatchStatus status;
  final String? destinationBranch;
  final String? driverUser;
  final String? createdByUser;
  final String? pickedUpAt;
  final String? outForDeliveryAt;
  final String? deliveredAt;
  final String? returnedAt;
  final String? returnReason;
  final List<MadarOrder> orders;

  factory DeliveryBatch.fromMap(Map<String, dynamic> map) {
    final rawOrders = map['orders'];
    final orders = rawOrders is List
        ? rawOrders
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(MadarOrder.fromMap)
              .toList(growable: false)
        : <MadarOrder>[];
    return DeliveryBatch(
      name: map['name']?.toString() ?? '',
      batchNumber:
          map['batch_number']?.toString() ?? map['name']?.toString() ?? '',
      batchType: DeliveryBatchType.fromString(map['batch_type']?.toString()),
      status: DeliveryBatchStatus.fromString(map['status']?.toString()),
      destinationBranch: map['destination_branch']?.toString(),
      driverUser: map['driver_user']?.toString(),
      createdByUser: map['created_by_user']?.toString(),
      pickedUpAt: map['picked_up_at']?.toString(),
      outForDeliveryAt: map['out_for_delivery_at']?.toString(),
      deliveredAt: map['delivered_at']?.toString(),
      returnedAt: map['returned_at']?.toString(),
      returnReason: map['return_reason']?.toString(),
      orders: orders,
    );
  }

  factory DeliveryBatch.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return DeliveryBatch.fromMap(map);
  }
}

class DeliveryBatchList {
  const DeliveryBatchList({required this.items});

  final List<DeliveryBatch> items;

  factory DeliveryBatchList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(DeliveryBatch.fromMap)
              .toList(growable: false)
        : <DeliveryBatch>[];
    return DeliveryBatchList(items: items);
  }
}
