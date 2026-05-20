import json

from madar.permissions.checks import get_permissions_for_roles


MANAGE_PERMISSION = "settings.manage"
FULL_ACCESS = "system.full_access"
PAYMENT_METHODS = {"cash", "card", "transfer", "online"}


DEFAULT_SETTINGS = [
    {
        "setting_key": "app.default_language",
        "setting_value": "ar",
        "value_type": "string",
        "category": "general",
        "label_ar": "اللغة الافتراضية",
        "description_ar": "لغة واجهة مدار الافتراضية.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "attendance.duplicate_window_seconds",
        "setting_value": "60",
        "value_type": "int",
        "category": "attendance",
        "label_ar": "مدة منع تكرار تسجيل الحضور",
        "description_ar": "عدد الثواني التي تمنع تكرار نفس حركة الحضور.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "orders.require_items_before_submit",
        "setting_value": "true",
        "value_type": "bool",
        "category": "orders",
        "label_ar": "منع إرسال الطلب بدون أصناف",
        "description_ar": "يتطلب وجود صنف واحد على الأقل قبل إرسال الطلب.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "payments.allow_overpayment",
        "setting_value": "false",
        "value_type": "bool",
        "category": "payments",
        "label_ar": "السماح بالدفع الزائد",
        "description_ar": "يسمح أو يمنع تحصيل مبلغ يتجاوز المتبقي على الطلب.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "payments.enabled_methods",
        "setting_value": json.dumps(["cash", "card", "transfer", "online"]),
        "value_type": "json",
        "category": "payments",
        "label_ar": "طرق الدفع المفعلة",
        "description_ar": "طرق الدفع المتاحة في واجهة التحصيل.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "cashbox.require_review",
        "setting_value": "true",
        "value_type": "bool",
        "category": "cashbox",
        "label_ar": "مراجعة الصندوق إلزامية",
        "description_ar": "يتطلب مراجعة الصندوق قبل الإقفال المحاسبي.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "notifications.enabled",
        "setting_value": "true",
        "value_type": "bool",
        "category": "notifications",
        "label_ar": "تفعيل الإشعارات الداخلية",
        "description_ar": "يفعل أو يوقف إنشاء إشعارات مدار الداخلية.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "erp.auto_sync_sales_order",
        "setting_value": "false",
        "value_type": "bool",
        "category": "erp",
        "label_ar": "مزامنة أمر البيع تلقائيًا",
        "description_ar": "إعداد تشغيلي مستقبلي، لا يفعّل مزامنة تلقائية في هذا الإصدار.",
        "is_secret": 0,
        "is_editable": 1,
    },
    {
        "setting_key": "erp.auto_create_sales_invoice",
        "setting_value": "false",
        "value_type": "bool",
        "category": "erp",
        "label_ar": "إنشاء الفاتورة تلقائيًا",
        "description_ar": "إعداد تشغيلي مستقبلي، لا ينشئ فواتير تلقائيًا في هذا الإصدار.",
        "is_secret": 0,
        "is_editable": 1,
    },
]


