import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';

void main() {
  test('ERP sync review methods call only Madar endpoints', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_sync_orders')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_syncOrderMap()],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {'ok': true, 'data': _syncOrderMap(), 'error': null},
        });
      }),
    );

    await client.listErpSyncOrders();
    await client.getErpSyncOrder('MADAR-ORD-1');
    await client.retryErpSyncOrder('MADAR-ORD-1');

    expect(
      requests[0].url.path,
      '/api/method/madar.api.erp_sync.list_sync_orders',
    );
    expect(
      requests[1].url.path,
      '/api/method/madar.api.erp_sync.get_sync_order',
    );
    expect(
      requests[2].url.path,
      '/api/method/madar.api.erp_sync.retry_sync_order',
    );
    expect(requests[2].bodyFields['order_name'], 'MADAR-ORD-1');
    expect(
      requests.any((request) => request.url.path.contains('/api/resource')),
      isFalse,
    );
  });
}

Map<String, dynamic> _syncOrderMap() {
  return {
    'name': 'MADAR-ORD-1',
    'customer_name': 'عميل',
    'subtotal': 12.5,
    'order_status': 'approved',
    'erp_sync_status': 'failed',
    'erp_sync_error': 'Customer missing',
    'erp_sales_order': null,
    'approved_at': '2026-05-19 12:00:00',
    'approved_by': 'branch.supervisor@example.com',
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
