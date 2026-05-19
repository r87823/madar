from madar.services import order_service


ITEM_FIELDS = ["item_code", "qty", "unit_price"]


def validate_order_ready_for_sync(order_name, frappe_module=None):
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_order(order)
    if validation_error:
        return validation_error
    return _ok(order_service._serialize_order(order))


def prepare_sales_order_payload(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_order(order)
    if validation_error:
        return validation_error

    items = _get_items(order_name, frappe_module)
    if not items:
        return _error("ORDER_HAS_NO_ITEMS", "لا يمكن مزامنة طلب بدون أصناف.")

    payload = {
        "customer": order_service._get_value(order, "customer_name"),
        "branch": order_service._get_value(order, "assigned_branch")
        or order_service._get_value(order, "branch"),
        "items": [
            {
                "item_code": order_service._get_value(item, "item_code"),
                "qty": _float(order_service._get_value(item, "qty")),
                "rate": _float(order_service._get_value(item, "unit_price")),
            }
            for item in items
        ],
        "notes": order_service._get_value(order, "notes"),
        "madar_order": order_service._get_value(order, "name"),
    }
    return _ok(payload)


def mark_sync_failed(order_name, error, frappe_module=None):
    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    order.erp_sync_status = "failed"
    order.erp_sync_error = (error or "").strip()
    order.save(ignore_permissions=True)
    _audit(order, "mark_sync_failed")
    _commit(frappe_module)
    return _ok(order_service._serialize_order(order))


def mark_sync_success(order_name, sales_order_name, frappe_module=None):
    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    order.erp_sync_status = "synced"
    order.erp_sync_error = None
    order.erp_sales_order = (sales_order_name or "").strip()
    order.save(ignore_permissions=True)
    _audit(order, "mark_sync_success")
    _commit(frappe_module)
    return _ok(order_service._serialize_order(order))


def _get_order(order_name, frappe_module):
    if frappe_module is None:
        import frappe as frappe_module

    try:
        return frappe_module.get_doc("Madar Order", order_name), None
    except Exception:
        return None, _error("ORDER_NOT_FOUND", "الطلب غير موجود.")


def _validate_order(order):
    if order_service._get_value(order, "order_status") != "approved":
        return _error("ORDER_NOT_APPROVED", "يمكن مزامنة الطلبات المعتمدة فقط.")
    if order_service._get_value(order, "erp_sync_status") == "synced":
        return _error("ORDER_ALREADY_SYNCED", "تمت مزامنة الطلب مسبقًا.")
    if int(_float(order_service._get_value(order, "items_count"))) <= 0:
        return _error("ORDER_HAS_NO_ITEMS", "لا يمكن مزامنة طلب بدون أصناف.")
    if _float(order_service._get_value(order, "subtotal")) < 0:
        return _error("INVALID_ORDER_STATE", "حالة الطلب غير صالحة للمزامنة.")
    return None


def _get_items(order_name, frappe_module):
    try:
        return frappe_module.get_all(
            "Madar Order Item",
            filters={"order_name": order_name},
            fields=ITEM_FIELDS,
            order_by="creation asc",
            limit=200,
        )
    except Exception:
        return []


def _audit(order, action):
    if hasattr(order, "add_comment"):
        order.add_comment("Info", action)


def _commit(frappe_module):
    if frappe_module is not None and hasattr(frappe_module, "db"):
        frappe_module.db.commit()


def _float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {"code": code, "message": message},
    }
