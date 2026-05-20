import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'erp_sync_models.dart';
import 'payment_sync_models.dart';

class ErpSyncReviewScreen extends StatefulWidget {
  const ErpSyncReviewScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<ErpSyncReviewScreen> createState() => _ErpSyncReviewScreenState();
}

class _ErpSyncReviewScreenState extends State<ErpSyncReviewScreen> {
  ErpSyncOrderList _orders = const ErpSyncOrderList(items: []);
  ErpSyncOrderList _invoiceOrders = const ErpSyncOrderList(items: []);
  PaymentSyncItemList _payments = const PaymentSyncItemList(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;
  String? _retryingOrder;
  String? _submittingSalesOrder;
  String? _retryingInvoice;
  String? _retryingPayment;

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
      if (!mounted) return;
      setState(() {
        _orders = orders;
        _invoiceOrders = invoiceOrders;
        _payments = payments;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = error.toString();
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
        _message = error.toString();
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
        _message = error.toString();
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
        _message = error.toString();
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
        _message = error.toString();
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
              _Line(label: 'حالة أمر البيع', value: order.salesOrderStatusLabel),
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
