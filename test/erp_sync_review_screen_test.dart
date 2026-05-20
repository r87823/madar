import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/accounting/erp_sync_review_screen.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';

void main() {
  testWidgets('accounting dashboard card opens ERP sync review', (
    tester,
  ) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'accountant.test@example.com',
              fullName: 'Accountant',
              roles: ['Madar Accountant'],
              permissions: ['accounting.view_sync_logs'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {
              opened = true;
            },
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
          ),
        ),
      ),
    );

    await tester.tap(find.text('المحاسبة والمزامنة'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets(
    'ERP sync review shows statuses errors references and retry buttons',
    (tester) async {
      final client = FrappeApiClient(
        baseUri: Uri.parse('https://madar-test.r8787m.cc'),
        sessionStore: MemorySessionStore(sid: 'abc123'),
        httpClient: MockClient((request) async {
          if (request.url.path.endsWith('list_payment_sync_items')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': {
                      'items': [
                        _payment('PAY-PENDING', 'pending', method: 'cash'),
                        _payment(
                          'PAY-FAILED',
                          'failed',
                          method: 'card',
                          error: 'Payment account missing',
                        ),
                        _payment(
                          'PAY-SYNCED',
                          'synced',
                          method: 'transfer',
                          paymentEntry: 'ACC-PAY-1',
                        ),
                      ],
                    },
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('list_orders_for_accounting_review')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': {
                      'items': [
                        _accountingSummary('MADAR-ORD-READY', 'ready_for_review'),
                        _accountingSummary(
                          'MADAR-ORD-ATTENTION',
                          'needs_attention',
                          alerts: ['CASHBOX_NOT_APPROVED'],
                          notes: 'راجع الصندوق',
                        ),
                      ],
                    },
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('mark_accounting_reviewed')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': _accountingSummary('MADAR-ORD-READY', 'reviewed'),
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('mark_accounting_needs_attention')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': _accountingSummary(
                      'MADAR-ORD-READY',
                      'needs_attention',
                      notes: 'مراجعة إضافية',
                    ),
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('list_invoice_sync_orders')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': {
                      'items': [
                        _order(
                          'MADAR-ORD-INVOICE-PENDING',
                          'synced',
                          salesOrder: 'SAL-ORD-2',
                          salesOrderDocstatus: 0,
                          invoiceStatus: 'pending',
                          deliveryStatus: 'customer_picked_up',
                        ),
                        _order(
                          'MADAR-ORD-INVOICE-FAILED',
                          'synced',
                          salesOrder: 'SAL-ORD-3',
                          salesOrderDocstatus: 1,
                          invoiceStatus: 'failed',
                          invoiceError: 'Income account missing',
                          deliveryStatus: 'delivered_to_customer',
                        ),
                        _order(
                          'MADAR-ORD-INVOICE-SYNCED',
                          'synced',
                          salesOrder: 'SAL-ORD-4',
                          salesOrderDocstatus: 1,
                          invoiceStatus: 'synced',
                          salesInvoice: 'ACC-SINV-1',
                          deliveryStatus: 'customer_picked_up',
                        ),
                      ],
                    },
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('submit_erp_sales_order')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': _order(
                      'MADAR-ORD-INVOICE-PENDING',
                      'synced',
                      salesOrder: 'SAL-ORD-2',
                      salesOrderDocstatus: 1,
                      invoiceStatus: 'pending',
                    ),
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('retry_invoice_sync')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': _order(
                      'MADAR-ORD-INVOICE-FAILED',
                      'synced',
                      salesOrder: 'SAL-ORD-3',
                      salesOrderDocstatus: 1,
                      invoiceStatus: 'synced',
                      salesInvoice: 'ACC-SINV-2',
                    ),
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          if (request.url.path.endsWith('retry_payment_sync')) {
            return http.Response.bytes(
              utf8.encode(
                jsonEncode({
                  'message': {
                    'ok': true,
                    'data': _payment(
                      'PAY-PENDING',
                      'synced',
                      paymentEntry: 'ACC-PAY-2',
                    ),
                    'error': null,
                  },
                }),
              ),
              200,
              headers: {'content-type': 'application/json; charset=utf-8'},
            );
          }
          return http.Response.bytes(
            utf8.encode(
              jsonEncode({
                'message': {
                  'ok': true,
                  'data': {
                    'items': [
                      _order('MADAR-ORD-PENDING', 'pending'),
                      _order(
                        'MADAR-ORD-FAILED',
                        'failed',
                        error: 'Customer missing',
                      ),
                      _order(
                        'MADAR-ORD-SYNCED',
                        'synced',
                        salesOrder: 'SAL-ORD-1',
                      ),
                    ],
                  },
                  'error': null,
                },
              }),
            ),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          );
        }),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Directionality(
            textDirection: TextDirection.rtl,
            child: ErpSyncReviewScreen(apiClient: client),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('مراجعة مزامنة ERP'), findsOneWidget);
      expect(find.text('بانتظار المزامنة'), findsOneWidget);
      expect(find.text('فشلت المزامنة'), findsOneWidget);
      expect(find.text('Customer missing'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('فواتير ERP'),
        500,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      expect(find.text('فواتير ERP'), findsOneWidget);
      expect(find.text('أمر بيع مسودة'), findsOneWidget);
      expect(find.text('اعتماد أمر البيع'), findsOneWidget);
      expect(find.text('فشل إنشاء الفاتورة'), findsOneWidget);
      expect(find.text('Income account missing'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('ACC-SINV-1'),
        250,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      expect(find.text('ACC-SINV-1'), findsWidgets);
      await tester.scrollUntilVisible(
        find.text('مراجعة الإقفال'),
        500,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      expect(find.text('مراجعة الإقفال'), findsOneWidget);
      expect(find.text('جاهز للمراجعة'), findsOneWidget);
      await tester.scrollUntilVisible(
        find.text('يحتاج انتباه'),
        250,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      expect(find.text('يحتاج انتباه'), findsOneWidget);
      expect(find.text('الطلب'), findsWidgets);
      expect(find.text('أمر البيع'), findsOneWidget);
      expect(find.text('الفاتورة'), findsOneWidget);
      expect(find.text('المدفوعات'), findsOneWidget);
      expect(find.text('الصندوق'), findsOneWidget);
      expect(find.text('التنبيهات'), findsOneWidget);
      expect(find.text('تمّت المراجعة'), findsOneWidget);
      expect(find.text('يحتاج مراجعة / ملاحظة'), findsWidgets);
      await tester.scrollUntilVisible(
        find.text('مدفوعات ERP'),
        500,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      expect(find.text('مدفوعات ERP'), findsOneWidget);
      expect(find.text('PAY-PENDING'), findsOneWidget);
      expect(find.text('نقد'), findsOneWidget);
      expect(find.text('إعادة المحاولة'), findsWidgets);
      await tester.scrollUntilVisible(
        find.text('Payment account missing'),
        500,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();

      expect(find.text('Payment account missing'), findsOneWidget);
      expect(find.text('ACC-PAY-1'), findsOneWidget);
    },
  );
}

Map<String, dynamic> _order(
  String name,
  String status, {
  String? error,
  String? salesOrder,
  int? salesOrderDocstatus,
  String? invoiceStatus,
  String? invoiceError,
  String? salesInvoice,
  String deliveryStatus = 'ready_for_dispatch',
}) {
  return {
    'name': name,
    'customer_name': 'عميل $name',
    'subtotal': 12.5,
    'order_status': 'approved',
    'delivery_status': deliveryStatus,
    'erp_sync_status': status,
    'erp_sync_error': error,
    'erp_sales_order': salesOrder,
    'erp_sales_order_docstatus': salesOrderDocstatus,
    'erp_sales_invoice': salesInvoice,
    'erp_invoice_sync_status': invoiceStatus ?? 'pending',
    'erp_invoice_sync_error': invoiceError,
    'erp_invoice_created_at': salesInvoice == null
        ? null
        : '2026-05-20 12:00:00',
    'approved_at': '2026-05-19 12:00:00',
    'approved_by': 'branch.supervisor@example.com',
  };
}

Map<String, dynamic> _payment(
  String name,
  String status, {
  String method = 'cash',
  String? error,
  String? paymentEntry,
}) {
  return {
    'name': name,
    'madar_order': 'MADAR-ORD-1',
    'customer_name': 'عميل الدفع',
    'amount': 40,
    'payment_method': method,
    'payment_status': 'collected',
    'erp_sync_status': status,
    'erp_sync_error': error,
    'erp_payment_entry': paymentEntry,
    'erp_sales_order': 'SAL-ORD-1',
    'reference_no': 'REF-1',
  };
}

Map<String, dynamic> _accountingSummary(
  String orderName,
  String status, {
  List<String> alerts = const [],
  String? notes,
}) {
  return {
    'order': {
      'name': orderName,
      'customer_name': 'عميل $orderName',
      'subtotal': 100,
      'paid_amount': status == 'ready_for_review' || status == 'reviewed'
          ? 100
          : 40,
      'remaining_amount': status == 'ready_for_review' || status == 'reviewed'
          ? 0
          : 60,
      'payment_status': status == 'ready_for_review' || status == 'reviewed'
          ? 'paid'
          : 'partially_paid',
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
      'erp_invoice_sync_status': 'synced',
      'erp_invoice_sync_error': null,
    },
    'payments': {
      'count': 1,
      'total_collected': status == 'ready_for_review' || status == 'reviewed'
          ? 100
          : 40,
      'methods': {'cash': 40},
      'erp_sync_statuses': {'synced': 1},
      'items': [],
    },
    'cashbox': {
      'cash_payments_total': 40,
      'cashbox_names': ['CASHBOX-1'],
      'statuses': status == 'needs_attention' ? ['submitted'] : ['approved'],
      'reviewed': status != 'needs_attention',
    },
    'readiness': {
      'has_erp_sales_order': true,
      'sales_order_submitted': true,
      'delivered_or_picked_up': true,
      'has_sales_invoice_draft': true,
      'payments_match_order_total': status != 'needs_attention',
      'payment_entries_synced_or_not_required': true,
      'cashboxes_reviewed_for_cash_payments': status != 'needs_attention',
    },
    'alerts': alerts,
    'accounting_status': status,
    'accounting_review_notes': notes,
    'accounting_reviewed_by': null,
    'accounting_reviewed_at': null,
  };
}
