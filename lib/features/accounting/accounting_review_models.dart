class AccountingReviewSummary {
  const AccountingReviewSummary({
    required this.order,
    required this.erpSalesOrder,
    required this.erpSalesInvoice,
    required this.payments,
    required this.cashbox,
    required this.readiness,
    required this.alerts,
    required this.accountingStatus,
    this.accountingReviewNotes,
    this.accountingReviewedBy,
    this.accountingReviewedAt,
    this.accountingFinalizedAt,
    this.accountingFinalizedBy,
    this.accountingFinalizationError,
  });

  final AccountingOrderSummary order;
  final AccountingErpSalesOrderSummary erpSalesOrder;
  final AccountingErpSalesInvoiceSummary erpSalesInvoice;
  final AccountingPaymentsSummary payments;
  final AccountingCashboxSummary cashbox;
  final AccountingReadiness readiness;
  final List<String> alerts;
  final String accountingStatus;
  final String? accountingReviewNotes;
  final String? accountingReviewedBy;
  final String? accountingReviewedAt;
  final String? accountingFinalizedAt;
  final String? accountingFinalizedBy;
  final String? accountingFinalizationError;

  String get statusLabel {
    switch (accountingStatus) {
      case 'ready_for_review':
        return 'جاهز للمراجعة';
      case 'needs_attention':
        return 'يحتاج انتباه';
      case 'reviewed':
        return 'تمت المراجعة';
      case 'closed_later':
        return 'إغلاق لاحق';
      case 'not_ready':
      default:
        return 'غير جاهز';
    }
  }

  bool get canMarkReviewed => accountingStatus == 'ready_for_review';

  factory AccountingReviewSummary.fromMap(Map<String, dynamic> map) {
    return AccountingReviewSummary(
      order: AccountingOrderSummary.fromMap(_map(map['order'])),
      erpSalesOrder: AccountingErpSalesOrderSummary.fromMap(
        _map(map['erp_sales_order']),
      ),
      erpSalesInvoice: AccountingErpSalesInvoiceSummary.fromMap(
        _map(map['erp_sales_invoice']),
      ),
      payments: AccountingPaymentsSummary.fromMap(_map(map['payments'])),
      cashbox: AccountingCashboxSummary.fromMap(_map(map['cashbox'])),
      readiness: AccountingReadiness.fromMap(_map(map['readiness'])),
      alerts: _stringList(map['alerts']),
      accountingStatus: map['accounting_status']?.toString() ?? 'not_ready',
      accountingReviewNotes: _nullableString(map['accounting_review_notes']),
      accountingReviewedBy: _nullableString(map['accounting_reviewed_by']),
      accountingReviewedAt: _nullableString(map['accounting_reviewed_at']),
      accountingFinalizedAt: _nullableString(map['accounting_finalized_at']),
      accountingFinalizedBy: _nullableString(map['accounting_finalized_by']),
      accountingFinalizationError: _nullableString(
        map['accounting_finalization_error'],
      ),
    );
  }

  factory AccountingReviewSummary.fromEnvelope(Map<String, dynamic> envelope) {
    return AccountingReviewSummary.fromMap(_map(envelope['data']));
  }
}

class AccountingReviewSummaryList {
  const AccountingReviewSummaryList({required this.items});

  final List<AccountingReviewSummary> items;

  factory AccountingReviewSummaryList.fromEnvelope(
    Map<String, dynamic> envelope,
  ) {
    final data = _map(envelope['data']);
    final rawItems = data['items'];
    final items = rawItems is List
        ? rawItems
              .map((item) => AccountingReviewSummary.fromMap(_map(item)))
              .toList(growable: false)
        : <AccountingReviewSummary>[];
    return AccountingReviewSummaryList(items: items);
  }
}

class AccountingOrderSummary {
  const AccountingOrderSummary({
    required this.name,
    required this.customerName,
    required this.subtotal,
    required this.paidAmount,
    required this.remainingAmount,
    required this.paymentStatus,
    required this.orderStatus,
    required this.deliveryStatus,
    required this.productionStatus,
    this.erpSalesInvoiceDocstatus,
    this.accountingFinalizedAt,
    this.accountingFinalizedBy,
    this.accountingFinalizationError,
  });

  final String name;
  final String customerName;
  final double subtotal;
  final double paidAmount;
  final double remainingAmount;
  final String paymentStatus;
  final String orderStatus;
  final String deliveryStatus;
  final String productionStatus;
  final int? erpSalesInvoiceDocstatus;
  final String? accountingFinalizedAt;
  final String? accountingFinalizedBy;
  final String? accountingFinalizationError;

