import 'dart:convert';

import 'package:http/http.dart' as http;

import '../auth/session_store.dart';
import '../auth/user_context.dart';
import '../../features/accounting/erp_sync_models.dart';
import '../../features/attendance/attendance_status.dart';
import '../../features/orders/items/order_item_models.dart';
import '../../features/orders/items/product_models.dart';
import '../../features/orders/order_models.dart';
import '../../features/production/production_mapping_models.dart';
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

  Future<OrderList> listOrders() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.orders.list_orders'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل الطلبات');
    return OrderList.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> getOrder(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.get_order'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل الطلب');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> createOrderDraft({
    required String customerName,
    required String customerPhone,
    required String notes,
  }) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.create_draft'),
      headers: _headers(),
      body: {
        'customer_name': customerName,
        'customer_phone': customerPhone,
        'notes': notes,
      },
    );
    _throwIfFailed(response, fallback: 'تعذر إنشاء الطلب');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> submitOrder(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.submit_order'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر إرسال الطلب');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> cancelOrder(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.cancel_order'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر إلغاء الطلب');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<OrderList> listApprovalQueue() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.orders.list_approval_queue'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل طلبات الاعتماد');
    return OrderList.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> approveOrder(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.approve_order'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر اعتماد الطلب');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> returnOrderForEdit(
    String orderName, {
    required String reason,
  }) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.return_order_for_edit'),
      headers: _headers(),
      body: {'order_name': orderName, 'reason': reason},
    );
    _throwIfFailed(response, fallback: 'تعذر إعادة الطلب للتعديل');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<MadarOrder> rejectOrder(
    String orderName, {
    required String reason,
  }) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.orders.reject_order'),
      headers: _headers(),
      body: {'order_name': orderName, 'reason': reason},
    );
    _throwIfFailed(response, fallback: 'تعذر رفض الطلب');
    return MadarOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<ErpSyncOrderList> listErpSyncOrders() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.erp_sync.list_sync_orders'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل سجل المزامنة');
    return ErpSyncOrderList.fromEnvelope(_safeEnvelope(response));
  }

  Future<ErpSyncOrder> getErpSyncOrder(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.erp_sync.get_sync_order'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل تفاصيل المزامنة');
    return ErpSyncOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<ErpSyncOrder> retryErpSyncOrder(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.erp_sync.retry_sync_order'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر إعادة محاولة المزامنة');
    return ErpSyncOrder.fromEnvelope(_safeEnvelope(response));
  }

  Future<ProductList> listProducts({String search = ''}) async {
    final response = await _httpClient.get(
      baseUri.replace(
        path: '/api/method/madar.api.catalog.list_products',
        queryParameters: search.isEmpty ? null : {'search': search},
      ),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل المنتجات');
    return ProductList.fromEnvelope(_safeEnvelope(response));
  }

  Future<ProductionCenterList> listProductionCenters() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.production_mapping.list_production_centers'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل مراكز الإنتاج');
    return ProductionCenterList.fromEnvelope(_safeEnvelope(response));
  }

  Future<ProductionDepartmentList> listProductionDepartments({
    String productionCenter = '',
  }) async {
    final response = await _httpClient.get(
      baseUri.replace(
        path:
            '/api/method/madar.api.production_mapping.list_production_departments',
        queryParameters: productionCenter.isEmpty
            ? null
            : {'production_center': productionCenter},
      ),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل أقسام الإنتاج');
    return ProductionDepartmentList.fromEnvelope(_safeEnvelope(response));
  }

  Future<ProductionMappingList> listItemDepartmentMappings() async {
    final response = await _httpClient.get(
      _methodUri('madar.api.production_mapping.list_item_department_mappings'),
      headers: _headers(),
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل ربط الأصناف');
    return ProductionMappingList.fromEnvelope(_safeEnvelope(response));
  }

  Future<ProductionCenter> createOrUpdateProductionCenter({
    required String centerName,
    required String centerCode,
    bool isActive = true,
  }) async {
    final response = await _httpClient.post(
      _methodUri(
        'madar.api.production_mapping.create_or_update_production_center',
      ),
      headers: _headers(),
      body: {
        'center_name': centerName,
        'center_code': centerCode,
        'is_active': isActive ? '1' : '0',
      },
    );
    _throwIfFailed(response, fallback: 'تعذر حفظ مركز الإنتاج');
    final data = _safeEnvelope(response)['data'];
    return ProductionCenter.fromMap(_map(data));
  }

  Future<ProductionDepartment> createOrUpdateProductionDepartment({
    required String departmentName,
    required String departmentCode,
    required String productionCenter,
    bool isActive = true,
  }) async {
    final response = await _httpClient.post(
      _methodUri(
        'madar.api.production_mapping.create_or_update_production_department',
      ),
      headers: _headers(),
      body: {
        'department_name': departmentName,
        'department_code': departmentCode,
        'production_center': productionCenter,
        'is_active': isActive ? '1' : '0',
      },
    );
    _throwIfFailed(response, fallback: 'تعذر حفظ قسم الإنتاج');
    final data = _safeEnvelope(response)['data'];
    return ProductionDepartment.fromMap(_map(data));
  }

  Future<ProductionMapping> createOrUpdateItemDepartmentMapping({
    required String itemCode,
    required String productionCenter,
    required String productionDepartment,
    bool isActive = true,
  }) async {
    final response = await _httpClient.post(
      _methodUri(
        'madar.api.production_mapping.create_or_update_item_department_mapping',
      ),
      headers: _headers(),
      body: {
        'item_code': itemCode,
        'production_center': productionCenter,
        'production_department': productionDepartment,
        'is_active': isActive ? '1' : '0',
      },
    );
    _throwIfFailed(response, fallback: 'تعذر حفظ ربط الصنف');
    return ProductionMapping.fromEnvelope(_safeEnvelope(response));
  }

  Future<OrderDepartmentMappingValidation> validateOrderDepartmentMappings(
    String orderName,
  ) async {
    final response = await _httpClient.post(
      _methodUri(
        'madar.api.production_mapping.validate_order_department_mappings',
      ),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر التحقق من ربط الإنتاج');
    return OrderDepartmentMappingValidation.fromEnvelope(
      _safeEnvelope(response),
    );
  }

  Future<OrderItemList> listOrderItems(String orderName) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.order_items.list_order_items'),
      headers: _headers(),
      body: {'order_name': orderName},
    );
    _throwIfFailed(response, fallback: 'تعذر تحميل أصناف الطلب');
    return OrderItemList.fromEnvelope(_safeEnvelope(response));
  }

  Future<OrderItemList> addOrderItem({
    required String orderName,
    required String itemCode,
    required double qty,
    String notes = '',
  }) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.order_items.add_item'),
      headers: _headers(),
      body: {
        'order_name': orderName,
        'item_code': itemCode,
        'qty': qty.toString(),
        'notes': notes,
      },
    );
    _throwIfFailed(response, fallback: 'تعذر إضافة الصنف');
    return OrderItemList.fromEnvelope(_normalizeItemMutationEnvelope(response));
  }

  Future<OrderItemList> updateOrderItemQty({
    required String orderName,
    required String itemName,
    required double qty,
  }) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.order_items.update_item_qty'),
      headers: _headers(),
      body: {
        'order_name': orderName,
        'item_name': itemName,
        'qty': qty.toString(),
      },
    );
    _throwIfFailed(response, fallback: 'تعذر تعديل الكمية');
    return OrderItemList.fromEnvelope(_normalizeItemMutationEnvelope(response));
  }

  Future<OrderItemList> removeOrderItem({
    required String orderName,
    required String itemName,
  }) async {
    final response = await _httpClient.post(
      _methodUri('madar.api.order_items.remove_item'),
      headers: _headers(),
      body: {'order_name': orderName, 'item_name': itemName},
    );
    _throwIfFailed(response, fallback: 'تعذر حذف الصنف');
    return OrderItemList.fromEnvelope(_safeEnvelope(response));
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

  Map<String, dynamic> _safeEnvelope(http.Response response) {
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
    return map;
  }

  Map<String, dynamic> _map(Object? value) {
    return value is Map
        ? value.map((key, value) => MapEntry('$key', value))
        : <String, dynamic>{};
  }

  Map<String, dynamic> _normalizeItemMutationEnvelope(http.Response response) {
    final map = _safeEnvelope(response);
    final data = map['data'];
    if (data is Map && data['item'] != null && data['items'] == null) {
      return {
        ...map,
        'data': {
          ...data.map((key, value) => MapEntry('$key', value)),
          'items': [data['item']],
        },
      };
    }
    return map;
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
