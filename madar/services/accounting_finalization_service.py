from madar.permissions.checks import has_permission
from madar.services import accounting_review_service


READ_PERMISSION = "accounting.view_sync_logs"
FINALIZE_PERMISSION = "accounting.finalize"
FULL_ACCESS_PERMISSION = "system.full_access"
FINAL_SUBMIT_ACCOUNTING_STATUSES = {"ready_for_review", "reviewed"}
FINALIZE_ORDER_FIELDS = [
    "name",
    "customer_name",
    "subtotal",
    "paid_amount",
    "remaining_amount",
    "payment_status",
    "order_status",
    "delivery_status",
    "fulfillment_method",
    "erp_sales_order",
    "erp_sales_order_docstatus",
    "erp_sales_invoice",
    "erp_sales_invoice_docstatus",
    "erp_invoice_sync_status",
    "accounting_status",
    "accounting_finalized_at",
    "accounting_finalized_by",
    "accounting_finalization_error",
]
FINALIZE_PAYMENT_FIELDS = [
    "name",
    "madar_order",
    "amount",
    "payment_method",
    "payment_status",
    "is_cancelled",
    "erp_sync_status",
    "erp_payment_entry",
    "erp_payment_entry_docstatus",
    "erp_payment_submitted_at",
    "erp_payment_submit_error",
]


