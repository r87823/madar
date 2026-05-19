from madar.permissions.checks import has_permission
from madar.services.order_service import CREATE_PERMISSION


PRODUCT_FIELDS = ["item_code", "item_name", "stock_uom", "disabled", "image"]
MAX_PRODUCT_LIMIT = 20


def list_products(user, search="", frappe_module=None, limit=MAX_PRODUCT_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles = frappe_module.get_roles(user)
    if not has_permission(roles, CREATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض المنتجات للطلبات.")

    safe_limit = max(1, min(int(limit or MAX_PRODUCT_LIMIT), MAX_PRODUCT_LIMIT))
    filters = {"disabled": 0}
    search_text = (search or "").strip()
    if search_text:
        filters["item_name"] = ["like", f"%{search_text}%"]

    rows = frappe_module.get_all(
        "Item",
        filters=filters,
        fields=PRODUCT_FIELDS,
        order_by="item_name asc",
        limit=safe_limit,
    )
    return _ok({"items": [_serialize_product(row, frappe_module) for row in rows]})


def get_default_price(item_code, frappe_module):
    try:
        rows = frappe_module.get_all(
            "Item Price",
            filters={"item_code": item_code, "selling": 1},
            fields=["price_list_rate"],
            order_by="modified desc",
            limit=1,
        )
        if not rows:
            rows = frappe_module.get_all(
                "Item Price",
                filters={"item_code": item_code},
                fields=["price_list_rate"],
                order_by="modified desc",
                limit=1,
            )
    except Exception:
        rows = []

    if not rows:
        return 0
    return _float(_get_value(rows[0], "price_list_rate"))


def _serialize_product(row, frappe_module):
    item_code = _get_value(row, "item_code")
    return {
        "item_code": item_code,
        "item_name": _get_value(row, "item_name"),
        "stock_uom": _get_value(row, "stock_uom"),
        "disabled": _get_value(row, "disabled") or 0,
        "image": _get_value(row, "image"),
        "default_price": get_default_price(item_code, frappe_module),
    }


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


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
