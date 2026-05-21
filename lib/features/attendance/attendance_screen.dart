import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import '../../core/errors/madar_error_messages.dart';
import '../../core/messages/madar_success_messages.dart';
import 'attendance_status.dart';

class AttendanceScreen extends StatefulWidget {
  const AttendanceScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends State<AttendanceScreen> {
  AttendanceStatus? _status;
  AttendanceHistory _history = const AttendanceHistory(items: []);
  bool _isLoading = true;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadAttendance();
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('الحضور والانصراف')),
      body: RefreshIndicator(
        onRefresh: _loadAttendance,
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
            _ActionButton(
              status: _status,
              isLoading: _isLoading,
              onCheckIn: () => _submit(checkIn: true),
              onCheckOut: () => _submit(checkIn: false),
            ),
            const SizedBox(height: 16),
            _HistorySection(history: _history),
          ],
        ),
      ),
    );
  }

  Future<void> _loadAttendance() async {
    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });
    try {
      final status = await widget.apiClient.getAttendanceStatus();
      final history = await widget.apiClient.getAttendanceHistory();
      setState(() {
        _status = status;
        _history = history;
      });
    } catch (error) {
      setState(() {
        _message = arabicMessageForError(error);
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
      final history = await widget.apiClient.getAttendanceHistory();
      setState(() {
        _status = status;
        _history = history;
        _message = checkIn
            ? MadarSuccessMessages.attendanceCheckIn
            : MadarSuccessMessages.attendanceCheckOut;
      });
    } catch (error) {
      setState(() {
        _message = arabicMessageForError(error);
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

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.status,
    required this.isLoading,
    required this.onCheckIn,
    required this.onCheckOut,
  });

  final AttendanceStatus? status;
  final bool isLoading;
  final VoidCallback onCheckIn;
  final VoidCallback onCheckOut;

  @override
  Widget build(BuildContext context) {
    final currentState = status?.state ?? AttendanceState.unknown;
    if (currentState == AttendanceState.inWork) {
      return FilledButton.icon(
        onPressed: isLoading ? null : onCheckOut,
        icon: const Icon(Icons.logout),
        label: const Text('تسجيل انصراف'),
      );
    }

    return FilledButton.icon(
      onPressed: isLoading ? null : onCheckIn,
      icon: const Icon(Icons.login),
      label: const Text('تسجيل حضور'),
    );
  }
}

class _HistorySection extends StatelessWidget {
  const _HistorySection({required this.history});

  final AttendanceHistory history;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'آخر تسجيلاتك',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 12),
            if (history.items.isEmpty)
              Text(
                'لا توجد تسجيلات بعد.',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
              )
            else
              ...history.items.map(
                (item) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(
                    item.logType == 'IN' ? Icons.login : Icons.logout,
                  ),
                  title: Text(item.arabicLogType),
                  subtitle: Text(item.time),
                  trailing: Text(item.state.arabicLabel),
                ),
              ),
          ],
        ),
      ),
    );
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
