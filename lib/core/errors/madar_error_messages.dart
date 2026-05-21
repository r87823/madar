import 'package:http/http.dart' as http;

import '../api/frappe_api_client.dart';

class MadarErrorMessages {
  static const generic = 'حدث خطأ غير متوقع، حاول مرة أخرى';
  static const network = 'تعذر الاتصال بالخادم';

  static const Map<String, String> _messages = {
    'AUTH_REQUIRED': 'يجب تسجيل الدخول أولًا',
    'PERMISSION_DENIED': 'لا تملك صلاحية تنفيذ هذا الإجراء',
    'OUT_OF_SCOPE': 'لا يمكنك الوصول إلى هذا السجل خارج نطاقك',
    'VALIDATION_FAILED': 'يرجى التحقق من البيانات المدخلة',
    'NOT_FOUND': 'لم يتم العثور على السجل',
    'SERVER_ERROR': generic,
    'NETWORK_ERROR': network,
    'SESSION_EXPIRED': 'انتهت الجلسة، يرجى تسجيل الدخول مرة أخرى',
    'EMPLOYEE_NOT_LINKED': 'لا يوجد موظف مرتبط بحسابك',
    'EMPLOYEE_CHECKIN_UNAVAILABLE': 'خدمة الحضور غير متاحة حاليًا',
    'DUPLICATE_CHECKIN': 'تم تسجيل نفس الحركة مؤخرًا',
    'ALREADY_CHECKED_IN': 'أنت مسجل حضور بالفعل',
    'ALREADY_CHECKED_OUT': 'أنت خارج الدوام بالفعل',
    'ORDER_NOT_FOUND': 'لم يتم العثور على الطلب',
    'ORDER_NOT_EDITABLE': 'لا يمكن تعديل هذا الطلب في حالته الحالية',
    'ORDER_HAS_NO_ITEMS': 'لا يمكن إرسال الطلب بدون أصناف',
    'INVALID_ORDER_TRANSITION':
        'لا يمكن تنفيذ هذه الحركة على الطلب في حالته الحالية',
    'ORDER_NOT_APPROVED': 'الطلب غير معتمد بعد',
    'ORDER_ALREADY_SYNCED': 'تمت مزامنة الطلب مسبقًا',
    'ITEM_DEPARTMENT_MAPPING_MISSING': 'يوجد صنف غير مربوط بقسم إنتاج',
    'MISSING_DEPARTMENT_MAPPING': 'يوجد صنف غير مربوط بقسم إنتاج',
    'WORK_ORDER_NOT_FOUND': 'لم يتم العثور على أمر الإنتاج',
    'INVALID_WORK_ORDER_TRANSITION':
        'لا يمكن تنفيذ هذه الحركة على أمر الإنتاج في حالته الحالية',
    'REASON_REQUIRED': 'يجب إدخال السبب',
    'FULFILLMENT_METHOD_REQUIRED': 'يجب تحديد طريقة الاستلام',
    'DESTINATION_BRANCH_REQUIRED': 'يجب تحديد فرع الاستلام',
    'INVALID_DELIVERY_TRANSITION':
        'لا يمكن تنفيذ هذه الحركة على حالة التوصيل الحالية',
    'ORDER_NOT_READY_FOR_DISPATCH': 'الطلب غير جاهز للإرسال',
    'DELIVERY_BATCH_NOT_FOUND': 'لم يتم العثور على دفعة التوصيل',
    'MIXED_DESTINATION_BRANCHES':
        'لا يمكن جمع طلبات لفروع مختلفة في نفس الدفعة',
    'MIXED_FULFILLMENT_METHODS': 'لا يمكن خلط طرق تسليم مختلفة في نفس الدفعة',
    'NON_READY_ORDER_IN_BATCH': 'يوجد طلب غير جاهز ضمن الدفعة',
    'PAYMENT_AMOUNT_INVALID': 'مبلغ الدفع غير صحيح',
    'PAYMENT_EXCEEDS_REMAINING_AMOUNT': 'مبلغ الدفع يتجاوز المتبقي',
    'PAYMENT_METHOD_INVALID': 'طريقة الدفع غير صحيحة',
    'PAYMENT_ALREADY_SYNCED': 'تمت مزامنة الدفع مسبقًا',
    'ORDER_NOT_PAYABLE': 'لا يمكن تحصيل الدفع لهذا الطلب في حالته الحالية',
    'CASHBOX_NOT_FOUND': 'لم يتم العثور على الصندوق',
    'CASHBOX_ALREADY_SUBMITTED': 'تم إرسال الصندوق للمراجعة مسبقًا',
    'CASHBOX_ALREADY_APPROVED': 'تم اعتماد الصندوق ولا يمكن تعديله',
    'CASHBOX_NOT_SUBMITTED': 'الصندوق لم يُرسل للمراجعة بعد',
    'CASHBOX_RETURN_REASON_REQUIRED': 'يجب إدخال سبب الإرجاع',
    'CASHBOX_SUBMITTED_CASH_INVALID': 'المبلغ المسلم غير صحيح',
    'CASHBOX_NOT_APPROVED': 'يجب اعتماد الصندوق أولًا',
    'ERP_SYNC_FAILED': 'فشلت مزامنة ERP، يرجى المراجعة',
    'ORDER_NOT_SYNCED_TO_ERP': 'الطلب لم تتم مزامنته مع ERP بعد',
    'ERP_INVOICE_SYNC_FAILED': 'فشل إنشاء فاتورة ERP',
    'SALES_INVOICE_NOT_SYNCED': 'فاتورة ERP لم يتم إنشاؤها بعد',
    'SALES_INVOICE_ALREADY_SYNCED': 'تم إنشاء فاتورة ERP مسبقًا',
    'SALES_INVOICE_ALREADY_SUBMITTED': 'تم اعتماد فاتورة ERP مسبقًا',
    'SALES_INVOICE_SUBMIT_FAILED': 'فشل اعتماد فاتورة ERP',
    'PAYMENT_ENTRY_NOT_SYNCED': 'سند الدفع لم تتم مزامنته مع ERP بعد',
    'PAYMENT_ENTRY_ALREADY_SUBMITTED': 'تم اعتماد سند الدفع مسبقًا',
    'PAYMENT_ENTRY_SUBMIT_FAILED': 'فشل اعتماد سند الدفع',
    'ORDER_NOT_READY_FOR_FINAL_SUBMIT': 'الطلب غير جاهز للإقفال النهائي',
    'ACCOUNTING_FINALIZE_PERMISSION_DENIED': 'لا تملك صلاحية الإقفال المحاسبي',
    'ERP_DOCUMENT_MISSING': 'مستند ERP المطلوب غير موجود',
    'ERP_FINALIZATION_FAILED': 'فشل الإقفال المحاسبي',
    'ORDER_NOT_DELIVERED': 'الطلب لم يتم تسليمه بعد',
    'ORDER_NOT_PAID': 'الطلب غير مدفوع بالكامل',
    'NOTIFICATION_NOT_FOUND': 'لم يتم العثور على الإشعار',
    'NOTIFICATION_ACCESS_DENIED': 'لا يمكنك الوصول إلى هذا الإشعار',
    'SETTING_NOT_FOUND': 'لم يتم العثور على الإعداد',
    'SETTING_NOT_EDITABLE': 'هذا الإعداد غير قابل للتعديل',
    'SETTING_SECRET_NOT_READABLE': 'لا يمكن عرض هذا الإعداد',
    'SETTING_VALUE_INVALID': 'قيمة الإعداد غير صحيحة',
  };

