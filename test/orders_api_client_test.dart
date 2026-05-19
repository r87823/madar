import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/orders/order_models.dart';

void main() {
  test('parses order list safe envelope', () {
    final list = OrderList.fromEnvelope({
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
            'notes': 'ملاحظة',
          },
        ],
      },
      'error': null,
    });

    expect(list.items.single.name, 'MADAR-ORD-1');
    expect(list.items.single.status, OrderStatus.draft);
    expect(list.items.single.status.arabicLabel, 'مسودة');
  });

  test('createOrderDraft calls only Madar order endpoint', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        return _jsonResponse({'message': _orderEnvelope()});
      }),
    );

    await client.createOrderDraft(
      customerName: 'عميل',
      customerPhone: '0500000000',
      notes: 'ملاحظة',
    );

    expect(
      requests.single.url.path,
      '/api/method/madar.api.orders.create_draft',
    );
    expect(requests.single.headers['cookie'], 'sid=abc123');
    expect(requests.single.bodyFields['customer_name'], 'عميل');
    expect(requests.single.bodyFields.containsKey('doctype'), isFalse);
  });

  test('listOrders and submitOrder use Madar endpoints', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_orders')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_orderMap()],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({'message': _orderEnvelope(status: 'submitted')});
      }),
    );

    final list = await client.listOrders();
    final submitted = await client.submitOrder('MADAR-ORD-1');

    expect(list.items.single.name, 'MADAR-ORD-1');
    expect(submitted.status, OrderStatus.submitted);
    expect(requests.first.url.path, '/api/method/madar.api.orders.list_orders');
    expect(requests.last.url.path, '/api/method/madar.api.orders.submit_order');
    expect(requests.last.bodyFields['order_name'], 'MADAR-ORD-1');
  });
}

Map<String, dynamic> _orderEnvelope({String status = 'draft'}) {
  return {'ok': true, 'data': _orderMap(status: status), 'error': null};
}

Map<String, dynamic> _orderMap({String status = 'draft'}) {
  return {
    'name': 'MADAR-ORD-1',
    'customer_name': 'عميل',
    'customer_phone': '0500000000',
    'order_status': status,
    'branch': 'Main Branch',
    'assigned_branch': 'Main Branch',
    'created_by_user': 'branch.user@example.com',
    'notes': 'ملاحظة',
    'submitted_at': status == 'submitted' ? '2026-05-19 12:00:00' : null,
    'cancelled_at': null,
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
