from madar.permissions.checks import has_permission
from madar.services import order_service


ITEM_FIELDS = ["item_code", "qty", "unit_price"]
SYNC_PERMISSION = "accounting.view_sync_logs"
SYNC_ORDER_FIELDS = [
    "name",
    "customer_name",
    "subtotal",
    "order_status",
    "delivery_status",
    "erp_sync_status",
    "erp_sync_error",
    "erp_sales_order",
    "erp_sales_order_docstatus",
    "erp_sales_invoice",
    "erp_sales_invoice_docstatus",
    "erp_invoice_sync_status",
    "erp_invoice_sync_error",
    "erp_invoice_created_at",
    "approved_at",
    "approved_by",
]
MAX_SYNC_LIST_LIMIT = 50


def list_sync_orders(user, frappe_module=None, limit=MAX_SYNC_LIST_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error

    rows = frappe_module.get_all(
        "Madar Order",
        filters={"order_status": "approved"},
        fields=SYNC_ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_SYNC_LIST_LIMIT), MAX_SYNC_LIST_LIMIT)),
    )
    return _ok({"items": [_serialize_sync_order(row) for row in rows]})


def get_sync_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error

    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    return _ok(_serialize_sync_order(order))


def retry_sync_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error

    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    if order_service._get_value(order, "erp_sync_status") == "synced":
        return _error("ORDER_ALREADY_SYNCED", "تمت مزامنة الطلب مسبقًا.")
    if order_service._get_value(order, "erp_sync_status") not in {"pending", "failed", None, ""}:
        return _error("INVALID_ORDER_STATE", "حالة المزامنة غير قابلة للإعادة.")

    result = sync_order_to_erp(order_name, frappe_module=frappe_module)
    if not result["ok"]:
        return result
    updated_order, updated_error = _get_order(order_name, frappe_module)
    if updated_error:
        return updated_error
    return _ok(_serialize_sync_order(updated_order))