def get_finalization_status(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permission_error = _require_read(user, frappe_module)
    if permission_error:
        return permission_error
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    return _ok(_build_status(order, roles, frappe_module))


def validate_order_ready_for_final_submit(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_order_ready(order, frappe_module)
    if validation_error:
        return validation_error
    return _ok(_serialize_order(order))


def submit_sales_invoice(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permission_error = _require_finalize(user, frappe_module)
    if permission_error:
        return permission_error
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_order_ready(order, frappe_module)
    if validation_error:
        return validation_error

    invoice_name = (_get_value(order, "erp_sales_invoice") or "").strip()
    if not invoice_name:
        return _store_order_error(
            order,
            "SALES_INVOICE_NOT_SYNCED",
            "لم يتم إنشاء فاتورة ERP للطلب.",
            frappe_module,
        )
    invoice = _get_erp_doc("Sales Invoice", invoice_name, frappe_module)
    if invoice is None:
        return _store_order_error(
            order,
            "ERP_DOCUMENT_MISSING",
            "فاتورة ERP غير موجودة.",
            frappe_module,
        )
    docstatus = _int(_get_value(invoice, "docstatus"))
    if docstatus == 1:
        order.erp_sales_invoice_docstatus = 1
        order.accounting_finalization_error = ""
        order.save(ignore_permissions=True)
        _commit(frappe_module)
        return _ok(_serialize_order(order))
    if docstatus != 0:
        return _store_order_error(
            order,
            "ORDER_NOT_READY_FOR_FINAL_SUBMIT",
            "فاتورة ERP ليست مسودة وقابلة للاعتماد.",
            frappe_module,
        )
    try:
        invoice.submit()
        order.erp_sales_invoice_docstatus = 1
        order.accounting_finalization_error = ""
        order.save(ignore_permissions=True)
        _audit(order, "submit_sales_invoice", user, frappe_module)
        _commit(frappe_module)
        return _ok(_serialize_order(order))
    except Exception as exc:
        return _store_order_error(
            order,
            "SALES_INVOICE_SUBMIT_FAILED",
            _safe_error_message(exc, "فشل اعتماد فاتورة ERP."),
            frappe_module,
        )


def submit_payment_entries_for_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permission_error = _require_finalize(user, frappe_module)
    if permission_error:
        return permission_error
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_order_ready(order, frappe_module)
    if validation_error:
        return validation_error

    payments = _payments(order_name, frappe_module)
    results = []
    for payment in payments:
        payment_error = _validate_payment(payment)
        if payment_error:
            _store_payment_error(payment, payment_error["error"]["message"], frappe_module)
            return payment_error
        payment_entry_name = (_get_value(payment, "erp_payment_entry") or "").strip()
        if not payment_entry_name:
            _store_payment_error(payment, "لم تتم مزامنة سند الدفع مع ERP.", frappe_module)
            return _error("PAYMENT_ENTRY_NOT_SYNCED", "لم تتم مزامنة سند الدفع مع ERP.")
        payment_entry = _get_erp_doc("Payment Entry", payment_entry_name, frappe_module)
        if payment_entry is None:
            _store_payment_error(payment, "سند الدفع في ERP غير موجود.", frappe_module)
            return _error("ERP_DOCUMENT_MISSING", "سند الدفع في ERP غير موجود.")

        docstatus = _int(_get_value(payment_entry, "docstatus"))
        if docstatus == 1:
            payment_doc = _mark_payment_entry_submitted(payment, user, frappe_module)
            results.append(_serialize_payment(payment_doc))
            continue
        if docstatus != 0:
            _store_payment_error(payment, "سند الدفع في ERP ليس مسودة قابلة للاعتماد.", frappe_module)
            return _error("PAYMENT_ENTRY_SUBMIT_FAILED", "سند الدفع في ERP ليس مسودة قابلة للاعتماد.")
        try:
            payment_entry.submit()
            payment_doc = _mark_payment_entry_submitted(payment, user, frappe_module)
            results.append(_serialize_payment(payment_doc))
        except Exception as exc:
            message = _safe_error_message(exc, "فشل اعتماد سند الدفع.")
            _store_payment_error(payment, message, frappe_module)
            return _error("PAYMENT_ENTRY_SUBMIT_FAILED", message)

    _commit(frappe_module)
    return _ok({"items": results})


def finalize_order_accounting(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permission_error = _require_finalize(user, frappe_module)
    if permission_error:
        return permission_error
    order, error = _get_order(order_name, frappe_module)
    if error:
        return error
    validation_error = _validate_order_ready(order, frappe_module)
    if validation_error:
        return validation_error
    if (_get_value(order, "payment_status") or "") != "paid" or _float(_get_value(order, "remaining_amount")) > 0:
        return _store_order_error(order, "ORDER_NOT_PAID", "لا يمكن الإقفال قبل سداد الطلب.", frappe_module)
    if _int(_get_value(order, "erp_sales_invoice_docstatus")) != 1:
        return _store_order_error(
            order,
            "SALES_INVOICE_NOT_SYNCED",
            "يجب اعتماد فاتورة ERP قبل الإقفال.",
            frappe_module,
        )
    payments = _payments(order_name, frappe_module)
    for payment in payments:
        if _int(_get_value(payment, "erp_payment_entry_docstatus")) != 1:
            return _error("PAYMENT_ENTRY_NOT_SYNCED", "يجب اعتماد كل سندات الدفع في ERP قبل الإقفال.")
    cashbox = accounting_review_service._cashbox_summary(order, payments, frappe_module)
    if cashbox["cash_payments_total"] > 0 and not cashbox["reviewed"]:
        return _store_order_error(
            order,
            "CASHBOX_NOT_APPROVED",
            "يجب اعتماد الصندوق قبل الإقفال المحاسبي.",
            frappe_module,
        )

    now = _server_now(frappe_module)
    order.accounting_status = "reviewed"
    order.accounting_finalized_at = now
    order.accounting_finalized_by = user
    order.accounting_finalization_error = ""
    order.save(ignore_permissions=True)
    _audit(order, "finalize_order_accounting", user, frappe_module)
    _commit(frappe_module)
    return _ok(_build_status(order, frappe_module.get_roles(user), frappe_module))


def _build_status(order, roles, frappe_module):
    payments = _payments(_get_value(order, "name"), frappe_module)
    return {
        "order": _serialize_order(order),
        "can_finalize": has_permission(roles, FINALIZE_PERMISSION) or has_permission(roles, FULL_ACCESS_PERMISSION),
        "erp_sales_invoice_docstatus": _int_or_none(_get_value(order, "erp_sales_invoice_docstatus")),
        "payments": [_serialize_payment(payment) for payment in payments],
        "finalized": bool(_get_value(order, "accounting_finalized_at")),
        "accounting_finalized_at": _string_or_none(_get_value(order, "accounting_finalized_at")),
        "accounting_finalized_by": _get_value(order, "accounting_finalized_by"),
        "accounting_finalization_error": _get_value(order, "accounting_finalization_error"),
    }


def _validate_order_ready(order, frappe_module):
    if (_get_value(order, "accounting_status") or "") not in FINAL_SUBMIT_ACCOUNTING_STATUSES:
        return _error("ORDER_NOT_READY_FOR_FINAL_SUBMIT", "الطلب غير جاهز للاعتماد المحاسبي النهائي.")
    if (_get_value(order, "order_status") or "") != "approved":
        return _error("ORDER_NOT_READY_FOR_FINAL_SUBMIT", "الطلب غير معتمد تشغيليًا.")
    if not (_get_value(order, "erp_sales_order") or "").strip():
        return _error("ORDER_NOT_SYNCED_TO_ERP", "لم تتم مزامنة الطلب مع أمر بيع ERP.")
    if _int(_get_value(order, "erp_sales_order_docstatus")) != 1:
        return _error("ORDER_NOT_READY_FOR_FINAL_SUBMIT", "أمر بيع ERP غير معتمد.")
    if not accounting_review_service._delivery_complete(order):
        return _error("ORDER_NOT_READY_FOR_FINAL_SUBMIT", "التسليم التشغيلي غير مكتمل.")
    if _float(_get_value(order, "subtotal")) <= 0:
        return _error("ORDER_NOT_READY_FOR_FINAL_SUBMIT", "إجمالي الطلب غير صالح.")
    sales_order = _get_erp_doc("Sales Order", _get_value(order, "erp_sales_order"), frappe_module)
    if sales_order is None:
        return _error("ERP_DOCUMENT_MISSING", "أمر بيع ERP غير موجود.")
    if _int(_get_value(sales_order, "docstatus")) != 1:
        return _error("ORDER_NOT_READY_FOR_FINAL_SUBMIT", "أمر بيع ERP غير معتمد.")
    return None


def _validate_payment(payment):
    if _get_value(payment, "payment_status") != "collected" or bool(_get_value(payment, "is_cancelled")):
        return _error("PAYMENT_ENTRY_NOT_SYNCED", "يمكن اعتماد المدفوعات المحصلة غير الملغاة فقط.")
    if _float(_get_value(payment, "amount")) <= 0:
        return _error("PAYMENT_ENTRY_SUBMIT_FAILED", "مبلغ الدفع غير صالح.")
    if _get_value(payment, "erp_sync_status") != "synced":
        return _error("PAYMENT_ENTRY_NOT_SYNCED", "لم تتم مزامنة سند الدفع مع ERP.")
    return None


def _payments(order_name, frappe_module):
    return list(
        frappe_module.get_all(
            "Madar Payment",
            filters={"madar_order": order_name, "payment_status": "collected", "is_cancelled": 0},
            fields=FINALIZE_PAYMENT_FIELDS,
            order_by="modified desc",
            limit=200,
        )
        or []
    )


def _mark_payment_entry_submitted(payment, user, frappe_module):
    payment_doc = payment
    if not callable(getattr(payment_doc, "save", None)):
        payment_doc, _error_result = _get_payment(_get_value(payment, "name"), frappe_module)
    payment_doc.erp_payment_entry_docstatus = 1
    payment_doc.erp_payment_submitted_at = _server_now(frappe_module)
    payment_doc.erp_payment_submit_error = ""
    payment_doc.save(ignore_permissions=True)
    _audit(payment_doc, "submit_payment_entry", user, frappe_module)
    return payment_doc


def _store_order_error(order, code, message, frappe_module):
    order.accounting_finalization_error = (message or "").strip()[:200]
    order.save(ignore_permissions=True)
    _commit(frappe_module)
    return _error(code, message)


def _store_payment_error(payment, message, frappe_module):
    payment_doc = payment
    if not callable(getattr(payment_doc, "save", None)):
        payment_doc, _error_result = _get_payment(_get_value(payment, "name"), frappe_module)
    payment_doc.erp_payment_submit_error = (message or "").strip()[:200]
    payment_doc.save(ignore_permissions=True)
    _commit(frappe_module)


def _require_read(user, frappe_module):
    roles = frappe_module.get_roles(user)
    if has_permission(roles, READ_PERMISSION) or has_permission(roles, FULL_ACCESS_PERMISSION):
        return roles, None
    return roles, _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض الإقفال المحاسبي.")


def _require_finalize(user, frappe_module):
    roles = frappe_module.get_roles(user)
    if has_permission(roles, FINALIZE_PERMISSION) or has_permission(roles, FULL_ACCESS_PERMISSION):
        return roles, None
    return roles, _error("ACCOUNTING_FINALIZE_PERMISSION_DENIED", "ليست لديك صلاحية الإقفال المحاسبي النهائي.")


def _get_order(order_name, frappe_module):
    try:
        return frappe_module.get_doc("Madar Order", order_name), None
    except Exception:
        return None, _error("ORDER_NOT_FOUND", "الطلب غير موجود.")


def _get_payment(payment_name, frappe_module):
    try:
        return frappe_module.get_doc("Madar Payment", payment_name), None
    except Exception:
        return None, _error("PAYMENT_ENTRY_NOT_SYNCED", "الدفع غير موجود.")


def _get_erp_doc(doctype, name, frappe_module):
    if not name:
        return None
    try:
        return frappe_module.get_doc(doctype, name)
    except Exception:
        return None


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
        "fulfillment_method": _get_value(order, "fulfillment_method") or "branch_pickup",
        "erp_sales_order": _get_value(order, "erp_sales_order"),
        "erp_sales_order_docstatus": _int_or_none(_get_value(order, "erp_sales_order_docstatus")),
        "erp_sales_invoice": _get_value(order, "erp_sales_invoice"),
        "erp_sales_invoice_docstatus": _int_or_none(_get_value(order, "erp_sales_invoice_docstatus")),
        "erp_invoice_sync_status": _get_value(order, "erp_invoice_sync_status"),
        "accounting_status": _get_value(order, "accounting_status"),
        "accounting_finalized_at": _string_or_none(_get_value(order, "accounting_finalized_at")),
        "accounting_finalized_by": _get_value(order, "accounting_finalized_by"),
        "accounting_finalization_error": _get_value(order, "accounting_finalization_error"),
    }


def _serialize_payment(payment):
    return {
        "name": _get_value(payment, "name"),
        "madar_order": _get_value(payment, "madar_order"),
        "amount": _float(_get_value(payment, "amount")),
        "payment_method": _get_value(payment, "payment_method"),
        "payment_status": _get_value(payment, "payment_status"),
        "erp_sync_status": _get_value(payment, "erp_sync_status"),
        "erp_payment_entry": _get_value(payment, "erp_payment_entry"),
        "erp_payment_entry_docstatus": _int_or_none(_get_value(payment, "erp_payment_entry_docstatus")),
        "erp_payment_submitted_at": _string_or_none(_get_value(payment, "erp_payment_submitted_at")),
        "erp_payment_submit_error": _get_value(payment, "erp_payment_submit_error"),
    }


def _audit(doc, action, user, frappe_module):
    if hasattr(doc, "add_comment"):
        doc.add_comment("Info", f"{action} by {user} at {_server_now(frappe_module)}")


def _server_now(frappe_module):
    utils = getattr(frappe_module, "utils", None)
    if utils is not None and hasattr(utils, "now_datetime"):
        return utils.now_datetime()
    if utils is not None and hasattr(utils, "now"):
        return utils.now()
    return None


def _commit(frappe_module):
    if frappe_module is not None and hasattr(frappe_module, "db"):
        frappe_module.db.commit()


def _safe_error_message(exc, fallback):
    message = str(exc).strip().splitlines()[0] if str(exc).strip() else fallback
    return message[:200]


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


def _int(value):
    return int(_float(value))


def _int_or_none(value):
    if value in {None, ""}:
        return None
    return _int(value)


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}
