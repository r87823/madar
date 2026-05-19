import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/delivery/delivery_batch_list_screen.dart';

void main() {
  testWidgets('driver dashboard card opens my batches', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'driver.test@example.com',
              fullName: 'Driver',
              roles: ['Madar Driver'],
              permissions: ['delivery.view_assigned_batches'],
              scopes: ScopeContext(
                branchNames: ['Main Branch'],
                departmentNames: [],
              ),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
            onOpenMyDeliveryBatches: () {
              opened = true;
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('دفعاتي'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('driver sees assigned batch and can mark picked up', (
    tester,
  ) async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_my_delivery_batches')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_batchMap(status: 'assigned')],
              },
              'error': null,
            },
          });
        }
        if (request.url.path.endsWith('get_delivery_batch')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': _batchMap(status: 'assigned', includeOrders: true),
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': _batchMap(status: 'picked_up', includeOrders: true),
            'error': null,
          },
        });
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DeliveryBatchListScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('MADAR-DBATCH-1'), findsOneWidget);
    expect(find.text('تم التعيين'), findsOneWidget);

    await tester.tap(find.text('MADAR-DBATCH-1'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('استلام الدفعة'));
    await tester.pumpAndSettle();

    expect(
      requests.any(
        (request) => request.url.path.endsWith('mark_batch_picked_up'),
      ),
      isTrue,
    );
  });
}

Map<String, dynamic> _batchMap({
  required String status,
  bool includeOrders = false,
}) {
  return {
    'name': 'MADAR-DBATCH-1',
    'batch_number': 'MADAR-DBATCH-1',
    'batch_type': 'branch_transfer',
    'destination_branch': 'Main Branch',
    'driver_user': 'driver.test@example.com',
    'status': status,
    'created_by_user': 'driver.test@example.com',
    if (includeOrders)
      'orders': [
        {
          'name': 'MADAR-ORD-1',
          'customer_name': 'عميل',
          'customer_phone': '0500000000',
          'order_status': 'approved',
          'fulfillment_method': 'branch_pickup',
          'destination_branch': 'Main Branch',
          'production_status': 'ready',
          'delivery_status': 'dispatched_to_branch',
          'subtotal': 10,
          'items_count': 1,
        },
      ],
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
