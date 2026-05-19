import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'delivery_batch_models.dart';

class DeliveryBatchListScreen extends StatefulWidget {
  const DeliveryBatchListScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<DeliveryBatchListScreen> createState() =>
      _DeliveryBatchListScreenState();
}

class _DeliveryBatchListScreenState extends State<DeliveryBatchListScreen> {
  DeliveryBatchList _batches = const DeliveryBatchList(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadBatches();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('دفعاتي')),
      body: RefreshIndicator(
        onRefresh: _loadBatches,
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
            else if (_batches.items.isEmpty)
              const _EmptyBatches()
            else
              ..._batches.items.map(
                (batch) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _BatchCard(
                    batch: batch,
                    onOpen: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => DeliveryBatchDetailScreen(
                            apiClient: widget.apiClient,
                            batchName: batch.name,
                          ),
                        ),
                      );
                      await _loadBatches();
                    },
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _loadBatches() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final batches = await widget.apiClient.listMyDeliveryBatches();
      if (!mounted) return;
      setState(() {
        _batches = batches;
      });
    } catch (error) {
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

class DeliveryBatchDetailScreen extends StatefulWidget {
  const DeliveryBatchDetailScreen({
    required this.apiClient,
    required this.batchName,
    super.key,
  });

  final FrappeApiClient apiClient;
  final String batchName;

  @override
  State<DeliveryBatchDetailScreen> createState() =>
      _DeliveryBatchDetailScreenState();
}

class _DeliveryBatchDetailScreenState extends State<DeliveryBatchDetailScreen> {
  DeliveryBatch? _batch;
  bool _isLoading = true;
  bool _isMutating = false;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadBatch();
  }

  @override
  Widget build(BuildContext context) {
    final batch = _batch;
    return Scaffold(
      appBar: AppBar(title: const Text('تفاصيل الدفعة')),
      body: RefreshIndicator(
        onRefresh: _loadBatch,
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
            else if (batch == null)
              const _EmptyBatches()
            else ...[
              _BatchCard(batch: batch, onOpen: null),
              const SizedBox(height: 12),
              Card(
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _actionsFor(batch)
                        .map(
                          (action) => FilledButton(
                            onPressed: _isMutating
                                ? null
                                : () => _runAction(action),
                            child: Text(action.labelFor(batch.batchType)),
                          ),
                        )
                        .toList(growable: false),
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'الطلبات المرتبطة',
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              ...batch.orders.map(
                (order) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Card(
                    color: Colors.white,
                    child: ListTile(
                      title: Text(
                        order.customerName.isEmpty
                            ? order.name
                            : order.customerName,
                      ),
                      subtitle: Text(order.deliveryStatus.arabicLabel),
                      trailing: Text(order.subtotal.toStringAsFixed(2)),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _loadBatch() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final batch = await widget.apiClient.getDeliveryBatch(widget.batchName);
      if (!mounted) return;
      setState(() {
        _batch = batch;
      });
    } catch (error) {
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

  Future<void> _runAction(_BatchAction action) async {
    final batch = _batch;
    if (batch == null) return;
    setState(() {
      _isMutating = true;
      _message = null;
      _isError = false;
    });
    try {
      switch (action) {
        case _BatchAction.pickedUp:
          await widget.apiClient.markBatchPickedUp(batch.name);
        case _BatchAction.outForDelivery:
          await widget.apiClient.markBatchOutForDelivery(batch.name);
        case _BatchAction.delivered:
          await widget.apiClient.markBatchDelivered(batch.name);
        case _BatchAction.returned:
          await widget.apiClient.markBatchReturned(
            batch.name,
            reason: 'إرجاع الدفعة',
          );
      }
      setState(() {
        _message = 'تم تحديث الدفعة.';
      });
      await _loadBatch();
    } catch (error) {
      setState(() {
        _message = error.toString();
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isMutating = false;
        });
      }
    }
  }

  List<_BatchAction> _actionsFor(DeliveryBatch batch) {
    return switch (batch.status) {
      DeliveryBatchStatus.assigned => [_BatchAction.pickedUp],
      DeliveryBatchStatus.pickedUp => [
        _BatchAction.outForDelivery,
        _BatchAction.returned,
      ],
      DeliveryBatchStatus.outForDelivery => [
        _BatchAction.delivered,
        _BatchAction.returned,
      ],
      _ => const [],
    };
  }
}

class _BatchCard extends StatelessWidget {
  const _BatchCard({required this.batch, required this.onOpen});

  final DeliveryBatch batch;
  final VoidCallback? onOpen;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: InkWell(
        onTap: onOpen,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                batch.batchNumber,
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              _Line(label: 'النوع', value: batch.batchType.arabicLabel),
              _Line(label: 'الحالة', value: batch.status.arabicLabel),
              _Line(label: 'السائق', value: batch.driverUser ?? 'غير محدد'),
              _Line(
                label: 'فرع الوصول',
                value: batch.destinationBranch?.isNotEmpty == true
                    ? batch.destinationBranch!
                    : 'لا يوجد',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

enum _BatchAction {
  pickedUp,
  outForDelivery,
  delivered,
  returned;

  String labelFor(DeliveryBatchType type) {
    switch (this) {
      case _BatchAction.pickedUp:
        return 'استلام الدفعة';
      case _BatchAction.outForDelivery:
        return type == DeliveryBatchType.branchTransfer
            ? 'خرج إلى الفرع'
            : 'خرج للتوصيل';
      case _BatchAction.delivered:
        return type == DeliveryBatchType.branchTransfer
            ? 'تم التسليم للفرع'
            : 'تم التسليم';
      case _BatchAction.returned:
        return 'إرجاع مع سبب';
    }
  }
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

class _EmptyBatches extends StatelessWidget {
  const _EmptyBatches();

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Text(
          'لا توجد دفعات.',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
