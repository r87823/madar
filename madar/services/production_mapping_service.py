from madar.permissions.checks import get_permissions_for_roles, has_permission


MANAGE_PERMISSION = "production.manage_mappings"
VIEW_PERMISSION = "production.view_work_orders"
FULL_ACCESS_PERMISSION = "system.full_access"
CENTER_FIELDS = ["name", "center_name", "center_code", "is_active"]
DEPARTMENT_FIELDS = [
    "name",
    "department_name",
    "department_code",
    "production_center",
    "is_active",
]
MAPPING_FIELDS = [
    "name",
    "item_code",
    "item_name",
    "production_center",
    "production_department",
    "is_active",
]
MAX_LIST_LIMIT = 100


def list_production_centers(user, frappe_module=None, include_inactive=False):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view(user, frappe_module)
    if not allowed:
        return error

    filters = {} if include_inactive else {"is_active": 1}
    rows = frappe_module.get_all(
        "Madar Production Center",
        filters=filters,
        fields=CENTER_FIELDS,
        order_by="center_name asc",
        limit=MAX_LIST_LIMIT,
    )
    return _ok({"items": [_serialize_center(row) for row in rows]})


def list_production_departments(
    user,
    frappe_module=None,
    production_center=None,
    include_inactive=False,
):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view(user, frappe_module)
    if not allowed:
        return error

    filters = {} if include_inactive else {"is_active": 1}
    if production_center:
        filters["production_center"] = production_center
    rows = frappe_module.get_all(
        "Madar Production Department",
        filters=filters,
        fields=DEPARTMENT_FIELDS,
        order_by="department_name asc",
        limit=MAX_LIST_LIMIT,
    )
    return _ok({"items": [_serialize_department(row) for row in rows]})


def list_item_department_mappings(user, frappe_module=None, include_inactive=False):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_manage(user, frappe_module)
    if not allowed:
        return error

    filters = {} if include_inactive else {"is_active": 1}
    rows = frappe_module.get_all(
        "Madar Item Department Mapping",
        filters=filters,
        fields=MAPPING_FIELDS,
        order_by="modified desc",
        limit=MAX_LIST_LIMIT,
    )
    return _ok({"items": [_serialize_mapping(row) for row in rows]})


