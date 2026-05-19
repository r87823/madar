from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.permissions.scopes import get_context_scopes
from madar.services.employee_context import get_employee_context


CREATE_PERMISSION = "orders.create"
SUBMIT_PERMISSION = "orders.submit_for_approval"
FULL_ACCESS_PERMISSION = "system.full_access"
ORDER_FIELDS = [
    "name",
    "customer_name",
    "customer_phone",
    "branch",
    "assigned_branch",
    "order_status",
    "created_by_user",
    "notes",
    "submitted_at",
    "cancelled_at",
    "creation",
    "modified",
]
MAX_LIST_LIMIT = 50


def create_draft(user, customer_name, customer_phone="", notes="", frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, CREATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إنشاء الطلبات.")

    employee = _employee(user, frappe_module)
    scopes = get_context_scopes(employee, permissions)
    branch = _default_branch(scopes, employee)
    now = _server_now(frappe_module)
    doc = frappe_module.get_doc(
        {
            "doctype": "Madar Order",
            "naming_series": "MADAR-ORD-.YYYY.-",
            "customer_name": (customer_name or "").strip(),
            "customer_phone": (customer_phone or "").strip(),
            "notes": (notes or "").strip(),
            "branch": branch,
            "assigned_branch": branch,
            "order_status": "draft",
            "created_by_user": user,
        }
    ).insert(ignore_permissions=True)
    _audit(doc, "create_draft", user, now)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def list_orders(user, frappe_module=None, limit=MAX_LIST_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permissions = _user_permissions(user, frappe_module)
    filters = _scope_filters(user, permissions, _employee(user, frappe_module))
    rows = frappe_module.get_all(
        "Madar Order",
        filters=filters,
        fields=ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_LIST_LIMIT), MAX_LIST_LIMIT)),
    )
    return _ok({"items": [_serialize_order(row) for row in rows]})


def get_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permissions = _user_permissions(user, frappe_module)
    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    return _ok(_serialize_order(doc))


def submit_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, SUBMIT_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إرسال الطلب.")

    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    if _get_value(doc, "order_status") != "draft":
        return _error("INVALID_ORDER_TRANSITION", "يمكن إرسال الطلبات المسودة فقط.")

    now = _server_now(frappe_module)
    doc.order_status = "submitted"
    doc.submitted_at = now
    doc.save(ignore_permissions=True)
    _audit(doc, "submit_order", user, now)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def cancel_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, CREATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إلغاء الطلب.")

    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    if _get_value(doc, "order_status") != "draft":
        return _error("INVALID_ORDER_TRANSITION", "يمكن إلغاء الطلبات المسودة فقط.")

    now = _server_now(frappe_module)
    doc.order_status = "cancelled"
    doc.cancelled_at = now
    doc.save(ignore_permissions=True)
    _audit(doc, "cancel_order", user, now)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def _get_scoped_order(user, order_name, permissions, frappe_module):
    try:
        doc = frappe_module.get_doc("Madar Order", order_name)
    except Exception:
        return None
    if not _is_visible(doc, user, permissions, _employee(user, frappe_module)):
        return None
    return doc


def _is_visible(order, user, permissions, employee):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return True
    if _get_value(order, "created_by_user") == user:
        return True
    scopes = get_context_scopes(employee, permissions)
    branch_names = scopes.get("branch_names") or []
    return _get_value(order, "assigned_branch") in branch_names or _get_value(order, "branch") in branch_names


def _scope_filters(user, permissions, employee):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return {}
    scopes = get_context_scopes(employee, permissions)
    branch_names = scopes.get("branch_names") or []
    if branch_names:
        return {"assigned_branch": ["in", branch_names]}
    return {"created_by_user": user}


def _default_branch(scopes, employee):
    branch_names = scopes.get("branch_names") or []
    if branch_names and branch_names != ["*"]:
        return branch_names[0]
    return _get_value(employee, "branch")


def _user_permissions(user, frappe_module):
    roles = frappe_module.get_roles(user)
    return roles, get_permissions_for_roles(roles)


def _employee(user, frappe_module):
    return get_employee_context(user, frappe_module=frappe_module)


def _server_now(frappe_module):
    return frappe_module.utils.now_datetime()


def _audit(doc, action, user, now):
    if hasattr(doc, "add_comment"):
        doc.add_comment("Info", f"{action} by {user} at {now}")


def _serialize_order(order):
    return {
        "name": _get_value(order, "name"),
        "customer_name": _get_value(order, "customer_name"),
        "customer_phone": _get_value(order, "customer_phone"),
        "branch": _get_value(order, "branch"),
        "assigned_branch": _get_value(order, "assigned_branch"),
        "order_status": _get_value(order, "order_status"),
        "created_by_user": _get_value(order, "created_by_user"),
        "notes": _get_value(order, "notes"),
        "submitted_at": _string_or_none(_get_value(order, "submitted_at")),
        "cancelled_at": _string_or_none(_get_value(order, "cancelled_at")),
        "creation": _string_or_none(_get_value(order, "creation")),
        "modified": _string_or_none(_get_value(order, "modified")),
    }


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _string_or_none(value):
    return str(value) if value else None


def _ok(data):
    return {
        "ok": True,
        "data": data,
        "error": None,
    }


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }
