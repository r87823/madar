import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';

void main() {
  testWidgets('attendance dashboard card opens attendance screen', (
    tester,
  ) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'employee.test@example.com',
              fullName: 'Madar Employee',
              roles: ['Madar Employee'],
              permissions: ['attendance.check_in', 'attendance.check_out'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
            onLogout: () async {},
            onOpenAttendance: () {
              opened = true;
            },
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
          ),
        ),
      ),
    );

    await tester.tap(find.text('الحضور والانصراف'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('cashbox dashboard card opens my cashbox screen', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'cashier.test@example.com',
              fullName: 'Cashier',
              roles: ['Madar Cashier'],
              permissions: ['cashbox.view_own', 'cashbox.submit'],
              scopes: ScopeContext(
                branchNames: ['Main Branch'],
                departmentNames: ['Finance'],
              ),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
            onOpenCashbox: () {
              opened = true;
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('الصندوق'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('dashboard groups visible cards by operational area', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1000, 3000));
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'admin@example.com',
              fullName: 'Admin',
              roles: ['Madar Admin'],
              permissions: ['system.full_access'],
              scopes: ScopeContext(branchNames: ['*'], departmentNames: ['*']),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
          ),
        ),
      ),
    );

    expect(find.text('الموظف'), findsOneWidget);
    expect(find.text('التشغيل'), findsOneWidget);
    expect(find.text('التوصيل'), findsOneWidget);
    expect(find.text('المالية'), findsOneWidget);
    expect(find.text('الإدارة'), findsWidgets);
    expect(find.text('لوحة المتابعة'), findsOneWidget);
    await tester.binding.setSurfaceSize(null);
  });
}
