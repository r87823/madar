import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import '../orders/order_models.dart';

class DispatchQueueScreen extends StatefulWidget {
  const DispatchQueueScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<DispatchQueueScreen> createState() => _DispatchQueueScreenState();
}

class _DispatchQueueScreenState extends State<DispatchQueueScreen> {
  OrderList _orders = const OrderList(items: []);
  final Set<String> _selectedOrders = {};
  final TextEditingController _driverController = TextEditingController();
  bool _isLoading = true;
  bool _isCreatingBatch = false;
  String? _message;
  bool _isError = false;

  @override
  void dispose() {
    _driverController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    _loadQueue();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('مهام التوصيل')),
      body: RefreshIndicator(
        onRefresh: _loadQueue,
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
            else ...[
              ..._orders.items.map(
                (order) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _DispatchCard(
                    order: order,
                    isSelected: _selectedOrders.contains(order.name),
                    onSelectedChanged:
                        order.deliveryStatus ==
                            OrderDeliveryStatus.readyForDispatch
                        ? (selected) {
                            setState(() {
                              if (selected) {
                                _selectedOrders.add(order.name);
                              } else {
                                _selectedOrders.remove(order.name);
                              }
                            });
                          }
                        : null,
                    onAction: _runAction,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Card(
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'إنشاء دفعة توصيل',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _driverController,
                        decoration: const InputDecoration(
                          labelText: 'بريد السائق',
                          hintText: 'driver.test@example.com',
                        ),
                      ),
                      const SizedBox(height: 12),
                      FilledButton.icon(
                        onPressed: _selectedOrders.isEmpty || _isCreatingBatch
                            ? null
                            : _createBatch,
                        icon: const Icon(Icons.inventory_2_outlined),
                        label: Text(
                          _isCreatingBatch
                              ? 'جاري إنشاء الدفعة...'
                              : 'إنشاء دفعة من المحدد',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _loadQueue() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final orders = await widget.apiClient.listDispatchQueue();
      if (!mounted) return;
      setState(() {
        _orders = orders;
        _selectedOrders.removeWhere(
          (orderName) => !orders.items.any((order) => order.name == orderName),
        );
      });
    } catch (error) {
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

  Future<void> _runAction(MadarOrder order, _DeliveryAction action) async {
    setState(() {
      _message = null;
      _isError = false;
    });
    try {
      if (action == _DeliveryAction.failedDelivery) {
        await widget.apiClient.markFailedDelivery(
          order.name,
          reason: 'تعذر التسليم',
        );
      } else {
        await switch (action) {
          _DeliveryAction.dispatchedToBranch =>
            widget.apiClient.markDispatchedToBranch(order.name),
          _DeliveryAction.receivedAtBranch =>
            widget.apiClient.markReceivedAtBranch(order.name),
          _DeliveryAction.readyForPickup =>
            widget.apiClient.markReadyForCustomerPickup(order.name),
          _DeliveryAction.customerPickedUp =>
            widget.apiClient.markCustomerPickedUp(order.name),
          _DeliveryAction.dispatchedToCustomer =>
            widget.apiClient.markDispatchedToCustomer(order.name),
          _DeliveryAction.deliveredToCustomer =>
            widget.apiClient.markDeliveredToCustomer(order.name),
          _DeliveryAction.failedDelivery => widget.apiClient.markFailedDelivery(
            order.name,
            reason: 'تعذر التسليم',
          ),
        };
      }
      setState(() {
        _message = 'تم تحديث حالة التسليم.';
      });
      await _loadQueue();
    } catch (error) {
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    }
  }

  Future<void> _createBatch() async {
    setState(() {
      _isCreatingBatch = true;
      _message = null;
      _isError = false;
    });
    try {
      final batch = await widget.apiClient.createDeliveryBatch(
        _selectedOrders.toList(growable: false),
      );
      final driverUser = _driverController.text.trim();
      if (driverUser.isNotEmpty) {
        await widget.apiClient.assignDeliveryBatchDriver(
          batchName: batch.name,
          driverUser: driverUser,
        );
      }
      setState(() {
        _selectedOrders.clear();
        _message = driverUser.isEmpty
            ? 'تم إنشاء الدفعة.'
            : 'تم إنشاء الدفعة وتعيين السائق.';
      });
      await _loadQueue();
    } catch (error) {
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isCreatingBatch = false;
        });
      }
    }
  }
}

class _DispatchCard extends StatelessWidget {
  const _DispatchCard({
    required this.order,
    required this.isSelected,
    required this.onSelectedChanged,
    required this.onAction,
  });

  final MadarOrder order;
  final bool isSelected;
  final ValueChanged<bool>? onSelectedChanged;
  final Future<void> Function(MadarOrder order, _DeliveryAction action)
  onAction;

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
                Checkbox(
                  value: isSelected,
                  onChanged: onSelectedChanged == null
                      ? null
                      : (value) => onSelectedChanged!(value ?? false),
                ),
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
              ],
            ),
            const SizedBox(height: 8),
            _Line(label: 'الجوال', value: order.customerPhone),
            _Line(
              label: 'طريقة التسليم',
              value: order.fulfillmentMethod.arabicLabel,
            ),
            _Line(
              label: 'فرع الاستلام',
              value: order.destinationBranch?.isNotEmpty == true
                  ? order.destinationBranch!
                  : 'لا يوجد',
            ),
            _Line(label: 'الإنتاج', value: order.productionStatus.arabicLabel),
            _Line(label: 'التسليم', value: order.deliveryStatus.arabicLabel),
            _Line(label: 'الإجمالي', value: order.subtotal.toStringAsFixed(2)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _actionsFor(order)
                  .map(
                    (action) => FilledButton(
                      onPressed: () => onAction(order, action),
                      child: Text(action.label),
                    ),
                  )
                  .toList(growable: false),
            ),
          ],
        ),
      ),
    );
  }

  List<_DeliveryAction> _actionsFor(MadarOrder order) {
    if (order.fulfillmentMethod == OrderFulfillmentMethod.branchPickup) {
      return switch (order.deliveryStatus) {
        OrderDeliveryStatus.readyForDispatch => [
          _DeliveryAction.dispatchedToBranch,
        ],
        OrderDeliveryStatus.dispatchedToBranch => [
          _DeliveryAction.receivedAtBranch,
        ],
        OrderDeliveryStatus.receivedAtBranch => [
          _DeliveryAction.readyForPickup,
        ],
        OrderDeliveryStatus.readyForCustomerPickup => [
          _DeliveryAction.customerPickedUp,
        ],
        _ => const [],
      };
    }
    if (order.fulfillmentMethod == OrderFulfillmentMethod.customerDelivery) {
      return switch (order.deliveryStatus) {
        OrderDeliveryStatus.readyForDispatch => [
          _DeliveryAction.dispatchedToCustomer,
        ],
        OrderDeliveryStatus.dispatchedToCustomer => [
          _DeliveryAction.deliveredToCustomer,
          _DeliveryAction.failedDelivery,
        ],
        _ => const [],
      };
    }
    return const [];
  }
}

enum _DeliveryAction {
  dispatchedToBranch('خرج إلى الفرع'),
  receivedAtBranch('تم الاستلام في الفرع'),
  readyForPickup('جاهز لاستلام العميل'),
  customerPickedUp('تم تسليم العميل'),
  dispatchedToCustomer('خرج للتوصيل'),
  deliveredToCustomer('تم التسليم للعميل'),
  failedDelivery('تعذر التسليم');

  const _DeliveryAction(this.label);

  final String label;
}

class _Line extends StatelessWidget {
  const _Line({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
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

class _EmptyQueue extends StatelessWidget {
  const _EmptyQueue();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد مهام توصيل.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
