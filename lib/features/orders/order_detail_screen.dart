import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'items/order_item_models.dart';
import 'items/order_items_section.dart';
import 'items/product_models.dart';
import 'items/product_picker_sheet.dart';
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
  OrderItemList _itemList = const OrderItemList(
    items: [],
    subtotal: 0,
    itemsCount: 0,
  );
  bool _isLoading = false;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadItems();
  }

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
                  _Row(
                    label: 'عدد الأصناف',
                    value: _currentItemsCount.toString(),
                  ),
                  _Row(
                    label: 'الإجمالي',
                    value: _currentSubtotal.toStringAsFixed(2),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          OrderItemsSection(
            items: _itemList.items,
            subtotal: _currentSubtotal,
            canEdit: _canEditOrder,
            onAdd: _openProductPicker,
            onIncrease: (item) => _setQty(item, item.qty + 1),
            onDecrease: (item) => _setQty(item, item.qty - 1),
            onRemove: _removeItem,
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
          if (_canSubmitOrder)
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

  bool get _canEditOrder {
    return _order.status == OrderStatus.draft ||
        _order.status == OrderStatus.returnedForEdit;
  }

  bool get _canSubmitOrder {
    return _order.status == OrderStatus.draft ||
        _order.status == OrderStatus.returnedForEdit;
  }

  double get _currentSubtotal {
    if (_itemList.items.isNotEmpty || _itemList.subtotal > 0) {
      return _itemList.subtotal;
    }
    return _order.subtotal;
  }

  int get _currentItemsCount {
    if (_itemList.items.isNotEmpty || _itemList.itemsCount > 0) {
      return _itemList.itemsCount;
    }
    return _order.itemsCount;
  }

  Future<void> _loadItems() async {
    try {
      final itemList = await widget.apiClient.listOrderItems(_order.name);
      if (!mounted) return;
      setState(() {
        _itemList = itemList;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = error.toString();
        _isError = true;
      });
    }
  }

  Future<void> _openProductPicker() async {
    final product = await showModalBottomSheet<ProductItem>(
      context: context,
      isScrollControlled: true,
      builder: (_) => ProductPickerSheet(apiClient: widget.apiClient),
    );
    if (product == null) return;
    await _mutateItems(
      () => widget.apiClient.addOrderItem(
        orderName: _order.name,
        itemCode: product.itemCode,
        qty: 1,
      ),
      'تمت إضافة الصنف.',
    );
  }

  Future<void> _setQty(MadarOrderItem item, double qty) async {
    if (qty <= 0) {
      await _removeItem(item);
      return;
    }
    await _mutateItems(
      () => widget.apiClient.updateOrderItemQty(
        orderName: _order.name,
        itemName: item.name,
        qty: qty,
      ),
      'تم تعديل الكمية.',
    );
  }

  Future<void> _removeItem(MadarOrderItem item) async {
    await _mutateItems(
      () => widget.apiClient.removeOrderItem(
        orderName: _order.name,
        itemName: item.name,
      ),
      'تم حذف الصنف.',
    );
  }

  Future<void> _mutateItems(
    Future<OrderItemList> Function() action,
    String message,
  ) async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      await action();
      final itemList = await widget.apiClient.listOrderItems(_order.name);
      setState(() {
        _itemList = itemList;
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
