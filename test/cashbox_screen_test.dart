import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/cashbox/cashbox_screen.dart';

void main() {
  testWidgets('cashbox screen renders entries and submits own cashbox', (
    tester,
  ) async {
    final requests = <http.Request>[];
    final client = _client(requests);

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: CashboxScreen(apiClient: client, userContext: _context()),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('صندوق اليوم'), findsOneWidget);
    expect(find.text('قيود الصندوق'), findsOneWidget);
    expect(find.textContaining('PAY-1'), findsOneWidget);

    await tester.enterText(
      find.widgetWithText(TextField, 'المبلغ المسلم'),
      '40',
    );
    await tester.tap(find.text('إرسال للمراجعة'));
    await tester.pumpAndSettle();

    expect(
      requests.any((request) => request.url.path.endsWith('submit_my_cashbox')),
      isTrue,
    );
  });

  testWidgets('cashbox reviewer sees approve and return actions', (
    tester,
  ) async {
    final requests = <http.Request>[];
    final client = _client(requests);

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: CashboxScreen(
            apiClient: client,
            userContext: _context(
              permissions: ['cashbox.view_own', 'cashbox.review'],
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.drag(find.byType(ListView), const Offset(0, -500));
    await tester.pumpAndSettle();

    expect(find.text('مراجعة الصناديق'), findsOneWidget);
    expect(find.byTooltip('اعتماد'), findsOneWidget);
    expect(find.byTooltip('إعادة'), findsOneWidget);

    await tester.tap(find.byTooltip('اعتماد'));
    await tester.pumpAndSettle();

    expect(
      requests.any((request) => request.url.path.endsWith('approve_cashbox')),
      isTrue,
    );
  });
}

FrappeApiClient _client(List<http.Request> requests) {
  return FrappeApiClient(
    baseUri: Uri.parse('https://madar-test.r8787m.cc'),
    sessionStore: MemorySessionStore(sid: 'abc123'),
    httpClient: MockClient((request) async {
      requests.add(request);
      if (request.url.path.endsWith('get_my_cashbox')) {
        return _jsonResponse({'message': _cashboxEnvelope()});
      }
      if (request.url.path.endsWith('list_cashboxes_for_review')) {
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': {
              'items': [_cashboxMap(status: 'submitted')],
            },
            'error': null,
          },
        });
      }
      if (request.url.path.endsWith('submit_my_cashbox') ||
          request.url.path.endsWith('approve_cashbox') ||
          request.url.path.endsWith('return_cashbox')) {
        return _jsonResponse({
          'message': _cashboxEnvelope(status: 'submitted'),
        });
      }
      return _jsonResponse({'message': _cashboxEnvelope()});
    }),
  );
}

UserContext _context({
  List<String> permissions = const ['cashbox.view_own', 'cashbox.submit'],
}) {
  return UserContext(
    user: 'cashier.test@example.com',
    fullName: 'Cashier',
    roles: const ['Madar Cashier'],
    permissions: permissions,
    scopes: const ScopeContext(
      branchNames: ['Main Branch'],
      departmentNames: ['Finance'],
    ),
  );
}

Map<String, dynamic> _cashboxEnvelope({String status = 'open'}) {
  return {'ok': true, 'data': _cashboxMap(status: status), 'error': null};
}

Map<String, dynamic> _cashboxMap({String status = 'open'}) {
  return {
    'name': 'CASHBOX-1',
    'user': 'cashier.test@example.com',
    'cashbox_date': '2026-05-19',
    'status': status,
    'expected_cash': 40,
    'submitted_cash': status == 'submitted' ? 40 : 0,
    'difference': status == 'submitted' ? 0 : -40,
    'entries': [
      {
        'name': 'ENTRY-1',
        'cashbox': 'CASHBOX-1',
        'payment': 'PAY-1',
        'madar_order': 'MADAR-ORD-1',
        'amount': 40,
        'entry_type': 'cash_payment',
        'created_by_user': 'cashier.test@example.com',
        'created_at': '2026-05-19 12:00:00',
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
