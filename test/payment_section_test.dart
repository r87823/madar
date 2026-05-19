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
  testWidgets('order detail shows payment summary history and collect form', (
    tester,
  ) async {
    final requests = <http.Request>[];
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_order_items')) {
          return _jsonResponse({'message': _itemsEnvelope()});
        }
        if (request.url.path.endsWith('list_order_payments')) {
          return _jsonResponse({'message': _paymentsEnvelope()});
        }
        if (request.url.path.endsWith('collect_payment')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'name': 'PAY-2',
                'madar_order': 'MADAR-ORD-1',
                'amount': 75,
                'payment_method': 'cash',
                'payment_status': 'collected',
                'collection_context': 'branch',
                'order': {
                  'name': 'MADAR-ORD-1',
                  'subtotal': 100,
                  'paid_amount': 100,
                  'remaining_amount': 0,
                  'payment_status': 'paid',
                },
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({'message': _itemsEnvelope()});
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: OrderDetailScreen(
            apiClient: client,
            canCollectPayments: true,
            initialOrder: const MadarOrder(
              name: 'MADAR-ORD-1',
              customerName: 'عميل',
              customerPhone: '0500000000',
              status: OrderStatus.approved,
              subtotal: 100,
              paidAmount: 25,
              remainingAmount: 75,
              paymentStatus: OrderPaymentStatus.partiallyPaid,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(find.byType(ListView), const Offset(0, -500));
    await tester.pumpAndSettle();

    expect(find.text('المدفوعات'), findsOneWidget);
    expect(find.text('مدفوع جزئيًا'), findsWidgets);
    expect(find.text('المتبقي'), findsOneWidget);
    expect(find.text('75.00'), findsWidgets);
    expect(find.textContaining('دفعة نقد'), findsOneWidget);

    await tester.enterText(find.widgetWithText(TextField, 'المبلغ'), '75');
    await tester.ensureVisible(find.text('تحصيل الدفع'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('تحصيل الدفع'));
    await tester.pumpAndSettle();

    expect(
      requests.any((request) => request.url.path.endsWith('collect_payment')),
      isTrue,
    );
  });
}

Map<String, dynamic> _itemsEnvelope() {
  return {
    'ok': true,
    'data': {
      'order': {'name': 'MADAR-ORD-1', 'subtotal': 100, 'items_count': 1},
      'items': [],
    },
    'error': null,
  };
}

Map<String, dynamic> _paymentsEnvelope() {
  return {
    'ok': true,
    'data': {
      'items': [
        {
          'name': 'PAY-1',
          'madar_order': 'MADAR-ORD-1',
          'amount': 25,
          'payment_method': 'cash',
          'payment_status': 'collected',
          'collected_by_user': 'cashier.test@example.com',
          'collected_at': '2026-05-19 12:00:00',
          'collection_context': 'branch',
          'reference_no': '',
          'notes': 'دفعة نقد',
          'is_cancelled': false,
        },
      ],
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
