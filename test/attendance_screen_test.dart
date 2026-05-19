import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/attendance/attendance_screen.dart';

void main() {
  testWidgets('in work state shows checkout action and history', (
    tester,
  ) async {
    await tester.pumpWidget(_screenForState('in_work'));
    await tester.pumpAndSettle();

    expect(find.text('داخل الدوام'), findsWidgets);
    expect(find.text('تسجيل انصراف'), findsOneWidget);
    expect(find.text('تسجيل حضور'), findsNothing);
    expect(find.text('آخر تسجيلاتك'), findsOneWidget);
    expect(find.textContaining('حضور'), findsWidgets);
  });

  testWidgets('out of work state shows checkin action', (tester) async {
    await tester.pumpWidget(_screenForState('out_of_work'));
    await tester.pumpAndSettle();

    expect(find.text('خارج الدوام'), findsWidgets);
    expect(find.text('تسجيل حضور'), findsOneWidget);
    expect(find.text('تسجيل انصراف'), findsNothing);
  });
}

Widget _screenForState(String state) {
  final client = FrappeApiClient(
    baseUri: Uri.parse('https://madar-test.r8787m.cc'),
    sessionStore: MemorySessionStore(sid: 'abc123'),
    httpClient: MockClient((request) async {
      if (request.url.path.endsWith('get_history')) {
        return http.Response(
          jsonEncode({
            'message': {
              'ok': true,
              'data': {
                'items': [
                  {
                    'log_type': 'IN',
                    'time': '2026-05-19 08:00:00',
                    'state': 'in_work',
                  },
                ],
              },
              'error': null,
            },
          }),
          200,
        );
      }
      return http.Response(
        jsonEncode({'message': _statusEnvelope(state)}),
        200,
      );
    }),
  );

  return MaterialApp(
    home: Directionality(
      textDirection: TextDirection.rtl,
      child: AttendanceScreen(apiClient: client),
    ),
  );
}

Map<String, dynamic> _statusEnvelope(String state) {
  return {
    'ok': true,
    'data': {
      'employee': {'name': 'EMP-0001', 'employee_name': 'Madar Dev Employee'},
      'state': state,
      'current_state': state,
      'last_log_type': state == 'in_work' ? 'IN' : 'OUT',
      'last_time': '2026-05-19 08:00:00',
      'last_checkin': {
        'name': 'CHK-1',
        'employee': 'EMP-0001',
        'time': '2026-05-19 08:00:00',
        'log_type': state == 'in_work' ? 'IN' : 'OUT',
      },
    },
    'error': null,
  };
}