  factory AccountingOrderSummary.fromMap(Map<String, dynamic> map) {
    return AccountingOrderSummary(
      name: map['name']?.toString() ?? '',
      customerName: map['customer_name']?.toString() ?? '',
      subtotal: _toDouble(map['subtotal']),
      paidAmount: _toDouble(map['paid_amount']),
      remainingAmount: _toDouble(map['remaining_amount']),
      paymentStatus: map['payment_status']?.toString() ?? '',
      orderStatus: map['order_status']?.toString() ?? '',
      deliveryStatus: map['delivery_status']?.toString() ?? '',
      productionStatus: map['production_status']?.toString() ?? '',
      erpSalesInvoiceDocstatus: _toIntOrNull(
        map['erp_sales_invoice_docstatus'],
      ),
      accountingFinalizedAt: _nullableString(map['accounting_finalized_at']),
      accountingFinalizedBy: _nullableString(map['accounting_finalized_by']),
      accountingFinalizationError: _nullableString(
        map['accounting_finalization_error'],
      ),
    );
  }
}

class AccountingErpSalesOrderSummary {
  const AccountingErpSalesOrderSummary({
    this.erpSalesOrder,
    this.erpSalesOrderDocstatus,
    this.erpSyncStatus,
    this.erpSyncError,
  });

  final String? erpSalesOrder;
  final int? erpSalesOrderDocstatus;
  final String? erpSyncStatus;
  final String? erpSyncError;

  factory AccountingErpSalesOrderSummary.fromMap(Map<String, dynamic> map) {
    return AccountingErpSalesOrderSummary(
      erpSalesOrder: _nullableString(map['erp_sales_order']),
      erpSalesOrderDocstatus: _toIntOrNull(map['erp_sales_order_docstatus']),
      erpSyncStatus: _nullableString(map['erp_sync_status']),
      erpSyncError: _nullableString(map['erp_sync_error']),
    );
  }
}

class AccountingErpSalesInvoiceSummary {
  const AccountingErpSalesInvoiceSummary({
    this.erpSalesInvoice,
    this.erpSalesInvoiceDocstatus,
    this.erpInvoiceSyncStatus,
    this.erpInvoiceSyncError,
  });

  final String? erpSalesInvoice;
  final int? erpSalesInvoiceDocstatus;
  final String? erpInvoiceSyncStatus;
  final String? erpInvoiceSyncError;

  factory AccountingErpSalesInvoiceSummary.fromMap(Map<String, dynamic> map) {
    return AccountingErpSalesInvoiceSummary(
      erpSalesInvoice: _nullableString(map['erp_sales_invoice']),
      erpSalesInvoiceDocstatus: _toIntOrNull(
        map['erp_sales_invoice_docstatus'],
      ),
      erpInvoiceSyncStatus: _nullableString(map['erp_invoice_sync_status']),
      erpInvoiceSyncError: _nullableString(map['erp_invoice_sync_error']),
    );
  }
}

class AccountingPaymentsSummary {
  const AccountingPaymentsSummary({
    required this.count,
    required this.totalCollected,
    required this.methods,
    required this.erpSyncStatuses,
    required this.items,
  });

  final int count;
  final double totalCollected;
  final Map<String, double> methods;
  final Map<String, int> erpSyncStatuses;
  final List<AccountingPaymentItem> items;

  factory AccountingPaymentsSummary.fromMap(Map<String, dynamic> map) {
    return AccountingPaymentsSummary(
      count: _toInt(map['count']),
      totalCollected: _toDouble(map['total_collected']),
      methods: _doubleMap(map['methods']),
      erpSyncStatuses: _intMap(map['erp_sync_statuses']),
      items: (map['items'] is List)
          ? (map['items'] as List)
                .map((item) => AccountingPaymentItem.fromMap(_map(item)))
                .toList(growable: false)
          : const [],
    );
  }
}

class AccountingPaymentItem {
  const AccountingPaymentItem({
    required this.name,
    required this.amount,
    required this.paymentMethod,
    this.erpSyncStatus,
    this.erpPaymentEntry,
    this.erpPaymentEntryDocstatus,
    this.erpPaymentSubmittedAt,
    this.erpPaymentSubmitError,
  });

  final String name;
  final double amount;
  final String paymentMethod;
  final String? erpSyncStatus;
  final String? erpPaymentEntry;
  final int? erpPaymentEntryDocstatus;
  final String? erpPaymentSubmittedAt;
  final String? erpPaymentSubmitError;

  String get docstatusLabel {
    if (erpPaymentEntryDocstatus == 1) return 'معتمد';
    if (erpPaymentSubmitError?.isNotEmpty == true) return 'فشل';
    return 'مسودة';
  }

  factory AccountingPaymentItem.fromMap(Map<String, dynamic> map) {
    return AccountingPaymentItem(
      name: map['name']?.toString() ?? '',
      amount: _toDouble(map['amount']),
      paymentMethod: map['payment_method']?.toString() ?? '',
      erpSyncStatus: _nullableString(map['erp_sync_status']),
      erpPaymentEntry: _nullableString(map['erp_payment_entry']),
      erpPaymentEntryDocstatus: _toIntOrNull(
        map['erp_payment_entry_docstatus'],
      ),
      erpPaymentSubmittedAt: _nullableString(map['erp_payment_submitted_at']),
      erpPaymentSubmitError: _nullableString(map['erp_payment_submit_error']),
    );
  }
}

