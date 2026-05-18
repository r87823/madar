import 'package:flutter_test/flutter_test.dart';
import 'package:madar/core/permissions/dashboard_cards.dart';

void main() {
  test('driver permissions show delivery payment and cashbox cards', () {
    final cards = DashboardCards.visibleFor({
      'attendance.check_in',
      'attendance.check_out',
      'employee_services.view_self',
      'delivery.view_assigned_batches',
      'delivery.update_batch',
      'payments.collect',
      'cashbox.view_own',
      'cashbox.submit',
    });

    expect(
      cards.map((card) => card.title),
      containsAll([
        'الحضور والانصراف',
        'خدمات الموظف',
        'مهام التوصيل',
        'تحصيل المدفوعات',
        'الصندوق',
      ]),
    );
    expect(
      cards.map((card) => card.title),
      isNot(contains('المحاسبة والمزامنة')),
    );
  });

  test(
    'accountant permissions show accounting card only with employee services',
    () {
      final cards = DashboardCards.visibleFor({
        'attendance.check_in',
        'attendance.check_out',
        'employee_services.view_self',
        'employee_services.request_leave',
        'accounting.view_sync_logs',
      });

      expect(
        cards.map((card) => card.title),
        containsAll(['الحضور والانصراف', 'خدمات الموظف', 'المحاسبة والمزامنة']),
      );
      expect(cards.map((card) => card.title), isNot(contains('مهام التوصيل')));
    },
  );

  test('branch supervisor permissions show approval card', () {
    final cards = DashboardCards.visibleFor({
      'attendance.check_in',
      'attendance.check_out',
      'employee_services.view_self',
      'orders.approve',
    });

    expect(cards.map((card) => card.title), contains('اعتماد الطلبات'));
    expect(cards.map((card) => card.title), isNot(contains('إنشاء طلب')));
  });
}
