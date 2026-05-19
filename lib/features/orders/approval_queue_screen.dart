import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'order_models.dart';

class ApprovalQueueScreen extends StatefulWidget {
  const ApprovalQueueScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<ApprovalQueueScreen> createState() => _ApprovalQueueScreenState();
}

class _ApprovalQueueScreenState extends State<ApprovalQueueScreen> {
  OrderList _orders = const OrderList(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('طلبات الاعتماد')),
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
              const _EmptyQueue()
            else
              ..._orders.items.map(
                (order) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _ApprovalCard(
                    order: order,
                    onApprove: () => _approve(order),
                    onReturn: () => _reasonAction(
                      title: 'إعادة للتعديل',
                      order: order,
                      action: widget.apiClient.returnOrderForEdit,
                      success: 'تمت إعادة الطلب للتعديل.',
                    ),
                    onReject: () => _reasonAction(
                      title: 'رفض الطلب',
                      order: order,
                      action: widget.apiClient.rejectOrder,
                      success: 'تم رفض الطلب.',
                    ),
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
      final orders = await widget.apiClient.listApprovalQueue();
      setState(() {
        _orders = orders;
      });
    } catch (error) {
      setState(() {
        _message = error.toString();
        _isError = true;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _approve(MadarOrder order) async {
    await _mutate(
      () => widget.apiClient.approveOrder(order.name),
      'تم اعتماد الطلب.',
    );
  }

  Future<void> _reasonAction({
    required String title,
    required MadarOrder order,
    required Future<MadarOrder> Function(String, {required String reason})
    action,
    required String success,
  }) async {
    final reason = await _askReason(title);
    if (reason == null || reason.trim().isEmpty) return;
    await _mutate(() => action(order.name, reason: reason.trim()), success);
  }

  Future<String?> _askReason(String title) {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(labelText: 'السبب'),
          maxLines: 3,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('إلغاء'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(controller.text),
            child: const Text('تأكيد'),
          ),
        ],
      ),
    );
  }

  Future<void> _mutate(
    Future<MadarOrder> Function() action,
    String message,
  ) async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      await action();
      final orders = await widget.apiClient.listApprovalQueue();
      setState(() {
        _orders = orders;
        _message = message;
      });
    } catch (error) {
      setState(() {
        _message = error.toString();
        _isError = true;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }
}

class _ApprovalCard extends StatelessWidget {
  const _ApprovalCard({
    required this.order,
    required this.onApprove,
    required this.onReturn,
    required this.onReject,
  });

  final MadarOrder order;
  final VoidCallback onApprove;
  final VoidCallback onReturn;
  final VoidCallback onReject;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              order.customerName,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text('${order.name} - ${order.status.arabicLabel}'),
            Text('الإجمالي: ${order.subtotal.toStringAsFixed(2)}'),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton.icon(
                  onPressed: onApprove,
                  icon: const Icon(Icons.verified_outlined),
                  label: const Text('اعتماد'),
                ),
                OutlinedButton.icon(
                  onPressed: onReturn,
                  icon: const Icon(Icons.undo_outlined),
                  label: const Text('إعادة للتعديل'),
                ),
                OutlinedButton.icon(
                  onPressed: onReject,
                  icon: const Icon(Icons.block_outlined),
                  label: const Text('رفض'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyQueue extends StatelessWidget {
  const _EmptyQueue();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد طلبات مرسلة للاعتماد.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
