import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/orders/approval_queue_screen.dart';

void main() {
  testWidgets('approval dashboard card opens approval queue', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'branch.supervisor@example.com',
              fullName: 'Supervisor',
              roles: ['Madar Branch Supervisor'],
              permissions: ['orders.approve'],
              scopes: ScopeContext(
                branchNames: ['Main Branch'],
                departmentNames: [],
              ),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {
              opened = true;
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('اعتماد الطلبات'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('approval queue shows submitted orders and actions', (
    tester,
  ) async {
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        return http.Response.bytes(
          utf8.encode(
            jsonEncode({
              'message': {
                'ok': true,
                'data': {
                  'items': [
                    {
                      'name': 'MADAR-ORD-1',
                      'customer_name': 'عميل',
                      'customer_phone': '050',
                      'order_status': 'submitted',
                      'assigned_branch': 'Main Branch',
                      'subtotal': 12.5,
                      'items_count': 1,
                    },
                  ],
                },
                'error': null,
              },
            }),
          ),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: ApprovalQueueScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('طلبات الاعتماد'), findsOneWidget);
    expect(find.text('عميل'), findsOneWidget);
    expect(find.text('اعتماد'), findsOneWidget);
    expect(find.text('إعادة للتعديل'), findsOneWidget);
    expect(find.text('رفض'), findsOneWidget);
  });
}
