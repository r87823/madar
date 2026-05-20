import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/accounting/erp_sync_review_screen.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';

void main() {
  testWidgets('accounting dashboard card opens ERP sync review', (
    tester,
  ) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'accountant.test@example.com',
              fullName: 'Accountant',
              roles: ['Madar Accountant'],
              permissions: ['accounting.view_sync_logs'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {
              opened = true;
            },
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
          ),
        ),
      ),
    );

    await tester.tap(find.text('المحاسبة والمزامنة'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets(
    'ERP sync review shows statuses errors references and retry buttons',
    (tester) async {
      final client = FrappeApiClient(
        baseUri: Uri.parse('https://madar-test.r8787m.cc'),
        sessionStore: MemorySessionStore(sid: 'abc123'),
        httpClient: MockClient((request) async {
          if (request.url.path.endsWith('list_payment_sync_items')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': {
                      'items': [
                        _payment('PAY-PENDING', 'pending', method: 'cash'),
                        _payment(
                          'PAY-FAILED',
                          'failed',
                          method: 'card',
                          error: 'Payment account missing',
                        ),
                        _payment(
                          'PAY-SYNCED',
                          'synced',
                          method: 'transfer',
                          paymentEntry: 'ACC-PAY-1',
                        ),
                      ],
                    },
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('retry_payment_sync')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': _payment(
                      'PAY-PENDING',
                      'synced',
                      paymentEntry: 'ACC-PAY-2',
                    ),
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          return http.Response.bytes(
            utf8.encode(
              jsonEncode({
                'message': {
                  'ok': true,
                  'data': {
                    'items': [
                      _order('MADAR-ORD-PENDING', 'pending'),
                      _order(
                        'MADAR-ORD-FAILED',
                        'failed',
                        error: 'Customer missing',
                      ),
                      _order(
                        'MADAR-ORD-SYNCED',
                        'synced',
                        salesOrder: 'SAL-ORD-1',
                      ),
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
            child: ErpSyncReviewScreen(apiClient: client),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('مراجعة مزامنة ERP'), findsOneWidget);
      expect(find.text('بانتظار المزامنة'), findsOneWidget);
      expect(find.text('فشلت المزامنة'), findsOneWidget);
      expect(find.text('Customer missing'), findsOneWidget);
      await tester.drag(find.byType(ListView), const Offset(0, -900));
      await tester.pumpAndSettle();

      expect(find.text('مدفوعات ERP'), findsOneWidget);
      expect(find.text('PAY-PENDING'), findsOneWidget);
      expect(find.text('نقد'), findsOneWidget);
      expect(find.text('إعادة المحاولة'), findsWidgets);
      await tester.drag(find.byType(ListView), const Offset(0, -420));
      await tester.pumpAndSettle();

      expect(find.text('Payment account missing'), findsOneWidget);
      expect(find.text('ACC-PAY-1'), findsOneWidget);
    },
  );
}

Map<String, dynamic> _order(
  String name,
  String status, {
  String? error,
  String? salesOrder,
}) {
  return {
    'name': name,
    'customer_name': 'عميل $name',
    'subtotal': 12.5,
    'order_status': 'approved',
    'erp_sync_status': status,
    'erp_sync_error': error,
    'erp_sales_order': salesOrder,
    'approved_at': '2026-05-19 12:00:00',
    'approved_by': 'branch.supervisor@example.com',
  };
}

Map<String, dynamic> _payment(
  String name,
  String status, {
  String method = 'cash',
  String? error,
  String? paymentEntry,
}) {
  return {
    'name': name,
    'madar_order': 'MADAR-ORD-1',
    'customer_name': 'عميل الدفع',
    'amount': 40,
    'payment_method': method,
    'payment_status': 'collected',
    'erp_sync_status': status,
    'erp_sync_error': error,
    'erp_payment_entry': paymentEntry,
    'erp_sales_order': 'SAL-ORD-1',
    'reference_no': 'REF-1',
  };
}
