import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'attendance_status.dart';

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  AttendanceStatus? _status;
  bool _isLoading = true;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('الحضور والانصراف')),
      body: RefreshIndicator(
        onRefresh: _loadStatus,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Card(
              color: Colors.white,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'حالة الدوام',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 16),
                    if (_isLoading)
                      const Center(child: CircularProgressIndicator())
                    else ...[
                      _StatusRow(
                        label: 'الموظف',
                        value: _status?.employeeName.isNotEmpty == true
                            ? _status!.employeeName
                            : 'غير معروف',
                      ),
                      _StatusRow(
                        label: 'الحالة',
                        value: _status?.state.arabicLabel ?? 'غير معروف',
                      ),
                      _StatusRow(
                        label: 'آخر حركة',
                        value: _formatLastCheckin(_status),
                      ),
                    ],
                    if (_message != null) ...[
                      const SizedBox(height: 14),
                      Text(
                        _message!,
                        style: TextStyle(
                          color: _isError
                              ? colorScheme.error
                              : colorScheme.primary,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            LayoutBuilder(
              builder: (context, constraints) {
                final buttons = [
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: _isLoading
                          ? null
                          : () => _submit(checkIn: true),
                      icon: const Icon(Icons.login),
                      label: const Text('تسجيل حضور'),
                    ),
                  ),
                  const SizedBox(width: 12, height: 12),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isLoading
                          ? null
                          : () => _submit(checkIn: false),
                      icon: const Icon(Icons.logout),
                      label: const Text('تسجيل انصراف'),
                    ),
                  ),
                ];
                if (constraints.maxWidth < 520) {
                  return Column(children: buttons);
                }
                return Row(children: buttons);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _loadStatus() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final status = await widget.apiClient.getAttendanceStatus();
      setState(() {
        _status = status;
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

  Future<void> _submit({required bool checkIn}) async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final status = checkIn
          ? await widget.apiClient.checkIn()
          : await widget.apiClient.checkOut();
      setState(() {
        _status = status;
        _message = checkIn
            ? 'تم تسجيل الحضور بنجاح.'
            : 'تم تسجيل الانصراف بنجاح.';
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

  String _formatLastCheckin(AttendanceStatus? status) {
    if (status == null || status.lastTime == null) return 'لا يوجد';
    final type = status.lastLogType == 'IN'
        ? 'حضور'
        : status.lastLogType == 'OUT'
        ? 'انصراف'
        : status.lastLogType ?? 'غير معروف';
    return '$type - ${status.lastTime}';
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({required this.label, required this.value});

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
