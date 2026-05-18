import 'package:flutter/foundation.dart';

import '../api/frappe_api_client.dart';
import 'user_context.dart';

class AuthController extends ChangeNotifier {
  AuthController({required FrappeApiClient apiClient}) : _apiClient = apiClient;

  final FrappeApiClient _apiClient;

  UserContext? _context;
  bool _isLoading = false;
  String? _errorMessage;

  UserContext? get context => _context;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> login({
    required String username,
    required String password,
  }) async {
    _setLoading(true);
    _errorMessage = null;
    try {
      await _apiClient.login(username: username.trim(), password: password);
      _context = await _apiClient.getContext();
    } catch (_) {
      _errorMessage = 'تعذر تسجيل الدخول. تأكد من البريد وكلمة المرور.';
    } finally {
      _setLoading(false);
    }
  }

  Future<void> logout() async {
    _setLoading(true);
    try {
      await _apiClient.logout();
    } finally {
      _context = null;
      _errorMessage = null;
      _setLoading(false);
    }
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }
}
