import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/attendance/attendance_status.dart';

void main() {
  test('parses attendance status safe envelope', () {
    final status = AttendanceStatus.fromEnvelope({
      'ok': true,
      'data': {
        'employee': {'name': 'EMP-0001', 'employee_name': 'Madar Dev Employee'},
        'state': 'in_work',
        'last_checkin': {
          'name': 'CHK-1',
          'time': '2026-05-19 08:30:00',
          'log_type': 'IN',
        },
      },
      'error': null,
    });

    expect(status.state, AttendanceState.inWork);
    expect(status.employeeName, 'Madar Dev Employee');
    expect(status.lastLogType, 'IN');
  });

  test('checkIn posts no employee time or log_type fields', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        return http.Response(jsonEncode(_okEnvelope('in_work')), 200);
      }),
    );

    await client.checkIn();

    expect(
      requests.single.url.path,
      '/api/method/madar.api.attendance.check_in',
    );
    expect(requests.single.body, isEmpty);
    expect(requests.single.headers['cookie'], 'sid=abc123');
  });

  test('checkOut posts no employee time or log_type fields', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        return http.Response(jsonEncode(_okEnvelope('out_of_work')), 200);
      }),
    );

    await client.checkOut();

    expect(
      requests.single.url.path,
      '/api/method/madar.api.attendance.check_out',
    );
    expect(requests.single.body, isEmpty);
    expect(requests.single.headers['cookie'], 'sid=abc123');
  });

  test('getAttendanceStatus calls Madar status endpoint', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        return http.Response(jsonEncode(_okEnvelope('unknown')), 200);
      }),
    );

    final status = await client.getAttendanceStatus();

    expect(
      requests.single.url.path,
      '/api/method/madar.api.attendance.get_status',
    );
    expect(status.state, AttendanceState.unknown);
  });
}

Map<String, dynamic> _okEnvelope(String state) {
  return {
    'ok': true,
    'data': {
      'employee': {'name': 'EMP-0001', 'employee_name': 'Madar Dev Employee'},
      'state': state,
      'last_checkin': null,
    },
    'error': null,
  };
}
