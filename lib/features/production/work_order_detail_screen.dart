import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import 'work_order_models.dart';

class WorkOrderDetailScreen extends StatefulWidget {
  const WorkOrderDetailScreen({
    required this.apiClient,
    required this.initialOrder,
    super.key,
  });

  final FrappeApiClient apiClient;
  final WorkOrder initialOrder;

  @override
  State<WorkOrderDetailScreen> createState() => _WorkOrderDetailScreenState();
}

class _WorkOrderDetailScreenState extends State<WorkOrderDetailScreen> {
  final _delayReasonController = TextEditingController();
  late WorkOrder _order = widget.initialOrder;
  bool _isLoading = true;
  bool _isSaving = false;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _delayReasonController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_order.name)),
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
              _Header(order: _order),
              const SizedBox(height: 12),
              _ItemsCard(items: _order.items),
              const SizedBox(height: 12),
              _ActionsCard(
                isSaving: _isSaving,
                delayReasonController: _delayReasonController,
                onAccept: () => _transition(
                  () => widget.apiClient.acceptWorkOrder(_order.name),
                ),
                onStart: () => _transition(
                  () => widget.apiClient.startWorkOrder(_order.name),
                ),
                onReady: () => _transition(
                  () => widget.apiClient.markWorkOrderReady(_order.name),
                ),
                onDelay: () => _transition(
                  () => widget.apiClient.markWorkOrderDelayed(
                    _order.name,
                    reason: _delayReasonController.text,
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
      final order = await widget.apiClient.getWorkOrder(_order.name);
      if (!mounted) return;
      setState(() {
        _order = order;
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

  Future<void> _transition(Future<WorkOrder> Function() action) async {
    setState(() {
      _isSaving = true;
      _message = null;
      _isError = false;
    });
    try {
      final order = await action();
      if (!mounted) return;
      setState(() {
        _order = order;
        _message = 'تم تحديث أمر الإنتاج';
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
          _isSaving = false;
        });
      }
    }
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.order});

  final WorkOrder order;

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
              children: [
                Expanded(
                  child: Text(
                    order.productionDepartment,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                Chip(label: Text(order.statusLabel)),
              ],
            ),
            const SizedBox(height: 8),
            _Line(label: 'الطلب', value: order.madarOrder),
            _Line(label: 'المركز', value: order.productionCenter),
            if (order.delayReason?.isNotEmpty == true)
              _Line(label: 'سبب التأخير', value: order.delayReason!),
          ],
        ),
      ),
    );
  }
}

class _ItemsCard extends StatelessWidget {
  const _ItemsCard({required this.items});

  final List<WorkOrderItem> items;

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
              'الأصناف',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            if (items.isEmpty)
              Text(
                'لا توجد أصناف.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ...items.map(
                (item) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(item.itemName),
                  subtitle: Text(item.itemCode),
                  trailing: Text(item.qty.toStringAsFixed(2)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ActionsCard extends StatelessWidget {
  const _ActionsCard({
    required this.isSaving,
    required this.delayReasonController,
    required this.onAccept,
    required this.onStart,
    required this.onReady,
    required this.onDelay,
  });

  final bool isSaving;
  final TextEditingController delayReasonController;
  final VoidCallback onAccept;
  final VoidCallback onStart;
  final VoidCallback onReady;
  final VoidCallback onDelay;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                FilledButton(
                  onPressed: isSaving ? null : onAccept,
                  child: const Text('قبول'),
                ),
                FilledButton(
                  onPressed: isSaving ? null : onStart,
                  child: const Text('بدء الإنتاج'),
                ),
                FilledButton(
                  onPressed: isSaving ? null : onReady,
                  child: const Text('جاهز'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: delayReasonController,
              decoration: const InputDecoration(labelText: 'سبب التأخير'),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: isSaving ? null : onDelay,
              icon: const Icon(Icons.schedule_outlined),
              label: const Text('تأخير'),
            ),
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
        children: [
          SizedBox(
            width: 88,
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
