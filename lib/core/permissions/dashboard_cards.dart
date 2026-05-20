import 'package:flutter/material.dart';

class DashboardCardDefinition {
  const DashboardCardDefinition({
    required this.title,
    required this.icon,
    required this.requiredAny,
  });

  final String title;
  final IconData icon;
  final Set<String> requiredAny;

  bool isVisibleFor(Set<String> permissions) {
    return requiredAny.any(permissions.contains);
  }
}

class DashboardCards {
  static const all = [
    DashboardCardDefinition(
      title: 'لوحة المتابعة',
      icon: Icons.dashboard_customize_outlined,
      requiredAny: {
        'system.full_access',
        'attendance.check_in',
        'attendance.check_out',
        'employee_services.view_self',
        'orders.create',
        'orders.approve',
        'production.view_work_orders',
        'delivery.view_assigned_batches',
        'delivery.update_batch',
        'payments.collect',
        'cashbox.view_own',
        'cashbox.review',
        'accounting.view_sync_logs',
      },
    ),
    DashboardCardDefinition(
      title: 'الحضور والانصراف',
      icon: Icons.schedule,
      requiredAny: {'attendance.check_in', 'attendance.check_out'},
    ),
    DashboardCardDefinition(
      title: 'خدمات الموظف',
      icon: Icons.badge_outlined,
      requiredAny: {'employee_services.view_self'},
    ),
    DashboardCardDefinition(
      title: 'إنشاء طلب',
      icon: Icons.add_business_outlined,
      requiredAny: {'orders.create'},
    ),
    DashboardCardDefinition(
      title: 'اعتماد الطلبات',
      icon: Icons.verified_outlined,
      requiredAny: {'orders.approve'},
    ),
    DashboardCardDefinition(
      title: 'أوامر الإنتاج',
      icon: Icons.precision_manufacturing_outlined,
      requiredAny: {'production.view_work_orders'},
    ),
    DashboardCardDefinition(
      title: 'إعدادات الإنتاج',
      icon: Icons.factory_outlined,
      requiredAny: {'system.full_access', 'production.manage_mappings'},
    ),
    DashboardCardDefinition(
      title: 'مهام التوصيل',
      icon: Icons.local_shipping_outlined,
      requiredAny: {'delivery.view_assigned_batches', 'delivery.update_batch'},
    ),
    DashboardCardDefinition(
      title: 'دفعاتي',
      icon: Icons.inventory_2_outlined,
      requiredAny: {'delivery.view_assigned_batches'},
    ),
    DashboardCardDefinition(
      title: 'تحصيل المدفوعات',
      icon: Icons.payments_outlined,
      requiredAny: {'payments.collect'},
    ),
    DashboardCardDefinition(
      title: 'الصندوق',
      icon: Icons.account_balance_wallet_outlined,
      requiredAny: {'cashbox.view_own', 'cashbox.submit'},
    ),
    DashboardCardDefinition(
      title: 'المحاسبة والمزامنة',
      icon: Icons.sync_alt_outlined,
      requiredAny: {'accounting.view_sync_logs'},
    ),
    DashboardCardDefinition(
      title: 'الإدارة',
      icon: Icons.admin_panel_settings_outlined,
      requiredAny: {'system.full_access'},
    ),
  ];

  static List<DashboardCardDefinition> visibleFor(Set<String> permissions) {
    return all.where((card) => card.isVisibleFor(permissions)).toList();
  }
}
