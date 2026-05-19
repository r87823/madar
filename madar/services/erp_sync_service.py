from madar.services import order_service


ITEM_FIELDS = ["item_code", "qty", "unit_price"]


def sync_order_to_erp(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    validation = validate_order_ready_for_sync(order_name, frappe_module=frappe_module)
    if not validation["ok"]:
        return validation

    payload = prepare_sales_order_payload(order_name, frappe_module=frappe_module)
    if not payload["ok"]:
        return payload

    created = create_sales_order(payload["data"], frappe_module=frappe_module)
    if not created["ok"]:
        mark_sync_failed(
            order_name,
            created["error"]["message"],
            frappe_module=frappe_module,
        )
        return created

    return mark_sync_success(
        order_name,
        created["data"]["name"],
        frappe_module=frappe_module,
    )


def create_sales_order(payload, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    try:
        doc = frappe_module.get_doc(
            map_madar_order_to_sales_order(payload, frappe_module=frappe_module)
        ).insert(ignore_permissions=True)
        _commit(frappe_module)
        return _ok({"name": order_service._get_value(doc, "name")})
    except Exception as exc:
        return _error("ERP_SYNC_FAILED", _safe_error_message(exc))


def map_madar_order_to_sales_order(payload, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    madar_order = payload.get("madar_order")
    notes = (payload.get("notes") or "").strip()
    remarks_parts = []
    if notes:
        remarks_parts.append(notes)
    if madar_order:
        remarks_parts.append(f"Madar Order: {madar_order}")

    transaction_date = frappe_module.utils.nowdate()
    return {
        "doctype": "Sales Order",
        "customer": payload.get("customer"),
        "transaction_date": transaction_date,
        "delivery_date": transaction_date,
        "items": [
            {
                "item_code": item.get("item_code"),
                "qty": _float(item.get("qty")),
                "rate": _float(item.get("rate")),
                "delivery_date": transaction_date,
            }
            for item in payload.get("items", [])
        ],
        "remarks": "\n".join(remarks_parts),
    }


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


def _safe_error_message(exc):
    message = str(exc).strip().splitlines()[0] if str(exc).strip() else "ERP sync failed"
    return message[:200]


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {"code": code, "message": message},
    }
