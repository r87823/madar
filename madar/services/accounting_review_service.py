from madar.permissions.checks import has_permission
from madar.services import order_service


ACCOUNTING_PERMISSION = "accounting.view_sync_logs"
FULL_ACCESS_PERMISSION = "system.full_access"
MAX_REVIEW_LIST_LIMIT = 50
ORDER_FIELDS = [
    "name",
    "customer_name",
    "subtotal",
    "paid_amount",
    "remaining_amount",
    "payment_status",
    "order_status",
    "delivery_status",
    "production_status",
    "fulfillment_method",
    "erp_sales_order",
    "erp_sales_order_docstatus",
    "erp_sync_status",
    "erp_sync_error",
    "erp_sales_invoice",
    "erp_sales_invoice_docstatus",
    "erp_invoice_sync_status",
    "erp_invoice_sync_error",
    "accounting_status",
    "accounting_review_notes",
    "accounting_reviewed_by",
    "accounting_reviewed_at",
    "accounting_finalized_at",
    "accounting_finalized_by",
    "accounting_finalization_error",
    "modified",
]
PAYMENT_FIELDS = [
    "name",
    "madar_order",
    "amount",
    "payment_method",
    "payment_status",
    "is_cancelled",
    "erp_sync_status",
    "erp_sync_error",
    "erp_payment_entry",
    "erp_payment_entry_docstatus",
    "erp_payment_submitted_at",
    "erp_payment_submit_error",
]
CASHBOX_ENTRY_FIELDS = ["name", "cashbox", "payment", "madar_order", "amount"]
CASHBOX_FIELDS = ["name", "status", "reviewed_by", "reviewed_at"]


def list_orders_for_accounting_review(user, frappe_module=None, limit=MAX_REVIEW_LIST_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permission_error = _require_accounting(user, frappe_module)
    if permission_error:
        return permission_error

    rows = frappe_module.get_all(
        "Madar Order",
        filters={"order_status": "approved", "accounting_status": ["!=", "reviewed"]},
        fields=ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_REVIEW_LIST_LIMIT), MAX_REVIEW_LIST_LIMIT)),
    )
    return _ok({"items": [_build_summary(row, frappe_module) for row in rows]})


