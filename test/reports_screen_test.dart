import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/reports/reports_models.dart';
import 'package:madar/features/reports/reports_screen.dart';

void main() {
  test('report result parses envelope with summary and rows', () {
    final result = ReportResult.fromEnvelope(_ordersEnvelope());

    expect(result.total, 1);
    expect(result.summary.count, 1);
    expect(result.summary.totalAmount, 150);
    expect(result.items.single['name'], 'ORD-1');
  });

  testWidgets('dashboard reports card opens التقارير', (tester) async {
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
            onOpenReports: () {
              opened = true;
            },
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

    await tester.tap(find.text('التقارير'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('reports screen renders Arabic menu and loads report rows', (
    tester,
  ) async {
    final client = _client();

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: ReportsScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('التقارير'), findsOneWidget);
    expect(find.text('تقرير الطلبات'), findsOneWidget);
    expect(find.text('تقرير أخطاء ERP'), findsOneWidget);

    await tester.tap(find.text('تقرير الطلبات'));
    await tester.pumpAndSettle();

    expect(find.text('ORD-1'), findsOneWidget);
    expect(find.text('الإجمالي: 150.0'), findsOneWidget);
    expect(find.text('تغيير الفلاتر'), findsOneWidget);
  });

  testWidgets('reports screen can change filters and render empty state', (
    tester,
  ) async {
    final client = _client(emptyWhenDraft: true);

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: ReportsScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('تقرير الطلبات'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('تغيير الفلاتر'));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const ValueKey('filter-order_status')),
      'draft',
    );
    await tester.ensureVisible(find.text('تطبيق'));
    await tester.tap(find.text('تطبيق'));
    await tester.pumpAndSettle();

    expect(find.text('لا توجد نتائج'), findsOneWidget);
  });
}

FrappeApiClient _client({bool emptyWhenDraft = false}) {
  return FrappeApiClient(
    baseUri: Uri.parse('https://madar-test.r8787m.cc'),
    sessionStore: MemorySessionStore(sid: 'abc123'),
    httpClient: MockClient((request) async {
      final body = request.bodyFields;
      if (emptyWhenDraft && (body['filters'] ?? '').contains('draft')) {
        return _json(_emptyEnvelope());
      }
      if (request.url.path.endsWith('get_orders_report')) {
        return _json(_ordersEnvelope());
      }
      return _json(_emptyEnvelope());
    }),
  );
}

http.Response _json(Map<String, dynamic> message) {
  return http.Response.bytes(
    utf8.encode(jsonEncode({'message': message})),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}

Map<String, dynamic> _ordersEnvelope() {
  return {
    'ok': true,
    'data': {
      'items': [
        {
          'name': 'ORD-1',
          'customer_name': 'Customer',
          'order_status': 'draft',
          'subtotal': 150.0,
        },
      ],
      'total': 1,
      'page': 1,
      'page_size': 20,
      'filters': {},
      'summary': {'count': 1, 'total_amount': 150.0},
    },
    'error': null,
  };
}

Map<String, dynamic> _emptyEnvelope() {
  return {
    'ok': true,
    'data': {
      'items': [],
      'total': 0,
      'page': 1,
      'page_size': 20,
      'filters': {},
      'summary': {'count': 0, 'total_amount': 0},
    },
    'error': null,
  };
}
