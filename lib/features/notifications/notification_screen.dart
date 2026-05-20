import 'package:flutter/material.dart';

import '../../core/api/frappe_api_client.dart';
import 'notification_models.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({required this.apiClient, super.key});

  final FrappeApiClient apiClient;

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  late Future<NotificationList> _future;
  String? _error;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.listNotifications();
  }

  void _reload() {
    setState(() {
      _error = null;
      _future = widget.apiClient.listNotifications();
    });
  }

  Future<void> _markRead(MadarNotification notification) async {
    try {
      await widget.apiClient.markNotificationRead(notification.name);
      _reload();
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  Future<void> _markAllRead() async {
    try {
      await widget.apiClient.markAllNotificationsRead();
      _reload();
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('الإشعارات'),
        actions: [
          TextButton.icon(
            onPressed: _markAllRead,
            icon: const Icon(Icons.done_all),
            label: const Text('تحديد الكل كمقروء'),
          ),
        ],
      ),
      body: FutureBuilder<NotificationList>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || _error != null) {
            return _MessageState(
              text: _error ?? 'تعذر تحميل الإشعارات',
              action: _reload,
            );
          }
          final items = snapshot.data?.items ?? const <MadarNotification>[];
          if (items.isEmpty) {
            return const _MessageState(text: 'لا توجد إشعارات');
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: items.length,
            separatorBuilder: (context, index) => const SizedBox(height: 10),
            itemBuilder: (context, index) {
              return _NotificationCard(
                notification: items[index],
                onTap: () => _markRead(items[index]),
              );
            },
          );
        },
      ),
    );
  }
}

class _NotificationCard extends StatelessWidget {
  const _NotificationCard({required this.notification, required this.onTap});

  final MadarNotification notification;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: notification.isRead ? Colors.white : colorScheme.primaryContainer,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      notification.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  if (!notification.isRead)
                    const Chip(
                      label: Text('غير مقروء'),
                      visualDensity: VisualDensity.compact,
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(notification.message),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (notification.createdAt.isNotEmpty)
                    Chip(label: Text(notification.createdAt)),
                  Chip(label: Text(_priorityLabel(notification.priority))),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _priorityLabel(String priority) {
    switch (priority) {
      case 'high':
        return 'عالية';
      case 'low':
        return 'منخفضة';
      default:
        return 'عادية';
    }
  }
}

class _MessageState extends StatelessWidget {
  const _MessageState({required this.text, this.action});

  final String text;
  final VoidCallback? action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(text, textAlign: TextAlign.center),
            if (action != null) ...[
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: action,
                icon: const Icon(Icons.refresh),
                label: const Text('إعادة المحاولة'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
