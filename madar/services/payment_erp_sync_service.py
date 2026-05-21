from madar.permissions.checks import has_permission
from madar.services import notification_service


SYNC_PERMISSION = "accounting.view_sync_logs"
FULL_ACCESS_PERMISSION = "system.full_access"
MAX_PAYMENT_SYNC_LIMIT = 100
SYNC_PAYMENT_FIELDS = [
    "name",
    "madar_order",
    "amount",
    "payment_method",
    "payment_status",
    "collected_by_user",
    "collected_at",
    "collection_context",
    "reference_no",
    "notes",
    "is_cancelled",
    "cancellation_reason",
    "erp_sync_status",
    "erp_sync_error",
    "erp_payment_entry",
    "erp_payment_entry_docstatus",
    "erp_payment_submitted_at",
    "erp_payment_submit_error",
    "modified",
]
MODE_OF_PAYMENT = {
    "cash": "Cash",
    "card": "Card",
    "transfer": "Bank Transfer",
    "online": "Online",
}


def list_payment_sync_items(user, frappe_module=None, limit=MAX_PAYMENT_SYNC_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error
    rows = frappe_module.get_all(
        "Madar Payment",
        filters={"payment_status": "collected", "is_cancelled": 0},
        fields=SYNC_PAYMENT_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_PAYMENT_SYNC_LIMIT), MAX_PAYMENT_SYNC_LIMIT)),
    )
    return _ok({"items": [_serialize_payment(row, frappe_module) for row in rows]})


