import 'package:flutter/material.dart';

import '../../core/auth/user_context.dart';
import '../../core/permissions/dashboard_cards.dart';
import '../../core/widgets/info_section.dart';

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
  final int unreadNotifications;
  final VoidCallback? onOpenNotifications;
  final VoidCallback? onOpenDispatchQueue;
  final VoidCallback? onOpenMyDeliveryBatches;
  final VoidCallback? onOpenCashbox;

  @override
  Widget build(BuildContext buildContext) {
    final cards = DashboardCards.visibleFor(context.permissions.toSet());
    final colorScheme = Theme.of(buildContext).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('لوحة مدار'),
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
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            color: colorScheme.primaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    context.fullName.isEmpty ? context.user : context.fullName,
                    style: Theme.of(buildContext).textTheme.headlineSmall
                        ?.copyWith(fontWeight: FontWeight.w800),
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
          ),
          const SizedBox(height: 16),
          _ContextGrid(userContext: context),
          const SizedBox(height: 20),
          Text(
            'المهام المتاحة',
            style: Theme.of(
              buildContext,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 12),
          LayoutBuilder(
            builder: (context, constraints) {
              final width = constraints.maxWidth;
              final crossAxisCount = width >= 980
                  ? 4
                  : width >= 680
                  ? 3
                  : 2;
              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: cards.length,
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: crossAxisCount,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  childAspectRatio: width < 520 ? 1.05 : 1.45,
                ),
                itemBuilder: (context, index) {
                  return _DashboardCard(
                    card: cards[index],
                    onOpenAttendance: onOpenAttendance,
                    onOpenOrders: onOpenOrders,
                    onOpenApprovalQueue: onOpenApprovalQueue,
                    onOpenErpSyncReview: onOpenErpSyncReview,
                    onOpenProductionMappings: onOpenProductionMappings,
                    onOpenWorkOrders: onOpenWorkOrders,
                    onOpenFollowupDashboard: onOpenFollowupDashboard,
                    onOpenDispatchQueue: onOpenDispatchQueue,
                    onOpenMyDeliveryBatches: onOpenMyDeliveryBatches,
                    onOpenCashbox: onOpenCashbox,
                  );
                },
              );
            },
          ),
        ],
      ),
    );
  }
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
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(card.icon, color: colorScheme.primary, size: 30),
              const Spacer(),
              Text(
                card.title,
                style: Theme.of(
                  context,
                ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              Text(
                'قريبًا',
                style: TextStyle(color: colorScheme.onSurfaceVariant),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
