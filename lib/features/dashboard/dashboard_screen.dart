import 'package:flutter/material.dart';

import '../../core/auth/user_context.dart';
import '../../core/permissions/dashboard_cards.dart';
import '../../core/widgets/info_section.dart';
import '../../core/widgets/madar_ui.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({
    required this.context,
    required this.onLogout,
    required this.onOpenAttendance,
    required this.onOpenOrders,
    required this.onOpenApprovalQueue,
    required this.onOpenErpSyncReview,
    required this.onOpenProductionMappings,
    required this.onOpenWorkOrders,
    this.onOpenFollowupDashboard,
    this.onOpenReports,
    this.onOpenSettings,
    this.unreadNotifications = 0,
    this.onOpenNotifications,
    this.onOpenDispatchQueue,
    this.onOpenMyDeliveryBatches,
    this.onOpenCashbox,
    super.key,
  });

  final UserContext context;
  final Future<void> Function() onLogout;
  final VoidCallback onOpenAttendance;
  final VoidCallback onOpenOrders;
  final VoidCallback onOpenApprovalQueue;
  final VoidCallback onOpenErpSyncReview;
  final VoidCallback onOpenProductionMappings;
  final VoidCallback onOpenWorkOrders;
  final VoidCallback? onOpenFollowupDashboard;
  final VoidCallback? onOpenReports;
  final VoidCallback? onOpenSettings;
  final int unreadNotifications;
  final VoidCallback? onOpenNotifications;
  final VoidCallback? onOpenDispatchQueue;
  final VoidCallback? onOpenMyDeliveryBatches;
  final VoidCallback? onOpenCashbox;

  @override
  Widget build(BuildContext buildContext) {
    final cards = DashboardCards.visibleFor(context.permissions.toSet());
    final colorScheme = Theme.of(buildContext).colorScheme;
    final groups = _groupCards(cards);

    return MadarAppScaffold(
      title: 'لوحة مدار',
      actions: [
        _NotificationIcon(
          unreadCount: unreadNotifications,
          onPressed: onOpenNotifications,
        ),
        IconButton(
          tooltip: 'تسجيل الخروج',
          onPressed: onLogout,
          icon: const Icon(Icons.logout),
        ),
      ],
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Card(
              color: colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 25,
                      backgroundColor: colorScheme.primary,
                      foregroundColor: colorScheme.onPrimary,
                      child: Text(_initials(context.fullName, context.user)),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            context.fullName.isEmpty
                                ? context.user
                                : context.fullName,
                            style: Theme.of(buildContext)
                                .textTheme
                                .headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w900),
                          ),
                          const SizedBox(height: 6),
                          Text(context.user),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: context.roles
                                .map((role) => Chip(label: Text(role)))
                                .toList(growable: false),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            _ContextGrid(userContext: context),
            const SizedBox(height: 20),
            ...groups.entries.map(
              (entry) => Padding(
                padding: const EdgeInsets.only(bottom: 18),
                child: _DashboardGroup(
                  title: entry.key,
                  cards: entry.value,
                  onOpenAttendance: onOpenAttendance,
                  onOpenOrders: onOpenOrders,
                  onOpenApprovalQueue: onOpenApprovalQueue,
                  onOpenErpSyncReview: onOpenErpSyncReview,
                  onOpenProductionMappings: onOpenProductionMappings,
                  onOpenWorkOrders: onOpenWorkOrders,
                  onOpenFollowupDashboard: onOpenFollowupDashboard,
                  onOpenReports: onOpenReports,
                  onOpenSettings: onOpenSettings,
                  onOpenDispatchQueue: onOpenDispatchQueue,
                  onOpenMyDeliveryBatches: onOpenMyDeliveryBatches,
                  onOpenCashbox: onOpenCashbox,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DashboardGroup extends StatelessWidget {
  const _DashboardGroup({
    required this.title,
    required this.cards,
    required this.onOpenAttendance,
    required this.onOpenOrders,
    required this.onOpenApprovalQueue,
    required this.onOpenErpSyncReview,
    required this.onOpenProductionMappings,
    required this.onOpenWorkOrders,
    this.onOpenFollowupDashboard,
    this.onOpenReports,
    this.onOpenSettings,
    this.onOpenDispatchQueue,
    this.onOpenMyDeliveryBatches,
    this.onOpenCashbox,
  });

  final String title;
  final List<DashboardCardDefinition> cards;
  final VoidCallback onOpenAttendance;
  final VoidCallback onOpenOrders;
  final VoidCallback onOpenApprovalQueue;
  final VoidCallback onOpenErpSyncReview;
  final VoidCallback onOpenProductionMappings;
  final VoidCallback onOpenWorkOrders;
  final VoidCallback? onOpenFollowupDashboard;
  final VoidCallback? onOpenReports;
  final VoidCallback? onOpenSettings;
  final VoidCallback? onOpenDispatchQueue;
  final VoidCallback? onOpenMyDeliveryBatches;
  final VoidCallback? onOpenCashbox;

  @override
  Widget build(BuildContext context) {
    return MadarSectionCard(
      title: title,
      subtitle: _groupSubtitle(title),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final width = constraints.maxWidth;
          final crossAxisCount = width >= 980
              ? 4
              : width >= 680
              ? 3
              : 1;
          final cardWidth =
              (width - (12 * (crossAxisCount - 1))) / crossAxisCount;
          return Wrap(
            spacing: 12,
            runSpacing: 12,
            children: cards
                .map(
                  (card) => SizedBox(
                    width: cardWidth,
                    child: _DashboardCard(
                      card: card,
                      onOpenAttendance: onOpenAttendance,
                      onOpenOrders: onOpenOrders,
                      onOpenApprovalQueue: onOpenApprovalQueue,
                      onOpenErpSyncReview: onOpenErpSyncReview,
                      onOpenProductionMappings: onOpenProductionMappings,
                      onOpenWorkOrders: onOpenWorkOrders,
                      onOpenFollowupDashboard: onOpenFollowupDashboard,
                      onOpenReports: onOpenReports,
                      onOpenSettings: onOpenSettings,
                      onOpenDispatchQueue: onOpenDispatchQueue,
                      onOpenMyDeliveryBatches: onOpenMyDeliveryBatches,
                      onOpenCashbox: onOpenCashbox,
                    ),
                  ),
                )
                .toList(growable: false),
          );
        },
      ),
    );
  }
}

String _groupSubtitle(String title) {
  switch (title) {
    case 'الموظف':
      return 'حضورك وخدماتك اليومية';
    case 'التشغيل':
      return 'الطلبات والإنتاج والاعتمادات';
    case 'التوصيل':
      return 'الإرسال والدفعات المسندة';
    case 'المالية':
      return 'المدفوعات والصندوق والمزامنة';
    case 'الإدارة':
      return 'المتابعة والتقارير والإعدادات';
    default:
      return '';
  }
}

Map<String, List<DashboardCardDefinition>> _groupCards(
  List<DashboardCardDefinition> cards,
) {
  const order = ['الموظف', 'التشغيل', 'التوصيل', 'المالية', 'الإدارة'];
  final grouped = <String, List<DashboardCardDefinition>>{};
  for (final group in order) {
    final groupCards = cards.where((card) => card.group == group).toList();
    if (groupCards.isNotEmpty) grouped[group] = groupCards;
  }
  for (final card in cards) {
    if (!order.contains(card.group)) {
      grouped.putIfAbsent(card.group, () => []).add(card);
    }
  }
  return grouped;
}

String _initials(String fullName, String fallback) {
  final source = fullName.trim().isEmpty ? fallback.trim() : fullName.trim();
  if (source.isEmpty) return 'م';
  return source.characters.take(1).toString().toUpperCase();
}

class _NotificationIcon extends StatelessWidget {
  const _NotificationIcon({required this.unreadCount, required this.onPressed});

  final int unreadCount;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        IconButton(
          tooltip: 'الإشعارات',
          onPressed: onPressed,
          icon: const Icon(Icons.notifications_outlined),
        ),
        if (unreadCount > 0)
          PositionedDirectional(
            top: 6,
            end: 6,
            child: Container(
              constraints: const BoxConstraints(minWidth: 18, minHeight: 18),
              padding: const EdgeInsets.symmetric(horizontal: 5),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.error,
                borderRadius: BorderRadius.circular(9),
              ),
              alignment: Alignment.center,
              child: Text(
                unreadCount > 99 ? '99+' : '$unreadCount',
                style: Theme.of(context).textTheme.labelSmall?.copyWith(
                  color: Theme.of(context).colorScheme.onError,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _ContextGrid extends StatelessWidget {
  const _ContextGrid({required this.userContext});

  final UserContext userContext;

  @override
  Widget build(BuildContext buildContext) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 780) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: InfoSection(
                  title: 'بيانات الموظف',
                  rows: userContext.employee?.toDisplayRows() ?? const {},
                ),
              ),
              const SizedBox(width: 12),
              Expanded(child: _ScopeSection(userContext: userContext)),
            ],
          );
        }
        return Column(
          children: [
            InfoSection(
              title: 'بيانات الموظف',
              rows: userContext.employee?.toDisplayRows() ?? const {},
            ),
            const SizedBox(height: 12),
            _ScopeSection(userContext: userContext),
          ],
        );
      },
    );
  }
}