def ensure_default_settings(frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    created = 0
    for setting in DEFAULT_SETTINGS:
        key = setting["setting_key"]
        if _exists(frappe_module, key):
            continue
        frappe_module.get_doc({"doctype": "Madar Setting", **setting}).insert(ignore_permissions=True)
        created += 1
    _commit(frappe_module)
    return {"created": created}


def get_settings(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    if not _can_manage(user, frappe_module):
        return _error("PERMISSION_DENIED", "غير مسموح بعرض الإعدادات.")
    ensure_default_settings(frappe_module=frappe_module)
    rows = _get_setting_rows(frappe_module)
    allowed_keys = _allowed_setting_keys()
    return _ok(
        {
            "items": [
                _serialize_setting(row)
                for row in rows
                if _get(row, "setting_key") in allowed_keys and not _bool(_get(row, "is_secret"))
            ]
        }
    )


def get_setting_metadata(user, frappe_module=None):
    return get_settings(user, frappe_module=frappe_module)


def update_setting(user, setting_key, value, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    if not _can_manage(user, frappe_module):
        return _error("PERMISSION_DENIED", "غير مسموح بتعديل الإعدادات.")
    if not _default_definition(setting_key):
        return _error("SETTING_NOT_FOUND", "الإعداد غير موجود.")
    ensure_default_settings(frappe_module=frappe_module)
    doc = _get_setting_doc(frappe_module, setting_key)
    if not doc:
        return _error("SETTING_NOT_FOUND", "الإعداد غير موجود.")
    if _bool(_get(doc, "is_secret")):
        return _error("SETTING_SECRET_NOT_READABLE", "لا يمكن عرض أو تعديل الإعدادات السرية.")
    if not _bool(_get(doc, "is_editable")):
        return _error("SETTING_NOT_EDITABLE", "هذا الإعداد غير قابل للتعديل.")

    parsed = _validate_value(_get(doc, "setting_key"), value, _get(doc, "value_type"))
    if not parsed["ok"]:
        return parsed

    doc.setting_value = _value_to_storage(parsed["value"], _get(doc, "value_type"))
    doc.updated_by = user
    doc.updated_at = _now(frappe_module)
    doc.save(ignore_permissions=True)
    _audit(doc, user)
    _commit(frappe_module)
    return _ok(_serialize_setting(doc))


def get_setting_value(setting_key, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    doc = _get_setting_doc(frappe_module, setting_key)
    if not doc or _bool(_get(doc, "is_secret")):
        default = _default_definition(setting_key)
        if not default:
            return None
        return _parse_value(default["setting_value"], default["value_type"])
    return _parse_value(_get(doc, "setting_value"), _get(doc, "value_type"))


def _get_setting_rows(frappe_module):
    return frappe_module.get_all(
        "Madar Setting",
        filters={},
        fields=[
            "name",
            "setting_key",
            "setting_value",
            "value_type",
            "category",
            "label_ar",
            "description_ar",
            "is_secret",
            "is_editable",
            "updated_by",
            "updated_at",
        ],
        order_by="category asc, setting_key asc",
        limit=1000,
    )


def _serialize_setting(setting):
    value_type = _get(setting, "value_type")
    return {
        "setting_key": _get(setting, "setting_key"),
        "value": _parse_value(_get(setting, "setting_value"), value_type),
        "value_type": value_type,
        "category": _get(setting, "category"),
        "label_ar": _get(setting, "label_ar"),
        "description_ar": _get(setting, "description_ar"),
        "is_editable": _bool(_get(setting, "is_editable")),
        "updated_by": _get(setting, "updated_by"),
        "updated_at": str(_get(setting, "updated_at")) if _get(setting, "updated_at") else None,
    }


def _validate_value(setting_key, value, value_type):
    try:
        parsed = _coerce_value(value, value_type)
    except (TypeError, ValueError, json.JSONDecodeError):
        return _error("SETTING_VALUE_INVALID", "قيمة غير صحيحة.")
    if setting_key == "payments.enabled_methods":
        if not isinstance(parsed, list) or not parsed or any(item not in PAYMENT_METHODS for item in parsed):
            return _error("SETTING_VALUE_INVALID", "قيمة غير صحيحة.")
        parsed = list(dict.fromkeys(parsed))
    if setting_key == "app.default_language" and parsed != "ar":
        return _error("SETTING_VALUE_INVALID", "قيمة غير صحيحة.")
    return {"ok": True, "value": parsed}


def _coerce_value(value, value_type):
    if value_type == "bool":
        if isinstance(value, bool):
            return value
        if str(value).lower() in {"true", "1", "yes"}:
            return True
        if str(value).lower() in {"false", "0", "no"}:
            return False
        raise ValueError(value)
    if value_type == "int":
        parsed = int(value)
        if parsed < 0:
            raise ValueError(value)
        return parsed
    if value_type == "json":
        parsed = json.loads(value) if isinstance(value, str) else value
        if not isinstance(parsed, list):
            raise ValueError(value)
        return [str(item) for item in parsed]
    return str(value)


def _parse_value(value, value_type):
    try:
        return _coerce_value(value, value_type)
    except Exception:
        default = _default_for_type(value_type)
        return default


def _value_to_storage(value, value_type):
    if value_type == "bool":
        return "true" if bool(value) else "false"
    if value_type == "json":
        return json.dumps(value)
    return str(value)


def _default_for_type(value_type):
    if value_type == "bool":
        return False
    if value_type == "int":
        return 0
    if value_type == "json":
        return []
    return ""


def _default_definition(setting_key):
    for setting in DEFAULT_SETTINGS:
        if setting["setting_key"] == setting_key:
            return setting
    return None


def _allowed_setting_keys():
    return {setting["setting_key"] for setting in DEFAULT_SETTINGS}


def _can_manage(user, frappe_module):
    permissions = set(get_permissions_for_roles(frappe_module.get_roles(user)))
    return FULL_ACCESS in permissions or MANAGE_PERMISSION in permissions


def _exists(frappe_module, setting_key):
    try:
        return bool(frappe_module.db.exists("Madar Setting", setting_key))
    except Exception:
        return False


def _get_setting_doc(frappe_module, setting_key):
    try:
        return frappe_module.get_doc("Madar Setting", setting_key)
    except Exception:
        return None


def _audit(doc, user):
    if hasattr(doc, "add_comment"):
        doc.add_comment("Info", f"Setting updated by {user}")


def _now(frappe_module):
    return frappe_module.utils.now_datetime()


def _commit(frappe_module):
    if hasattr(frappe_module, "db") and hasattr(frappe_module.db, "commit"):
        frappe_module.db.commit()


def _get(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _bool(value):
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no", ""}:
        return False
    return bool(value)


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }
