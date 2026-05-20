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
        if (request.url.path.endsWith('list_sync_orders') ||
            request.url.path.endsWith('list_invoice_sync_orders') ||
            request.url.path.endsWith('list_orders_for_accounting_review')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items':
                    request.url.path.endsWith(
                      'list_orders_for_accounting_review',
                    )
                    ? [_accountingSummaryMap()]
                    : [_syncOrderMap()],
              },
              'error': null,
            },
          });
        }
        if (request.url.path.endsWith('get_order_accounting_summary') ||
            request.url.path.endsWith('mark_accounting_reviewed') ||
            request.url.path.endsWith('mark_accounting_needs_attention') ||
            request.url.path.endsWith('submit_sales_invoice')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': _accountingSummaryMap(),
              'error': null,
            },
          });
        }
        if (request.url.path.endsWith('get_finalization_status') ||
            request.url.path.endsWith('finalize_order_accounting')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': _finalizationStatusMap(),
              'error': null,
            },
          });
        }
        if (request.url.path.endsWith('submit_payment_entries')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_paymentItemMap()],
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
    await client.submitErpSalesOrder('MADAR-ORD-1');
    await client.listInvoiceSyncOrders();
    await client.getInvoiceSyncOrder('MADAR-ORD-1');
    await client.retryInvoiceSync('MADAR-ORD-1');
    await client.listOrdersForAccountingReview();
    await client.getOrderAccountingSummary('MADAR-ORD-1');
    await client.markAccountingReviewed('MADAR-ORD-1');
    await client.markAccountingNeedsAttention('MADAR-ORD-1', 'راجع الصندوق');
    await client.getFinalizationStatus('MADAR-ORD-1');
    await client.submitFinalSalesInvoice('MADAR-ORD-1');
    await client.submitPaymentEntries('MADAR-ORD-1');
    await client.finalizeOrderAccounting('MADAR-ORD-1');

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
      requests[3].url.path,
      '/api/method/madar.api.erp_sync.submit_erp_sales_order',
    );
    expect(
      requests[4].url.path,
      '/api/method/madar.api.erp_sync.list_invoice_sync_orders',
    );
    expect(
      requests[5].url.path,
      '/api/method/madar.api.erp_sync.get_invoice_sync_order',
    );
    expect(
      requests[6].url.path,
      '/api/method/madar.api.erp_sync.retry_invoice_sync',
    );
    expect(requests[6].bodyFields['order_name'], 'MADAR-ORD-1');
    expect(
      requests[7].url.path,
      '/api/method/madar.api.accounting_review.list_orders_for_accounting_review',
    );
    expect(
      requests[8].url.path,
      '/api/method/madar.api.accounting_review.get_order_accounting_summary',
    );
    expect(
      requests[9].url.path,
      '/api/method/madar.api.accounting_review.mark_accounting_reviewed',
    );
    expect(
      requests[10].url.path,
      '/api/method/madar.api.accounting_review.mark_accounting_needs_attention',
    );
    expect(requests[10].bodyFields['notes'], 'راجع الصندوق');
    expect(
      requests[11].url.path,
      '/api/method/madar.api.accounting_finalization.get_finalization_status',
    );
    expect(
      requests[12].url.path,
      '/api/method/madar.api.accounting_finalization.submit_sales_invoice',
    );
    expect(
      requests[13].url.path,
      '/api/method/madar.api.accounting_finalization.submit_payment_entries',
    );
    expect(
      requests[14].url.path,
      '/api/method/madar.api.accounting_finalization.finalize_order_accounting',
    );
    expect(
      requests.any((request) => request.url.path.contains('/api/resource')),
      isFalse,
    );
  });
}

Map<String, dynamic> _accountingSummaryMap() {
  return {
    'order': {
      'name': 'MADAR-ORD-1',
      'customer_name': 'عميل',
      'subtotal': 100,
      'paid_amount': 100,
      'remaining_amount': 0,
      'payment_status': 'paid',
      'order_status': 'approved',
      'delivery_status': 'customer_picked_up',
      'production_status': 'ready',
    },
    'erp_sales_order': {
      'erp_sales_order': 'SAL-ORD-1',
      'erp_sales_order_docstatus': 1,
      'erp_sync_status': 'synced',
      'erp_sync_error': null,
    },
    'erp_sales_invoice': {
      'erp_sales_invoice': 'ACC-SINV-1',
      'erp_sales_invoice_docstatus': 0,
      'erp_invoice_sync_status': 'synced',
      'erp_invoice_sync_error': null,
    },
    'payments': {
      'count': 1,
      'total_collected': 100,
      'methods': {'cash': 100},
      'erp_sync_statuses': {'synced': 1},
      'items': [_paymentItemMap()],
    },
    'cashbox': {
      'cash_payments_total': 100,
      'cashbox_names': ['CASHBOX-1'],
      'statuses': ['approved'],
      'reviewed': true,
    },
    'readiness': {
      'has_erp_sales_order': true,
      'sales_order_submitted': true,
      'delivered_or_picked_up': true,
      'has_sales_invoice_draft': true,
      'payments_match_order_total': true,
      'payment_entries_synced_or_not_required': true,
      'cashboxes_reviewed_for_cash_payments': true,
    },
    'alerts': [],
    'accounting_status': 'ready_for_review',
    'accounting_review_notes': null,
    'accounting_reviewed_by': null,
    'accounting_reviewed_at': null,
    'accounting_finalized_at': null,
    'accounting_finalized_by': null,
    'accounting_finalization_error': null,
  };
}

Map<String, dynamic> _finalizationStatusMap() {
  return {
    'order': _accountingSummaryMap()['order'],
    'can_finalize': true,
    'erp_sales_invoice_docstatus': 1,
    'payments': [_paymentItemMap(erpPaymentEntryDocstatus: 1)],
    'finalized': true,
    'accounting_finalized_at': '2026-05-20 16:00:00',
    'accounting_finalized_by': 'accountant.test@example.com',
    'accounting_finalization_error': null,
  };
}

Map<String, dynamic> _paymentItemMap({int erpPaymentEntryDocstatus = 0}) {
  return {
    'name': 'PAY-1',
    'amount': 100,
    'payment_method': 'cash',
    'erp_sync_status': 'synced',
    'erp_payment_entry': 'ACC-PAY-1',
    'erp_payment_entry_docstatus': erpPaymentEntryDocstatus,
    'erp_payment_submitted_at': erpPaymentEntryDocstatus == 1
        ? '2026-05-20 16:00:00'
        : null,
    'erp_payment_submit_error': null,
  };
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
