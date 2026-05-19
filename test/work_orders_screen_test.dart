import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/production/work_order_list_screen.dart';

void main() {
  testWidgets('production work orders dashboard card opens work order list', (
    tester,
  ) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'production.user@example.com',
              fullName: 'Production User',
              roles: ['Madar Production User'],
              permissions: ['production.view_work_orders'],
              scopes: ScopeContext(branchNames: [], departmentNames: ['DAIRY']),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {
              opened = true;
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('أوامر الإنتاج'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets(
    'work order screen lists orders opens detail and sends lifecycle actions',
    (tester) async {
      final requests = <http.Request>[];
      final client = FrappeApiClient(
        baseUri: Uri.parse('https://madar-test.r8787m.cc'),
        sessionStore: MemorySessionStore(sid: 'abc123'),
        httpClient: MockClient((request) async {
          requests.add(request);
          if (request.url.path.endsWith('list_work_orders')) {
            return _jsonResponse({
              'message': {
                'ok': true,
                'data': {
                  'items': [_workOrderMap()],
                },
                'error': null,
              },
            });
          }
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                ..._workOrderMap(),
                'items': [_workOrderItemMap()],
              },
              'error': null,
            },
          });
        }),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Directionality(
            textDirection: TextDirection.rtl,
            child: WorkOrderListScreen(apiClient: client),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('أوامر الإنتاج'), findsOneWidget);
      expect(find.text('DAIRY'), findsOneWidget);
      expect(find.text('بانتظار القبول'), findsOneWidget);

      await tester.tap(find.text('DAIRY'));
      await tester.pumpAndSettle();
      expect(find.text('Milk'), findsOneWidget);

      await tester.tap(find.text('قبول'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('بدء الإنتاج'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('جاهز'));
      await tester.pumpAndSettle();
      await tester.enterText(find.byType(TextField), 'Machine issue');
      await tester.tap(find.text('تأخير'));
      await tester.pumpAndSettle();

      expect(
        requests.any(
          (request) => request.url.path.endsWith('accept_work_order'),
        ),
        isTrue,
      );
      expect(
        requests.any(
          (request) => request.url.path.endsWith('start_work_order'),
        ),
        isTrue,
      );
      expect(
        requests.any(
          (request) => request.url.path.endsWith('mark_work_order_ready'),
        ),
        isTrue,
      );
      expect(
        requests.any(
          (request) => request.url.path.endsWith('mark_work_order_delayed'),
        ),
        isTrue,
      );
    },
  );
}

Map<String, dynamic> _workOrderMap({String status = 'pending'}) {
  return {
    'name': 'WO-1',
    'madar_order': 'MADAR-ORD-1',
    'production_center': 'MAIN',
    'production_department': 'DAIRY',
    'status': status,
    'accepted_at': null,
    'started_at': null,
    'ready_at': null,
    'delayed_at': null,
    'delay_reason': null,
    'created_from_order_at': '2026-05-19 12:00:00',
  };
}

Map<String, dynamic> _workOrderItemMap() {
  return {
    'name': 'WOI-1',
    'work_order': 'WO-1',
    'madar_order_item': 'LINE-1',
    'item_code': 'MILK-001',
    'item_name': 'Milk',
    'qty': 2,
    'notes': '',
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
