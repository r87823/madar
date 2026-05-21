import 'package:flutter/material.dart';

class DashboardCardDefinition {
  const DashboardCardDefinition({
    required this.title,
    required this.icon,
    required this.requiredAny,
    required this.group,
    required this.subtitle,
  });

  final String title;
  final IconData icon;
  final Set<String> requiredAny;
  final String group;
  final String subtitle;

  bool isVisibleFor(Set<String> permissions) {
    return requiredAny.any(permissions.contains);
  }
}

class DashboardCards {
  static const all = [
    DashboardCardDefinition(
      title: 'لوحة المتابعة',
      icon: Icons.dashboard_customize_outlined,
      group: 'الإدارة',
      subtitle: 'ملخصات وتنبيهات حسب صلاحياتك',
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
      title: 'الإعدادات',
      icon: Icons.settings_outlined,
      group: 'الإدارة',
      subtitle: 'إعدادات تشغيلية غير سرية',
      requiredAny: {'system.full_access', 'settings.manage'},
    ),
    DashboardCardDefinition(
      title: 'الحضور والانصراف',
      icon: Icons.schedule,
      group: 'الموظف',
      subtitle: 'تسجيل ومتابعة حضورك',
      requiredAny: {'attendance.check_in', 'attendance.check_out'},
    ),
    DashboardCardDefinition(
      title: 'خدمات الموظف',
      icon: Icons.badge_outlined,
      group: 'الموظف',
      subtitle: 'بيانات وخدمات الموظف',
      requiredAny: {'employee_services.view_self'},
    ),
    DashboardCardDefinition(
      title: 'إنشاء طلب',
      icon: Icons.add_business_outlined,
      group: 'التشغيل',
      subtitle: 'إنشاء ومتابعة طلبات الفرع',
      requiredAny: {'orders.create'},
    ),
    DashboardCardDefinition(
      title: 'اعتماد الطلبات',
      icon: Icons.verified_outlined,
      group: 'التشغيل',
      subtitle: 'مراجعة الطلبات المرسلة',
      requiredAny: {'orders.approve'},
    ),
    DashboardCardDefinition(
      title: 'أوامر الإنتاج',
      icon: Icons.precision_manufacturing_outlined,
      group: 'التشغيل',
      subtitle: 'مهام الإنتاج حسب القسم',
      requiredAny: {'production.view_work_orders'},
    ),
    DashboardCardDefinition(
      title: 'إعدادات الإنتاج',
      icon: Icons.factory_outlined,
      group: 'الإدارة',
      subtitle: 'ربط الأصناف بمراكز الإنتاج',
      requiredAny: {'system.full_access', 'production.manage_mappings'},
    ),
    DashboardCardDefinition(
      title: 'مهام التوصيل',
      icon: Icons.local_shipping_outlined,
      group: 'التوصيل',
      subtitle: 'قائمة الإرسال والتسليم',
      requiredAny: {'delivery.view_assigned_batches', 'delivery.update_batch'},
    ),
    DashboardCardDefinition(
      title: 'دفعاتي',
      icon: Icons.inventory_2_outlined,
      group: 'التوصيل',
      subtitle: 'الدفعات المسندة لك',
      requiredAny: {'delivery.view_assigned_batches'},
    ),
    DashboardCardDefinition(
      title: 'تحصيل المدفوعات',
      icon: Icons.payments_outlined,
      group: 'المالية',
      subtitle: 'تحصيل من تفاصيل الطلب',
      requiredAny: {'payments.collect'},
    ),
    DashboardCardDefinition(
      title: 'الصندوق',
      icon: Icons.account_balance_wallet_outlined,
      group: 'المالية',
      subtitle: 'صندوقك اليومي والمراجعة',
      requiredAny: {'cashbox.view_own', 'cashbox.submit'},
    ),
    DashboardCardDefinition(
      title: 'التقارير',
      icon: Icons.table_chart_outlined,
      group: 'الإدارة',
      subtitle: 'تقارير تشغيلية للقراءة فقط',
      requiredAny: {
        'system.full_access',
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
      title: 'المحاسبة والمزامنة',
      icon: Icons.sync_alt_outlined,
      group: 'المالية',
      subtitle: 'مراجعة ERP والإقفال',
      requiredAny: {'accounting.view_sync_logs'},
    ),
    DashboardCardDefinition(
      title: 'الإدارة',
      icon: Icons.admin_panel_settings_outlined,
      group: 'الإدارة',
      subtitle: 'صلاحيات الإدارة العامة',
      requiredAny: {'system.full_access'},
    ),
  ];

  static List<DashboardCardDefinition> visibleFor(Set<String> permissions) {
    if (permissions.contains('system.full_access')) return List.of(all);
    return all.where((card) => card.isVisibleFor(permissions)).toList();
  }
}
