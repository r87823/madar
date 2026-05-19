import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/production/work_order_models.dart';

void main() {
  test('work order models parse safe envelopes and status labels', () {
    final list = WorkOrderList.fromEnvelope({
      'ok': true,
      'data': {
        'items': [_workOrderMap(status: 'in_production')],
      },
      'error': null,
    });

    expect(list.items.single.name, 'WO-1');
    expect(list.items.single.statusLabel, 'قيد الإنتاج');
  });

  test('work order methods call only Madar endpoints', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_work_orders')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_workOrderMap()],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': {
              ..._workOrderMap(),
              'items': [_workOrderItemMap()],
            },
            'error': null,
          },
        });
      }),
    );

    await client.createWorkOrdersFromOrder('MADAR-ORD-1');
    await client.listWorkOrders();
    await client.getWorkOrder('WO-1');
    await client.acceptWorkOrder('WO-1');
    await client.startWorkOrder('WO-1');
    await client.markWorkOrderReady('WO-1');
    await client.markWorkOrderDelayed('WO-1', reason: 'Machine issue');

    expect(
      requests[0].url.path,
      '/api/method/madar.api.work_orders.create_work_orders_from_order',
    );
    expect(requests[0].bodyFields['order_name'], 'MADAR-ORD-1');
    expect(
      requests[1].url.path,
      '/api/method/madar.api.work_orders.list_work_orders',
    );
    expect(
      requests[2].url.path,
      '/api/method/madar.api.work_orders.get_work_order',
    );
    expect(
      requests[3].url.path,
      '/api/method/madar.api.work_orders.accept_work_order',
    );
    expect(
      requests[4].url.path,
      '/api/method/madar.api.work_orders.start_work_order',
    );
    expect(
      requests[5].url.path,
      '/api/method/madar.api.work_orders.mark_work_order_ready',
    );
    expect(
      requests[6].url.path,
      '/api/method/madar.api.work_orders.mark_work_order_delayed',
    );
    expect(requests[6].bodyFields['reason'], 'Machine issue');
    expect(
      requests.any((request) => request.url.path.contains('/api/resource')),
      isFalse,
    );
  });
}

Map<String, dynamic> _workOrderMap({String status = 'pending'}) {
  return {
    'name': 'WO-1',
    'madar_order': 'MADAR-ORD-1',
    'production_center': 'MAIN',
    'production_department': 'DAIRY',
    'status': status,
    'accepted_at': null,
    'started_at': null,
    'ready_at': null,
    'delayed_at': null,
    'delay_reason': null,
    'created_from_order_at': '2026-05-19 12:00:00',
  };
}

Map<String, dynamic> _workOrderItemMap() {
  return {
    'name': 'WOI-1',
    'work_order': 'WO-1',
    'madar_order_item': 'LINE-1',
    'item_code': 'MILK-001',
    'item_name': 'Milk',
    'qty': 2,
    'notes': '',
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
