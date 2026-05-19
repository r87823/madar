import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/auth/user_context.dart';
import 'order_models.dart';

class CreateOrderScreen extends StatefulWidget {
  const CreateOrderScreen({
    required this.apiClient,
    this.userContext,
    super.key,
  });

  final FrappeApiClient apiClient;
  final UserContext? userContext;

  @override
  State<CreateOrderScreen> createState() => _CreateOrderScreenState();
}

class _CreateOrderScreenState extends State<CreateOrderScreen> {
  final _formKey = GlobalKey<FormState>();
  final _customerName = TextEditingController();
  final _customerPhone = TextEditingController();
  final _notes = TextEditingController();
  late final TextEditingController _destinationBranch;
  OrderFulfillmentMethod _fulfillmentMethod =
      OrderFulfillmentMethod.branchPickup;
  bool _isSaving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _destinationBranch = TextEditingController(text: _defaultBranch);
  }

  @override
  void dispose() {
    _customerName.dispose();
    _customerPhone.dispose();
    _notes.dispose();
    _destinationBranch.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('طلب جديد')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            TextFormField(
              controller: _customerName,
              decoration: const InputDecoration(labelText: 'اسم العميل'),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'اسم العميل مطلوب';
                }
                return null;
              },
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _customerPhone,
              decoration: const InputDecoration(labelText: 'رقم الجوال'),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _notes,
              decoration: const InputDecoration(labelText: 'ملاحظات'),
              maxLines: 4,
            ),
            const SizedBox(height: 16),
            Text(
              'طريقة التسليم',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            SegmentedButton<OrderFulfillmentMethod>(
              segments: const [
                ButtonSegment(
                  value: OrderFulfillmentMethod.branchPickup,
                  label: Text('استلام من الفرع'),
                  icon: Icon(Icons.storefront_outlined),
                ),
                ButtonSegment(
                  value: OrderFulfillmentMethod.customerDelivery,
                  label: Text('توصيل للعميل'),
                  icon: Icon(Icons.local_shipping_outlined),
                ),
              ],
              selected: {_fulfillmentMethod},
              onSelectionChanged: (values) =>
                  _setFulfillmentMethod(values.first),
            ),
            if (_fulfillmentMethod == OrderFulfillmentMethod.branchPickup) ...[
              const SizedBox(height: 12),
              TextFormField(
                controller: _destinationBranch,
                decoration: const InputDecoration(labelText: 'فرع الاستلام'),
                validator: (value) {
                  if (_fulfillmentMethod ==
                          OrderFulfillmentMethod.branchPickup &&
                      (value == null || value.trim().isEmpty)) {
                    return 'فرع الاستلام مطلوب';
                  }
                  return null;
                },
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(
                _error!,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.error,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              onPressed: _isSaving ? null : _save,
              icon: const Icon(Icons.save_outlined),
              label: Text(_isSaving ? 'جار الحفظ...' : 'حفظ كمسودة'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isSaving = true;
      _error = null;
    });
    try {
      final order = await widget.apiClient.createOrderDraft(
        customerName: _customerName.text.trim(),
        customerPhone: _customerPhone.text.trim(),
        notes: _notes.text.trim(),
        fulfillmentMethod: _fulfillmentMethod,
        destinationBranch:
            _fulfillmentMethod == OrderFulfillmentMethod.branchPickup
            ? _destinationBranch.text.trim()
            : '',
      );
      if (!mounted) return;
      Navigator.of(context).pop<MadarOrder>(order);
    } catch (error) {
      setState(() {
        _error = error.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  String get _defaultBranch {
    final branches = widget.userContext?.scopes.branchNames ?? const [];
    if (branches.length == 1 && branches.single != '*') {
      return branches.single;
    }
    return widget.userContext?.employee?.branch ?? '';
  }

  void _setFulfillmentMethod(OrderFulfillmentMethod? value) {
    if (value == null) return;
    setState(() {
      _fulfillmentMethod = value;
      if (value == OrderFulfillmentMethod.branchPickup &&
          _destinationBranch.text.trim().isEmpty) {
        _destinationBranch.text = _defaultBranch;
      }
    });
  }
}
