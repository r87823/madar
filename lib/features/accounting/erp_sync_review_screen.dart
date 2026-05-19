import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'erp_sync_models.dart';

class ErpSyncReviewScreen extends StatefulWidget {
  const ErpSyncReviewScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<ErpSyncReviewScreen> createState() => _ErpSyncReviewScreenState();
}

class _ErpSyncReviewScreenState extends State<ErpSyncReviewScreen> {
  ErpSyncOrderList _orders = const ErpSyncOrderList(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;
  String? _retryingOrder;

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
            else if (_orders.items.isEmpty)
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
      if (!mounted) return;
      setState(() {
        _orders = orders;
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