class AccountingFinalizationStatus {
  const AccountingFinalizationStatus({
    required this.order,
    required this.canFinalize,
    required this.payments,
    required this.finalized,
    this.erpSalesInvoiceDocstatus,
    this.accountingFinalizedAt,
    this.accountingFinalizedBy,
    this.accountingFinalizationError,
  });

  final AccountingOrderSummary order;
  final bool canFinalize;
  final int? erpSalesInvoiceDocstatus;
  final List<AccountingPaymentItem> payments;
  final bool finalized;
  final String? accountingFinalizedAt;
  final String? accountingFinalizedBy;
  final String? accountingFinalizationError;

  factory AccountingFinalizationStatus.fromEnvelope(
    Map<String, dynamic> envelope,
  ) {
    final data = _map(envelope['data']);
    final rawPayments = data['payments'];
    return AccountingFinalizationStatus(
      order: AccountingOrderSummary.fromMap(_map(data['order'])),
      canFinalize: data['can_finalize'] == true,
      erpSalesInvoiceDocstatus: _toIntOrNull(
        data['erp_sales_invoice_docstatus'],
      ),
      payments: rawPayments is List
          ? rawPayments
                .map((item) => AccountingPaymentItem.fromMap(_map(item)))
                .toList(growable: false)
          : const [],
      finalized: data['finalized'] == true,
      accountingFinalizedAt: _nullableString(data['accounting_finalized_at']),
      accountingFinalizedBy: _nullableString(data['accounting_finalized_by']),
      accountingFinalizationError: _nullableString(
        data['accounting_finalization_error'],
      ),
    );
  }
}

class AccountingFinalizationPaymentList {
  const AccountingFinalizationPaymentList({required this.items});

  final List<AccountingPaymentItem> items;

  factory AccountingFinalizationPaymentList.fromEnvelope(
    Map<String, dynamic> envelope,
  ) {
    final data = _map(envelope['data']);
    final rawItems = data['items'];
    return AccountingFinalizationPaymentList(
      items: rawItems is List
          ? rawItems
                .map((item) => AccountingPaymentItem.fromMap(_map(item)))
                .toList(growable: false)
          : const [],
    );
  }
}

class AccountingCashboxSummary {
  const AccountingCashboxSummary({
    required this.cashPaymentsTotal,
    required this.cashboxNames,
    required this.statuses,
    required this.reviewed,
  });

  final double cashPaymentsTotal;
  final List<String> cashboxNames;
  final List<String> statuses;
  final bool reviewed;

  factory AccountingCashboxSummary.fromMap(Map<String, dynamic> map) {
    return AccountingCashboxSummary(
      cashPaymentsTotal: _toDouble(map['cash_payments_total']),
      cashboxNames: _stringList(map['cashbox_names']),
      statuses: _stringList(map['statuses']),
      reviewed: map['reviewed'] == true,
    );
  }
}

class AccountingReadiness {
  const AccountingReadiness({
    required this.hasErpSalesOrder,
    required this.salesOrderSubmitted,
    required this.deliveredOrPickedUp,
    required this.hasSalesInvoiceDraft,
    required this.paymentsMatchOrderTotal,
    required this.paymentEntriesSyncedOrNotRequired,
    required this.cashboxesReviewedForCashPayments,
  });

  final bool hasErpSalesOrder;
  final bool salesOrderSubmitted;
  final bool deliveredOrPickedUp;
  final bool hasSalesInvoiceDraft;
  final bool paymentsMatchOrderTotal;
  final bool paymentEntriesSyncedOrNotRequired;
  final bool cashboxesReviewedForCashPayments;

  factory AccountingReadiness.fromMap(Map<String, dynamic> map) {
    return AccountingReadiness(
      hasErpSalesOrder: map['has_erp_sales_order'] == true,
      salesOrderSubmitted: map['sales_order_submitted'] == true,
      deliveredOrPickedUp: map['delivered_or_picked_up'] == true,
      hasSalesInvoiceDraft: map['has_sales_invoice_draft'] == true,
      paymentsMatchOrderTotal: map['payments_match_order_total'] == true,
      paymentEntriesSyncedOrNotRequired:
          map['payment_entries_synced_or_not_required'] == true,
      cashboxesReviewedForCashPayments:
          map['cashboxes_reviewed_for_cash_payments'] == true,
    );
  }
}

Map<String, dynamic> _map(Object? value) {
  if (value is Map) return value.map((key, value) => MapEntry('$key', value));
  return <String, dynamic>{};
}

List<String> _stringList(Object? value) {
  if (value is List) {
    return value.map((item) => item.toString()).toList(growable: false);
  }
  return const [];
}

Map<String, double> _doubleMap(Object? value) {
  return _map(value).map((key, value) => MapEntry(key, _toDouble(value)));
}

Map<String, int> _intMap(Object? value) {
  return _map(value).map((key, value) => MapEntry(key, _toInt(value)));
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

int _toInt(Object? value) {
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? 0;
}

int? _toIntOrNull(Object? value) {
  if (value == null || value.toString().isEmpty || value.toString() == 'null') {
    return null;
  }
  return _toInt(value);
}
