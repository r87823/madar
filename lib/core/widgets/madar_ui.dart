import 'package:flutter/material.dart';

class MadarAppScaffold extends StatelessWidget {
  const MadarAppScaffold({
    required this.title,
    required this.body,
    this.actions,
    this.floatingActionButton,
    super.key,
  });

  final String title;
  final Widget body;
  final List<Widget>? actions;
  final Widget? floatingActionButton;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title), actions: actions),
      floatingActionButton: floatingActionButton,
      body: SafeArea(
        child: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1180),
            child: body,
          ),
        ),
      ),
    );
  }
}

class MadarSectionCard extends StatelessWidget {
  const MadarSectionCard({
    required this.title,
    required this.child,
    this.subtitle,
    this.trailing,
    super.key,
  });

  final String title;
  final String? subtitle;
  final Widget? trailing;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      if (subtitle != null && subtitle!.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          subtitle!,
                          style: TextStyle(
                            color: Theme.of(
                              context,
                            ).colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                ?trailing,
              ],
            ),
            const SizedBox(height: 14),
            child,
          ],
        ),
      ),
    );
  }
}

class MadarInfoCard extends StatelessWidget {
  const MadarInfoCard({
    required this.title,
    required this.rows,
    this.icon,
    super.key,
  });

  final String title;
  final Map<String, String> rows;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    if (rows.isEmpty) return const SizedBox.shrink();
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: colorScheme.surface,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (icon != null) ...[
                  Icon(icon, color: colorScheme.primary),
                  const SizedBox(width: 8),
                ],
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...rows.entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 104,
                      child: Text(
                        entry.key,
                        style: TextStyle(color: colorScheme.onSurfaceVariant),
                      ),
                    ),
                    Expanded(
                      child: Text(
                        entry.value,
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
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

class MadarStatusChip extends StatelessWidget {
  const MadarStatusChip({
    required this.status,
    this.label,
    this.highPriority = false,
    super.key,
  });

  final String status;
  final String? label;
  final bool highPriority;

  @override
  Widget build(BuildContext context) {
    final colors = _statusColors(context, status, highPriority);
    return Material(
      color: Colors.transparent,
      child: Chip(
        label: Text(label ?? madarStatusLabel(status)),
        backgroundColor: colors.$1,
        side: BorderSide(color: colors.$2),
        labelStyle: TextStyle(color: colors.$3, fontWeight: FontWeight.w700),
        visualDensity: VisualDensity.compact,
      ),
    );
  }
}

class MadarActionButton extends StatelessWidget {
  const MadarActionButton({
    required this.label,
    required this.onPressed,
    this.icon,
    this.isDanger = false,
    super.key,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isDanger;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final child = Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (icon != null) ...[Icon(icon), const SizedBox(width: 6)],
        Text(label),
      ],
    );
    if (isDanger) {
      return FilledButton.tonal(
        onPressed: onPressed,
        style: FilledButton.styleFrom(
          foregroundColor: colorScheme.onErrorContainer,
          backgroundColor: colorScheme.errorContainer,
        ),
        child: child,
      );
    }
    return FilledButton(onPressed: onPressed, child: child);
  }
}

class MadarEmptyState extends StatelessWidget {
  const MadarEmptyState({
    this.message = 'لا توجد بيانات للعرض',
    this.icon = Icons.inbox_outlined,
    super.key,
  });

  final String message;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return _StatePanel(icon: icon, message: message);
  }
}

class MadarErrorState extends StatelessWidget {
  const MadarErrorState({
    this.message = 'تعذر تحميل البيانات',
    this.icon = Icons.error_outline,
    super.key,
  });

  final String message;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return _StatePanel(
      icon: icon,
      message: message,
      color: Theme.of(context).colorScheme.error,
    );
  }
}

class MadarLoadingState extends StatelessWidget {
  const MadarLoadingState({this.message = 'جاري التحميل...', super.key});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 12),
            Text(message),
          ],
        ),
      ),
    );
  }
}

class MadarListTile extends StatelessWidget {
  const MadarListTile({
    required this.title,
    this.subtitle,
    this.leading,
    this.trailing,
    this.onTap,
    super.key,
  });

  final String title;
  final String? subtitle;
  final Widget? leading;
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: Theme.of(context).colorScheme.surface,
      child: ListTile(
        leading: leading,
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
        subtitle: subtitle == null ? null : Text(subtitle!),
        trailing: trailing,
        onTap: onTap,
      ),
    );
  }
}

class MadarMetricCard extends StatelessWidget {
  const MadarMetricCard({
    required this.title,
    required this.value,
    this.subtitle,
    this.icon,
    this.highPriority = false,
    this.onTap,
    super.key,
  });

