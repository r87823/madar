import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'create_order_screen.dart';
import 'order_detail_screen.dart';
import 'order_models.dart';

class OrderListScreen extends StatefulWidget {
  const OrderListScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<OrderListScreen> createState() => _OrderListScreenState();
}

class _OrderListScreenState extends State<OrderListScreen> {
  OrderList _orders = const OrderList(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadOrders();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('الطلبات')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isLoading ? null : _openCreate,
        icon: const Icon(Icons.add),
        label: const Text('طلب جديد'),
      ),
      body: RefreshIndicator(
        onRefresh: _loadOrders,
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
              const _EmptyOrders()
            else
              ..._orders.items.map(
                (order) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _OrderCard(
                    order: order,
                    onTap: () => _openDetails(order),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _loadOrders() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final orders = await widget.apiClient.listOrders();
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

  Future<void> _openCreate() async {
    final created = await Navigator.of(context).push<MadarOrder>(
      MaterialPageRoute(
        builder: (_) => CreateOrderScreen(apiClient: widget.apiClient),
      ),
    );
    if (created != null) {
      setState(() {
        _message = 'تم إنشاء الطلب ${created.name}.';
        _isError = false;
      });
      await _loadOrders();
    }
  }

  Future<void> _openDetails(MadarOrder order) async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) =>
            OrderDetailScreen(apiClient: widget.apiClient, initialOrder: order),
      ),
    );
    await _loadOrders();
  }
}

class _OrderCard extends StatelessWidget {
  const _OrderCard({required this.order, required this.onTap});

  final MadarOrder order;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: ListTile(
        onTap: onTap,
        leading: const Icon(Icons.receipt_long_outlined),
        title: Text(
          order.customerName.isEmpty ? order.name : order.customerName,
        ),
        subtitle: Text(
          [
            if (order.customerPhone.isNotEmpty) order.customerPhone,
            if (order.assignedBranch?.isNotEmpty == true) order.assignedBranch!,
          ].join(' - '),
        ),
        trailing: Chip(label: Text(order.displayStatusLabel)),
      ),
    );
  }
}

class _EmptyOrders extends StatelessWidget {
  const _EmptyOrders();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد طلبات بعد.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
