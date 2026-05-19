from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.permissions.scopes import get_context_scopes
from madar.services.employee_context import get_employee_context


COLLECT_PERMISSION = "payments.collect"
BRANCH_PERMISSION = "orders.create"
DELIVERY_UPDATE_PERMISSION = "delivery.update_batch"
ACCOUNTING_PERMISSION = "accounting.view_sync_logs"
FULL_ACCESS_PERMISSION = "system.full_access"
PAYMENT_METHODS = {"cash", "card", "transfer", "online"}
PAYABLE_ORDER_STATUSES = {"approved"}
BRANCH_PICKUP = "branch_pickup"
CUSTOMER_DELIVERY = "customer_delivery"
PAYMENT_FIELDS = [
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
    "modified",
]
ORDER_PAYMENT_FIELDS = [
    "name",
    "customer_name",
    "customer_phone",
    "order_status",
    "fulfillment_method",
    "destination_branch",
    "delivery_status",
    "subtotal",
    "paid_amount",
    "remaining_amount",
    "payment_status",
]
MAX_PAYMENT_LIMIT = 100


def collect_payment(
    user,
    order_name,
    amount,
    payment_method,
    reference_no="",
    notes="",
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, COLLECT_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تحصيل المدفوعات.")

    amount = _float(amount)
    if amount <= 0:
        return _error("PAYMENT_AMOUNT_INVALID", "مبلغ الدفع يجب أن يكون أكبر من صفر.")
    if payment_method not in PAYMENT_METHODS:
        return _error("PAYMENT_METHOD_INVALID", "طريقة الدفع غير مدعومة.")

    order = _get_order(frappe_module, order_name)
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")
    if _get_value(order, "order_status") not in PAYABLE_ORDER_STATUSES:
        return _error("ORDER_NOT_PAYABLE", "لا يمكن تحصيل دفعة لهذا الطلب.")

    context = _collection_context(user, roles, permissions, order, frappe_module)
    if not context:
        return _error("OUT_OF_SCOPE", "الطلب خارج نطاق التحصيل المسموح.")

    _recalculate_order_payment_summary(order, frappe_module)
    remaining = _float(_get_value(order, "remaining_amount"))
    if amount > remaining:
        return _error("PAYMENT_EXCEEDS_REMAINING_AMOUNT", "مبلغ الدفع يتجاوز المتبقي على الطلب.")

    payment = frappe_module.get_doc(
        {
            "doctype": "Madar Payment",
            "madar_order": _get_value(order, "name"),
            "amount": amount,
            "payment_method": payment_method,
            "payment_status": "collected",
            "collected_by_user": user,
            "collected_at": _server_now(frappe_module),
            "collection_context": context,
            "reference_no": (reference_no or "").strip(),
            "notes": (notes or "").strip(),
            "is_cancelled": 0,
            "cancellation_reason": "",
        }
    )
    payment.insert(ignore_permissions=True)
    _audit(payment, "collect_payment", user, frappe_module)

    cashbox = None
    if payment_method == "cash":
        from madar.services import cashbox_service

        cashbox = cashbox_service.record_cash_payment(payment, frappe_module=frappe_module)
        if not cashbox["ok"]:
            return cashbox

    _recalculate_order_payment_summary(order, frappe_module)
    _audit(order, "recalculate_payment_summary", user, frappe_module)
    _commit(frappe_module)
    data = _serialize_payment(payment)
    data["order"] = _serialize_order_payment(order)
    if cashbox:
        data["cashbox"] = cashbox["data"]
    return _ok(data)


def list_order_payments(user, order_name, frappe_module=None, limit=MAX_PAYMENT_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    order = _get_order(frappe_module, order_name)
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")
    if not _can_view_payments(user, roles, permissions, order, frappe_module):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض مدفوعات هذا الطلب.")

    rows = frappe_module.get_all(
        "Madar Payment",
        filters={"madar_order": order_name},
        fields=PAYMENT_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_PAYMENT_LIMIT), MAX_PAYMENT_LIMIT)),
    )
    return _ok({"items": [_serialize_payment(row) for row in rows]})


