import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/followup_dashboard/followup_dashboard_models.dart';
import 'package:madar/features/followup_dashboard/followup_dashboard_screen.dart';

void main() {
  test('follow-up dashboard models parse cards and alerts', () {
    final summary = FollowupDashboardSummary.fromEnvelope({
      'ok': true,
      'data': {
        'cards': [_card('orders_today', 'طلبات اليوم', 3)],
        'alerts': [_alert('erp_sync_failed', 'أخطاء مزامنة ERP')],
      },
      'error': null,
    });

    expect(summary.cards.single.title, 'طلبات اليوم');
    expect(summary.cards.single.valueText, '3');
    expect(summary.alerts.single.priority, 'high');
  });

  testWidgets('dashboard card opens لوحة المتابعة', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'employee.test@example.com',
              fullName: 'Employee',
              roles: ['Madar Employee'],
              permissions: ['employee_services.view_self'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
            onOpenFollowupDashboard: () {
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

    await tester.tap(find.text('لوحة المتابعة'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('follow-up dashboard renders cards alerts and opens route', (
    tester,
  ) async {
    String? openedRoute;
    final client = _client(summary: _summaryEnvelope());

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: FollowupDashboardScreen(
            apiClient: client,
            onOpenRoute: (routeKey, routeParams) async {
              openedRoute = routeKey;
              return true;
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('لوحة المتابعة'), findsOneWidget);
    expect(find.text('طلبات اليوم'), findsOneWidget);
    expect(find.text('أخطاء مزامنة ERP'), findsWidgets);
    expect(find.text('تنبيهات'), findsOneWidget);

    await tester.tap(find.text('طلبات اليوم'));
    await tester.pumpAndSettle();

    expect(openedRoute, 'orders_list');
  });

  testWidgets('unsupported route shows safe Arabic message', (tester) async {
    final client = _client(summary: _summaryEnvelope());

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: FollowupDashboardScreen(
            apiClient: client,
            onOpenRoute: (routeKey, routeParams) async => false,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('طلبات اليوم'));
    await tester.pumpAndSettle();

    expect(find.text('لا يمكن فتح هذا القسم الآن'), findsOneWidget);
  });

  testWidgets('follow-up dashboard empty state renders', (tester) async {
    final client = _client(
      summary: {
        'ok': true,
        'data': {'cards': [], 'alerts': []},
        'error': null,
      },
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: FollowupDashboardScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('لا توجد بيانات للعرض'), findsOneWidget);
  });
}

FrappeApiClient _client({required Map<String, dynamic> summary}) {
  return FrappeApiClient(
    baseUri: Uri.parse('https://madar-test.r8787m.cc'),
    sessionStore: MemorySessionStore(sid: 'abc123'),
    httpClient: MockClient((request) async {
      return http.Response.bytes(
        utf8.encode(jsonEncode({'message': summary})),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    }),
  );
}

Map<String, dynamic> _summaryEnvelope() {
  return {
    'ok': true,
    'data': {
      'cards': [
        _card('orders_today', 'طلبات اليوم', 3, routeKey: 'orders_list'),
        _card(
          'erp_sync_failed',
          'أخطاء مزامنة ERP',
          2,
          priority: 'high',
          routeKey: 'erp_sync_review',
        ),
      ],
      'alerts': [_alert('erp_sync_failed', 'أخطاء مزامنة ERP')],
    },
    'error': null,
  };
}

Map<String, dynamic> _card(
  String key,
  String title,
  Object value, {
  String priority = 'normal',
  String routeKey = 'none',
}) {
  return {
    'key': key,
    'title': title,
    'value': value,
    'subtitle': 'حسب نطاقك',
    'priority': priority,
    'route_key': routeKey,
    'route_params': {},
  };
}

Map<String, dynamic> _alert(String key, String title) {
  return {
    'key': key,
    'title': title,
    'message': 'يوجد 2 عناصر تحتاج مراجعة',
    'priority': 'high',
    'route_key': 'erp_sync_review',
    'route_params': {},
  };
}
