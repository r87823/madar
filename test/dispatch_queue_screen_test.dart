import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/delivery/dispatch_queue_screen.dart';

void main() {
  testWidgets('delivery dashboard card opens dispatch queue', (tester) async {
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
            onOpenDispatchQueue: () {
              opened = true;
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('مهام التوصيل'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('dispatch queue displays fulfillment and valid branch actions', (
    tester,
  ) async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_dispatch_queue')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_orderMap(deliveryStatus: 'ready_for_dispatch')],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': _orderMap(deliveryStatus: 'dispatched_to_branch'),
            'error': null,
          },
        });
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DispatchQueueScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('مهام التوصيل'), findsOneWidget);
    expect(find.text('استلام من الفرع'), findsOneWidget);
    expect(find.text('جاهز للإرسال'), findsOneWidget);
    expect(find.text('خرج إلى الفرع'), findsOneWidget);
    expect(find.text('تم الاستلام في الفرع'), findsNothing);

    await tester.tap(find.text('خرج إلى الفرع'));
    await tester.pumpAndSettle();

    expect(
      requests.any(
        (request) => request.url.path.endsWith('mark_dispatched_to_branch'),
      ),
      isTrue,
    );
  });

  testWidgets('dispatch queue shows customer delivery actions', (tester) async {
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': {
              'items': [
                _orderMap(
                  fulfillmentMethod: 'customer_delivery',
                  destinationBranch: '',
                  deliveryStatus: 'dispatched_to_customer',
                ),
              ],
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
          child: DispatchQueueScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('توصيل للعميل'), findsOneWidget);
    expect(find.text('خرج للتوصيل'), findsOneWidget);
    expect(find.text('تم التسليم للعميل'), findsOneWidget);
    expect(find.text('تعذر التسليم'), findsOneWidget);
  });
}

Map<String, dynamic> _orderMap({
  String fulfillmentMethod = 'branch_pickup',
  String destinationBranch = 'Main Branch',
  String deliveryStatus = 'ready_for_dispatch',
}) {
  return {
    'name': 'MADAR-ORD-1',
    'customer_name': 'عميل',
    'customer_phone': '0500000000',
    'order_status': 'approved',
    'fulfillment_method': fulfillmentMethod,
    'destination_branch': destinationBranch,
    'production_status': 'ready',
    'delivery_status': deliveryStatus,
    'subtotal': 10,
    'items_count': 1,
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