def get_payment(user, payment_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    payment = _get_payment(frappe_module, payment_name)
    if not payment:
        return _error("PAYMENT_NOT_FOUND", "الدفع غير موجود.")
    order = _get_order(frappe_module, _get_value(payment, "madar_order"))
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")
    if not _can_view_payments(user, roles, permissions, order, frappe_module):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض هذا الدفع.")
    return _ok(_serialize_payment(payment))


def _recalculate_order_payment_summary(order, frappe_module):
    subtotal = _float(_get_value(order, "subtotal"))
    payments = frappe_module.get_all(
        "Madar Payment",
        filters={"madar_order": _get_value(order, "name"), "payment_status": "collected", "is_cancelled": 0},
        fields=["amount"],
        limit=MAX_PAYMENT_LIMIT,
    )
    paid = sum(_float(_get_value(payment, "amount")) for payment in payments)
    remaining = max(subtotal - paid, 0)
    order.paid_amount = paid
    order.remaining_amount = remaining
    if paid <= 0:
        order.payment_status = "unpaid"
    elif remaining <= 0:
        order.payment_status = "paid"
    else:
        order.payment_status = "partially_paid"
    order.save(ignore_permissions=True)


def _collection_context(user, roles, permissions, order, frappe_module):
    if _has_full_access(permissions):
        return "admin"

    fulfillment_method = _get_value(order, "fulfillment_method") or BRANCH_PICKUP
    if fulfillment_method == BRANCH_PICKUP:
        if has_permission(roles, DELIVERY_UPDATE_PERMISSION) and not has_permission(roles, BRANCH_PERMISSION):
            return None
        return "branch" if _branch_in_scope(order, permissions, user, frappe_module) else None

    if fulfillment_method == CUSTOMER_DELIVERY:
        return "delivery" if _driver_assigned_to_order(user, _get_value(order, "name"), frappe_module) else None

    return None


def _can_view_payments(user, roles, permissions, order, frappe_module):
    if _has_full_access(permissions) or has_permission(roles, ACCOUNTING_PERMISSION):
        return True
    if has_permission(roles, COLLECT_PERMISSION):
        return bool(_collection_context(user, roles, permissions, order, frappe_module))
    return False


def _branch_in_scope(order, permissions, user, frappe_module):
    scopes = get_context_scopes(get_employee_context(user, frappe_module=frappe_module), permissions)
    branches = scopes.get("branch_names") or []
    if branches == ["*"]:
        return True
    return _get_value(order, "destination_branch") in branches


def _driver_assigned_to_order(user, order_name, frappe_module):
    links = frappe_module.get_all(
        "Madar Delivery Batch Order",
        filters={"madar_order": order_name},
        fields=["delivery_batch"],
        limit=MAX_PAYMENT_LIMIT,
    )
    for link in links:
        batch = _get_batch(frappe_module, _get_value(link, "delivery_batch"))
        if batch and _get_value(batch, "driver_user") == user:
            return True
    return False


def _get_order(frappe_module, order_name):
    try:
        return frappe_module.get_doc("Madar Order", order_name)
    except Exception:
        return None


def _get_payment(frappe_module, payment_name):
    try:
        return frappe_module.get_doc("Madar Payment", payment_name)
    except Exception:
        return None


def _get_batch(frappe_module, batch_name):
    try:
        return frappe_module.get_doc("Madar Delivery Batch", batch_name)
    except Exception:
        return None


def _user_permissions(user, frappe_module):
    roles = frappe_module.get_roles(user)
    return roles, get_permissions_for_roles(roles)


def _has_full_access(permissions):
    return FULL_ACCESS_PERMISSION in set(permissions or [])


def _serialize_payment(payment):
    return {
        "name": _get_value(payment, "name"),
        "madar_order": _get_value(payment, "madar_order"),
        "amount": _float(_get_value(payment, "amount")),
        "payment_method": _get_value(payment, "payment_method"),
        "payment_status": _get_value(payment, "payment_status"),
        "collected_by_user": _get_value(payment, "collected_by_user"),
        "collected_at": _string_or_none(_get_value(payment, "collected_at")),
        "collection_context": _get_value(payment, "collection_context"),
        "reference_no": _get_value(payment, "reference_no"),
        "notes": _get_value(payment, "notes"),
        "is_cancelled": bool(_get_value(payment, "is_cancelled")),
        "cancellation_reason": _get_value(payment, "cancellation_reason"),
    }


def _serialize_order_payment(order):
    return {
        "name": _get_value(order, "name"),
        "customer_name": _get_value(order, "customer_name"),
        "customer_phone": _get_value(order, "customer_phone"),
        "order_status": _get_value(order, "order_status"),
        "fulfillment_method": _get_value(order, "fulfillment_method") or BRANCH_PICKUP,
        "destination_branch": _get_value(order, "destination_branch"),
        "delivery_status": _get_value(order, "delivery_status"),
        "subtotal": _float(_get_value(order, "subtotal")),
        "paid_amount": _float(_get_value(order, "paid_amount")),
        "remaining_amount": _float(_get_value(order, "remaining_amount")),
        "payment_status": _get_value(order, "payment_status") or "unpaid",
    }


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
