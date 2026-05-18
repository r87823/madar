import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';

void main() {
  test(
    'login posts only to Frappe login method and stores sid cookie',
    () async {
      final requests = <http.Request>[];
      final sessionStore = MemorySessionStore();
      final client = FrappeApiClient(
        baseUri: Uri.parse('https://madar-test.r8787m.cc'),
        httpClient: MockClient((request) async {
          requests.add(request);
          return http.Response(
            jsonEncode({'message': 'Logged In'}),
            200,
            headers: {'set-cookie': 'sid=abc123; Path=/; HttpOnly'},
          );
        }),
        sessionStore: sessionStore,
      );

      await client.login(
        username: 'driver.test@example.com',
        password: 'secret',
      );

      expect(requests.single.url.path, '/api/method/login');
      expect(requests.single.bodyFields['usr'], 'driver.test@example.com');
      expect(sessionStore.sid, 'abc123');
    },
  );

  test('getContext calls Madar get_context endpoint', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      httpClient: MockClient((request) async {
        requests.add(request);
        return http.Response(
          jsonEncode({
            'message': {
              'user': 'accountant.test@example.com',
              'full_name': 'Madar Accountant',
              'roles': ['Madar Employee', 'Madar Accountant'],
              'permissions': ['accounting.view_sync_logs'],
              'employee': null,
              'branch': null,
              'scopes': {'branch_names': [], 'department_names': []},
            },
          }),
          200,
        );
      }),
      sessionStore: MemorySessionStore(sid: 'abc123'),
    );

    final context = await client.getContext();

    expect(requests.single.url.path, '/api/method/madar.api.me.get_context');
    expect(requests.single.headers['cookie'], 'sid=abc123');
    expect(context.permissions, ['accounting.view_sync_logs']);
  });
}
