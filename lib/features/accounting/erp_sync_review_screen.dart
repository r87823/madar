import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import 'accounting_review_models.dart';
import 'erp_sync_models.dart';
import 'payment_sync_models.dart';

class ErpSyncReviewScreen extends StatefulWidget {
  const ErpSyncReviewScreen({
    required this.apiClient,
    this.permissions = const [],
    super.key,
  });

  final FrappeApiClient apiClient;
  final List<String> permissions;

  @override
  State<ErpSyncReviewScreen> createState() => _ErpSyncReviewScreenState();
}

class _ErpSyncReviewScreenState extends State<ErpSyncReviewScreen> {
  ErpSyncOrderList _orders = const ErpSyncOrderList(items: []);
  ErpSyncOrderList _invoiceOrders = const ErpSyncOrderList(items: []);
  PaymentSyncItemList _payments = const PaymentSyncItemList(items: []);
  AccountingReviewSummaryList _accountingReviews =
      const AccountingReviewSummaryList(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;
  String? _retryingOrder;
  String? _submittingSalesOrder;
  String? _retryingInvoice;
  String? _retryingPayment;
  String? _reviewingOrder;
  String? _markingAttentionOrder;
  String? _submittingInvoiceOrder;
  String? _submittingPaymentEntriesOrder;
  String? _finalizingOrder;

  bool get _canFinalize =>
      widget.permissions.contains('accounting.finalize') ||
      widget.permissions.contains('system.full_access');

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('مراجعة مزامنة ERP')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            if (_message != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(
                  _message!,
                  style: TextStyle(
                    color: _isError
                        ? Theme.of(context).colorScheme.error
                        : Theme.of(context).colorScheme.primary,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else ...[
              Text(
                'طلبات ERP',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 12),
              if (_orders.items.isEmpty)
                const _EmptySyncOrders()
              else
                ..._orders.items.map(
                  (order) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _SyncOrderCard(
                      order: order,
                      isRetrying: _retryingOrder == order.name,
                      onRetry: order.canRetry ? () => _retry(order) : null,
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              Text(
                'فواتير ERP',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 12),
              if (_invoiceOrders.items.isEmpty)
                const _EmptyInvoices()
              else
                ..._invoiceOrders.items.map(
                  (order) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _InvoiceSyncOrderCard(
                      order: order,
                      isSubmittingSalesOrder:
                          _submittingSalesOrder == order.name,
                      isRetryingInvoice: _retryingInvoice == order.name,
                      onSubmitSalesOrder: order.canSubmitSalesOrder
                          ? () => _submitSalesOrder(order)
                          : null,
                      onRetryInvoice: order.canRetryInvoice
                          ? () => _retryInvoice(order)
                          : null,
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              Text(
                'مراجعة الإقفال',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 12),
              if (_accountingReviews.items.isEmpty)
                const _EmptyAccountingReviews()
              else
                ..._accountingReviews.items.map(
                  (summary) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _AccountingReviewCard(
                      summary: summary,
                      canFinalize: _canFinalize,
                      isReviewing: _reviewingOrder == summary.order.name,
                      isMarkingAttention:
                          _markingAttentionOrder == summary.order.name,
                      isSubmittingInvoice:
                          _submittingInvoiceOrder == summary.order.name,
                      isSubmittingPaymentEntries:
                          _submittingPaymentEntriesOrder == summary.order.name,
                      isFinalizing: _finalizingOrder == summary.order.name,
                      onReviewed: summary.canMarkReviewed
                          ? () => _markReviewed(summary)
                          : null,
                      onNeedsAttention: () => _markNeedsAttention(summary),
                      onSubmitInvoice: _canFinalize
                          ? () => _confirmAndSubmitInvoice(summary)
                          : null,
                      onSubmitPaymentEntries: _canFinalize
                          ? () => _confirmAndSubmitPaymentEntries(summary)
                          : null,
                      onFinalizeAccounting: _canFinalize
                          ? () => _confirmAndFinalizeAccounting(summary)
                          : null,
                    ),
                  ),
                ),
              const SizedBox(height: 8),
              Text(
                'مدفوعات ERP',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 12),
              if (_payments.items.isEmpty)
                const _EmptySyncPayments()
              else
                ..._payments.items.map(
                  (payment) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _SyncPaymentCard(
                      payment: payment,
                      isRetrying: _retryingPayment == payment.name,
                      onRetry: payment.canRetry
                          ? () => _retryPayment(payment)
                          : null,
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final orders = await widget.apiClient.listErpSyncOrders();
      final invoiceOrders = await widget.apiClient.listInvoiceSyncOrders();
      final payments = await widget.apiClient.listPaymentSyncItems();
      final accountingReviews = await widget.apiClient
          .listOrdersForAccountingReview();
      if (!mounted) return;
      setState(() {
        _orders = orders;
        _invoiceOrders = invoiceOrders;
        _payments = payments;
        _accountingReviews = accountingReviews;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _retry(ErpSyncOrder order) async {
    setState(() {
      _retryingOrder = order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.retryErpSyncOrder(order.name);
      if (!mounted) return;
      setState(() {
        _message = 'تمت إعادة المحاولة: ${result.statusLabel}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _retryingOrder = null;
        });
      }
    }
  }

  Future<void> _retryPayment(PaymentSyncItem payment) async {
    setState(() {
      _retryingPayment = payment.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.retryPaymentSync(payment.name);
      if (!mounted) return;
      setState(() {
        _message = 'تمت إعادة محاولة الدفع: ${result.statusLabel}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _retryingPayment = null;
        });
      }
    }
  }

  Future<void> _submitSalesOrder(ErpSyncOrder order) async {
    setState(() {
      _submittingSalesOrder = order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.submitErpSalesOrder(order.name);
      if (!mounted) return;
      setState(() {
        _message = 'تم اعتماد أمر البيع: ${result.salesOrderStatusLabel}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _submittingSalesOrder = null;
        });
      }
    }
  }

  Future<void> _retryInvoice(ErpSyncOrder order) async {
    setState(() {
      _retryingInvoice = order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.retryInvoiceSync(order.name);
      if (!mounted) return;
      setState(() {
        _message = 'تمت إعادة محاولة الفاتورة: ${result.invoiceStatusLabel}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _retryingInvoice = null;
        });
      }
    }
  }

  Future<void> _markReviewed(AccountingReviewSummary summary) async {
    setState(() {
      _reviewingOrder = summary.order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.markAccountingReviewed(
        summary.order.name,
      );
      if (!mounted) return;
      setState(() {
        _message = 'تم تحديث المراجعة: ${result.statusLabel}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _reviewingOrder = null;
        });
      }
    }
  }

  Future<void> _markNeedsAttention(AccountingReviewSummary summary) async {
    setState(() {
      _markingAttentionOrder = summary.order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.markAccountingNeedsAttention(
        summary.order.name,
        'مراجعة محاسبية مطلوبة من التطبيق',
      );
      if (!mounted) return;
      setState(() {
        _message = 'تم تحديث المراجعة: ${result.statusLabel}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _markingAttentionOrder = null;
        });
      }
    }
  }

  Future<bool> _confirmFinalAction() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('تأكيد محاسبي'),
        content: const Text(
          'هذا الإجراء قد يؤثر على القيود المحاسبية في ERPNext. هل أنت متأكد؟',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('إلغاء'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('تأكيد'),
          ),
        ],
      ),
    );
    return confirmed == true;
  }

  Future<void> _confirmAndSubmitInvoice(AccountingReviewSummary summary) async {
    if (!await _confirmFinalAction()) return;
    setState(() {
      _submittingInvoiceOrder = summary.order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.submitFinalSalesInvoice(
        summary.order.name,
      );
      if (!mounted) return;
      setState(() {
        _message = result.erpSalesInvoiceDocstatus == 1
            ? 'تم اعتماد فاتورة ERP'
            : 'تم تحديث حالة فاتورة ERP';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _submittingInvoiceOrder = null;
        });
      }
    }
  }

  Future<void> _confirmAndSubmitPaymentEntries(
    AccountingReviewSummary summary,
  ) async {
    if (!await _confirmFinalAction()) return;
    setState(() {
      _submittingPaymentEntriesOrder = summary.order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.submitPaymentEntries(
        summary.order.name,
      );
      if (!mounted) return;
      setState(() {
        _message = 'تم اعتماد سندات الدفع: ${result.items.length}';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _submittingPaymentEntriesOrder = null;
        });
      }
    }
  }

  Future<void> _confirmAndFinalizeAccounting(
    AccountingReviewSummary summary,
  ) async {
    if (!await _confirmFinalAction()) return;
    setState(() {
      _finalizingOrder = summary.order.name;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.finalizeOrderAccounting(
        summary.order.name,
      );
      if (!mounted) return;
      setState(() {
        _message = result.finalized
            ? 'تم إنهاء الإقفال المحاسبي'
            : 'تم تحديث الإقفال';
      });
      await _load();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _finalizingOrder = null;
        });
      }
    }
  }
}

class _SyncOrderCard extends StatelessWidget {
  const _SyncOrderCard({
    required this.order,
    required this.isRetrying,
    required this.onRetry,
  });

  final ErpSyncOrder order;
  final bool isRetrying;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    order.customerName.isEmpty
                        ? order.name
                        : order.customerName,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Chip(label: Text(order.statusLabel)),
              ],
            ),
            const SizedBox(height: 8),
            _Line(label: 'الطلب', value: order.name),
            _Line(label: 'الإجمالي', value: order.subtotal.toStringAsFixed(2)),
            if (order.approvedBy?.isNotEmpty == true)
              _Line(label: 'اعتمد بواسطة', value: order.approvedBy!),
            if (order.approvedAt?.isNotEmpty == true)
              _Line(label: 'وقت الاعتماد', value: order.approvedAt!),
            if (order.erpSalesOrder?.isNotEmpty == true)
              _Line(label: 'طلب ERP', value: order.erpSalesOrder!),
            if (order.erpSyncError?.isNotEmpty == true)
              _Line(label: 'الخطأ', value: order.erpSyncError!),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: isRetrying ? null : onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('إعادة المحاولة'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SyncPaymentCard extends StatelessWidget {
  const _SyncPaymentCard({
    required this.payment,
    required this.isRetrying,
    required this.onRetry,
  });

  final PaymentSyncItem payment;
  final bool isRetrying;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    payment.name,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Chip(label: Text(payment.statusLabel)),
              ],
            ),
            const SizedBox(height: 8),
            _Line(label: 'الطلب', value: payment.madarOrder),
            _Line(label: 'المبلغ', value: payment.amount.toStringAsFixed(2)),
            _Line(label: 'الطريقة', value: payment.paymentMethod.arabicLabel),
            if (payment.customerName.isNotEmpty)
              _Line(label: 'العميل', value: payment.customerName),
            if (payment.erpSalesOrder?.isNotEmpty == true)
              _Line(label: 'طلب ERP', value: payment.erpSalesOrder!),
            if (payment.erpPaymentEntry?.isNotEmpty == true)
              _Line(label: 'قيد ERP', value: payment.erpPaymentEntry!),
            if (payment.erpSyncError?.isNotEmpty == true)
              _Line(label: 'الخطأ', value: payment.erpSyncError!),
            if (onRetry != null) ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: isRetrying ? null : onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('إعادة المحاولة'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _InvoiceSyncOrderCard extends StatelessWidget {
  const _InvoiceSyncOrderCard({
    required this.order,
    required this.isSubmittingSalesOrder,
    required this.isRetryingInvoice,
    required this.onSubmitSalesOrder,
    required this.onRetryInvoice,
  });

  final ErpSyncOrder order;
  final bool isSubmittingSalesOrder;
  final bool isRetryingInvoice;
  final VoidCallback? onSubmitSalesOrder;
  final VoidCallback? onRetryInvoice;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    order.customerName.isEmpty
                        ? order.name
                        : order.customerName,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Chip(label: Text(order.invoiceStatusLabel)),
              ],
            ),
            const SizedBox(height: 8),
            _Line(label: 'الطلب', value: order.name),
            _Line(label: 'الإجمالي', value: order.subtotal.toStringAsFixed(2)),
            _Line(label: 'التسليم', value: order.deliveryStatus ?? '-'),
            if (order.erpSalesOrder?.isNotEmpty == true) ...[
              _Line(label: 'طلب ERP', value: order.erpSalesOrder!),
              _Line(
                label: 'حالة أمر البيع',
                value: order.salesOrderStatusLabel,
              ),
            ],
            if (order.erpSalesInvoice?.isNotEmpty == true)
              _Line(label: 'فاتورة ERP', value: order.erpSalesInvoice!),
            if (order.erpInvoiceCreatedAt?.isNotEmpty == true)
              _Line(label: 'وقت الفاتورة', value: order.erpInvoiceCreatedAt!),
            if (order.erpInvoiceSyncError?.isNotEmpty == true)
              _Line(label: 'الخطأ', value: order.erpInvoiceSyncError!),
            if (onSubmitSalesOrder != null || onRetryInvoice != null) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (onSubmitSalesOrder != null)
                    FilledButton.icon(
                      onPressed: isSubmittingSalesOrder
                          ? null
                          : onSubmitSalesOrder,
                      icon: const Icon(Icons.verified),
                      label: const Text('اعتماد أمر البيع'),
                    ),
                  if (onRetryInvoice != null)
                    FilledButton.icon(
                      onPressed: isRetryingInvoice ? null : onRetryInvoice,
                      icon: const Icon(Icons.refresh),
                      label: const Text('إعادة محاولة الفاتورة'),
                    ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _AccountingReviewCard extends StatelessWidget {
  const _AccountingReviewCard({
    required this.summary,
    required this.canFinalize,
    required this.isReviewing,
    required this.isMarkingAttention,
    required this.isSubmittingInvoice,
    required this.isSubmittingPaymentEntries,
    required this.isFinalizing,
    required this.onReviewed,
    required this.onNeedsAttention,
    required this.onSubmitInvoice,
    required this.onSubmitPaymentEntries,
    required this.onFinalizeAccounting,
  });

  final AccountingReviewSummary summary;
  final bool canFinalize;
  final bool isReviewing;
  final bool isMarkingAttention;
  final bool isSubmittingInvoice;
  final bool isSubmittingPaymentEntries;
  final bool isFinalizing;
  final VoidCallback? onReviewed;
  final VoidCallback onNeedsAttention;
  final VoidCallback? onSubmitInvoice;
  final VoidCallback? onSubmitPaymentEntries;
  final VoidCallback? onFinalizeAccounting;

  @override
  Widget build(BuildContext context) {
    final order = summary.order;
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    order.customerName.isEmpty
                        ? order.name
                        : order.customerName,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Chip(label: Text(summary.statusLabel)),
              ],
            ),
            const SizedBox(height: 8),
            _Line(label: 'الطلب', value: order.name),
            _Line(label: 'الإجمالي', value: order.subtotal.toStringAsFixed(2)),
            _Line(label: 'المدفوع', value: order.paidAmount.toStringAsFixed(2)),
            _Line(
              label: 'المتبقي',
              value: order.remainingAmount.toStringAsFixed(2),
            ),
            const Divider(height: 20),
            _Line(
              label: 'أمر البيع',
              value: summary.erpSalesOrder.erpSalesOrder ?? '-',
            ),
            _Line(
              label: 'الفاتورة',
              value: summary.erpSalesInvoice.erpSalesInvoice ?? '-',
            ),
            _Line(
              label: 'حالة الفاتورة',
              value: summary.erpSalesInvoice.erpSalesInvoiceDocstatus == 1
                  ? 'معتمد'
                  : 'مسودة',
            ),
            _Line(
              label: 'المدفوعات',
              value:
                  '${summary.payments.count} / ${summary.payments.totalCollected.toStringAsFixed(2)}',
            ),
            if (summary.payments.items.isNotEmpty)
              _Line(
                label: 'سندات الدفع',
                value: summary.payments.items
                    .map(
                      (payment) => '${payment.name}: ${payment.docstatusLabel}',
                    )
                    .join('، '),
              ),
            _Line(
              label: 'الصندوق',
              value: summary.cashbox.statuses.isEmpty
                  ? '-'
                  : summary.cashbox.statuses.join(', '),
            ),
            _ReadinessLine(
              label: 'التسليم',
              ok: summary.readiness.deliveredOrPickedUp,
            ),
            _ReadinessLine(
              label: 'مطابقة الدفع',
              ok: summary.readiness.paymentsMatchOrderTotal,
            ),
            _ReadinessLine(
              label: 'قيود الدفع',
              ok: summary.readiness.paymentEntriesSyncedOrNotRequired,
            ),
            _ReadinessLine(
              label: 'مراجعة الصندوق',
              ok: summary.readiness.cashboxesReviewedForCashPayments,
            ),
            if (summary.alerts.isNotEmpty)
              _Line(label: 'التنبيهات', value: summary.alerts.join(', ')),
            if (summary.accountingReviewNotes?.isNotEmpty == true)
              _Line(label: 'ملاحظات', value: summary.accountingReviewNotes!),
            if (summary.accountingFinalizedAt?.isNotEmpty == true)
              _Line(
                label: 'الإقفال',
                value: 'مقفل محاسبيًا ${summary.accountingFinalizedAt}',
              ),
            if (summary.accountingFinalizationError?.isNotEmpty == true)
              _Line(
                label: 'خطأ الإقفال',
                value: summary.accountingFinalizationError!,
              ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: isReviewing ? null : onReviewed,
                  icon: const Icon(Icons.task_alt),
                  label: const Text('تمّت المراجعة'),
                ),
                OutlinedButton.icon(
                  onPressed: isMarkingAttention ? null : onNeedsAttention,
                  icon: const Icon(Icons.report_problem_outlined),
                  label: const Text('يحتاج مراجعة / ملاحظة'),
                ),
                if (canFinalize) ...[
                  FilledButton.icon(
                    onPressed: isSubmittingInvoice ? null : onSubmitInvoice,
                    icon: const Icon(Icons.receipt_long),
                    label: const Text('اعتماد فاتورة ERP'),
                  ),
                  FilledButton.icon(
                    onPressed: isSubmittingPaymentEntries
                        ? null
                        : onSubmitPaymentEntries,
                    icon: const Icon(Icons.payments),
                    label: const Text('اعتماد سندات الدفع'),
                  ),
                  FilledButton.icon(
                    onPressed: isFinalizing ? null : onFinalizeAccounting,
                    icon: const Icon(Icons.lock),
                    label: const Text('إنهاء الإقفال المحاسبي'),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ReadinessLine extends StatelessWidget {
  const _ReadinessLine({required this.label, required this.ok});

  final String label;
  final bool ok;

  @override
  Widget build(BuildContext context) {
    return _Line(label: label, value: ok ? 'نعم' : 'لا');
  }
}

class _Line extends StatelessWidget {
  const _Line({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 94,
            child: Text(
              label,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _EmptySyncOrders extends StatelessWidget {
  const _EmptySyncOrders();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد طلبات للمزامنة.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

class _EmptySyncPayments extends StatelessWidget {
  const _EmptySyncPayments();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد مدفوعات للمزامنة.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

class _EmptyAccountingReviews extends StatelessWidget {
  const _EmptyAccountingReviews();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد طلبات لمراجعة الإقفال.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}

class _EmptyInvoices extends StatelessWidget {
  const _EmptyInvoices();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد فواتير للمزامنة.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
