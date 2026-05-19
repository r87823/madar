from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.permissions.scopes import get_context_scopes
from madar.services.employee_context import get_employee_context
from madar.services import production_mapping_service


CREATE_PERMISSION = "production.manage_mappings"
VIEW_PERMISSION = "production.view_work_orders"
UPDATE_PERMISSION = "production.update_work_order"
FULL_ACCESS_PERMISSION = "system.full_access"
WORK_ORDER_FIELDS = [
    "name",
    "madar_order",
    "production_center",
    "production_department",
    "status",
    "accepted_at",
    "started_at",
    "ready_at",
    "delayed_at",
    "delay_reason",
    "created_from_order_at",
]
WORK_ORDER_ITEM_FIELDS = [
    "name",
    "work_order",
    "madar_order_item",
    "item_code",
    "item_name",
    "qty",
    "notes",
]
MAX_LIST_LIMIT = 100


def create_work_orders_from_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, CREATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إنشاء أوامر الإنتاج.")

    order = _get_doc(frappe_module, "Madar Order", order_name)
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")
    if _get_value(order, "order_status") != "approved":
        return _error("ORDER_NOT_APPROVED", "يمكن إنشاء أوامر الإنتاج من الطلبات المعتمدة فقط.")

    existing = _work_orders_for_order(frappe_module, order_name)
    if existing:
        return _ok({"items": [_serialize_work_order(row) for row in existing]})

    validation = production_mapping_service.validate_order_department_mappings(
        user=user,
        order_name=order_name,
        frappe_module=frappe_module,
    )
    if not validation["ok"]:
        return validation
    if not validation["data"]["is_valid"]:
        return _error(
            "ITEM_DEPARTMENT_MAPPING_MISSING",
            "بعض أصناف الطلب غير مرتبطة بأقسام إنتاج.",
            data={"missing_item_codes": validation["data"]["missing_item_codes"]},
        )

    order_items = _order_items_for_order(frappe_module, order_name)
    mappings = _mapping_by_item_code(
        frappe_module,
        [_get_value(item, "item_code") for item in order_items],
    )
    grouped = {}
    for item in order_items:
        item_code = _get_value(item, "item_code")
        mapping = mappings[item_code]
        key = (_get_value(mapping, "production_center"), _get_value(mapping, "production_department"))
        grouped.setdefault(key, []).append(item)

    created = []
    now = _server_now(frappe_module)
    for (center, department), items in sorted(grouped.items()):
        work_order = frappe_module.get_doc(
            {
                "doctype": "Madar Work Order",
                "naming_series": "MADAR-WO-.YYYY.-",
                "madar_order": order_name,
                "production_center": center,
                "production_department": department,
                "status": "pending",
                "created_from_order_at": now,
            }
        ).insert(ignore_permissions=True)
        _audit(work_order, "create_work_order", user, frappe_module)
        for item in items:
            frappe_module.get_doc(
                {
                    "doctype": "Madar Work Order Item",
                    "work_order": _get_value(work_order, "name"),
                    "madar_order_item": _get_value(item, "name"),
                    "item_code": _get_value(item, "item_code"),
                    "item_name": _get_value(item, "item_name"),
                    "qty": _float(_get_value(item, "qty")),
                    "notes": _get_value(item, "notes") or "",
                }
            ).insert(ignore_permissions=True)
        created.append(work_order)
    _commit(frappe_module)
    return _ok({"items": [_serialize_work_order(row) for row in created]})


def list_work_orders(user, frappe_module=None, limit=MAX_LIST_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, VIEW_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض أوامر الإنتاج.")

    filters = _scope_filters(user, permissions, frappe_module)
    rows = frappe_module.get_all(
        "Madar Work Order",
        filters=filters,
        fields=WORK_ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_LIST_LIMIT), MAX_LIST_LIMIT)),
    )
    return _ok({"items": [_serialize_work_order(row) for row in rows]})


