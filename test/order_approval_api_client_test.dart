import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/orders/order_models.dart';

void main() {
  test('order statuses include approval labels', () {
    expect(OrderStatus.fromString('submitted').arabicLabel, 'مرسل للاعتماد');
    expect(
      OrderStatus.fromString('approved').arabicLabel,
      'معتمد - جاهز للمزامنة',
    );
    expect(
      OrderStatus.fromString('returned_for_edit').arabicLabel,
      'معاد للتعديل',
    );
    expect(OrderStatus.fromString('rejected').arabicLabel, 'مرفوض');
  });

  test('order production statuses include Arabic labels', () {
    expect(
      OrderProductionStatus.fromString('not_started').arabicLabel,
      'لم يبدأ',
    );
    expect(
      OrderProductionStatus.fromString('pending').arabicLabel,
      'بانتظار الإنتاج',
    );
    expect(
      OrderProductionStatus.fromString('in_progress').arabicLabel,
      'قيد الإنتاج',
    );
    expect(OrderProductionStatus.fromString('delayed').arabicLabel, 'متأخر');
    expect(
      OrderProductionStatus.fromString('partially_ready').arabicLabel,
      'جاهز جزئيًا',
    );
    expect(OrderProductionStatus.fromString('ready').arabicLabel, 'جاهز');
    expect(OrderProductionStatus.fromString('blocked').arabicLabel, 'متوقف');
  });

  test('order display label reflects ERP sync metadata', () {
    const synced = MadarOrder(
      name: 'MADAR-ORD-1',
      customerName: 'عميل',
      customerPhone: '0500000000',
      status: OrderStatus.approved,
      erpSyncStatus: 'synced',
      erpSalesOrder: 'SAL-ORD-1',
    );
    const failed = MadarOrder(
      name: 'MADAR-ORD-2',
      customerName: 'عميل',
      customerPhone: '0500000000',
      status: OrderStatus.approved,
      erpSyncStatus: 'failed',
    );

    expect(synced.displayStatusLabel, 'تمت المزامنة');
    expect(failed.displayStatusLabel, 'فشل في المزامنة');
  });

  test('approval methods call only Madar endpoints', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_approval_queue')) {
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
        return _jsonResponse({'message': _orderEnvelope()});
      }),
    );

    await client.listApprovalQueue();
    await client.approveOrder('MADAR-ORD-1');
    await client.returnOrderForEdit('MADAR-ORD-1', reason: 'Needs edit');
    await client.rejectOrder('MADAR-ORD-1', reason: 'Duplicate');

    expect(
      requests[0].url.path,
      '/api/method/madar.api.orders.list_approval_queue',
    );
    expect(requests[1].url.path, '/api/method/madar.api.orders.approve_order');
    expect(
      requests[2].url.path,
      '/api/method/madar.api.orders.return_order_for_edit',
    );
    expect(requests[2].bodyFields['reason'], 'Needs edit');
    expect(requests[3].url.path, '/api/method/madar.api.orders.reject_order');
    expect(
      requests.any((request) => request.url.path.contains('/api/resource')),
      isFalse,
    );
  });
}

Map<String, dynamic> _orderEnvelope() {
  return {'ok': true, 'data': _orderMap(), 'error': null};
}

Map<String, dynamic> _orderMap() {
  return {
    'name': 'MADAR-ORD-1',
    'customer_name': 'عميل',
    'customer_phone': '0500000000',
    'order_status': 'approved',
    'branch': 'Main Branch',
    'assigned_branch': 'Main Branch',
    'created_by_user': 'branch.user@example.com',
    'notes': '',
    'subtotal': 12.5,
    'items_count': 1,
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
