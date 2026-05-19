from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.permissions.scopes import get_context_scopes
from madar.services.employee_context import get_employee_context


VIEW_PERMISSION = "delivery.view_assigned_batches"
UPDATE_PERMISSION = "delivery.update_batch"
BRANCH_PERMISSION = "orders.create"
FULL_ACCESS_PERMISSION = "system.full_access"
BRANCH_PICKUP = "branch_pickup"
CUSTOMER_DELIVERY = "customer_delivery"
ACTIVE_DELIVERY_STATUSES = {
    "ready_for_dispatch",
    "dispatched_to_branch",
    "received_at_branch",
    "ready_for_customer_pickup",
    "dispatched_to_customer",
    "failed_delivery",
}
FINAL_DELIVERY_STATUSES = {"customer_picked_up", "delivered_to_customer"}
ORDER_FIELDS = [
    "name",
    "customer_name",
    "customer_phone",
    "branch",
    "assigned_branch",
    "fulfillment_method",
    "destination_branch",
    "order_status",
    "production_status",
    "delivery_status",
    "ready_for_dispatch_at",
    "dispatched_at",
    "received_at_branch_at",
    "ready_for_customer_pickup_at",
    "customer_picked_up_at",
    "delivered_at",
    "failed_delivery_at",
    "failed_delivery_reason",
    "subtotal",
    "items_count",
    "modified",
]
MAX_QUEUE_LIMIT = 100


def sync_delivery_readiness(order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    order = _get_order(frappe_module, order_name)
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")

    current = _get_value(order, "delivery_status") or "not_ready"
    production_status = _get_value(order, "production_status") or "not_started"
    changed = False

    if production_status != "ready":
        if current not in {"not_ready"} | FINAL_DELIVERY_STATUSES:
            order.delivery_status = "not_ready"
            order.ready_for_dispatch_at = None
            changed = True
    elif current == "not_ready":
        order.delivery_status = "ready_for_dispatch"
        if not _get_value(order, "ready_for_dispatch_at"):
            order.ready_for_dispatch_at = _server_now(frappe_module)
        changed = True

    if changed:
        order.save(ignore_permissions=True)
        _audit(order, "sync_delivery_readiness", "system", frappe_module)
        _commit(frappe_module)
    return _ok(_serialize_order(order))


def list_dispatch_queue(user, frappe_module=None, limit=MAX_QUEUE_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, VIEW_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض مهام التوصيل.")

    filters = {"delivery_status": ["in", sorted(ACTIVE_DELIVERY_STATUSES)]}
    rows = frappe_module.get_all(
        "Madar Order",
        filters=filters,
        fields=ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_QUEUE_LIMIT), MAX_QUEUE_LIMIT)),
    )
    return _ok({"items": [_serialize_order(row) for row in rows]})


def mark_dispatched_to_branch(user, order_name, frappe_module=None):
    return _transition(
        user=user,
        order_name=order_name,
        next_status="dispatched_to_branch",
        allowed_from={"ready_for_dispatch"},
        timestamp_field="dispatched_at",
        action="mark_dispatched_to_branch",
        required_permission=UPDATE_PERMISSION,
        required_fulfillment=BRANCH_PICKUP,
        frappe_module=frappe_module,
    )


def mark_dispatched_to_customer(user, order_name, frappe_module=None):
    return _transition(
        user=user,
        order_name=order_name,
        next_status="dispatched_to_customer",
        allowed_from={"ready_for_dispatch"},
        timestamp_field="dispatched_at",
        action="mark_dispatched_to_customer",
        required_permission=UPDATE_PERMISSION,
        required_fulfillment=CUSTOMER_DELIVERY,
        frappe_module=frappe_module,
    )


def mark_delivered_to_customer(user, order_name, frappe_module=None):
    return _transition(
        user=user,
        order_name=order_name,
        next_status="delivered_to_customer",
        allowed_from={"dispatched_to_customer"},
        timestamp_field="delivered_at",
        action="mark_delivered_to_customer",
        required_permission=UPDATE_PERMISSION,
        required_fulfillment=CUSTOMER_DELIVERY,
        frappe_module=frappe_module,
    )


def mark_failed_delivery(user, order_name, reason, frappe_module=None):
    if not (reason or "").strip():
        return _error("REASON_REQUIRED", "سبب تعذر التسليم مطلوب.")
    return _transition(
        user=user,
        order_name=order_name,
        next_status="failed_delivery",
        allowed_from={"dispatched_to_customer"},
        timestamp_field="failed_delivery_at",
        action="mark_failed_delivery",
        required_permission=UPDATE_PERMISSION,
        required_fulfillment=CUSTOMER_DELIVERY,
        reason=reason,
        frappe_module=frappe_module,
    )


def mark_received_at_branch(user, order_name, frappe_module=None):
    return _transition(
        user=user,
        order_name=order_name,
        next_status="received_at_branch",
        allowed_from={"dispatched_to_branch"},
        timestamp_field="received_at_branch_at",
        action="mark_received_at_branch",
        required_permission=BRANCH_PERMISSION,
        required_fulfillment=BRANCH_PICKUP,
        require_branch_scope=True,
        frappe_module=frappe_module,
    )


def mark_ready_for_customer_pickup(user, order_name, frappe_module=None):
    return _transition(
        user=user,
        order_name=order_name,
        next_status="ready_for_customer_pickup",
        allowed_from={"received_at_branch"},
        timestamp_field="ready_for_customer_pickup_at",
        action="mark_ready_for_customer_pickup",
        required_permission=BRANCH_PERMISSION,
        required_fulfillment=BRANCH_PICKUP,
        require_branch_scope=True,
        frappe_module=frappe_module,
    )