def get_work_order(user, work_order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, VIEW_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض أوامر الإنتاج.")

    work_order = _get_scoped_work_order(user, work_order_name, permissions, frappe_module)
    if not work_order:
        return _error("WORK_ORDER_NOT_FOUND", "أمر الإنتاج غير موجود أو خارج نطاقك.")
    items = frappe_module.get_all(
        "Madar Work Order Item",
        filters={"work_order": work_order_name},
        fields=WORK_ORDER_ITEM_FIELDS,
        order_by="creation asc",
        limit=500,
    )
    data = _serialize_work_order(work_order)
    data["items"] = [_serialize_item(item) for item in items]
    return _ok(data)


def accept_work_order(user, work_order_name, frappe_module=None):
    return _transition(
        user=user,
        work_order_name=work_order_name,
        next_status="accepted",
        allowed_from={"pending"},
        timestamp_field="accepted_at",
        action="accept_work_order",
        frappe_module=frappe_module,
    )


def start_work_order(user, work_order_name, frappe_module=None):
    return _transition(
        user=user,
        work_order_name=work_order_name,
        next_status="in_production",
        allowed_from={"accepted"},
        timestamp_field="started_at",
        action="start_work_order",
        frappe_module=frappe_module,
    )


def mark_work_order_ready(user, work_order_name, frappe_module=None):
    return _transition(
        user=user,
        work_order_name=work_order_name,
        next_status="ready",
        allowed_from={"in_production"},
        timestamp_field="ready_at",
        action="mark_work_order_ready",
        frappe_module=frappe_module,
    )


def mark_work_order_delayed(user, work_order_name, reason, frappe_module=None):
    if not (reason or "").strip():
        return _error("REASON_REQUIRED", "سبب التأخير مطلوب.")
    return _transition(
        user=user,
        work_order_name=work_order_name,
        next_status="delayed",
        allowed_from={"pending", "in_production"},
        timestamp_field="delayed_at",
        action="mark_work_order_delayed",
        reason=reason,
        frappe_module=frappe_module,
    )


def _transition(
    user,
    work_order_name,
    next_status,
    allowed_from,
    timestamp_field,
    action,
    reason="",
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, UPDATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تحديث أمر الإنتاج.")

    work_order = _get_scoped_work_order(user, work_order_name, permissions, frappe_module)
    if not work_order:
        return _error("WORK_ORDER_NOT_FOUND", "أمر الإنتاج غير موجود أو خارج نطاقك.")
    if _get_value(work_order, "status") not in allowed_from:
        return _error("INVALID_WORK_ORDER_TRANSITION", "انتقال حالة أمر الإنتاج غير مسموح.")

    now = _server_now(frappe_module)
    work_order.status = next_status
    setattr(work_order, timestamp_field, now)
    if next_status == "delayed":
        work_order.delay_reason = (reason or "").strip()
    work_order.save(ignore_permissions=True)
    _audit(work_order, action, user, frappe_module, reason=reason)
    _commit(frappe_module)
    return _ok(_serialize_work_order(work_order))


def _work_orders_for_order(frappe_module, order_name):
    return frappe_module.get_all(
        "Madar Work Order",
        filters={"madar_order": order_name},
        fields=WORK_ORDER_FIELDS,
        order_by="production_center asc",
        limit=MAX_LIST_LIMIT,
    )


def _order_items_for_order(frappe_module, order_name):
    return frappe_module.get_all(
        "Madar Order Item",
        filters={"order_name": order_name},
        fields=["name", "item_code", "item_name", "qty", "notes"],
        order_by="creation asc",
        limit=500,
    )


def _mapping_by_item_code(frappe_module, item_codes):
    rows = frappe_module.get_all(
        "Madar Item Department Mapping",
        filters={"item_code": ["in", item_codes], "is_active": 1},
        fields=["item_code", "production_center", "production_department"],
        limit=500,
    )
    return {_get_value(row, "item_code"): row for row in rows}


def _get_scoped_work_order(user, work_order_name, permissions, frappe_module):
    try:
        work_order = frappe_module.get_doc("Madar Work Order", work_order_name)
    except Exception:
        return None
    if not _is_visible(work_order, user, permissions, frappe_module):
        return None
    return work_order


def _is_visible(work_order, user, permissions, frappe_module):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return True
    scopes = get_context_scopes(get_employee_context(user, frappe_module=frappe_module), permissions)
    departments = scopes.get("department_names") or []
    if departments == ["*"]:
        return True
    return _get_value(work_order, "production_department") in departments


def _scope_filters(user, permissions, frappe_module):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return {}
    scopes = get_context_scopes(get_employee_context(user, frappe_module=frappe_module), permissions)
    departments = scopes.get("department_names") or []
    if departments == ["*"]:
        return {}
    if departments:
        return {"production_department": ["in", departments]}
    return {"name": "__none__"}


def _get_doc(frappe_module, doctype, name):
    try:
        return frappe_module.get_doc(doctype, name)
    except Exception:
        return None


def _user_permissions(user, frappe_module):
    roles = frappe_module.get_roles(user)
    return roles, get_permissions_for_roles(roles)


def _serialize_work_order(work_order):
    return {
        "name": _get_value(work_order, "name"),
        "madar_order": _get_value(work_order, "madar_order"),
        "production_center": _get_value(work_order, "production_center"),
        "production_department": _get_value(work_order, "production_department"),
        "status": _get_value(work_order, "status"),
        "accepted_at": _string_or_none(_get_value(work_order, "accepted_at")),
        "started_at": _string_or_none(_get_value(work_order, "started_at")),
        "ready_at": _string_or_none(_get_value(work_order, "ready_at")),
        "delayed_at": _string_or_none(_get_value(work_order, "delayed_at")),
        "delay_reason": _get_value(work_order, "delay_reason"),
        "created_from_order_at": _string_or_none(_get_value(work_order, "created_from_order_at")),
    }


def _serialize_item(item):
    return {
        "name": _get_value(item, "name"),
        "work_order": _get_value(item, "work_order"),
        "madar_order_item": _get_value(item, "madar_order_item"),
        "item_code": _get_value(item, "item_code"),
        "item_name": _get_value(item, "item_name"),
        "qty": _float(_get_value(item, "qty")),
        "notes": _get_value(item, "notes"),
    }


def _audit(doc, action, user, frappe_module, reason=""):
    if hasattr(doc, "add_comment"):
        suffix = f" reason={reason}" if reason else ""
        doc.add_comment("Info", f"{action} by {user} at {_server_now(frappe_module)}{suffix}")


def _server_now(frappe_module):
    return frappe_module.utils.now_datetime()


def _commit(frappe_module):
    if hasattr(frappe_module, "db"):
        frappe_module.db.commit()


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _string_or_none(value):
    return str(value) if value else None


def _float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message, data=None):
    return {"ok": False, "data": data, "error": {"code": code, "message": message}}
