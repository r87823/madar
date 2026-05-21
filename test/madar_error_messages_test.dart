import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:madar/core/api/frappe_api_client.dart';
import 'package:madar/core/auth/session_store.dart';
import 'package:madar/core/errors/madar_error_messages.dart';
import 'package:madar/core/messages/madar_success_messages.dart';

void main() {
  test('known backend error code maps to Arabic message', () {
    expect(
      MadarErrorMessages.fromCode('PERMISSION_DENIED'),
      'لا تملك صلاحية تنفيذ هذا الإجراء',
    );
    expect(
      arabicMessageForError('ORDER_HAS_NO_ITEMS'),
      'لا يمكن إرسال الطلب بدون أصناف',
    );
  });

  test('unknown error maps to generic Arabic message', () {
    expect(
      arabicMessageForError(Exception('Traceback: sensitive ERP details')),
      'حدث خطأ غير متوقع، حاول مرة أخرى',
    );
    expect(
      arabicMessageForError(const FrappeApiException('Customer missing')),
      'حدث خطأ غير متوقع، حاول مرة أخرى',
    );
  });

  test('network error maps to Arabic network message', () {
    expect(
      arabicMessageForError(
        http.ClientException(
          'Connection closed before full header was received',
        ),
      ),
      'تعذر الاتصال بالخادم',
    );
  });

  test('api client preserves backend error code for UI translation', () async {
    final client = FrappeApiClient(
      baseUri: Uri.parse('https://madar-test.r8787m.cc'),
      sessionStore: MemorySessionStore(sid: 'abc123'),
      httpClient: MockClient((request) async {
        return http.Response.bytes(
          utf8.encode(
            jsonEncode({
              'message': {
                'ok': false,
                'data': null,
                'error': {
                  'code': 'ORDER_HAS_NO_ITEMS',
                  'message': 'ORDER_HAS_NO_ITEMS',
                },
              },
            }),
          ),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

    expect(
      () => client.submitOrder('MADAR-ORD-1'),
      throwsA(
        isA<FrappeApiException>()
            .having((error) => error.code, 'code', 'ORDER_HAS_NO_ITEMS')
            .having(
              arabicMessageForError,
              'Arabic message',
              'لا يمكن إرسال الطلب بدون أصناف',
            ),
      ),
    );
  });

  test('success messages are centralized Arabic strings', () {
    expect(MadarSuccessMessages.paymentCollected, 'تم تحصيل الدفع بنجاح');
    expect(MadarSuccessMessages.settingSaved, 'تم حفظ الإعداد بنجاح');
  });
}
