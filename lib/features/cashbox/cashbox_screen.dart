import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import '../../core/auth/user_context.dart';
import 'cashbox_models.dart';

class CashboxScreen extends StatefulWidget {
  const CashboxScreen({
    required this.apiClient,
    required this.userContext,
    super.key,
  });

  final FrappeApiClient apiClient;
  final UserContext userContext;

  @override
  State<CashboxScreen> createState() => _CashboxScreenState();
}

class _CashboxScreenState extends State<CashboxScreen> {
  final TextEditingController _submittedCashController =
      TextEditingController();
  final TextEditingController _returnReasonController = TextEditingController();
  Cashbox? _cashbox;
  CashboxList _reviewList = const CashboxList(items: []);
  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _message;
  bool _isError = false;

  bool get _canReview {
    final permissions = widget.userContext.permissions.toSet();
    return permissions.contains('system.full_access') ||
        permissions.contains('cashbox.review');
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _submittedCashController.dispose();
    _returnReasonController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('الصندوق')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  if (_cashbox != null) _MyCashboxCard(cashbox: _cashbox!),
                  const SizedBox(height: 12),
                  if (_cashbox != null) _buildSubmitCard(),
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
                  _EntriesCard(entries: _cashbox?.entries ?? const []),
                  if (_canReview) ...[
                    const SizedBox(height: 16),
                    _ReviewCard(
                      cashboxes: _reviewList.items,
                      returnReasonController: _returnReasonController,
                      onApprove: _approve,
                      onReturn: _returnCashbox,
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildSubmitCard() {
    final cashbox = _cashbox!;
    final canSubmit =
        cashbox.status == CashboxStatus.open ||
        cashbox.status == CashboxStatus.returned;
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'تسليم الصندوق',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _submittedCashController,
              keyboardType: TextInputType.number,
              enabled: canSubmit && !_isSubmitting,
              decoration: const InputDecoration(labelText: 'المبلغ المسلم'),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: canSubmit && !_isSubmitting ? _submit : null,
              icon: const Icon(Icons.outbox_outlined),
              label: Text(_isSubmitting ? 'جاري التسليم...' : 'إرسال للمراجعة'),
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
      final cashbox = await widget.apiClient.getMyCashbox();
      CashboxList reviewList = const CashboxList(items: []);
      if (_canReview) {
        reviewList = await widget.apiClient.listCashboxesForReview();
      }
      if (!mounted) return;
      setState(() {
        _cashbox = cashbox;
        _reviewList = reviewList;
        _submittedCashController.text = cashbox.expectedCash.toStringAsFixed(2);
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

  Future<void> _submit() async {
    final submitted = double.tryParse(_submittedCashController.text.trim());
    setState(() {
      _isSubmitting = true;
      _message = null;
      _isError = false;
    });
    try {
      final cashbox = await widget.apiClient.submitMyCashbox(submitted ?? -1);
      setState(() {
        _cashbox = cashbox;
        _message = 'تم إرسال الصندوق للمراجعة.';
      });
      await _load();
    } catch (error) {
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  Future<void> _approve(String cashboxName) async {
    await _reviewAction(() => widget.apiClient.approveCashbox(cashboxName));
  }

  Future<void> _returnCashbox(String cashboxName) async {
    final reason = _returnReasonController.text.trim();
    await _reviewAction(
      () => widget.apiClient.returnCashbox(
        cashboxName: cashboxName,
        reason: reason,
      ),
    );
  }

  Future<void> _reviewAction(Future<Cashbox> Function() action) async {
    setState(() {
      _message = null;
      _isError = false;
    });
    try {
      await action();
      setState(() {
        _message = 'تم تحديث حالة الصندوق.';
      });
      await _load();
    } catch (error) {
      setState(() {
        _message = arabicMessageForError(error);
        _isError = true;
      });
    }
  }
}

class _MyCashboxCard extends StatelessWidget {
  const _MyCashboxCard({required this.cashbox});

  final Cashbox cashbox;

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
              'صندوق اليوم',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            _Line(label: 'التاريخ', value: cashbox.cashboxDate),
            _Line(label: 'الحالة', value: cashbox.status.arabicLabel),
            _Line(
              label: 'المتوقع',
              value: cashbox.expectedCash.toStringAsFixed(2),
            ),
            _Line(
              label: 'المسلم',
              value: cashbox.submittedCash.toStringAsFixed(2),
            ),
            _Line(label: 'الفرق', value: cashbox.difference.toStringAsFixed(2)),
            if (cashbox.returnReason?.isNotEmpty == true)
              _Line(label: 'سبب الإعادة', value: cashbox.returnReason!),
          ],
        ),
      ),
    );
  }
}

class _EntriesCard extends StatelessWidget {
  const _EntriesCard({required this.entries});

  final List<CashboxEntry> entries;

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
              'قيود الصندوق',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            if (entries.isEmpty)
              Text(
                'لا توجد قيود نقدية.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ...entries.map(
                (entry) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(entry.amount.toStringAsFixed(2)),
                  subtitle: Text(
                    [
                      entry.madarOrder,
                      if (entry.payment.isNotEmpty) entry.payment,
                    ].join(' - '),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _ReviewCard extends StatelessWidget {
  const _ReviewCard({
    required this.cashboxes,
    required this.returnReasonController,
    required this.onApprove,
    required this.onReturn,
  });

  final List<Cashbox> cashboxes;
  final TextEditingController returnReasonController;
  final Future<void> Function(String cashboxName) onApprove;
  final Future<void> Function(String cashboxName) onReturn;

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
              'مراجعة الصناديق',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: returnReasonController,
              decoration: const InputDecoration(labelText: 'سبب الإعادة'),
            ),
            const SizedBox(height: 10),
            if (cashboxes.isEmpty)
              Text(
                'لا توجد صناديق مرسلة للمراجعة.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ...cashboxes.map(
                (cashbox) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(cashbox.user),
                  subtitle: Text(
                    '${cashbox.cashboxDate} - ${cashbox.expectedCash.toStringAsFixed(2)}',
                  ),
                  trailing: Wrap(
                    spacing: 8,
                    children: [
                      IconButton(
                        tooltip: 'اعتماد',
                        onPressed: () => onApprove(cashbox.name),
                        icon: const Icon(Icons.check_circle_outline),
                      ),
                      IconButton(
                        tooltip: 'إعادة',
                        onPressed: () => onReturn(cashbox.name),
                        icon: const Icon(Icons.reply_outlined),
                      ),
                    ],
                  ),
                ),
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
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 104,
            child: Text(
              label,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value.isEmpty ? '-' : value,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}
