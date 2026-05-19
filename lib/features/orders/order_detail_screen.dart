import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'order_models.dart';

class OrderDetailScreen extends StatefulWidget {
  const OrderDetailScreen({
    required this.apiClient,
    required this.initialOrder,
    super.key,
  });

  final FrappeApiClient apiClient;
  final MadarOrder initialOrder;

  @override
  State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  late MadarOrder _order = widget.initialOrder;
  bool _isLoading = false;
  String? _message;
  bool _isError = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_order.name)),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            color: Colors.white,
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _Row(label: 'العميل', value: _order.customerName),
                  _Row(label: 'الجوال', value: _order.customerPhone),
                  _Row(label: 'الحالة', value: _order.status.arabicLabel),
                  _Row(
                    label: 'الفرع',
                    value: _order.assignedBranch ?? _order.branch ?? 'لا يوجد',
                  ),
                  _Row(
                    label: 'ملاحظات',
                    value: _order.notes?.isNotEmpty == true
                        ? _order.notes!
                        : 'لا يوجد',
                  ),
                ],
              ),
            ),
          ),
          if (_message != null) ...[
            const SizedBox(height: 12),
            Text(
              _message!,
              style: TextStyle(
                color: _isError
                    ? Theme.of(context).colorScheme.error
                    : Theme.of(context).colorScheme.primary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
          const SizedBox(height: 16),
          if (_order.status == OrderStatus.draft)
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                FilledButton.icon(
                  onPressed: _isLoading ? null : _submit,
                  icon: const Icon(Icons.send_outlined),
                  label: const Text('إرسال الطلب'),
                ),
                OutlinedButton.icon(
                  onPressed: _isLoading ? null : _cancel,
                  icon: const Icon(Icons.cancel_outlined),
                  label: const Text('إلغاء الطلب'),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    await _mutate(
      () => widget.apiClient.submitOrder(_order.name),
      'تم إرسال الطلب.',
    );
  }

  Future<void> _cancel() async {
    await _mutate(
      () => widget.apiClient.cancelOrder(_order.name),
      'تم إلغاء الطلب.',
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
      final order = await action();
      setState(() {
        _order = order;
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

class _Row extends StatelessWidget {
  const _Row({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 92,
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