  final String title;
  final String value;
  final String? subtitle;
  final IconData? icon;
  final bool highPriority;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final borderColor = highPriority
        ? colorScheme.error
        : colorScheme.outlineVariant;
    final iconColor = highPriority ? colorScheme.error : colorScheme.primary;
    return Card(
      color: highPriority
          ? colorScheme.errorContainer.withValues(alpha: 0.25)
          : colorScheme.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: borderColor),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  if (icon != null) ...[
                    Icon(icon, color: iconColor),
                    const SizedBox(width: 8),
                  ],
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
              const Spacer(),
              Text(
                value,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                  color: highPriority ? colorScheme.error : colorScheme.primary,
                ),
              ),
              if (subtitle != null && subtitle!.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  subtitle!,
                  style: TextStyle(color: colorScheme.onSurfaceVariant),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

Future<bool?> showMadarConfirmDialog({
  required BuildContext context,
  required String title,
  required String message,
  String confirmLabel = 'تأكيد',
  String cancelLabel = 'إلغاء',
  bool isDanger = false,
}) {
  return showDialog<bool>(
    context: context,
    builder: (context) {
      return AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(cancelLabel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: isDanger
                ? FilledButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.error,
                    foregroundColor: Theme.of(context).colorScheme.onError,
                  )
                : null,
            child: Text(confirmLabel),
          ),
        ],
      );
    },
  );
}

String madarStatusLabel(String status) {
  switch (status) {
    case 'draft':
      return 'مسودة';
    case 'submitted':
      return 'مرسل للاعتماد';
    case 'approved':
      return 'معتمد';
    case 'returned_for_edit':
      return 'معاد للتعديل';
    case 'rejected':
      return 'مرفوض';
    case 'cancelled':
      return 'ملغي';
    case 'not_started':
      return 'لم يبدأ';
    case 'pending':
      return 'بانتظار';
    case 'in_progress':
    case 'in_production':
    case 'accepted':
      return 'قيد التنفيذ';
    case 'delayed':
      return 'متأخر';
    case 'partially_ready':
      return 'جاهز جزئيًا';
    case 'ready':
      return 'جاهز';
    case 'blocked':
      return 'متوقف';
    case 'not_ready':
      return 'غير جاهز';
    case 'ready_for_dispatch':
      return 'جاهز للإرسال';
    case 'dispatched_to_branch':
      return 'خرج إلى الفرع';
    case 'received_at_branch':
      return 'تم الاستلام في الفرع';
    case 'ready_for_customer_pickup':
      return 'جاهز لاستلام العميل';
    case 'customer_picked_up':
      return 'تم تسليم العميل';
    case 'dispatched_to_customer':
      return 'خرج للتوصيل';
    case 'delivered_to_customer':
      return 'تم التسليم للعميل';
    case 'failed_delivery':
      return 'تعذر التسليم';
    case 'unpaid':
      return 'غير مدفوع';
    case 'partially_paid':
      return 'مدفوع جزئيًا';
    case 'paid':
      return 'مدفوع';
    case 'not_ready_accounting':
      return 'غير جاهز';
    case 'ready_for_review':
      return 'جاهز للمراجعة';
    case 'needs_attention':
      return 'يحتاج انتباه';
    case 'reviewed':
      return 'تمت المراجعة';
    case 'closed_later':
      return 'إغلاق لاحق';
    case 'open':
      return 'مفتوح';
    case 'completed':
      return 'مكتمل';
    case 'failed':
      return 'فشل';
    case 'synced':
      return 'تمت المزامنة';
    default:
      return status.isEmpty ? 'غير معروف' : status;
  }
}

(Color, Color, Color) _statusColors(
  BuildContext context,
  String status,
  bool highPriority,
) {
  final colorScheme = Theme.of(context).colorScheme;
  if (highPriority ||
      {
        'failed',
        'rejected',
        'cancelled',
        'delayed',
        'failed_delivery',
        'needs_attention',
        'blocked',
      }.contains(status)) {
    return (
      colorScheme.errorContainer,
      colorScheme.error,
      colorScheme.onErrorContainer,
    );
  }
  if ({
    'approved',
    'ready',
    'paid',
    'synced',
    'reviewed',
    'completed',
  }.contains(status)) {
    return (
      colorScheme.primaryContainer,
      colorScheme.primary,
      colorScheme.onPrimaryContainer,
    );
  }
  return (
    colorScheme.surfaceContainerHighest,
    colorScheme.outline,
    colorScheme.onSurfaceVariant,
  );
}

class _StatePanel extends StatelessWidget {
  const _StatePanel({required this.icon, required this.message, this.color});

  final IconData icon;
  final String message;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final resolvedColor =
        color ?? Theme.of(context).colorScheme.onSurfaceVariant;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: resolvedColor),
            const SizedBox(height: 10),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
