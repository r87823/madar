import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../orders/order_models.dart';
import 'payment_models.dart';

class PaymentSection extends StatefulWidget {
  const PaymentSection({
    required this.apiClient,
    required this.order,
    required this.canCollect,
    super.key,
  });

  final FrappeApiClient apiClient;
  final MadarOrder order;
  final bool canCollect;

  @override
  State<PaymentSection> createState() => _PaymentSectionState();
}

class _PaymentSectionState extends State<PaymentSection> {
  final TextEditingController _amountController = TextEditingController();
  final TextEditingController _referenceController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  PaymentMethod _method = PaymentMethod.cash;
  late MadarOrder _summaryOrder = widget.order;
  PaymentList _payments = const PaymentList(items: []);
  bool _isLoading = true;
  bool _isCollecting = false;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _amountController.text = widget.order.remainingAmount > 0
        ? widget.order.remainingAmount.toStringAsFixed(2)
        : '';
    _loadPayments();
  }

  @override
  void dispose() {
    _amountController.dispose();
    _referenceController.dispose();
    _notesController.dispose();
    super.dispose();
  }

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
              'المدفوعات',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            _Line(
              label: 'الإجمالي',
              value: _summaryOrder.subtotal.toStringAsFixed(2),
            ),
            _Line(
              label: 'المدفوع',
              value: _summaryOrder.paidAmount.toStringAsFixed(2),
            ),
            _Line(
              label: 'المتبقي',
              value: _summaryOrder.remainingAmount.toStringAsFixed(2),
            ),
            _Line(
              label: 'حالة الدفع',
              value: _summaryOrder.paymentStatus.arabicLabel,
            ),
            if (widget.canCollect) ...[
              const Divider(height: 24),
              TextField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'المبلغ'),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<PaymentMethod>(
                initialValue: _method,
                decoration: const InputDecoration(labelText: 'طريقة الدفع'),
                items: PaymentMethod.values
                    .where((method) => method != PaymentMethod.unknown)
                    .map(
                      (method) => DropdownMenuItem(
                        value: method,
                        child: Text(method.arabicLabel),
                      ),
                    )
                    .toList(growable: false),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      _method = value;
                    });
                  }
                },
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _referenceController,
                decoration: const InputDecoration(labelText: 'رقم المرجع'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _notesController,
                decoration: const InputDecoration(labelText: 'ملاحظات'),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _isCollecting ? null : _collect,
                icon: const Icon(Icons.payments_outlined),
                label: Text(_isCollecting ? 'جاري التحصيل...' : 'تحصيل الدفع'),
              ),
            ],
            if (_message != null) ...[
              const SizedBox(height: 10),
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
            const Divider(height: 24),
            Text(
              'سجل المدفوعات',
              style: Theme.of(
                context,
              ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else if (_payments.items.isEmpty)
              Text(
                'لا توجد مدفوعات.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ..._payments.items.map(
                (payment) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    '${payment.paymentMethod.arabicLabel} - ${payment.amount.toStringAsFixed(2)}',
                  ),
                  subtitle: Text(
                    [
                      payment.collectionContext.arabicLabel,
                      if (payment.notes?.isNotEmpty == true) payment.notes!,
                    ].join(' - '),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _loadPayments() async {
    try {
      final payments = await widget.apiClient.listOrderPayments(
        widget.order.name,
      );
      if (!mounted) return;
      setState(() {
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

  Future<void> _collect() async {
    final amount = double.tryParse(_amountController.text.trim()) ?? 0;
    setState(() {
      _isCollecting = true;
      _message = null;
      _isError = false;
    });
    try {
      final result = await widget.apiClient.collectPayment(
        orderName: widget.order.name,
        amount: amount,
        paymentMethod: _method,
        referenceNo: _referenceController.text.trim(),
        notes: _notesController.text.trim(),
      );
      setState(() {
        if (result.order != null) {
          _summaryOrder = result.order!;
          _amountController.text = result.order!.remainingAmount > 0
              ? result.order!.remainingAmount.toStringAsFixed(2)
              : '';
        }
        _message = 'تم تحصيل الدفع.';
      });
      await _loadPayments();
    } catch (error) {
      setState(() {
        _message = error.toString();
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isCollecting = false;
        });
      }
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
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 96,
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