def submit_erp_sales_order_for_user(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error

    return submit_erp_sales_order(order_name, frappe_module=frappe_module)


def list_invoice_sync_orders(user, frappe_module=None, limit=MAX_SYNC_LIST_LIMIT):
    return list_sync_orders(user, frappe_module=frappe_module, limit=limit)


def get_invoice_sync_order(user, order_name, frappe_module=None):
    return get_sync_order(user, order_name, frappe_module=frappe_module)


def retry_invoice_sync(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error

    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    if _has_synced_invoice(order):
        return _error("SALES_INVOICE_ALREADY_SYNCED", "تم إنشاء فاتورة ERP لهذا الطلب مسبقًا.")
    if order_service._get_value(order, "erp_invoice_sync_status") not in {"pending", "failed", None, ""}:
        return _error("INVALID_ORDER_STATE", "حالة مزامنة الفاتورة غير قابلة للإعادة.")

    result = sync_sales_invoice_to_erp(order_name, frappe_module=frappe_module)
    if not result["ok"]:
        return result
    updated_order, updated_error = _get_order(order_name, frappe_module)
    if updated_error:
        return updated_error
    return _ok(_serialize_sync_order(updated_order))


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
    order.erp_sales_order_docstatus = 0
    if not order_service._get_value(order, "erp_invoice_sync_status"):
        order.erp_invoice_sync_status = "pending"
    order.save(ignore_permissions=True)
    _audit(order, "mark_sync_success")
    _commit(frappe_module)
    return _ok(order_service._serialize_order(order))


def submit_erp_sales_order(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    sales_order_name = (order_service._get_value(order, "erp_sales_order") or "").strip()
    if not sales_order_name:
        return _error("ORDER_NOT_SYNCED_TO_ERP", "لم تتم مزامنة الطلب مع أمر بيع ERP.")

    try:
        sales_order = frappe_module.get_doc("Sales Order", sales_order_name)
        docstatus = int(_float(order_service._get_value(sales_order, "docstatus")))
        if docstatus != 1:
            sales_order.submit()
            docstatus = int(_float(order_service._get_value(sales_order, "docstatus") or 1))
        order.erp_sales_order_docstatus = docstatus
        order.save(ignore_permissions=True)
        _audit(order, "submit_erp_sales_order")
        _commit(frappe_module)
        return _ok(_serialize_sync_order(order))
    except Exception as exc:
        return _error("ERP_SALES_ORDER_SUBMIT_FAILED", _safe_error_message(exc))


def validate_order_ready_for_invoice(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, error = _get_order(order_name, frappe_module)
    if error:
        return error

    validation_error = _validate_invoice_order(order, frappe_module)
    if validation_error:
        return validation_error
    return _ok(_serialize_sync_order(order))


def prepare_sales_invoice_payload(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_invoice_order(order, frappe_module)
    if validation_error:
        return validation_error

    items = _get_items(order_name, frappe_module)
    if not items:
        return _error("ORDER_HAS_NO_ITEMS", "لا يمكن إنشاء فاتورة بدون أصناف.")

    sales_order = _get_sales_order_doc(order, frappe_module)
    sales_order_name = order_service._get_value(order, "erp_sales_order")
    payload = {
        "madar_order": order_service._get_value(order, "name"),
        "sales_order": sales_order_name,
        "customer": order_service._get_value(sales_order, "customer")
        or order_service._get_value(order, "customer_name"),
        "company": order_service._get_value(sales_order, "company"),
        "posting_date": frappe_module.utils.nowdate(),
        "items": [
            {
                "item_code": order_service._get_value(item, "item_code"),
                "qty": _float(order_service._get_value(item, "qty")),
                "rate": _float(order_service._get_value(item, "unit_price")),
                "sales_order": sales_order_name,
            }
            for item in items
        ],
        "remarks": f"Madar Order: {order_service._get_value(order, 'name')}\nSales Order: {sales_order_name}",
    }
    return _ok(payload)


def create_sales_invoice_draft(payload, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    try:
        doc = frappe_module.get_doc(
            map_madar_order_to_sales_invoice(payload)
        ).insert(ignore_permissions=True)
        _commit(frappe_module)
        return _ok({"name": order_service._get_value(doc, "name")})
    except Exception as exc:
        return _error("ERP_INVOICE_SYNC_FAILED", _safe_error_message(exc))


def map_madar_order_to_sales_invoice(payload):
    invoice = {
        "doctype": "Sales Invoice",
        "docstatus": 0,
        "customer": payload.get("customer"),
        "posting_date": payload.get("posting_date"),
        "items": [
            {
                "item_code": item.get("item_code"),
                "qty": _float(item.get("qty")),
                "rate": _float(item.get("rate")),
                "sales_order": item.get("sales_order"),
            }
            for item in payload.get("items", [])
        ],
        "remarks": payload.get("remarks") or "",
    }
    if payload.get("company"):
        invoice["company"] = payload.get("company")
    return invoice


def sync_sales_invoice_to_erp(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    validation = validate_order_ready_for_invoice(order_name, frappe_module=frappe_module)
    if not validation["ok"]:
        return validation

    payload = prepare_sales_invoice_payload(order_name, frappe_module=frappe_module)
    if not payload["ok"]:
        return payload

    created = create_sales_invoice_draft(payload["data"], frappe_module=frappe_module)
    if not created["ok"]:
        mark_invoice_sync_failed(
            order_name,
            created["error"]["message"],
            frappe_module=frappe_module,
        )
        return created

    return mark_invoice_sync_success(
        order_name,
        created["data"]["name"],
        frappe_module=frappe_module,
    )


def mark_invoice_sync_success(order_name, sales_invoice_name, frappe_module=None):
    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    order.erp_invoice_sync_status = "synced"
    order.erp_invoice_sync_error = None
    order.erp_sales_invoice = (sales_invoice_name or "").strip()
    order.erp_sales_invoice_docstatus = 0
    order.erp_invoice_created_at = _server_now(frappe_module)
    order.save(ignore_permissions=True)
    _audit(order, "mark_invoice_sync_success")
    _commit(frappe_module)
    return _ok(_serialize_sync_order(order))


def mark_invoice_sync_failed(order_name, error, frappe_module=None):
    order, lookup_error = _get_order(order_name, frappe_module)
    if lookup_error:
        return lookup_error
    order.erp_invoice_sync_status = "failed"
    order.erp_invoice_sync_error = (error or "").strip()
    order.save(ignore_permissions=True)
    _audit(order, "mark_invoice_sync_failed")
    _commit(frappe_module)
    return _ok(_serialize_sync_order(order))


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


def _validate_invoice_order(order, frappe_module):
    if order_service._get_value(order, "order_status") != "approved":
        return _error("ORDER_NOT_APPROVED", "يمكن إنشاء فاتورة للطلبات المعتمدة فقط.")
    if _has_synced_invoice(order):
        return _error("SALES_INVOICE_ALREADY_SYNCED", "تم إنشاء فاتورة ERP لهذا الطلب مسبقًا.")
    sales_order_name = (order_service._get_value(order, "erp_sales_order") or "").strip()
    if not sales_order_name:
        return _error("ORDER_NOT_SYNCED_TO_ERP", "لم تتم مزامنة الطلب مع أمر بيع ERP.")
    if int(_float(order_service._get_value(order, "items_count"))) <= 0:
        return _error("ORDER_HAS_NO_ITEMS", "لا يمكن إنشاء فاتورة بدون أصناف.")
    if _float(order_service._get_value(order, "subtotal")) < 0:
        return _error("INVALID_ORDER_STATE", "حالة الطلب غير صالحة للفوترة.")
    sales_order = _get_sales_order_doc(order, frappe_module)
    if sales_order is None:
        return _error("ORDER_NOT_SYNCED_TO_ERP", "لم يتم العثور على أمر بيع ERP المرتبط.")
    sales_order_docstatus = int(_float(order_service._get_value(sales_order, "docstatus")))
    if sales_order_docstatus != 1:
        return _error("ORDER_NOT_READY_FOR_INVOICE", "يجب اعتماد أمر البيع في ERP قبل إنشاء الفاتورة.")
    if int(_float(order_service._get_value(order, "erp_sales_order_docstatus"))) != sales_order_docstatus:
        order.erp_sales_order_docstatus = sales_order_docstatus
        order.save(ignore_permissions=True)
    if not _order_delivery_completed(order):
        return _error("ORDER_NOT_DELIVERED", "لا يمكن إنشاء فاتورة قبل اكتمال التسليم التشغيلي.")
    return None


def _get_sales_order_doc(order, frappe_module):
    sales_order_name = (order_service._get_value(order, "erp_sales_order") or "").strip()
    if not sales_order_name:
        return None
    try:
        return frappe_module.get_doc("Sales Order", sales_order_name)
    except Exception:
        return None


def _has_synced_invoice(order):
    return (
        order_service._get_value(order, "erp_invoice_sync_status") == "synced"
        or bool(order_service._get_value(order, "erp_sales_invoice"))
    )


def _order_delivery_completed(order):
    fulfillment_method = order_service._get_value(order, "fulfillment_method") or "branch_pickup"
    delivery_status = order_service._get_value(order, "delivery_status")
    if fulfillment_method == "customer_delivery":
        return delivery_status == "delivered_to_customer"
    return delivery_status == "customer_picked_up"


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


def _can_view_sync(user, frappe_module):
    roles = frappe_module.get_roles(user)
    if has_permission(roles, SYNC_PERMISSION):
        return True, None
    return False, _error("PERMISSION_DENIED", "ليست لديك صلاحية مراجعة مزامنة ERP.")


def _serialize_sync_order(order):
    return {
        "name": order_service._get_value(order, "name"),
        "customer_name": order_service._get_value(order, "customer_name"),
        "subtotal": _float(order_service._get_value(order, "subtotal")),
        "order_status": order_service._get_value(order, "order_status"),
        "delivery_status": order_service._get_value(order, "delivery_status"),
        "erp_sync_status": order_service._get_value(order, "erp_sync_status"),
        "erp_sync_error": order_service._get_value(order, "erp_sync_error"),
        "erp_sales_order": order_service._get_value(order, "erp_sales_order"),
        "erp_sales_order_docstatus": int(
            _float(order_service._get_value(order, "erp_sales_order_docstatus"))
        )
        if order_service._get_value(order, "erp_sales_order_docstatus") not in {None, ""}
        else None,
        "erp_sales_invoice": order_service._get_value(order, "erp_sales_invoice"),
        "erp_sales_invoice_docstatus": int(
            _float(order_service._get_value(order, "erp_sales_invoice_docstatus"))
        )
        if order_service._get_value(order, "erp_sales_invoice_docstatus") not in {None, ""}
        else None,
        "erp_invoice_sync_status": order_service._get_value(order, "erp_invoice_sync_status")
        or "pending",
        "erp_invoice_sync_error": order_service._get_value(order, "erp_invoice_sync_error"),
        "erp_invoice_created_at": order_service._string_or_none(
            order_service._get_value(order, "erp_invoice_created_at")
        ),
        "approved_at": order_service._string_or_none(order_service._get_value(order, "approved_at")),
        "approved_by": order_service._get_value(order, "approved_by"),
    }


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


def _server_now(frappe_module):
    utils = getattr(frappe_module, "utils", None)
    if utils is not None and hasattr(utils, "now_datetime"):
        return utils.now_datetime()
    if utils is not None and hasattr(utils, "now"):
        return utils.now()
    if utils is not None and hasattr(utils, "nowdate"):
        return utils.nowdate()
    return None


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {"code": code, "message": message},
    }
