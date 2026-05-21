import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import '../../core/messages/madar_success_messages.dart';
import 'settings_models.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late Future<SettingsList> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getSettings();
  }

  Future<void> _reload() async {
    setState(() {
      _future = widget.apiClient.getSettings();
    });
    await _future;
  }

  Future<void> _update(MadarSetting setting, Object value) async {
    try {
      await widget.apiClient.updateSetting(setting.settingKey, value);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(MadarSuccessMessages.settingSaved)),
      );
      await _reload();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(arabicMessageForError(error))));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('الإعدادات')),
      body: FutureBuilder<SettingsList>(
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
          final items = snapshot.data?.items ?? const <MadarSetting>[];
          if (items.isEmpty) {
            return const _StateMessage(message: 'لا توجد إعدادات');
          }
          final grouped = <String, List<MadarSetting>>{};
          for (final item in items) {
            grouped.putIfAbsent(item.category, () => []).add(item);
          }
          const categoryOrder = [
            'general',
            'attendance',
            'orders',
            'payments',
            'cashbox',
            'erp',
            'notifications',
          ];
          final orderedEntries = [
            for (final category in categoryOrder)
              if (grouped.containsKey(category))
                MapEntry(category, grouped[category]!),
            for (final entry in grouped.entries)
              if (!categoryOrder.contains(entry.key)) entry,
          ];
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              for (final entry in orderedEntries) ...[
                Text(
                  settingsCategoryLabel(entry.key),
                  style: Theme.of(
                    context,
                  ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 10),
                ...entry.value.map(
                  (setting) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _SettingTile(setting: setting, onUpdate: _update),
                  ),
                ),
                const SizedBox(height: 10),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _SettingTile extends StatelessWidget {
  const _SettingTile({required this.setting, required this.onUpdate});

  final MadarSetting setting;
  final Future<void> Function(MadarSetting setting, Object value) onUpdate;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              setting.labelAr,
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
            ),
            if (setting.descriptionAr.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(setting.descriptionAr),
            ],
            const SizedBox(height: 10),
            _SettingControl(setting: setting, onUpdate: onUpdate),
          ],
        ),
      ),
    );
  }
}

class _SettingControl extends StatefulWidget {
  const _SettingControl({required this.setting, required this.onUpdate});

  final MadarSetting setting;
  final Future<void> Function(MadarSetting setting, Object value) onUpdate;

  @override
  State<_SettingControl> createState() => _SettingControlState();
}

class _SettingControlState extends State<_SettingControl> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(
      text: widget.setting.intValue.toString(),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final setting = widget.setting;
    if (setting.valueType == 'bool') {
      return SwitchListTile(
        key: ValueKey('setting-${setting.settingKey}'),
        contentPadding: EdgeInsets.zero,
        title: const Text('تفعيل'),
        value: setting.boolValue,
        onChanged: setting.isEditable
            ? (value) => widget.onUpdate(setting, value)
            : null,
      );
    }
    if (setting.valueType == 'int') {
      return Row(
        children: [
          SizedBox(
            width: 160,
            child: TextField(
              key: ValueKey('setting-${setting.settingKey}'),
              controller: _controller,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'القيمة'),
            ),
          ),
          const SizedBox(width: 10),
          FilledButton(
            onPressed: setting.isEditable
                ? () {
                    final value = int.tryParse(_controller.text);
                    if (value == null) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('قيمة غير صحيحة')),
                      );
                      return;
                    }
                    widget.onUpdate(setting, value);
                  }
                : null,
            child: const Text('حفظ'),
          ),
        ],
      );
    }
    if (setting.settingKey == 'payments.enabled_methods') {
      final selected = setting.stringListValue.toSet();
      const methods = {
        'cash': 'نقد',
        'card': 'بطاقة',
        'transfer': 'تحويل',
        'online': 'إلكتروني',
      };
      return Wrap(
        spacing: 8,
        children: methods.entries
            .map((entry) {
              return FilterChip(
                label: Text(entry.value),
                selected: selected.contains(entry.key),
                onSelected: setting.isEditable
                    ? (checked) {
                        final next = {...selected};
                        checked ? next.add(entry.key) : next.remove(entry.key);
                        widget.onUpdate(setting, next.toList());
                      }
                    : null,
              );
            })
            .toList(growable: false),
      );
    }
    return Text(setting.value?.toString() ?? '');
  }
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