class _ScopeSection extends StatelessWidget {
  const _ScopeSection({required this.userContext});

  final UserContext userContext;

  @override
  Widget build(BuildContext buildContext) {
    return InfoSection(
      title: 'النطاق',
      rows: {
        if (userContext.branch != null) 'الفرع': userContext.branch!.name,
        'الفروع': _joinScope(userContext.scopes.branchNames),
        'الأقسام': _joinScope(userContext.scopes.departmentNames),
      },
    );
  }

  static String _joinScope(List<String> values) {
    if (values.isEmpty) return 'لا يوجد';
    if (values.contains('*')) return 'كل النطاقات';
    return values.join('، ');
  }
}

class _DashboardCard extends StatelessWidget {
  const _DashboardCard({
    required this.card,
    required this.onOpenAttendance,
    required this.onOpenOrders,
    required this.onOpenApprovalQueue,
    required this.onOpenErpSyncReview,
    required this.onOpenProductionMappings,
    required this.onOpenWorkOrders,
    this.onOpenFollowupDashboard,
    this.onOpenReports,
    this.onOpenSettings,
    this.onOpenDispatchQueue,
    this.onOpenMyDeliveryBatches,
    this.onOpenCashbox,
  });

  final DashboardCardDefinition card;
  final VoidCallback onOpenAttendance;
  final VoidCallback onOpenOrders;
  final VoidCallback onOpenApprovalQueue;
  final VoidCallback onOpenErpSyncReview;
  final VoidCallback onOpenProductionMappings;
  final VoidCallback onOpenWorkOrders;
  final VoidCallback? onOpenFollowupDashboard;
  final VoidCallback? onOpenReports;
  final VoidCallback? onOpenSettings;
  final VoidCallback? onOpenDispatchQueue;
  final VoidCallback? onOpenMyDeliveryBatches;
  final VoidCallback? onOpenCashbox;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Card(
      color: Colors.white,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () {
          if (card.title == 'لوحة المتابعة' &&
              onOpenFollowupDashboard != null) {
            onOpenFollowupDashboard!();
            return;
          }
          if (card.title == 'التقارير' && onOpenReports != null) {
            onOpenReports!();
            return;
          }
          if (card.title == 'الإعدادات' && onOpenSettings != null) {
            onOpenSettings!();
            return;
          }
          if (card.title == 'الحضور والانصراف') {
            onOpenAttendance();
            return;
          }
          if (card.title == 'إنشاء طلب') {
            onOpenOrders();
            return;
          }
          if (card.title == 'اعتماد الطلبات') {
            onOpenApprovalQueue();
            return;
          }
          if (card.title == 'أوامر الإنتاج') {
            onOpenWorkOrders();
            return;
          }
          if (card.title == 'المحاسبة والمزامنة') {
            onOpenErpSyncReview();
            return;
          }
          if (card.title == 'إعدادات الإنتاج') {
            onOpenProductionMappings();
            return;
          }
          if (card.title == 'مهام التوصيل' && onOpenDispatchQueue != null) {
            onOpenDispatchQueue!();
            return;
          }
          if (card.title == 'دفعاتي' && onOpenMyDeliveryBatches != null) {
            onOpenMyDeliveryBatches!();
            return;
          }
          if (card.title == 'الصندوق' && onOpenCashbox != null) {
            onOpenCashbox!();
            return;
          }
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text('${card.title}: قريبًا')));
        },
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 132),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(card.icon, color: colorScheme.primary, size: 30),
                const SizedBox(height: 12),
                Text(
                  card.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  card.subtitle,
                  style: TextStyle(color: colorScheme.onSurfaceVariant),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
