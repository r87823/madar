import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/features/orders/order_detail_screen.dart';
import 'package:madar/features/orders/order_models.dart';

void main() {
  testWidgets('order detail shows items and subtotal', (tester) async {
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        if (request.url.path.endsWith('list_order_items')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'order': {
                  'name': 'MADAR-ORD-1',
                  'subtotal': 25,
                  'items_count': 1,
                },
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
            },
          });
        }
        return _jsonResponse({'message': _itemEnvelope()});
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: OrderDetailScreen(
            apiClient: client,
            initialOrder: const MadarOrder(
              name: 'MADAR-ORD-1',
              customerName: 'عميل',
              customerPhone: '050',
              status: OrderStatus.draft,
              subtotal: 25,
              itemsCount: 1,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.drag(find.byType(ListView), const Offset(0, -260));
    await tester.pumpAndSettle();

    expect(find.text('الأصناف'), findsOneWidget);
    expect(find.text('Milk'), findsOneWidget);
    expect(find.text('الإجمالي: 25.00'), findsOneWidget);
    expect(find.text('إضافة صنف'), findsOneWidget);
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
