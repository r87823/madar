import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import 'reports_models.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  ReportDefinition? _selected;
  Future<ReportResult>? _future;
  bool _filtersOpen = false;
  final Map<String, TextEditingController> _controllers = {};

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  void _select(ReportDefinition definition) {
    setState(() {
      _selected = definition;
      _filtersOpen = false;
      _future = widget.apiClient.getReport(definition, filters: _filters());
    });
  }

  void _applyFilters() {
    final selected = _selected;
    if (selected == null) return;
    setState(() {
      _filtersOpen = false;
      _future = widget.apiClient.getReport(selected, filters: _filters());
    });
  }

  Map<String, String> _filters() {
    final selected = _selected;
    if (selected == null) return {};
    return {
      for (final key in selected.filterKeys)
        if ((_controllers[key]?.text.trim() ?? '').isNotEmpty)
          key: _controllers[key]!.text.trim(),
    };
  }

  TextEditingController _controller(String key) {
    return _controllers.putIfAbsent(key, TextEditingController.new);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('التقارير')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: ReportDefinitions.all
                .map((definition) {
                  final selected = definition.key == _selected?.key;
                  return ChoiceChip(
                    label: Text(definition.title),
                    selected: selected,
                    onSelected: (_) => _select(definition),
                  );
                })
                .toList(growable: false),
          ),
          const SizedBox(height: 16),
          if (_selected == null)
            const _StateMessage(message: 'اختر تقريرًا للعرض')
          else ...[
            _ReportHeader(
              title: _selected!.title,
              filtersOpen: _filtersOpen,
              onToggleFilters: () {
                setState(() => _filtersOpen = !_filtersOpen);
              },
            ),
            if (_filtersOpen)
              _FilterPanel(
                definition: _selected!,
                controllerFor: _controller,
                onApply: _applyFilters,
              ),
            const SizedBox(height: 12),
            FutureBuilder<ReportResult>(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.connectionState != ConnectionState.done) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return _StateMessage(
                    message: arabicMessageForError(snapshot.error),
                  );
                }
                final result = snapshot.data;
                if (result == null || result.items.isEmpty) {
                  return const _StateMessage(message: 'لا توجد نتائج');
                }
                return _ReportResultView(result: result);
              },
            ),
          ],
        ],
      ),
    );
  }
}

class _ReportHeader extends StatelessWidget {
  const _ReportHeader({
    required this.title,
    required this.filtersOpen,
    required this.onToggleFilters,
  });

  final String title;
  final bool filtersOpen;
  final VoidCallback onToggleFilters;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: Text(
            title,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
          ),
        ),
        OutlinedButton.icon(
          onPressed: onToggleFilters,
          icon: const Icon(Icons.filter_alt_outlined),
          label: Text(filtersOpen ? 'إخفاء الفلاتر' : 'تغيير الفلاتر'),
        ),
      ],
    );
  }
}

class _FilterPanel extends StatelessWidget {
  const _FilterPanel({
    required this.definition,
    required this.controllerFor,
    required this.onApply,
  });

  final ReportDefinition definition;
  final TextEditingController Function(String key) controllerFor;
  final VoidCallback onApply;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            Align(
              alignment: AlignmentDirectional.centerStart,
              child: FilledButton.icon(
                onPressed: onApply,
                icon: const Icon(Icons.check),
                label: const Text('تطبيق'),
              ),
            ),
            const SizedBox(height: 12),
            LayoutBuilder(
              builder: (context, constraints) {
                final width = constraints.maxWidth;
                return Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: definition.filterKeys
                      .map((key) {
                        return SizedBox(
                          width: width >= 760 ? 220 : width,
                          child: TextFormField(
                            key: ValueKey('filter-$key'),
                            controller: controllerFor(key),
                            decoration: InputDecoration(
                              labelText: reportFilterLabel(key),
                              hintText: key.startsWith('date_')
                                  ? '2026-05-20'
                                  : null,
                            ),
                          ),
                        );
                      })
                      .toList(growable: false),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _ReportResultView extends StatelessWidget {
  const _ReportResultView({required this.result});

  final ReportResult result;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Card(
          color: Theme.of(context).colorScheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Expanded(child: Text('النتائج: ${result.summary.count}')),
                Expanded(
                  child: Text('الإجمالي: ${result.summary.totalAmount}'),
                ),
                Expanded(
                  child: Text('صفحة ${result.page} / ${result.pageSize}'),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        ...result.items.map(
          (item) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _ReportRow(item: item),
          ),
        ),
      ],
    );
  }
}

class _ReportRow extends StatelessWidget {
  const _ReportRow({required this.item});

  final Map<String, dynamic> item;

  @override
  Widget build(BuildContext context) {
    final title =
        item['name']?.toString() ??
        item['entity_name']?.toString() ??
        _firstDisplayValue(item) ??
        '';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: item.entries
                  .where(
                    (entry) =>
                        entry.value != null &&
                        entry.value.toString().isNotEmpty,
                  )
                  .map(
                    (entry) =>
                        Chip(label: Text('${entry.key}: ${entry.value}')),
                  )
                  .toList(growable: false),
            ),
          ],
        ),
      ),
    );
  }
}

String? _firstDisplayValue(Map<String, dynamic> item) {
  for (final value in item.values) {
    if (value != null && value.toString().isNotEmpty) {
      return value.toString();
    }
  }
  return null;
}

class _StateMessage extends StatelessWidget {
  const _StateMessage({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(message, textAlign: TextAlign.center),
      ),
    );
  }
}
