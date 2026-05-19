from madar.permissions.checks import has_permission
from madar.services import order_service
from madar.services.catalog_service import get_default_price


ITEM_FIELDS = [
    "name",
    "order_name",
    "item_code",
    "item_name",
    "qty",
    "unit_price",
    "line_total",
    "notes",
    "creation",
    "modified",
]
EDITABLE_STATUSES = {"draft", "returned_for_edit"}


def list_order_items(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, error = _get_scoped_order_for_items(user, order_name, frappe_module)
    if error:
        return error

    return _ok(
        {
            "order": order_service._serialize_order(order),
            "items": [_serialize_item(row) for row in _get_items(frappe_module, order_name)],
        }
    )


def add_item(user, order_name, item_code, qty, notes="", frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_mutate(user, order_name, qty, frappe_module)
    if error:
        return error
    order = allowed

    item = _get_item(frappe_module, item_code)
    if not item:
        return _error("PRODUCT_NOT_FOUND", "المنتج غير موجود.")

    safe_qty = _quantity(qty)
    unit_price = get_default_price(item_code, frappe_module)
    line_total = safe_qty * unit_price
    created = frappe_module.get_doc(
        {
            "doctype": "Madar Order Item",
            "order_name": order_name,
            "item_code": item_code,
            "item_name": _get_value(item, "item_name") or item_code,
            "qty": safe_qty,
            "unit_price": unit_price,
            "line_total": line_total,
            "notes": (notes or "").strip(),
        }
    ).insert(ignore_permissions=True)
    order = _recalculate_totals(frappe_module, order)
    _audit(order, "add_item", user, frappe_module)
    frappe_module.db.commit()
    return _ok({"order": order_service._serialize_order(order), "item": _serialize_item(created)})


def update_item_qty(user, order_name, item_name, qty, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_mutate(user, order_name, qty, frappe_module)
    if error:
        return error
    order = allowed
    item = _get_order_item(frappe_module, order_name, item_name)
    if not item:
        return _error("ORDER_ITEM_NOT_FOUND", "عنصر الطلب غير موجود.")

    safe_qty = _quantity(qty)
    item.qty = safe_qty
    item.line_total = safe_qty * _float(_get_value(item, "unit_price"))
    item.save(ignore_permissions=True)
    order = _recalculate_totals(frappe_module, order)
    _audit(order, "update_item_qty", user, frappe_module)
    frappe_module.db.commit()
    return _ok({"order": order_service._serialize_order(order), "item": _serialize_item(item)})


def remove_item(user, order_name, item_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, error = _can_mutate(user, order_name, 1, frappe_module)
    if error:
        return error
    item = _get_order_item(frappe_module, order_name, item_name)
    if not item:
        return _error("ORDER_ITEM_NOT_FOUND", "عنصر الطلب غير موجود.")

    if hasattr(frappe_module, "delete_doc"):
        frappe_module.delete_doc("Madar Order Item", item_name, ignore_permissions=True)
    else:
        item.delete(ignore_permissions=True)
    order = _recalculate_totals(frappe_module, order)
    _audit(order, "remove_item", user, frappe_module)
    frappe_module.db.commit()
    return _ok({"order": order_service._serialize_order(order), "items": [_serialize_item(row) for row in _get_items(frappe_module, order_name)]})


def _can_mutate(user, order_name, qty, frappe_module):
    roles, permissions = order_service._user_permissions(user, frappe_module)
    if not has_permission(roles, order_service.CREATE_PERMISSION):
        return None, _error("PERMISSION_DENIED", "ليست لديك صلاحية تعديل عناصر الطلب.")

    if _quantity(qty) <= 0:
        return None, _error("INVALID_QUANTITY", "الكمية يجب أن تكون أكبر من صفر.")

    order, error = _get_scoped_order_for_items(user, order_name, frappe_module, permissions=permissions)
    if error:
        return None, error
    if order_service._get_value(order, "order_status") not in EDITABLE_STATUSES:
        return None, _error("ORDER_NOT_EDITABLE", "يمكن تعديل عناصر الطلبات المسودة فقط.")
    return order, None


def _get_scoped_order_for_items(user, order_name, frappe_module, permissions=None):
    if permissions is None:
        _roles, permissions = order_service._user_permissions(user, frappe_module)
    order = order_service._get_scoped_order(user, order_name, permissions, frappe_module)
    if not order:
        return None, _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    return order, None


def _get_item(frappe_module, item_code):
    try:
        return frappe_module.get_doc("Item", item_code)
    except Exception:
        return None


def _get_order_item(frappe_module, order_name, item_name):
    try:
        item = frappe_module.get_doc("Madar Order Item", item_name)
    except Exception:
        return None
    if _get_value(item, "order_name") != order_name:
        return None
    return item


def _get_items(frappe_module, order_name):
    return frappe_module.get_all(
        "Madar Order Item",
        filters={"order_name": order_name},
        fields=ITEM_FIELDS,
        order_by="creation asc",
        limit=200,
    )


def _recalculate_totals(frappe_module, order):
    items = _get_items(frappe_module, order_service._get_value(order, "name"))
    order.subtotal = sum(_float(_get_value(item, "line_total")) for item in items)
    order.items_count = len(items)
    order.save(ignore_permissions=True)
    return order


def _audit(order, action, user, frappe_module):
    if hasattr(order, "add_comment"):
        order.add_comment("Info", f"{action} by {user} at {frappe_module.utils.now_datetime()}")


def _serialize_item(item):
    return {
        "name": _get_value(item, "name"),
        "order_name": _get_value(item, "order_name"),
        "item_code": _get_value(item, "item_code"),
        "item_name": _get_value(item, "item_name"),
        "qty": _float(_get_value(item, "qty")),
        "unit_price": _float(_get_value(item, "unit_price")),
        "line_total": _float(_get_value(item, "line_total")),
        "notes": _get_value(item, "notes"),
    }


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _quantity(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


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
