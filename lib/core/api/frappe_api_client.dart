import 'dart:convert';

import 'package:http/http.dart' as http;

import '../auth/session_store.dart';
import '../auth/user_context.dart';
import '../../features/attendance/attendance_status.dart';
import 'http_client_factory.dart';

class FrappeApiClient {
  FrappeApiClient({
    required this.baseUri,
    http.Client? httpClient,
    SessionStore? sessionStore,
  }) : _httpClient = httpClient ?? createHttpClient(),
       _sessionStore = sessionStore ?? MemorySessionStore();

  static final staging = Uri.parse('https://madar-test.r8787m.cc');

  final Uri baseUri;
  final http.Client _httpClient;
  final SessionStore _sessionStore;

  Future<void> login({
    required String username,
    required String password,
  }) async {
    final response = await _httpClient.post(
      _methodUri('login'),
      headers: _headers(),
      body: {'usr': username, 'pwd': password},
    );
    _throwIfFailed(response, fallback: 'تعذر تسجيل الدخول');
    final sid = _extractSid(response.headers['set-cookie']);
    if (sid != null) {
      await _sessionStore.saveSid(sid);
    }
  }

  Future<UserContext> getContext() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.me.get_context'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل بيانات المستخدم');
    return UserContext.fromFrappeMessage(_decodeJson(response));
  }

  Future<void> logout() async {
    await _httpClient.get(_methodUri('logout'), headers: _headers());
    await _sessionStore.clear();
  }

  Future<AttendanceStatus> getAttendanceStatus() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.attendance.get_status'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل حالة الحضور');
    return _attendanceFromResponse(response);
  }

  Future<AttendanceHistory> getAttendanceHistory() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.attendance.get_history'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل سجل الحضور');
    return _attendanceHistoryFromResponse(response);
  }

  Future<AttendanceStatus> checkIn() async {
    final response = await _httpClient.post(
      _methodUri('madar.api.attendance.check_in'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تسجيل الحضور');
    return _attendanceFromResponse(response);
  }

  Future<AttendanceStatus> checkOut() async {
    final response = await _httpClient.post(
      _methodUri('madar.api.attendance.check_out'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تسجيل الانصراف');
    return _attendanceFromResponse(response);
  }

  Uri _methodUri(String method) {
    return baseUri.replace(path: '/api/method/$method', query: '');
  }

  Map<String, String> _headers() {
    final sid = _sessionStore.sid;
    return {
      'accept': 'application/json',
      if (sid != null && sid.isNotEmpty) 'cookie': 'sid=$sid',
    };
  }

  Map<String, dynamic> _decodeJson(http.Response response) {
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    if (decoded is Map) {
      return decoded.map((key, value) => MapEntry('$key', value));
    }
    return <String, dynamic>{};
  }

  AttendanceStatus _attendanceFromResponse(http.Response response) {
    final payload = _decodeJson(response);
    final message = payload['message'];
    final map = message is Map
        ? message.map((key, value) => MapEntry('$key', value))
        : payload;
    if (map['ok'] == false) {
      final error = map['error'];
      final message = error is Map ? error['message'] : null;
      throw FrappeApiException(message?.toString() ?? 'تعذر تنفيذ العملية');
    }
    return AttendanceStatus.fromEnvelope(map);
  }

  AttendanceHistory _attendanceHistoryFromResponse(http.Response response) {
    final payload = _decodeJson(response);
    final message = payload['message'];
    final map = message is Map
        ? message.map((key, value) => MapEntry('$key', value))
        : payload;
    if (map['ok'] == false) {
      final error = map['error'];
      final message = error is Map ? error['message'] : null;
      throw FrappeApiException(message?.toString() ?? 'تعذر تنفيذ العملية');
    }
    return AttendanceHistory.fromEnvelope(map);
  }

  void _throwIfFailed(http.Response response, {required String fallback}) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    throw FrappeApiException(fallback, statusCode: response.statusCode);
  }

  String? _extractSid(String? setCookie) {
    if (setCookie == null || setCookie.isEmpty) return null;
    final match = RegExp(r'(^|,\s*)sid=([^;,\s]+)').firstMatch(setCookie);
    return match?.group(2);
  }
}

class FrappeApiException implements Exception {
  const FrappeApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}