  static String fromCode(String? code, {String? fallback}) {
    final normalized = _normalizeCode(code);
    if (normalized != null && _messages.containsKey(normalized)) {
      return _messages[normalized]!;
    }
    if (fallback != null && _looksArabic(fallback)) return fallback;
    return generic;
  }

  static String? _normalizeCode(String? value) {
    if (value == null) return null;
    final trimmed = value.trim();
    if (trimmed.isEmpty) return null;
    final match = RegExp(r'[A-Z][A-Z0-9_]{2,}').firstMatch(trimmed);
    return match?.group(0) ?? trimmed.toUpperCase();
  }
}

bool _looksArabic(String value) {
  return RegExp(r'[\u0600-\u06FF]').hasMatch(value);
}

String arabicMessageForError(Object? error) {
  if (error == null) return MadarErrorMessages.generic;
  if (error is FrappeApiException) {
    return MadarErrorMessages.fromCode(error.code, fallback: error.message);
  }
  if (error is http.ClientException) return MadarErrorMessages.network;
  if (_looksLikeNetworkError(error)) return MadarErrorMessages.network;
  if (error is String) return MadarErrorMessages.fromCode(error);
  return MadarErrorMessages.generic;
}

bool _looksLikeNetworkError(Object error) {
  final text = error.toString().toLowerCase();
  return text.contains('socket') ||
      text.contains('connection') ||
      text.contains('network') ||
      text.contains('failed host lookup') ||
      text.contains('connection refused');
}