def mark_customer_picked_up(user, order_name, frappe_module=None):
    return _transition(
        user=user,
        order_name=order_name,
        next_status="customer_picked_up",
        allowed_from={"ready_for_customer_pickup"},
        timestamp_field="customer_picked_up_at",
        action="mark_customer_picked_up",
        required_permission=BRANCH_PERMISSION,
        required_fulfillment=BRANCH_PICKUP,
        require_branch_scope=True,
        frappe_module=frappe_module,
    )


def _transition(
    *,
    user,
    order_name,
    next_status,
    allowed_from,
    timestamp_field,
    action,
    required_permission,
    required_fulfillment,
    require_branch_scope=False,
    reason="",
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, required_permission):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تحديث حالة التسليم.")

    order = _get_order(frappe_module, order_name)
    if not order:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود.")
    if not _has_full_access(permissions):
        if require_branch_scope and not _branch_in_scope(order, user, permissions, frappe_module):
            return _error("OUT_OF_SCOPE", "الطلب خارج نطاق فرعك.")

    validation_error = _validate_ready_and_fulfillment(order, required_fulfillment)
    if validation_error:
        return validation_error
    if _get_value(order, "delivery_status") not in allowed_from:
        if _get_value(order, "delivery_status") == "not_ready":
            return _error("ORDER_NOT_READY_FOR_DISPATCH", "الطلب غير جاهز للإرسال.")
        return _error("INVALID_DELIVERY_TRANSITION", "انتقال حالة التسليم غير مسموح.")

    now = _server_now(frappe_module)
    order.delivery_status = next_status
    setattr(order, timestamp_field, now)
    if next_status == "failed_delivery":
        order.failed_delivery_reason = (reason or "").strip()
    order.save(ignore_permissions=True)
    _audit(order, action, user, frappe_module, reason=reason)
    _commit(frappe_module)
    return _ok(_serialize_order(order))


def _validate_ready_and_fulfillment(order, required_fulfillment):
    fulfillment_method = _get_value(order, "fulfillment_method") or BRANCH_PICKUP
    if not fulfillment_method:
        return _error("FULFILLMENT_METHOD_REQUIRED", "طريقة التسليم مطلوبة.")
    if fulfillment_method != required_fulfillment:
        return _error("INVALID_DELIVERY_TRANSITION", "انتقال حالة التسليم غير مناسب لطريقة التسليم.")
    if fulfillment_method == BRANCH_PICKUP and not (_get_value(order, "destination_branch") or "").strip():
        return _error("DESTINATION_BRANCH_REQUIRED", "فرع الاستلام مطلوب.")
    if _get_value(order, "production_status") != "ready":
        return _error("ORDER_NOT_READY_FOR_DISPATCH", "الطلب غير جاهز للإرسال.")
    return None


def _branch_in_scope(order, user, permissions, frappe_module):
    scopes = get_context_scopes(get_employee_context(user, frappe_module=frappe_module), permissions)
    branches = scopes.get("branch_names") or []
    if branches == ["*"]:
        return True
    return _get_value(order, "destination_branch") in branches


def _has_full_access(permissions):
    return FULL_ACCESS_PERMISSION in set(permissions or [])


def _get_order(frappe_module, order_name):
    try:
        return frappe_module.get_doc("Madar Order", order_name)
    except Exception:
        return None


def _user_permissions(user, frappe_module):
    roles = frappe_module.get_roles(user)
    return roles, get_permissions_for_roles(roles)


def _serialize_order(order):
    return {
        "name": _get_value(order, "name"),
        "customer_name": _get_value(order, "customer_name"),
        "customer_phone": _get_value(order, "customer_phone"),
        "branch": _get_value(order, "branch"),
        "assigned_branch": _get_value(order, "assigned_branch"),
        "fulfillment_method": _get_value(order, "fulfillment_method") or BRANCH_PICKUP,
        "destination_branch": _get_value(order, "destination_branch"),
        "order_status": _get_value(order, "order_status"),
        "production_status": _get_value(order, "production_status") or "not_started",
        "delivery_status": _get_value(order, "delivery_status") or "not_ready",
        "ready_for_dispatch_at": _string_or_none(_get_value(order, "ready_for_dispatch_at")),
        "dispatched_at": _string_or_none(_get_value(order, "dispatched_at")),
        "received_at_branch_at": _string_or_none(_get_value(order, "received_at_branch_at")),
        "ready_for_customer_pickup_at": _string_or_none(_get_value(order, "ready_for_customer_pickup_at")),
        "customer_picked_up_at": _string_or_none(_get_value(order, "customer_picked_up_at")),
        "delivered_at": _string_or_none(_get_value(order, "delivered_at")),
        "failed_delivery_at": _string_or_none(_get_value(order, "failed_delivery_at")),
        "failed_delivery_reason": _get_value(order, "failed_delivery_reason"),
        "subtotal": _float(_get_value(order, "subtotal")),
        "items_count": int(_float(_get_value(order, "items_count"))),
    }


def _audit(doc, action, user, frappe_module, reason=""):
    if hasattr(doc, "add_comment"):
        suffix = f" reason={reason}" if reason else ""
        doc.add_comment("Info", f"{action} by {user} at {_server_now(frappe_module)}{suffix}")


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

