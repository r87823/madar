import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/core/permissions/dashboard_cards.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/production/production_mapping_screen.dart';

void main() {
  test('production manage permission shows production settings card', () {
    final titles = DashboardCardsForTest.visibleTitles({
      'production.manage_mappings',
    });

    expect(titles, contains('إعدادات الإنتاج'));
  });

  testWidgets('production dashboard card opens mapping screen', (tester) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'admin@example.com',
              fullName: 'Admin',
              roles: ['Madar Admin'],
              permissions: ['production.manage_mappings'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
            onLogout: () async {},
            onOpenAttendance: () {},
            onOpenOrders: () {},
            onOpenApprovalQueue: () {},
            onOpenErpSyncReview: () {},
            onOpenProductionMappings: () {
              opened = true;
            },
          ),
        ),
      ),
    );

    await tester.tap(find.text('إعدادات الإنتاج'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets(
    'production mapping screen lists mappings and can save selected mapping',
    (tester) async {
      final requests = <http.Request>[];
      final client = FrappeApiClient(
        baseUri: Uri.parse('https://madar-test.r8787m.cc'),
        sessionStore: MemorySessionStore(sid: 'abc123'),
        httpClient: MockClient((request) async {
          requests.add(request);
          if (request.url.path.endsWith('list_production_centers')) {
            return _jsonResponse({
              'message': _listEnvelope([_centerMap()]),
            });
          }
          if (request.url.path.endsWith('list_production_departments')) {
            return _jsonResponse({
              'message': _listEnvelope([_departmentMap()]),
            });
          }
          if (request.url.path.endsWith('list_item_department_mappings')) {
            return _jsonResponse({
              'message': _listEnvelope([_mappingMap()]),
            });
          }
          if (request.url.path.endsWith('list_products')) {
            return _jsonResponse({
              'message': _listEnvelope([
                {
                  'item_code': 'MILK-001',
                  'item_name': 'Milk',
                  'stock_uom': 'Nos',
                  'disabled': 0,
                  'image': null,
                  'default_price': 12.5,
                },
              ]),
            });
          }
          return _jsonResponse({
            'message': {'ok': true, 'data': _mappingMap(), 'error': null},
          });
        }),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Directionality(
            textDirection: TextDirection.rtl,
            child: ProductionMappingScreen(apiClient: client),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('إعدادات الإنتاج'), findsOneWidget);
      await tester.drag(find.byType(ListView), const Offset(0, -420));
      await tester.pumpAndSettle();
      expect(find.text('Milk'), findsWidgets);
      expect(find.text('MAIN / MILK'), findsOneWidget);

      await tester.tap(find.text('حفظ الربط'));
      await tester.pumpAndSettle();

      expect(
        requests.any(
          (request) => request.url.path.endsWith(
            'create_or_update_item_department_mapping',
          ),
        ),
        isTrue,
      );
      await tester.drag(find.byType(ListView), const Offset(0, 420));
      await tester.pumpAndSettle();
      expect(find.text('تم حفظ الربط'), findsOneWidget);
    },
  );
}

class DashboardCardsForTest {
  static List<String> visibleTitles(Set<String> permissions) {
    return DashboardCards.visibleFor(
      permissions,
    ).map((card) => card.title).toList(growable: false);
  }
}

Map<String, dynamic> _listEnvelope(List<Map<String, dynamic>> items) {
  return {
    'ok': true,
    'data': {'items': items},
    'error': null,
  };
}

Map<String, dynamic> _centerMap() {
  return {
    'name': 'MAIN',
    'center_name': 'Main',
    'center_code': 'MAIN',
    'is_active': 1,
  };
}

Map<String, dynamic> _departmentMap() {
  return {
    'name': 'MILK',
    'department_name': 'Milk',
    'department_code': 'MILK',
    'production_center': 'MAIN',
    'is_active': 1,
  };
}

Map<String, dynamic> _mappingMap() {
  return {
    'name': 'MILK-001',
    'item_code': 'MILK-001',
    'item_name': 'Milk',
    'production_center': 'MAIN',
    'production_department': 'MILK',
    'is_active': 1,
  };
}

http.Response _jsonResponse(Map<String, dynamic> payload) {
  return http.Response.bytes(
    utf8.encode(jsonEncode(payload)),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}
