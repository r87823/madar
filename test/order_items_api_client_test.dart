import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/orders/items/order_item_models.dart';
import 'package:madar/features/orders/items/product_models.dart';

void main() {
  test('parses product catalog safe envelope', () {
    final products = ProductList.fromEnvelope({
      'ok': true,
      'data': {
        'items': [
          {
            'item_code': 'MILK-001',
            'item_name': 'Milk',
            'stock_uom': 'Nos',
            'disabled': 0,
            'image': '/files/milk.png',
            'default_price': 12.5,
          },
        ],
      },
      'error': null,
    });

    expect(products.items.single.itemCode, 'MILK-001');
    expect(products.items.single.defaultPrice, 12.5);
  });

  test('parses order items envelope with totals', () {
    final list = OrderItemList.fromEnvelope({
      'ok': true,
      'data': {
        'order': {'name': 'MADAR-ORD-1', 'subtotal': 25, 'items_count': 1},
        'items': [
          {
            'name': 'LINE-1',
            'order_name': 'MADAR-ORD-1',
            'item_code': 'MILK-001',
            'item_name': 'Milk',
            'qty': 2,
            'unit_price': 12.5,
            'line_total': 25,
          },
        ],
      },
      'error': null,
    });

    expect(list.items.single.lineTotal, 25);
    expect(list.subtotal, 25);
    expect(list.itemsCount, 1);
  });

  test('catalog and item methods call only Madar endpoints', () async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_products')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [
                  {
                    'item_code': 'MILK-001',
                    'item_name': 'Milk',
                    'stock_uom': 'Nos',
                    'disabled': 0,
                    'image': null,
                    'default_price': 12.5,
                  },
                ],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({'message': _itemEnvelope()});
      }),
    );

    await client.listProducts(search: 'milk');
    await client.addOrderItem(
      orderName: 'MADAR-ORD-1',
      itemCode: 'MILK-001',
      qty: 2,
    );
    await client.updateOrderItemQty(
      orderName: 'MADAR-ORD-1',
      itemName: 'LINE-1',
      qty: 3,
    );
    await client.removeOrderItem(orderName: 'MADAR-ORD-1', itemName: 'LINE-1');

    expect(requests[0].url.path, '/api/method/madar.api.catalog.list_products');
    expect(requests[0].url.queryParameters['search'], 'milk');
    expect(requests[1].url.path, '/api/method/madar.api.order_items.add_item');
    expect(requests[1].bodyFields.containsKey('unit_price'), isFalse);
    expect(
      requests[2].url.path,
      '/api/method/madar.api.order_items.update_item_qty',
    );
    expect(
      requests[3].url.path,
      '/api/method/madar.api.order_items.remove_item',
    );
    expect(
      requests.any((request) => request.url.path.contains('/api/resource')),
      isFalse,
    );
  });
}

Map<String, dynamic> _itemEnvelope() {
  return {
    'ok': true,
    'data': {
      'order': {'name': 'MADAR-ORD-1', 'subtotal': 25, 'items_count': 1},
      'item': {
        'name': 'LINE-1',
        'order_name': 'MADAR-ORD-1',
        'item_code': 'MILK-001',
        'item_name': 'Milk',
        'qty': 2,
        'unit_price': 12.5,
        'line_total': 25,
      },
      'items': [],
    },
    'error': null,
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