def get_payment_sync_item(user, payment_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error
    payment, lookup_error = _get_payment(payment_name, frappe_module)
    if lookup_error:
        return lookup_error
    return _ok(_serialize_payment(payment, frappe_module))


def retry_payment_sync(user, payment_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    allowed, error = _can_view_sync(user, frappe_module)
    if not allowed:
        return error
    payment, lookup_error = _get_payment(payment_name, frappe_module)
    if lookup_error:
        return lookup_error
    if _get_value(payment, "erp_sync_status") == "synced":
        return _error("PAYMENT_ALREADY_SYNCED", "تمت مزامنة الدفع مسبقًا.")
    return sync_payment_to_erp(payment_name, frappe_module=frappe_module)


def validate_payment_ready_for_sync(payment_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    payment, lookup_error = _get_payment(payment_name, frappe_module)
    if lookup_error:
        return lookup_error
    validation_error = _validate_payment(payment)
    if validation_error:
        return validation_error
    order, order_error = _get_order(_get_value(payment, "madar_order"), frappe_module)
    if order_error:
        return order_error
    if not (_get_value(order, "erp_sales_order") or "").strip():
        return _error("ORDER_NOT_SYNCED_TO_ERP", "يجب مزامنة الطلب مع ERP قبل مزامنة الدفع.")
    return _ok(_serialize_payment(payment, frappe_module, order=order))


def prepare_payment_entry_payload(payment_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    ready = validate_payment_ready_for_sync(payment_name, frappe_module=frappe_module)
    if not ready["ok"]:
        return ready

    payment, _lookup_error = _get_payment(payment_name, frappe_module)
    order, _order_error = _get_order(_get_value(payment, "madar_order"), frappe_module)
    sales_order = _get_sales_order(_get_value(order, "erp_sales_order"), frappe_module)
    amount = _float(_get_value(payment, "amount"))
    payment_method = _get_value(payment, "payment_method")
    mode_of_payment = MODE_OF_PAYMENT.get(payment_method, payment_method)
    company = _get_value(sales_order, "company")
    paid_to = _default_paid_to_account(mode_of_payment, company, frappe_module)
    paid_from = _default_receivable_account(sales_order, company, frappe_module)
    account_context = _payment_entry_account_context(paid_from, paid_to, company, frappe_module)
    if not account_context["ok"]:
        return account_context
    remarks = "\n".join(
        part
        for part in [
            f"Madar Payment: {_get_value(payment, 'name')}",
            f"Madar Order: {_get_value(payment, 'madar_order')}",
            f"ERP Sales Order: {_get_value(order, 'erp_sales_order')}",
            (_get_value(payment, "notes") or "").strip(),
        ]
        if part
    )
    return _ok(
        {
            "payment": _get_value(payment, "name"),
            "madar_order": _get_value(payment, "madar_order"),
            "erp_sales_order": _get_value(order, "erp_sales_order"),
            "party_type": "Customer",
            "party": _get_value(sales_order, "customer") or _get_value(order, "customer_name"),
            "company": company,
            "paid_from": paid_from,
            "paid_to": paid_to,
            "paid_from_account_currency": account_context["data"]["paid_from_account_currency"],
            "paid_to_account_currency": account_context["data"]["paid_to_account_currency"],
            "source_exchange_rate": account_context["data"]["source_exchange_rate"],
            "target_exchange_rate": account_context["data"]["target_exchange_rate"],
            "paid_amount": amount,
            "received_amount": amount,
            "mode_of_payment": mode_of_payment,
            "reference_no": _get_value(payment, "reference_no") or _get_value(payment, "name"),
            "reference_date": _today(frappe_module),
            "posting_date": _today(frappe_module),
            "remarks": remarks,
        }
    )


def create_payment_entry(payload, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    try:
        doc = frappe_module.get_doc(map_payment_to_payment_entry(payload)).insert(ignore_permissions=True)
        _commit(frappe_module)
        return _ok({"name": _get_value(doc, "name")})
    except Exception as exc:
        return _error("ERP_PAYMENT_SYNC_FAILED", _safe_error_message(exc))


def map_payment_to_payment_entry(payload):
    data = {
        "doctype": "Payment Entry",
        "docstatus": 0,
        "payment_type": "Receive",
        "party_type": "Customer",
        "party": payload.get("party"),
        "posting_date": payload.get("posting_date"),
        "paid_from": payload.get("paid_from"),
        "paid_to": payload.get("paid_to"),
        "paid_from_account_currency": payload.get("paid_from_account_currency"),
        "paid_to_account_currency": payload.get("paid_to_account_currency"),
        "source_exchange_rate": _float(payload.get("source_exchange_rate")),
        "target_exchange_rate": _float(payload.get("target_exchange_rate")),
        "paid_amount": _float(payload.get("paid_amount")),
        "received_amount": _float(payload.get("received_amount")),
        "mode_of_payment": payload.get("mode_of_payment"),
        "reference_no": payload.get("reference_no"),
        "reference_date": payload.get("reference_date"),
        "remarks": payload.get("remarks"),
    }
    if payload.get("company"):
        data["company"] = payload.get("company")
    return data


def sync_payment_to_erp(payment_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    validation = validate_payment_ready_for_sync(payment_name, frappe_module=frappe_module)
    if not validation["ok"]:
        return validation
    payload = prepare_payment_entry_payload(payment_name, frappe_module=frappe_module)
    if not payload["ok"]:
        if payload["error"]["code"] in {"ERP_PAYMENT_ACCOUNT_UNRESOLVED", "ERP_PAYMENT_CURRENCY_UNRESOLVED"}:
            mark_payment_sync_failed(payment_name, payload["error"]["message"], frappe_module=frappe_module)
        return payload
    created = create_payment_entry(payload["data"], frappe_module=frappe_module)
    if not created["ok"]:
        mark_payment_sync_failed(payment_name, created["error"]["message"], frappe_module=frappe_module)
        return created
    return mark_payment_sync_success(payment_name, created["data"]["name"], frappe_module=frappe_module)


def mark_payment_sync_success(payment_name, payment_entry_name, frappe_module=None):
    payment, lookup_error = _get_payment(payment_name, frappe_module)
    if lookup_error:
        return lookup_error
    payment.erp_sync_status = "synced"
    payment.erp_sync_error = ""
    payment.erp_payment_entry = (payment_entry_name or "").strip()
    payment.erp_payment_entry_docstatus = 0
    payment.erp_payment_submit_error = ""
    payment.save(ignore_permissions=True)
    _audit(payment, "mark_payment_sync_success")
    _commit(frappe_module)
    return _ok(_serialize_payment(payment, frappe_module))


def mark_payment_sync_failed(payment_name, error, frappe_module=None):
    payment, lookup_error = _get_payment(payment_name, frappe_module)
    if lookup_error:
        return lookup_error
    payment.erp_sync_status = "failed"
    payment.erp_sync_error = (error or "").strip()[:200]
    payment.save(ignore_permissions=True)
    _audit(payment, "mark_payment_sync_failed")
    _notify_payment_sync_failed(payment_name, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_payment(payment, frappe_module))


def _notify_payment_sync_failed(payment_name, frappe_module):
    notification_service.safe_notify_users(
        notification_service.users_with_permission(
            SYNC_PERMISSION,
            frappe_module=frappe_module,
        ),
        title="فشل في مزامنة ERP",
        message=f"فشلت مزامنة Madar Payment {payment_name}. يرجى المراجعة.",
        event_type="erp_sync_failed",
        entity_type="Madar Payment",
        entity_name=payment_name,
        priority="high",
        route_key="erp_sync_review",
        route_params={"entity_type": "Madar Payment", "entity_name": payment_name},
        action_label="مراجعة المزامنة",
        frappe_module=frappe_module,
    )


def _validate_payment(payment):
    if _get_value(payment, "erp_sync_status") == "synced":
        return _error("PAYMENT_ALREADY_SYNCED", "تمت مزامنة الدفع مسبقًا.")
    if _get_value(payment, "payment_status") != "collected" or bool(_get_value(payment, "is_cancelled")):
        return _error("PAYMENT_NOT_COLLECTED", "يمكن مزامنة المدفوعات المحصلة غير الملغاة فقط.")
    if _float(_get_value(payment, "amount")) <= 0:
        return _error("PAYMENT_AMOUNT_INVALID", "مبلغ الدفع يجب أن يكون أكبر من صفر.")
    return None


def _can_view_sync(user, frappe_module):
    roles = frappe_module.get_roles(user)
    if has_permission(roles, SYNC_PERMISSION) or has_permission(roles, FULL_ACCESS_PERMISSION):
        return True, None
    return False, _error("PERMISSION_DENIED", "ليست لديك صلاحية مراجعة مزامنة المدفوعات.")


def _get_payment(payment_name, frappe_module):
    if frappe_module is None:
        import frappe as frappe_module

    try:
        return frappe_module.get_doc("Madar Payment", payment_name), None
    except Exception:
        return None, _error("PAYMENT_NOT_FOUND", "الدفع غير موجود.")


def _get_order(order_name, frappe_module):
    try:
        return frappe_module.get_doc("Madar Order", order_name), None
    except Exception:
        return None, _error("ORDER_NOT_FOUND", "الطلب غير موجود.")


def _get_sales_order(sales_order_name, frappe_module):
    if not sales_order_name:
        return None
    try:
        return frappe_module.get_doc("Sales Order", sales_order_name)
    except Exception:
        return None


def _default_paid_to_account(mode_of_payment, company, frappe_module):
    if mode_of_payment and company:
        rows = _safe_get_all(
            frappe_module,
            "Mode of Payment Account",
            filters={"parent": mode_of_payment, "company": company},
            fields=["default_account"],
            limit=1,
        )
        if rows:
            account = _get_value(rows[0], "default_account")
            if account:
                return account
    account_type = "Cash" if mode_of_payment == "Cash" else "Bank"
    return _first_account(frappe_module, company, account_type)


def _default_receivable_account(sales_order, company, frappe_module):
    debit_to = _get_value(sales_order, "debit_to")
    if debit_to:
        return debit_to
    return _first_account(frappe_module, company, "Receivable")


def _first_account(frappe_module, company, account_type):
    filters = {"account_type": account_type, "is_group": 0}
    if company:
        filters["company"] = company
    rows = _safe_get_all(
        frappe_module,
        "Account",
        filters=filters,
        fields=["name"],
        limit=1,
    )
    return _get_value(rows[0], "name") if rows else None


def _payment_entry_account_context(paid_from, paid_to, company, frappe_module):
    if not paid_from or not paid_to:
        return _error(
            "ERP_PAYMENT_ACCOUNT_UNRESOLVED",
            "تعذر تحديد حسابات سند الدفع في ERP. راجع إعدادات الحسابات وطرق الدفع.",
        )
    company_currency = _company_currency(company, frappe_module)
    paid_from_currency = _account_currency(paid_from, company_currency, frappe_module)
    paid_to_currency = _account_currency(paid_to, company_currency, frappe_module)
    if not company_currency or not paid_from_currency or not paid_to_currency:
        return _error(
            "ERP_PAYMENT_CURRENCY_UNRESOLVED",
            "تعذر تحديد عملة سند الدفع في ERP.",
        )
    if paid_from_currency != company_currency or paid_to_currency != company_currency:
        return _error(
            "ERP_PAYMENT_CURRENCY_UNRESOLVED",
            "عملة سند الدفع مختلفة عن عملة الشركة وتحتاج سعر صرف معتمد.",
        )
    return _ok(
        {
            "paid_from_account_currency": paid_from_currency,
            "paid_to_account_currency": paid_to_currency,
            "source_exchange_rate": 1.0,
            "target_exchange_rate": 1.0,
        }
    )


def _company_currency(company, frappe_module):
    if not company:
        return None
    try:
        return frappe_module.get_cached_value("Company", company, "default_currency")
    except Exception:
        return None


def _account_currency(account, fallback_currency, frappe_module):
    if not account:
        return None
    try:
        return frappe_module.get_cached_value("Account", account, "account_currency") or fallback_currency
    except Exception:
        return fallback_currency


def _safe_get_all(frappe_module, doctype, filters=None, fields=None, limit=1):
    try:
        return frappe_module.get_all(doctype, filters=filters, fields=fields or ["name"], limit=limit)
    except Exception:
        return []


def _serialize_payment(payment, frappe_module, order=None):
    if order is None:
        order, _error_result = _get_order(_get_value(payment, "madar_order"), frappe_module)
    return {
        "name": _get_value(payment, "name"),
        "madar_order": _get_value(payment, "madar_order"),
        "customer_name": _get_value(order, "customer_name") if order else "",
        "erp_sales_order": _get_value(order, "erp_sales_order") if order else "",
        "amount": _float(_get_value(payment, "amount")),
        "payment_method": _get_value(payment, "payment_method"),
        "payment_status": _get_value(payment, "payment_status"),
        "collected_by_user": _get_value(payment, "collected_by_user"),
        "collected_at": _string_or_none(_get_value(payment, "collected_at")),
        "collection_context": _get_value(payment, "collection_context"),
        "reference_no": _get_value(payment, "reference_no"),
        "notes": _get_value(payment, "notes"),
        "is_cancelled": bool(_get_value(payment, "is_cancelled")),
        "erp_sync_status": _get_value(payment, "erp_sync_status") or "pending",
        "erp_sync_error": _get_value(payment, "erp_sync_error"),
        "erp_payment_entry": _get_value(payment, "erp_payment_entry"),
        "erp_payment_entry_docstatus": int(_float(_get_value(payment, "erp_payment_entry_docstatus")))
        if _get_value(payment, "erp_payment_entry_docstatus") not in {None, ""}
        else None,
        "erp_payment_submitted_at": _string_or_none(_get_value(payment, "erp_payment_submitted_at")),
        "erp_payment_submit_error": _get_value(payment, "erp_payment_submit_error"),
    }


def _audit(doc, action):
    if hasattr(doc, "add_comment"):
        doc.add_comment("Info", action)


def _commit(frappe_module):
    if frappe_module is not None and hasattr(frappe_module, "db"):
        frappe_module.db.commit()


def _today(frappe_module):
    if hasattr(frappe_module.utils, "nowdate"):
        return frappe_module.utils.nowdate()
    return frappe_module.utils.now_datetime().date().isoformat()


def _safe_error_message(exc):
    message = str(exc).strip().splitlines()[0] if str(exc).strip() else "ERP payment sync failed"
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


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}
