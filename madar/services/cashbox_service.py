from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.services import notification_service


VIEW_OWN_PERMISSION = "cashbox.view_own"
SUBMIT_PERMISSION = "cashbox.submit"
REVIEW_PERMISSION = "cashbox.review"
ACCOUNTING_PERMISSION = "accounting.view_sync_logs"
FULL_ACCESS_PERMISSION = "system.full_access"
MAX_ENTRY_LIMIT = 200
CASHBOX_FIELDS = [
    "name",
    "user",
    "cashbox_date",
    "status",
    "expected_cash",
    "submitted_cash",
    "difference",
    "submitted_at",
    "reviewed_by",
    "reviewed_at",
    "return_reason",
    "closed_at",
    "modified",
]
CASHBOX_ENTRY_FIELDS = [
    "name",
    "cashbox",
    "payment",
    "madar_order",
    "amount",
    "entry_type",
    "created_by_user",
    "created_at",
    "modified",
]


def record_cash_payment(payment, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    if _get_value(payment, "payment_method") != "cash":
        return _ok({"skipped": True})

    owner = _get_value(payment, "collected_by_user")
    cashbox = _get_or_create_daily_cashbox(owner, frappe_module)
    if _get_value(cashbox, "status") in {"approved", "closed"}:
        return _error("CASHBOX_ALREADY_APPROVED", "الصندوق معتمد ولا يمكن تعديله.")

    existing = frappe_module.get_all(
        "Madar Cashbox Entry",
        filters={"payment": _get_value(payment, "name")},
        fields=["name", "cashbox"],
        limit=1,
    )
    if existing:
        return _ok({"cashbox": _get_value(existing[0], "cashbox"), "entry": _get_value(existing[0], "name")})

    entry = frappe_module.get_doc(
        {
            "doctype": "Madar Cashbox Entry",
            "cashbox": _get_value(cashbox, "name"),
            "payment": _get_value(payment, "name"),
            "madar_order": _get_value(payment, "madar_order"),
            "amount": _float(_get_value(payment, "amount")),
            "entry_type": "cash_payment",
            "created_by_user": owner,
            "created_at": _server_now(frappe_module),
        }
    )
    entry.insert(ignore_permissions=True)
    _sync_cashbox_totals(cashbox, frappe_module)
    _audit(entry, "record_cash_payment", owner, frappe_module)
    _commit(frappe_module)
    return _ok({"cashbox": _get_value(cashbox, "name"), "entry": _get_value(entry, "name")})


def get_my_cashbox(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, VIEW_OWN_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض صندوقك.")
    cashbox = _find_daily_cashbox(user, frappe_module) or _get_or_create_daily_cashbox(user, frappe_module)
    _sync_cashbox_totals(cashbox, frappe_module)
    return _ok(_serialize_cashbox(cashbox, frappe_module))


def list_my_cashbox_entries(user, frappe_module=None, cashbox_name=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, VIEW_OWN_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض قيود صندوقك.")
    cashbox = _get_cashbox(frappe_module, cashbox_name) if cashbox_name else _find_daily_cashbox(user, frappe_module)
    if not cashbox:
        return _error("CASHBOX_NOT_FOUND", "الصندوق غير موجود.")
    if _get_value(cashbox, "user") != user and not _can_review(permissions):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض هذا الصندوق.")
    return _ok({"items": _cashbox_entries(_get_value(cashbox, "name"), frappe_module)})


def submit_my_cashbox(user, submitted_cash, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, SUBMIT_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تسليم الصندوق.")
    submitted_cash = _float(submitted_cash)
    if submitted_cash < 0:
        return _error("CASHBOX_SUBMITTED_CASH_INVALID", "المبلغ المسلم يجب ألا يكون سالبًا.")
    cashbox = _find_daily_cashbox(user, frappe_module)
    if not cashbox:
        return _error("CASHBOX_NOT_FOUND", "الصندوق غير موجود.")
    if _get_value(cashbox, "status") == "submitted":
        return _error("CASHBOX_ALREADY_SUBMITTED", "تم تسليم الصندوق مسبقًا.")
    if _get_value(cashbox, "status") in {"approved", "closed"}:
        return _error("CASHBOX_ALREADY_APPROVED", "الصندوق معتمد ولا يمكن تعديله.")

    expected = _expected_cash(_get_value(cashbox, "name"), frappe_module)
    cashbox.expected_cash = expected
    cashbox.submitted_cash = submitted_cash
    cashbox.difference = submitted_cash - expected
    cashbox.status = "submitted"
    cashbox.submitted_at = _server_now(frappe_module)
    cashbox.return_reason = ""
    cashbox.save(ignore_permissions=True)
    _audit(cashbox, "submit_cashbox", user, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_cashbox(cashbox, frappe_module))


def list_cashboxes_for_review(user, frappe_module=None, limit=100):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not (_can_review(permissions) or has_permission(roles, ACCOUNTING_PERMISSION)):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية مراجعة الصناديق.")
    rows = frappe_module.get_all(
        "Madar Cashbox",
        filters={"status": ["in", ["submitted"]]},
        fields=CASHBOX_FIELDS,
        order_by="modified desc",
        limit=limit,
    )
    return _ok({"items": [_serialize_cashbox(row, frappe_module, include_entries=False) for row in rows]})


def get_cashbox(user, cashbox_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    cashbox = _get_cashbox(frappe_module, cashbox_name)
    if not cashbox:
        return _error("CASHBOX_NOT_FOUND", "الصندوق غير موجود.")
    if _get_value(cashbox, "user") != user and not (_can_review(permissions) or has_permission(roles, ACCOUNTING_PERMISSION)):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض هذا الصندوق.")
    _sync_cashbox_totals(cashbox, frappe_module)
    return _ok(_serialize_cashbox(cashbox, frappe_module))


def approve_cashbox(user, cashbox_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permissions = _user_permissions(user, frappe_module)
    if not _can_review(permissions):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية اعتماد الصندوق.")
    cashbox = _get_cashbox(frappe_module, cashbox_name)
    if not cashbox:
        return _error("CASHBOX_NOT_FOUND", "الصندوق غير موجود.")
    if _get_value(cashbox, "status") != "submitted":
        if _get_value(cashbox, "status") in {"approved", "closed"}:
            return _error("CASHBOX_ALREADY_APPROVED", "الصندوق معتمد بالفعل.")
        return _error("CASHBOX_NOT_SUBMITTED", "لا يمكن اعتماد صندوق غير مرسل.")
    cashbox.status = "approved"
    cashbox.reviewed_by = user
    cashbox.reviewed_at = _server_now(frappe_module)
    cashbox.save(ignore_permissions=True)
    _audit(cashbox, "approve_cashbox", user, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_cashbox(cashbox, frappe_module))


def return_cashbox(user, cashbox_name, reason, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    if not (reason or "").strip():
        return _error("CASHBOX_RETURN_REASON_REQUIRED", "سبب إعادة الصندوق مطلوب.")
    _roles, permissions = _user_permissions(user, frappe_module)
    if not _can_review(permissions):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إعادة الصندوق.")
    cashbox = _get_cashbox(frappe_module, cashbox_name)
    if not cashbox:
        return _error("CASHBOX_NOT_FOUND", "الصندوق غير موجود.")
    if _get_value(cashbox, "status") != "submitted":
        if _get_value(cashbox, "status") in {"approved", "closed"}:
            return _error("CASHBOX_ALREADY_APPROVED", "الصندوق معتمد ولا يمكن تعديله.")
        return _error("CASHBOX_NOT_SUBMITTED", "لا يمكن إعادة صندوق غير مرسل.")
    cashbox.status = "returned"
    cashbox.reviewed_by = user
    cashbox.reviewed_at = _server_now(frappe_module)
    cashbox.return_reason = reason.strip()
    cashbox.save(ignore_permissions=True)
    _audit(cashbox, "return_cashbox", user, frappe_module)
    notification_service.safe_notify_user(
        _get_value(cashbox, "user"),
        title="تم إرجاع الصندوق",
        message=f"تم إرجاع الصندوق للمراجعة. السبب: {reason.strip()}",
        event_type="cashbox_returned",
        entity_type="Madar Cashbox",
        entity_name=_get_value(cashbox, "name"),
        priority="high",
        frappe_module=frappe_module,
    )
    _commit(frappe_module)
    return _ok(_serialize_cashbox(cashbox, frappe_module))


def _get_or_create_daily_cashbox(user, frappe_module):
    cashbox = _find_daily_cashbox(user, frappe_module)
    if cashbox:
        return cashbox
    doc = frappe_module.get_doc(
        {
            "doctype": "Madar Cashbox",
            "user": user,
            "cashbox_date": _cashbox_date(frappe_module),
            "status": "open",
            "expected_cash": 0,
            "submitted_cash": 0,
            "difference": 0,
            "submitted_at": None,
            "reviewed_by": "",
            "reviewed_at": None,
            "return_reason": "",
            "closed_at": None,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def _find_daily_cashbox(user, frappe_module):
    rows = frappe_module.get_all(
        "Madar Cashbox",
        filters={"user": user, "cashbox_date": _cashbox_date(frappe_module)},
        fields=["name"],
        limit=1,
    )
    if not rows:
        return None
    return _get_cashbox(frappe_module, _get_value(rows[0], "name"))


def _get_cashbox(frappe_module, cashbox_name):
    try:
        return frappe_module.get_doc("Madar Cashbox", cashbox_name)
    except Exception:
        return None


def _sync_cashbox_totals(cashbox, frappe_module):
    expected = _expected_cash(_get_value(cashbox, "name"), frappe_module)
    cashbox.expected_cash = expected
    cashbox.difference = _float(_get_value(cashbox, "submitted_cash")) - expected
    cashbox.save(ignore_permissions=True)


def _expected_cash(cashbox_name, frappe_module):
    entries = frappe_module.get_all(
        "Madar Cashbox Entry",
        filters={"cashbox": cashbox_name},
        fields=["amount"],
        limit=MAX_ENTRY_LIMIT,
    )
    return sum(_float(_get_value(entry, "amount")) for entry in entries)


def _cashbox_entries(cashbox_name, frappe_module):
    rows = frappe_module.get_all(
        "Madar Cashbox Entry",
        filters={"cashbox": cashbox_name},
        fields=CASHBOX_ENTRY_FIELDS,
        order_by="modified desc",
        limit=MAX_ENTRY_LIMIT,
    )
    return [_serialize_entry(row) for row in rows]


def _serialize_cashbox(cashbox, frappe_module, include_entries=True):
    expected = _expected_cash(_get_value(cashbox, "name"), frappe_module)
    submitted = _float(_get_value(cashbox, "submitted_cash"))
    data = {
        "name": _get_value(cashbox, "name"),
        "user": _get_value(cashbox, "user"),
        "cashbox_date": _string_or_none(_get_value(cashbox, "cashbox_date")),
        "status": _get_value(cashbox, "status") or "open",
        "expected_cash": expected,
        "submitted_cash": submitted,
        "difference": submitted - expected,
        "submitted_at": _string_or_none(_get_value(cashbox, "submitted_at")),
        "reviewed_by": _get_value(cashbox, "reviewed_by"),
        "reviewed_at": _string_or_none(_get_value(cashbox, "reviewed_at")),
        "return_reason": _get_value(cashbox, "return_reason"),
        "closed_at": _string_or_none(_get_value(cashbox, "closed_at")),
    }
    if include_entries:
        data["entries"] = _cashbox_entries(data["name"], frappe_module)
    return data


def _serialize_entry(entry):
    return {
        "name": _get_value(entry, "name"),
        "cashbox": _get_value(entry, "cashbox"),
        "payment": _get_value(entry, "payment"),
        "madar_order": _get_value(entry, "madar_order"),
        "amount": _float(_get_value(entry, "amount")),
        "entry_type": _get_value(entry, "entry_type"),
        "created_by_user": _get_value(entry, "created_by_user"),
        "created_at": _string_or_none(_get_value(entry, "created_at")),
    }


def _cashbox_date(frappe_module):
    return _server_now(frappe_module).date().isoformat()


def _user_permissions(user, frappe_module):
    roles = frappe_module.get_roles(user)
    return roles, get_permissions_for_roles(roles)


def _can_review(permissions):
    permissions = set(permissions or [])
    return FULL_ACCESS_PERMISSION in permissions or REVIEW_PERMISSION in permissions


def _audit(doc, action, user, frappe_module):
    if hasattr(doc, "add_comment"):
        doc.add_comment("Info", f"{action} by {user} at {_server_now(frappe_module)}")


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


def _error(code, message):
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}
