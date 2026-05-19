import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'work_order_detail_screen.dart';
import 'work_order_models.dart';

class WorkOrderListScreen extends StatefulWidget {
  const WorkOrderListScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<WorkOrderListScreen> createState() => _WorkOrderListScreenState();
}

class _WorkOrderListScreenState extends State<WorkOrderListScreen> {
  WorkOrderList _orders = const WorkOrderList(items: []);
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
      appBar: AppBar(title: const Text('أوامر الإنتاج')),
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
              const _EmptyWorkOrders()
            else
              ..._orders.items.map(
                (order) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _WorkOrderCard(
                    order: order,
                    onTap: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => WorkOrderDetailScreen(
                            apiClient: widget.apiClient,
                            initialOrder: order,
                          ),
                        ),
                      );
                      if (mounted) {
                        await _load();
                      }
                    },
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
      final orders = await widget.apiClient.listWorkOrders();
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
}

class _WorkOrderCard extends StatelessWidget {
  const _WorkOrderCard({required this.order, required this.onTap});

  final WorkOrder order;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: ListTile(
        onTap: onTap,
        title: Text(order.productionDepartment),
        subtitle: Text('${order.madarOrder} / ${order.productionCenter}'),
        trailing: Chip(label: Text(order.statusLabel)),
      ),
    );
  }
}

class _EmptyWorkOrders extends StatelessWidget {
  const _EmptyWorkOrders();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد أوامر إنتاج.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
