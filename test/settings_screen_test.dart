import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/auth/user_context.dart';
import 'package:madar/features/dashboard/dashboard_screen.dart';
import 'package:madar/features/settings/settings_models.dart';
import 'package:madar/features/settings/settings_screen.dart';

void main() {
  test('settings list parses non-secret settings', () {
    final list = SettingsList.fromEnvelope(_settingsEnvelope());

    expect(
      list.items.map((item) => item.settingKey),
      contains('payments.allow_overpayment'),
    );
    expect(
      list.items.any((item) => item.settingKey.contains('secret')),
      isFalse,
    );
  });

  testWidgets('settings card is visible for admin and opens screen', (
    tester,
  ) async {
    var opened = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'Administrator',
              fullName: 'Administrator',
              roles: ['Administrator'],
              permissions: ['system.full_access'],
              scopes: ScopeContext(branchNames: ['*'], departmentNames: ['*']),
            ),
            onOpenSettings: () {
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

    await tester.ensureVisible(find.text('الإعدادات'));
    await tester.tap(find.text('الإعدادات'));
    await tester.pump();

    expect(opened, isTrue);
  });

  testWidgets('settings card is hidden for non-admin employee', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: DashboardScreen(
            context: const UserContext(
              user: 'employee.test@example.com',
              fullName: 'Employee',
              roles: ['Madar Employee'],
              permissions: ['attendance.check_in'],
              scopes: ScopeContext(branchNames: [], departmentNames: []),
            ),
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

    expect(find.text('الإعدادات'), findsNothing);
  });

  testWidgets('settings screen renders Arabic sections and saves setting', (
    tester,
  ) async {
    final client = _client();

    await tester.pumpWidget(
      MaterialApp(
        home: Directionality(
          textDirection: TextDirection.rtl,
          child: SettingsScreen(apiClient: client),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('الإعدادات'), findsOneWidget);
    expect(find.text('إعدادات المدفوعات'), findsOneWidget);
    expect(find.text('السماح بالدفع الزائد'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('setting-payments.allow_overpayment')),
    );
    await tester.pumpAndSettle();

    expect(find.text('تم الحفظ'), findsOneWidget);
  });
}

FrappeApiClient _client() {
  return FrappeApiClient(
    baseUri: Uri.parse('https://madar-test.r8787m.cc'),
    sessionStore: MemorySessionStore(sid: 'abc123'),
    httpClient: MockClient((request) async {
      if (request.url.path.endsWith('get_settings')) {
        return _json(_settingsEnvelope());
      }
      if (request.url.path.endsWith('update_setting')) {
        return _json({
          'ok': true,
          'data': {
            'setting_key': request.bodyFields['setting_key'],
            'value': true,
            'value_type': 'bool',
            'category': 'payments',
            'label_ar': 'السماح بالدفع الزائد',
            'description_ar': '',
            'is_editable': true,
          },
          'error': null,
        });
      }
      return _json(_settingsEnvelope());
    }),
  );
}

http.Response _json(Map<String, dynamic> message) {
  return http.Response.bytes(
    utf8.encode(jsonEncode({'message': message})),
    200,
    headers: {'content-type': 'application/json; charset=utf-8'},
  );
}

Map<String, dynamic> _settingsEnvelope() {
  return {
    'ok': true,
    'data': {
      'items': [
        {
          'setting_key': 'app.default_language',
          'value': 'ar',
          'value_type': 'string',
          'category': 'general',
          'label_ar': 'اللغة الافتراضية',
          'description_ar': 'لغة واجهة مدار الافتراضية.',
          'is_editable': true,
        },
        {
          'setting_key': 'payments.allow_overpayment',
          'value': false,
          'value_type': 'bool',
          'category': 'payments',
          'label_ar': 'السماح بالدفع الزائد',
          'description_ar': '',
          'is_editable': true,
        },
        {
          'setting_key': 'payments.enabled_methods',
          'value': ['cash', 'card', 'transfer', 'online'],
          'value_type': 'json',
          'category': 'payments',
          'label_ar': 'طرق الدفع المفعلة',
          'description_ar': '',
          'is_editable': true,
        },
      ],
    },
    'error': null,
  };
}
