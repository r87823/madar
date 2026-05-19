import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/orders/create_order_screen.dart';
import 'package:madar/features/orders/order_detail_screen.dart';
import 'package:madar/features/orders/order_list_screen.dart';
import 'package:madar/features/orders/order_models.dart';

void main() {
  testWidgets('orders dashboard card opens orders flow', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'branch.user@example.com',
              fullName: 'Branch User',
              roles: ['Madar Employee', 'Madar Branch User'],
              permissions: ['orders.create', 'orders.submit_for_approval'],
              scopes: ScopeContext(
                branchNames: ['Main Branch'],
                departmentNames: [],
              ),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {
              opened = true;
            },
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
          ),
        ),
      ),
    );

    await tester.tap(find.text('إنشاء طلب'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('order list shows create action and submitted status', (
    tester,
  ) async {
    final client = _ordersClient();

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: OrderListScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('الطلبات'), findsOneWidget);
    expect(find.text('طلب جديد'), findsOneWidget);
    expect(find.text('عميل'), findsOneWidget);
    expect(find.text('مسودة'), findsOneWidget);
  });

  testWidgets('approved order detail is read-only and shows sync readiness', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: OrderDetailScreen(
            apiClient: _approvedOrderClient(),
            initialOrder: const MadarOrder(
              name: 'MADAR-ORD-APPROVED',
              customerName: 'عميل معتمد',
              customerPhone: '0500000000',
              status: OrderStatus.approved,
              productionStatus: OrderProductionStatus.ready,
              erpSyncStatus: 'pending',
              itemsCount: 1,
              subtotal: 12.5,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('معتمد - جاهز للمزامنة'), findsOneWidget);
    expect(find.text('جاهز للمزامنة'), findsOneWidget);
    expect(find.text('الإنتاج'), findsOneWidget);
    expect(find.text('جاهز'), findsOneWidget);
    expect(find.text('إضافة صنف'), findsNothing);
    expect(find.text('إرسال الطلب'), findsNothing);
  });

  testWidgets('order list shows synced and failed ERP labels', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: OrderListScreen(apiClient: _syncStatusOrdersClient()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('تمت المزامنة'), findsOneWidget);
    expect(find.text('فشل في المزامنة'), findsOneWidget);
  });

  testWidgets(
    'create order defaults to branch pickup and sends destination branch',
    (tester) async {
      final requests = <http.Request>[];
      final client = FrappeApiClient(
        baseUri: Uri.parse('https://madar-test.r8787m.cc'),
        sessionStore: MemorySessionStore(sid: 'abc123'),
        httpClient: MockClient((request) async {
          requests.add(request);
          return http.Response.bytes(
            utf8.encode(jsonEncode({'message': _orderEnvelope()})),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          );
        }),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Directionality(
            textDirection: TextDirection.rtl,
            child: CreateOrderScreen(
              apiClient: client,
              userContext: const UserContext(
                user: 'branch.user@example.com',
                fullName: 'Branch User',
                roles: ['Madar Branch User'],
                permissions: ['orders.create'],
                scopes: ScopeContext(
                  branchNames: ['Main Branch'],
                  departmentNames: [],
                ),
              ),
            ),
          ),
        ),
      );

      expect(find.text('استلام من الفرع'), findsOneWidget);
      expect(find.text('توصيل للعميل'), findsOneWidget);
      final segmented = tester.widget<SegmentedButton<OrderFulfillmentMethod>>(
        find.byType(SegmentedButton<OrderFulfillmentMethod>),
      );
      expect(
        segmented.segments.first.value,
        OrderFulfillmentMethod.branchPickup,
      );
      expect(segmented.selected.single, OrderFulfillmentMethod.branchPickup);
      expect(
        find.widgetWithText(TextFormField, 'فرع الاستلام'),
        findsOneWidget,
      );

      await tester.enterText(
        find.widgetWithText(TextFormField, 'اسم العميل'),
        'عميل',
      );
      await tester.drag(find.byType(ListView), const Offset(0, -220));
      await tester.pumpAndSettle();
      await tester.tap(find.byType(FilledButton));
      await tester.pumpAndSettle();

      expect(requests.single.bodyFields['fulfillment_method'], 'branch_pickup');
      expect(requests.single.bodyFields['destination_branch'], 'Main Branch');
    },
  );
}

FrappeApiClient _ordersClient() {
  return FrappeApiClient(
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
                    'customer_phone': '0500000000',
                    'order_status': 'draft',
                    'branch': 'Main Branch',
                    'assigned_branch': 'Main Branch',
                    'created_by_user': 'branch.user@example.com',
                    'notes': '',
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
}

FrappeApiClient _syncStatusOrdersClient() {
  return FrappeApiClient(
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
                    'name': 'MADAR-ORD-SYNCED',
                    'customer_name': 'عميل تمت مزامنته',
                    'customer_phone': '0500000000',
                    'order_status': 'approved',
                    'erp_sync_status': 'synced',
                    'erp_sales_order': 'SAL-ORD-1',
                  },
                  {
                    'name': 'MADAR-ORD-FAILED',
                    'customer_name': 'عميل فشل',
                    'customer_phone': '0500000001',
                    'order_status': 'approved',
                    'erp_sync_status': 'failed',
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
}

Map<String, dynamic> _orderEnvelope() {
  return {
    'ok': true,
    'data': {
      'name': 'MADAR-ORD-1',
      'customer_name': 'عميل',
      'customer_phone': '',
      'order_status': 'draft',
      'fulfillment_method': 'branch_pickup',
      'destination_branch': 'Main Branch',
      'delivery_status': 'not_ready',
    },
    'error': null,
  };
}

FrappeApiClient _approvedOrderClient() {
  return FrappeApiClient(
    baseUri: Uri.parse('https://madar-test.r8787m.cc'),
    sessionStore: MemorySessionStore(sid: 'abc123'),
    httpClient: MockClient((request) async {
      return http.Response.bytes(
        utf8.encode(
          jsonEncode({
            'message': {
              'ok': true,
              'data': {
                'order': {
                  'name': 'MADAR-ORD-APPROVED',
                  'customer_name': 'عميل معتمد',
                  'customer_phone': '0500000000',
                  'order_status': 'approved',
                  'erp_sync_status': 'pending',
                  'subtotal': 12.5,
                  'items_count': 1,
                },
                'items': [],
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
}