def create_or_update_production_center(
    user,
    center_name,
    center_code,
    is_active=1,
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_manage(user, frappe_module)
    if not allowed:
        return error

    code = _clean(center_code)
    if not code:
        return _error("CENTER_CODE_REQUIRED", "رمز مركز الإنتاج مطلوب.")

    values = {
        "doctype": "Madar Production Center",
        "center_name": _clean(center_name) or code,
        "center_code": code,
        "is_active": 1 if _truthy(is_active) else 0,
    }
    doc = _upsert_doc(frappe_module, "Madar Production Center", code, values)
    _audit(doc, "create_or_update_production_center", user, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_center(doc))


def create_or_update_production_department(
    user,
    department_name,
    department_code,
    production_center,
    is_active=1,
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_manage(user, frappe_module)
    if not allowed:
        return error

    code = _clean(department_code)
    center = _clean(production_center)
    if not code:
        return _error("DEPARTMENT_CODE_REQUIRED", "رمز قسم الإنتاج مطلوب.")
    if not _exists(frappe_module, "Madar Production Center", center):
        return _error("PRODUCTION_CENTER_NOT_FOUND", "مركز الإنتاج غير موجود.")

    values = {
        "doctype": "Madar Production Department",
        "department_name": _clean(department_name) or code,
        "department_code": code,
        "production_center": center,
        "is_active": 1 if _truthy(is_active) else 0,
    }
    doc = _upsert_doc(frappe_module, "Madar Production Department", code, values)
    _audit(doc, "create_or_update_production_department", user, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_department(doc))


def create_or_update_item_department_mapping(
    user,
    item_code,
    production_center,
    production_department,
    is_active=1,
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_manage(user, frappe_module)
    if not allowed:
        return error

    item_code = _clean(item_code)
    center = _clean(production_center)
    department = _clean(production_department)
    item = _get_item(frappe_module, item_code)
    if not item:
        return _error("ITEM_NOT_FOUND", "الصنف غير موجود.")
    if not _exists(frappe_module, "Madar Production Center", center):
        return _error("PRODUCTION_CENTER_NOT_FOUND", "مركز الإنتاج غير موجود.")
    if not _exists(frappe_module, "Madar Production Department", department):
        return _error("PRODUCTION_DEPARTMENT_NOT_FOUND", "قسم الإنتاج غير موجود.")

    values = {
        "doctype": "Madar Item Department Mapping",
        "item_code": item_code,
        "item_name": _get_value(item, "item_name") or item_code,
        "production_center": center,
        "production_department": department,
        "is_active": 1 if _truthy(is_active) else 0,
    }
    doc = _upsert_doc(frappe_module, "Madar Item Department Mapping", item_code, values)
    _audit(doc, "create_or_update_item_department_mapping", user, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_mapping(doc))


def validate_order_department_mappings(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_manage(user, frappe_module)
    if not allowed:
        return error

    order = _get_doc(frappe_module, "Madar Order", order_name)
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")
    if _get_value(order, "order_status") != "approved":
        return _error("ORDER_NOT_APPROVED", "يمكن التحقق من الطلبات المعتمدة فقط.")

    rows = frappe_module.get_all(
        "Madar Order Item",
        filters={"order_name": order_name},
        fields=["item_code", "item_name"],
        order_by="creation asc",
        limit=500,
    )
    item_codes = []
    for row in rows:
        code = _get_value(row, "item_code")
        if code and code not in item_codes:
            item_codes.append(code)

    active_mappings = _active_mapping_item_codes(frappe_module, item_codes)
    missing = [item_code for item_code in item_codes if item_code not in active_mappings]
    return _ok(
        {
            "order_name": order_name,
            "is_valid": not missing,
            "missing_item_codes": missing,
            "mapped_item_codes": [item_code for item_code in item_codes if item_code in active_mappings],
        }
    )


def _can_view(user, frappe_module):
    roles = frappe_module.get_roles(user)
    permissions = get_permissions_for_roles(roles)
    if (
        FULL_ACCESS_PERMISSION in permissions
        or VIEW_PERMISSION in permissions
        or MANAGE_PERMISSION in permissions
    ):
        return True, None
    return False, _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض إعدادات الإنتاج.")


def _can_manage(user, frappe_module):
    roles = frappe_module.get_roles(user)
    if has_permission(roles, MANAGE_PERMISSION):
        return True, None
    return False, _error("PERMISSION_DENIED", "ليست لديك صلاحية إدارة ربط الإنتاج.")


def _upsert_doc(frappe_module, doctype, name, values):
    existing = _get_doc(frappe_module, doctype, name)
    if existing:
        for field, value in values.items():
            if field != "doctype":
                setattr(existing, field, value)
        existing.save(ignore_permissions=True)
        return existing
    return frappe_module.get_doc(values).insert(ignore_permissions=True)


def _get_item(frappe_module, item_code):
    return _get_doc(frappe_module, "Item", item_code)


def _get_doc(frappe_module, doctype, name):
    try:
        return frappe_module.get_doc(doctype, name)
    except Exception:
        return None


def _exists(frappe_module, doctype, name):
    if not name:
        return False
    if hasattr(frappe_module, "db") and hasattr(frappe_module.db, "exists"):
        return bool(frappe_module.db.exists(doctype, name))
    return _get_doc(frappe_module, doctype, name) is not None


def _active_mapping_item_codes(frappe_module, item_codes):
    if not item_codes:
        return set()
    rows = frappe_module.get_all(
        "Madar Item Department Mapping",
        filters={"item_code": ["in", item_codes], "is_active": 1},
        fields=["item_code"],
        limit=500,
    )
    return {_get_value(row, "item_code") for row in rows}


def _serialize_center(center):
    return {
        "name": _get_value(center, "name"),
        "center_name": _get_value(center, "center_name"),
        "center_code": _get_value(center, "center_code"),
        "is_active": int(_truthy(_get_value(center, "is_active"))),
    }


def _serialize_department(department):
    return {
        "name": _get_value(department, "name"),
        "department_name": _get_value(department, "department_name"),
        "department_code": _get_value(department, "department_code"),
        "production_center": _get_value(department, "production_center"),
        "is_active": int(_truthy(_get_value(department, "is_active"))),
    }


def _serialize_mapping(mapping):
    return {
        "name": _get_value(mapping, "name"),
        "item_code": _get_value(mapping, "item_code"),
        "item_name": _get_value(mapping, "item_name"),
        "production_center": _get_value(mapping, "production_center"),
        "production_department": _get_value(mapping, "production_department"),
        "is_active": int(_truthy(_get_value(mapping, "is_active"))),
    }


def _audit(doc, action, user, frappe_module):
    if hasattr(doc, "add_comment"):
        doc.add_comment("Info", f"{action} by {user} at {frappe_module.utils.now_datetime()}")


def _commit(frappe_module):
    if hasattr(frappe_module, "db"):
        frappe_module.db.commit()


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _clean(value):
    return (value or "").strip()


def _truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}
