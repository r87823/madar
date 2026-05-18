import 'package:flutter_test/flutter_test.dart';
import 'package:madar/core/auth/user_context.dart';

void main() {
  test('parses safe current user context from Frappe message wrapper', () {
    final context = UserContext.fromFrappeMessage({
      'message': {
        'user': 'driver.test@example.com',
        'full_name': 'Madar Driver',
        'roles': ['Madar Employee', 'Madar Driver'],
        'permissions': ['delivery.view_assigned_batches', 'payments.collect'],
        'employee': {
          'name': 'HR-EMP-0001',
          'employee_name': 'Madar Dev Driver',
          'department': 'Delivery - T',
          'branch': 'Main Branch',
        },
        'branch': {'name': 'Main Branch', 'branch': 'Main Branch'},
        'scopes': {
          'branch_names': ['Main Branch'],
          'department_names': ['Delivery - T'],
        },
      },
    });

    expect(context.user, 'driver.test@example.com');
    expect(context.fullName, 'Madar Driver');
    expect(context.roles, contains('Madar Driver'));
    expect(context.permissions, contains('payments.collect'));
    expect(context.employee?.branch, 'Main Branch');
    expect(context.branch?.name, 'Main Branch');
    expect(context.scopes.branchNames, ['Main Branch']);
  });

  test(
    'does not expose unknown sensitive fields in employee context model',
    () {
      final context = UserContext.fromFrappeMessage({
        'message': {
          'user': 'employee.test@example.com',
          'full_name': 'Employee',
          'roles': ['Madar Employee'],
          'permissions': ['employee_services.view_self'],
          'employee': {
            'name': 'HR-EMP-0002',
            'employee_name': 'Employee',
            'bank_ac_no': 'hidden',
            'salary': 999,
          },
          'branch': null,
          'scopes': {'branch_names': [], 'department_names': []},
        },
      });

      expect(context.employee?.name, 'HR-EMP-0002');
      expect(context.employee?.toDisplayRows().keys, isNot(contains('salary')));
      expect(
        context.employee?.toDisplayRows().keys,
        isNot(contains('bank_ac_no')),
      );
    },
  );
}