def get_order_accounting_summary(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permission_error = _require_accounting(user, frappe_module)
    if permission_error:
        return permission_error
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    return _ok(_build_summary(order, frappe_module))


def mark_accounting_reviewed(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permission_error = _require_accounting(user, frappe_module)
    if permission_error:
        return permission_error
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    summary = _build_summary(order, frappe_module)
    if summary["accounting_status"] != "ready_for_review" and not has_permission(roles, FULL_ACCESS_PERMISSION):
        return _error(
            "ORDER_NOT_READY_FOR_ACCOUNTING_REVIEW",
            "الطلب غير جاهز للمراجعة المحاسبية النهائية.",
        )
    order.accounting_status = "reviewed"
    order.accounting_reviewed_by = user
    order.accounting_reviewed_at = _server_now(frappe_module)
    order.save(ignore_permissions=True)
    _audit(order, "mark_accounting_reviewed", user, frappe_module)
    _commit(frappe_module)
    return _ok(_build_summary(order, frappe_module))


def mark_accounting_needs_attention(user, order_name, notes, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permission_error = _require_accounting(user, frappe_module)
    if permission_error:
        return permission_error
    if not (notes or "").strip():
        return _error("ACCOUNTING_REVIEW_NOTES_REQUIRED", "ملاحظات المراجعة مطلوبة.")
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    order.accounting_status = "needs_attention"
    order.accounting_review_notes = (notes or "").strip()
    order.accounting_reviewed_by = user
    order.accounting_reviewed_at = _server_now(frappe_module)
    order.save(ignore_permissions=True)
    _audit(order, "mark_accounting_needs_attention", user, frappe_module)
    _commit(frappe_module)
    return _ok(_build_summary(order, frappe_module))


def _build_summary(order, frappe_module):
    payments = _payments(_get_value(order, "name"), frappe_module)
    cashbox = _cashbox_summary(order, payments, frappe_module)
    payment_summary = _payment_summary(payments)
    readiness = _readiness(order, payment_summary, cashbox)
    alerts = _alerts(order, payment_summary, cashbox, readiness)
    return {
        "order": _serialize_order(order),
        "erp_sales_order": {
            "erp_sales_order": _get_value(order, "erp_sales_order"),
            "erp_sales_order_docstatus": _int_or_none(_get_value(order, "erp_sales_order_docstatus")),
            "erp_sync_status": _get_value(order, "erp_sync_status"),
            "erp_sync_error": _get_value(order, "erp_sync_error"),
        },
        "erp_sales_invoice": {
            "erp_sales_invoice": _get_value(order, "erp_sales_invoice"),
            "erp_sales_invoice_docstatus": _int_or_none(_get_value(order, "erp_sales_invoice_docstatus")),
            "erp_invoice_sync_status": _get_value(order, "erp_invoice_sync_status"),
            "erp_invoice_sync_error": _get_value(order, "erp_invoice_sync_error"),
        },
        "payments": payment_summary,
        "cashbox": cashbox,
        "readiness": readiness,
        "alerts": alerts,
        "accounting_status": _accounting_status(order, alerts, readiness),
        "accounting_review_notes": _get_value(order, "accounting_review_notes"),
        "accounting_reviewed_by": _get_value(order, "accounting_reviewed_by"),
        "accounting_reviewed_at": _string_or_none(_get_value(order, "accounting_reviewed_at")),
        "accounting_finalized_at": _string_or_none(_get_value(order, "accounting_finalized_at")),
        "accounting_finalized_by": _get_value(order, "accounting_finalized_by"),
        "accounting_finalization_error": _get_value(order, "accounting_finalization_error"),
    }


def _serialize_order(order):
    return {
        "name": _get_value(order, "name"),
        "customer_name": _get_value(order, "customer_name"),
        "subtotal": _float(_get_value(order, "subtotal")),
        "paid_amount": _float(_get_value(order, "paid_amount")),
        "remaining_amount": _float(_get_value(order, "remaining_amount")),
        "payment_status": _get_value(order, "payment_status") or "unpaid",
        "order_status": _get_value(order, "order_status"),
        "delivery_status": _get_value(order, "delivery_status"),
        "production_status": _get_value(order, "production_status"),
    }


def _payments(order_name, frappe_module):
    rows = frappe_module.get_all(
        "Madar Payment",
        filters={"madar_order": order_name, "payment_status": "collected", "is_cancelled": 0},
        fields=PAYMENT_FIELDS,
        order_by="modified desc",
        limit=200,
    )
    return list(rows or [])


def _payment_summary(payments):
    total = 0
    methods = {}
    sync_statuses = {}
    items = []
    for payment in payments:
        amount = _float(_get_value(payment, "amount"))
        method = _get_value(payment, "payment_method") or "unknown"
        sync_status = _get_value(payment, "erp_sync_status") or "pending"
        total += amount
        methods[method] = methods.get(method, 0) + amount
        sync_statuses[sync_status] = sync_statuses.get(sync_status, 0) + 1
        items.append(
            {
                "name": _get_value(payment, "name"),
                "amount": amount,
                "payment_method": method,
                "erp_sync_status": sync_status,
                "erp_payment_entry": _get_value(payment, "erp_payment_entry"),
                "erp_payment_entry_docstatus": _int_or_none(
                    _get_value(payment, "erp_payment_entry_docstatus")
                ),
                "erp_payment_submitted_at": _string_or_none(
                    _get_value(payment, "erp_payment_submitted_at")
                ),
                "erp_payment_submit_error": _get_value(payment, "erp_payment_submit_error"),
            }
        )
    return {
        "count": len(payments),
        "total_collected": total,
        "methods": methods,
        "erp_sync_statuses": sync_statuses,
        "items": items,
    }


def _cashbox_summary(order, payments, frappe_module):
    cash_payments = [payment for payment in payments if _get_value(payment, "payment_method") == "cash"]
    cash_payment_names = [_get_value(payment, "name") for payment in cash_payments]
    if not cash_payment_names:
        return {
            "cash_payments_total": 0,
            "cashbox_names": [],
            "statuses": [],
            "reviewed": True,
        }
    entries = frappe_module.get_all(
        "Madar Cashbox Entry",
        filters={"payment": ["in", cash_payment_names]},
        fields=CASHBOX_ENTRY_FIELDS,
        limit=200,
    )
    cashbox_names = sorted({(_get_value(entry, "cashbox") or "") for entry in entries if _get_value(entry, "cashbox")})
    cashboxes = []
    if cashbox_names:
        cashboxes = frappe_module.get_all(
            "Madar Cashbox",
            filters={"name": ["in", cashbox_names]},
            fields=CASHBOX_FIELDS,
            limit=200,
        )
    statuses = sorted({(_get_value(cashbox, "status") or "open") for cashbox in cashboxes})
    return {
        "cash_payments_total": sum(_float(_get_value(payment, "amount")) for payment in cash_payments),
        "cashbox_names": cashbox_names,
        "statuses": statuses,
        "reviewed": bool(cash_payment_names) and len(cashbox_names) == len(cash_payment_names)
        and all(status in {"approved", "closed"} for status in statuses),
    }


def _readiness(order, payments, cashbox):
    subtotal = _float(_get_value(order, "subtotal"))
    total_collected = _float(payments["total_collected"])
    return {
        "has_erp_sales_order": bool(_get_value(order, "erp_sales_order")),
        "sales_order_submitted": _int_or_none(_get_value(order, "erp_sales_order_docstatus")) == 1,
        "delivered_or_picked_up": _delivery_complete(order),
        "has_sales_invoice_draft": bool(_get_value(order, "erp_sales_invoice"))
        and _get_value(order, "erp_invoice_sync_status") == "synced",
        "payments_match_order_total": abs(total_collected - subtotal) < 0.0001
        and _get_value(order, "payment_status") == "paid"
        and abs(_float(_get_value(order, "remaining_amount"))) < 0.0001,
        "payment_entries_synced_or_not_required": payments["count"] > 0
        and payments["erp_sync_statuses"].get("failed", 0) == 0
        and payments["erp_sync_statuses"].get("pending", 0) == 0
        and payments["erp_sync_statuses"].get("synced", 0) == payments["count"],
        "cashboxes_reviewed_for_cash_payments": cashbox["reviewed"],
    }


def _alerts(order, payments, cashbox, readiness):
    alerts = []
    if _get_value(order, "erp_sync_status") == "failed":
        alerts.append("ERP_SYNC_FAILED")
    if _get_value(order, "erp_invoice_sync_status") == "failed":
        alerts.append("ERP_INVOICE_SYNC_FAILED")
    if not readiness["payments_match_order_total"]:
        alerts.append("PAYMENTS_DO_NOT_MATCH_TOTAL")
    if payments["erp_sync_statuses"].get("failed", 0):
        alerts.append("PAYMENT_SYNC_FAILED")
    if cashbox["cash_payments_total"] > 0 and not readiness["cashboxes_reviewed_for_cash_payments"]:
        alerts.append("CASHBOX_NOT_APPROVED")
    missing_flags = [
        "has_erp_sales_order",
        "sales_order_submitted",
        "has_sales_invoice_draft",
        "payment_entries_synced_or_not_required",
    ]
    for flag in missing_flags:
        if not readiness[flag]:
            alerts.append(flag.upper())
    return alerts


def _accounting_status(order, alerts, readiness):
    stored = _get_value(order, "accounting_status")
    if stored == "reviewed":
        return "reviewed"
    if stored == "closed_later":
        return "closed_later"
    if stored == "needs_attention":
        return "needs_attention"
    if not readiness["delivered_or_picked_up"]:
        return "not_ready"
    if alerts:
        return "needs_attention"
    return "ready_for_review"


def _delivery_complete(order):
    fulfillment_method = _get_value(order, "fulfillment_method") or "branch_pickup"
    delivery_status = _get_value(order, "delivery_status")
    if fulfillment_method == "customer_delivery":
        return delivery_status == "delivered_to_customer"
    return delivery_status == "customer_picked_up"


def _require_accounting(user, frappe_module):
    roles = frappe_module.get_roles(user)
    if has_permission(roles, ACCOUNTING_PERMISSION) or has_permission(roles, FULL_ACCESS_PERMISSION):
        return roles, None
    return roles, _error("PERMISSION_DENIED", "ليست لديك صلاحية مراجعة الإقفال المحاسبي.")


def _get_order(order_name, frappe_module):
    try:
        return frappe_module.get_doc("Madar Order", order_name), None
    except Exception:
        return None, _error("ORDER_NOT_FOUND", "الطلب غير موجود.")


def _audit(order, action, user, frappe_module):
    if hasattr(order, "add_comment"):
        order.add_comment("Info", f"{action} by {user} at {_server_now(frappe_module)}")


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


def _int_or_none(value):
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}
