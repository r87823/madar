import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/notifications/notification_models.dart';
import 'package:madar/features/notifications/notification_screen.dart';

void main() {
  test('notification models parse list and unread count envelopes', () {
    final list = NotificationList.fromEnvelope({
      'ok': true,
      'data': {
        'items': [_notificationMap()],
      },
      'error': null,
    });
    final count = NotificationUnreadCount.fromEnvelope({
      'ok': true,
      'data': {'unread_count': 3},
      'error': null,
    });

    expect(list.items.single.title, 'طلب جديد بانتظار الاعتماد');
    expect(list.items.single.isRead, isFalse);
    expect(list.items.single.routeKey, 'order_detail');
    expect(list.items.single.routeParams['order_name'], 'MADAR-ORD-1');
    expect(list.items.single.actionLabel, 'عرض الطلب');
    expect(count.unreadCount, 3);
  });

  testWidgets('dashboard notification icon opens notifications', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'employee.test@example.com',
              fullName: 'Employee',
              roles: ['Madar Employee'],
              permissions: ['employee_services.view_self'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
            unreadNotifications: 2,
            onOpenNotifications: () {
              opened = true;
            },
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {},
            onOpenWorkOrders: () {},
          ),
        ),
      ),
    );

    expect(find.text('2'), findsOneWidget);
    await tester.tap(find.byTooltip('الإشعارات'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('notification screen renders Arabic items and opens route', (
    tester,
  ) async {
    final requests = <http.Request>[];
    MadarNotification? openedNotification;
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        requests.add(request);
        if (request.url.path.endsWith('list_notifications')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_notificationMap()],
              },
              'error': null,
            },
          });
        }
        if (request.url.path.endsWith('mark_notification_read')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {..._notificationMap(), 'is_read': 1},
              'error': null,
            },
          });
        }
        if (request.url.path.endsWith('mark_all_notifications_read')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {'updated': 1},
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': {'unread_count': 1},
            'error': null,
          },
        });
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: NotificationScreen(
            apiClient: client,
            onOpenNotification: (notification) async {
              openedNotification = notification;
              return true;
            },
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('الإشعارات'), findsOneWidget);
    expect(find.text('طلب جديد بانتظار الاعتماد'), findsOneWidget);
    expect(find.text('غير مقروء'), findsOneWidget);
    expect(find.text('فتح'), findsOneWidget);
    expect(find.text('عرض الطلب'), findsOneWidget);

    await tester.tap(find.text('فتح'));
    await tester.pumpAndSettle();

    expect(
      requests.any((request) => request.url.path.endsWith('mark_notification_read')),
      isTrue,
    );
    expect(openedNotification?.routeKey, 'order_detail');
  });

  testWidgets('blocked notification route shows safe Arabic error', (
    tester,
  ) async {
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        if (request.url.path.endsWith('list_notifications')) {
          return _jsonResponse({
            'message': {
              'ok': true,
              'data': {
                'items': [_notificationMap()],
              },
              'error': null,
            },
          });
        }
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': {..._notificationMap(), 'is_read': 1},
            'error': null,
          },
        });
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: NotificationScreen(
            apiClient: client,
            onOpenNotification: (_) async => false,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('فتح'));
    await tester.pumpAndSettle();

    expect(
      find.text('لا يمكن فتح هذا العنصر أو لا تملك صلاحية الوصول'),
      findsOneWidget,
    );
  });

  testWidgets('notification screen shows empty state', (tester) async {
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        return _jsonResponse({
          'message': {
            'ok': true,
            'data': {'items': []},
            'error': null,
          },
        });
      }),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: NotificationScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('لا توجد إشعارات'), findsOneWidget);
  });
}

Map<String, dynamic> _notificationMap() {
  return {
    'name': 'NOTIF-1',
    'recipient_user': 'employee.test@example.com',
    'title': 'طلب جديد بانتظار الاعتماد',
    'message': 'تم إرسال الطلب MADAR-ORD-1 للاعتماد.',
    'event_type': 'order_submitted',
    'entity_type': 'Madar Order',
    'entity_name': 'MADAR-ORD-1',
    'is_read': 0,
    'read_at': null,
    'created_at': '2026-05-20 12:00:00',
    'priority': 'normal',
    'route_key': 'order_detail',
    'route_params': {'order_name': 'MADAR-ORD-1'},
    'action_label': 'عرض الطلب',
    'deep_link_status': '',
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
