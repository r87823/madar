enum OrderStatus {
  draft,
  submitted,
  approved,
  returnedForEdit,
  rejected,
  cancelled,
  unknown;

  String get arabicLabel {
    switch (this) {
      case OrderStatus.draft:
        return 'مسودة';
      case OrderStatus.submitted:
        return 'مرسل للاعتماد';
      case OrderStatus.approved:
        return 'معتمد - جاهز للمزامنة';
      case OrderStatus.returnedForEdit:
        return 'معاد للتعديل';
      case OrderStatus.rejected:
        return 'مرفوض';
      case OrderStatus.cancelled:
        return 'ملغي';
      case OrderStatus.unknown:
        return 'غير معروف';
    }
  }

  static OrderStatus fromString(String? value) {
    switch (value) {
      case 'draft':
        return OrderStatus.draft;
      case 'submitted':
        return OrderStatus.submitted;
      case 'approved':
        return OrderStatus.approved;
      case 'returned_for_edit':
        return OrderStatus.returnedForEdit;
      case 'rejected':
        return OrderStatus.rejected;
      case 'cancelled':
        return OrderStatus.cancelled;
      default:
        return OrderStatus.unknown;
    }
  }
}

enum OrderProductionStatus {
  notStarted,
  pending,
  inProgress,
  delayed,
  partiallyReady,
  ready,
  blocked,
  unknown;

  String get arabicLabel {
    switch (this) {
      case OrderProductionStatus.notStarted:
        return 'لم يبدأ';
      case OrderProductionStatus.pending:
        return 'بانتظار الإنتاج';
      case OrderProductionStatus.inProgress:
        return 'قيد الإنتاج';
      case OrderProductionStatus.delayed:
        return 'متأخر';
      case OrderProductionStatus.partiallyReady:
        return 'جاهز جزئيًا';
      case OrderProductionStatus.ready:
        return 'جاهز';
      case OrderProductionStatus.blocked:
        return 'متوقف';
      case OrderProductionStatus.unknown:
        return 'غير معروف';
    }
  }

  static OrderProductionStatus fromString(String? value) {
    switch (value) {
      case 'not_started':
        return OrderProductionStatus.notStarted;
      case 'pending':
        return OrderProductionStatus.pending;
      case 'in_progress':
        return OrderProductionStatus.inProgress;
      case 'delayed':
        return OrderProductionStatus.delayed;
      case 'partially_ready':
        return OrderProductionStatus.partiallyReady;
      case 'ready':
        return OrderProductionStatus.ready;
      case 'blocked':
        return OrderProductionStatus.blocked;
      default:
        return OrderProductionStatus.unknown;
    }
  }
}

class MadarOrder {
  const MadarOrder({
    required this.name,
    required this.customerName,
    required this.customerPhone,
    required this.status,
    this.branch,
    this.assignedBranch,
    this.createdByUser,
    this.notes,
    this.subtotal = 0,
    this.itemsCount = 0,
    this.submittedAt,
    this.cancelledAt,
    this.approvedAt,
    this.approvedBy,
    this.productionStatus = OrderProductionStatus.notStarted,
    this.productionReadyAt,
    this.erpSyncStatus,
    this.erpSyncError,
    this.erpSalesOrder,
  });

  final String name;
  final String customerName;
  final String customerPhone;
  final OrderStatus status;
  final String? branch;
  final String? assignedBranch;
  final String? createdByUser;
  final String? notes;
  final double subtotal;
  final int itemsCount;
  final String? submittedAt;
  final String? cancelledAt;
  final String? approvedAt;
  final String? approvedBy;
  final OrderProductionStatus productionStatus;
  final String? productionReadyAt;
  final String? erpSyncStatus;
  final String? erpSyncError;
  final String? erpSalesOrder;

  String get displayStatusLabel {
    if (status == OrderStatus.approved) {
      if (erpSyncStatus == 'synced' || erpSalesOrder?.isNotEmpty == true) {
        return 'تمت المزامنة';
      }
      if (erpSyncStatus == 'failed') {
        return 'فشل في المزامنة';
      }
    }
    return status.arabicLabel;
  }

  factory MadarOrder.fromMap(Map<String, dynamic> map) {
    return MadarOrder(
      name: map['name']?.toString() ?? '',
      customerName: map['customer_name']?.toString() ?? '',
      customerPhone: map['customer_phone']?.toString() ?? '',
      status: OrderStatus.fromString(map['order_status']?.toString()),
      branch: map['branch']?.toString(),
      assignedBranch: map['assigned_branch']?.toString(),
      createdByUser: map['created_by_user']?.toString(),
      notes: map['notes']?.toString(),
      subtotal: _toDouble(map['subtotal']),
      itemsCount: _toInt(map['items_count']),
      submittedAt: map['submitted_at']?.toString(),
      cancelledAt: map['cancelled_at']?.toString(),
      approvedAt: map['approved_at']?.toString(),
      approvedBy: map['approved_by']?.toString(),
      productionStatus: OrderProductionStatus.fromString(
        map['production_status']?.toString() ?? 'not_started',
      ),
      productionReadyAt: map['production_ready_at']?.toString(),
      erpSyncStatus: map['erp_sync_status']?.toString(),
      erpSyncError: map['erp_sync_error']?.toString(),
      erpSalesOrder: map['erp_sales_order']?.toString(),
    );
  }

  factory MadarOrder.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    return MadarOrder.fromMap(map);
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

class OrderList {
  const OrderList({required this.items});

  final List<MadarOrder> items;

  factory OrderList.fromEnvelope(Map<String, dynamic> envelope) {
    final data = envelope['data'];
    final map = data is Map
        ? data.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
    final rawItems = map['items'];
    final items = rawItems is List
        ? rawItems
              .whereType<Map>()
              .map((item) => item.map((key, value) => MapEntry('$key', value)))
              .map(MadarOrder.fromMap)
              .toList(growable: false)
        : <MadarOrder>[];
    return OrderList(items: items);
  }
}
