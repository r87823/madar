from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.permissions.scopes import get_context_scopes
from madar.services import notification_service
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
BATCH_TYPE_BRANCH_TRANSFER = "branch_transfer"
BATCH_TYPE_CUSTOMER_DELIVERY = "customer_delivery"
BATCH_FIELDS = [
    "name",
    "batch_number",
    "batch_type",
    "destination_branch",
    "driver_user",
    "status",
    "created_by_user",
    "picked_up_at",
    "out_for_delivery_at",
    "delivered_at",
    "returned_at",
    "return_reason",
    "modified",
]
BATCH_ORDER_FIELDS = [
    "name",
    "delivery_batch",
    "madar_order",
    "delivery_status_snapshot",
    "modified",
]
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
    "paid_amount",
    "remaining_amount",
    "payment_status",
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


def create_delivery_batch(user, order_names, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, UPDATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إنشاء دفعات التوصيل.")

    order_names = _normalize_names(order_names)
    if not order_names:
        return _error("ORDER_REQUIRED", "يجب اختيار طلب واحد على الأقل.")

    orders = []
    for order_name in order_names:
        order = _get_order(frappe_module, order_name)
        if not order:
            return _error("ORDER_NOT_FOUND", "أحد الطلبات غير موجود.")
        orders.append(order)

    validation = _validate_batch_orders(orders)
    if validation:
        return validation

    existing = _find_existing_batch_for_orders(frappe_module, order_names)
    if existing:
        return _ok(_serialize_batch(existing, frappe_module))

    batch_type = _batch_type_for_order(orders[0])
    destination_branch = _get_value(orders[0], "destination_branch") if batch_type == BATCH_TYPE_BRANCH_TRANSFER else ""
    batch = frappe_module.get_doc(
        {
            "doctype": "Madar Delivery Batch",
            "naming_series": "MADAR-DBATCH-.YYYY.-",
            "batch_number": "",
            "batch_type": batch_type,
            "destination_branch": destination_branch or "",
            "driver_user": "",
            "status": "draft",
            "created_by_user": user,
            "picked_up_at": None,
            "out_for_delivery_at": None,
            "delivered_at": None,
            "returned_at": None,
            "return_reason": "",
        }
    )
    batch.insert(ignore_permissions=True)
    if not _get_value(batch, "batch_number"):
        batch.batch_number = _get_value(batch, "name")
        batch.save(ignore_permissions=True)

    for order in orders:
        _insert_batch_order(frappe_module, batch, order)

    _audit(batch, "create_delivery_batch", user, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_batch(batch, frappe_module))


def assign_driver(user, batch_name, driver_user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, UPDATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تعيين السائق.")
    if not (driver_user or "").strip():
        return _error("DRIVER_REQUIRED", "السائق مطلوب.")

    batch = _get_batch(frappe_module, batch_name)
    if not batch:
        return _error("BATCH_NOT_FOUND", "دفعة التوصيل غير موجودة.")
    if _get_value(batch, "status") not in {"draft", "assigned"}:
        return _error("INVALID_BATCH_TRANSITION", "لا يمكن تعيين السائق في هذه الحالة.")

    batch.driver_user = driver_user.strip()
    batch.status = "assigned"
    batch.save(ignore_permissions=True)
    _audit(batch, "assign_driver", user, frappe_module)
    notification_service.safe_notify_user(
        driver_user.strip(),
        title="تم إسناد دفعة توصيل",
        message=f"تم إسناد الدفعة {_get_value(batch, 'name')} إليك.",
        event_type="delivery_batch_assigned",
        entity_type="Madar Delivery Batch",
        entity_name=_get_value(batch, "name"),
        priority="normal",
        frappe_module=frappe_module,
    )
    _commit(frappe_module)
    return _ok(_serialize_batch(batch, frappe_module))


def list_delivery_batches(user, frappe_module=None, limit=MAX_QUEUE_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, UPDATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض دفعات التوصيل.")
    return _ok({"items": _list_batches(frappe_module, {}, limit)})


def list_my_delivery_batches(user, frappe_module=None, limit=MAX_QUEUE_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, VIEW_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض دفعاتك.")
    filters = {} if _has_full_access(permissions) else {"driver_user": user}
    return _ok({"items": _list_batches(frappe_module, filters, limit)})


def get_delivery_batch(user, batch_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    batch = _get_batch(frappe_module, batch_name)
    if not batch:
        return _error("BATCH_NOT_FOUND", "دفعة التوصيل غير موجودة.")
    if not _can_access_batch(user, roles, permissions, batch):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض هذه الدفعة.")
    return _ok(_serialize_batch(batch, frappe_module))


def mark_batch_picked_up(user, batch_name, frappe_module=None):
    return _batch_transition(
        user=user,
        batch_name=batch_name,
        next_status="picked_up",
        allowed_from={"assigned"},
        timestamp_field="picked_up_at",
        action="mark_batch_picked_up",
        frappe_module=frappe_module,
    )


def mark_batch_out_for_delivery(user, batch_name, frappe_module=None):
    return _batch_transition(
        user=user,
        batch_name=batch_name,
        next_status="out_for_delivery",
        allowed_from={"picked_up"},
        timestamp_field="out_for_delivery_at",
        action="mark_batch_out_for_delivery",
        cascade=True,
        frappe_module=frappe_module,
    )


def mark_batch_delivered(user, batch_name, frappe_module=None):
    return _batch_transition(
        user=user,
        batch_name=batch_name,
        next_status="completed",
        allowed_from={"out_for_delivery"},
        timestamp_field="delivered_at",
        action="mark_batch_delivered",
        cascade=True,
        frappe_module=frappe_module,
    )


def mark_batch_returned(user, batch_name, reason, frappe_module=None):
    if not (reason or "").strip():
        return _error("REASON_REQUIRED", "سبب الإرجاع مطلوب.")
    return _batch_transition(
        user=user,
        batch_name=batch_name,
        next_status="returned",
        allowed_from={"picked_up", "out_for_delivery"},
        timestamp_field="returned_at",
        action="mark_batch_returned",
        reason=reason,
        cascade=True,
        frappe_module=frappe_module,
    )


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


def _batch_transition(
    *,
    user,
    batch_name,
    next_status,
    allowed_from,
    timestamp_field,
    action,
    cascade=False,
    reason="",
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, UPDATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تحديث دفعة التوصيل.")

    batch = _get_batch(frappe_module, batch_name)
    if not batch:
        return _error("BATCH_NOT_FOUND", "دفعة التوصيل غير موجودة.")
    if not _has_full_access(permissions) and _get_value(batch, "driver_user") != user:
        return _error("PERMISSION_DENIED", "يمكن للسائق تحديث الدفعات المسندة له فقط.")
    if _get_value(batch, "status") not in allowed_from:
        return _error("INVALID_BATCH_TRANSITION", "انتقال حالة الدفعة غير مسموح.")

    now = _server_now(frappe_module)
    batch.status = next_status
    setattr(batch, timestamp_field, now)
    if next_status == "returned":
        batch.return_reason = (reason or "").strip()
    batch.save(ignore_permissions=True)

    if cascade:
        cascade_error = _cascade_batch_status(batch, next_status, user, frappe_module, reason=reason)
        if cascade_error:
            return cascade_error

    _audit(batch, action, user, frappe_module, reason=reason)
    if action == "mark_batch_delivered" and _get_value(batch, "batch_type") == BATCH_TYPE_BRANCH_TRANSFER:
        _notify_branch_transfer_received(batch, frappe_module)
    _commit(frappe_module)
    return _ok(_serialize_batch(batch, frappe_module))


def _notify_branch_transfer_received(batch, frappe_module):
    recipients = notification_service.users_with_permission(
        BRANCH_PERMISSION,
        frappe_module=frappe_module,
    )
    for order in _orders_for_batch(frappe_module, _get_value(batch, "name")):
        order_name = _get_value(order, "name")
        notification_service.safe_notify_users(
            recipients,
            title="طلب وصل إلى الفرع",
            message=f"وصل الطلب {order_name} إلى الفرع.",
            event_type="branch_order_received",
            entity_type="Madar Order",
            entity_name=order_name,
            priority="normal",
            frappe_module=frappe_module,
        )


def _cascade_batch_status(batch, next_status, user, frappe_module, reason=""):
    orders = _orders_for_batch(frappe_module, _get_value(batch, "name"))
    batch_type = _get_value(batch, "batch_type")

    if next_status == "out_for_delivery":
        order_status = "dispatched_to_branch" if batch_type == BATCH_TYPE_BRANCH_TRANSFER else "dispatched_to_customer"
        timestamp_field = "dispatched_at"
        allowed_from = {"ready_for_dispatch"}
    elif next_status == "completed":
        order_status = "received_at_branch" if batch_type == BATCH_TYPE_BRANCH_TRANSFER else "delivered_to_customer"
        timestamp_field = "received_at_branch_at" if batch_type == BATCH_TYPE_BRANCH_TRANSFER else "delivered_at"
        allowed_from = {"dispatched_to_branch"} if batch_type == BATCH_TYPE_BRANCH_TRANSFER else {"dispatched_to_customer"}
    elif next_status == "returned":
        order_status = "failed_delivery"
        timestamp_field = "failed_delivery_at"
        allowed_from = {
            "ready_for_dispatch",
            "dispatched_to_branch",
            "dispatched_to_customer",
        }
    else:
        return None

    for order in orders:
        current = _get_value(order, "delivery_status")
        if current not in allowed_from:
            return _error("INVALID_DELIVERY_TRANSITION", "لا يمكن تحديث أحد طلبات الدفعة من حالته الحالية.")
        _set_order_delivery_status(
            order,
            order_status,
            timestamp_field,
            user,
            frappe_module,
            action=f"cascade_{next_status}",
            reason=reason,
        )
    return None


def _set_order_delivery_status(order, status, timestamp_field, user, frappe_module, action, reason=""):
    order.delivery_status = status
    setattr(order, timestamp_field, _server_now(frappe_module))
    if status == "failed_delivery":
        order.failed_delivery_reason = (reason or "").strip()
    order.save(ignore_permissions=True)
    _audit(order, action, user, frappe_module, reason=reason)


def _validate_batch_orders(orders):
    batch_type = None
    destination_branch = None
    for order in orders:
        if _get_value(order, "delivery_status") != "ready_for_dispatch":
            return _error("ORDER_NOT_READY_FOR_DISPATCH", "كل الطلبات المختارة يجب أن تكون جاهزة للإرسال.")
        if _get_value(order, "production_status") != "ready":
            return _error("ORDER_NOT_READY_FOR_DISPATCH", "كل الطلبات المختارة يجب أن تكون جاهزة إنتاجيًا.")

        current_batch_type = _batch_type_for_order(order)
        if batch_type and current_batch_type != batch_type:
            return _error("MIXED_FULFILLMENT_METHOD", "لا يمكن خلط أنواع التسليم في دفعة واحدة.")
        batch_type = current_batch_type

        if current_batch_type == BATCH_TYPE_BRANCH_TRANSFER:
            branch = (_get_value(order, "destination_branch") or "").strip()
            if not branch:
                return _error("DESTINATION_BRANCH_REQUIRED", "فرع الاستلام مطلوب.")
            if destination_branch and branch != destination_branch:
                return _error("MIXED_DESTINATION_BRANCH", "لا يمكن خلط فروع مختلفة في دفعة تحويل فرعي.")
            destination_branch = branch
    return None


def _batch_type_for_order(order):
    fulfillment_method = _get_value(order, "fulfillment_method") or BRANCH_PICKUP
    if fulfillment_method == CUSTOMER_DELIVERY:
        return BATCH_TYPE_CUSTOMER_DELIVERY
    return BATCH_TYPE_BRANCH_TRANSFER


def _normalize_names(names):
    if isinstance(names, str):
        names = names.split(",")
    seen = set()
    normalized = []
    for name in names or []:
        value = str(name or "").strip()
        if value and value not in seen:
            seen.add(value)
            normalized.append(value)
    return normalized


def _find_existing_batch_for_orders(frappe_module, order_names):
    wanted = set(order_names)
    if not wanted:
        return None
    rows = frappe_module.get_all(
        "Madar Delivery Batch Order",
        filters={"madar_order": ["in", sorted(wanted)]},
        fields=BATCH_ORDER_FIELDS,
        limit=MAX_QUEUE_LIMIT,
    )
    by_batch = {}
    for row in rows:
        by_batch.setdefault(_get_value(row, "delivery_batch"), set()).add(_get_value(row, "madar_order"))
    for batch_name, linked_orders in by_batch.items():
        if linked_orders == wanted:
            batch = _get_batch(frappe_module, batch_name)
            if batch and _get_value(batch, "status") != "cancelled":
                return batch
    return None


def _insert_batch_order(frappe_module, batch, order):
    batch_name = _get_value(batch, "name")
    order_name = _get_value(order, "name")
    existing = frappe_module.get_all(
        "Madar Delivery Batch Order",
        filters={"delivery_batch": batch_name, "madar_order": order_name},
        fields=["name"],
        limit=1,
    )
    if existing:
        return existing[0]
    link = frappe_module.get_doc(
        {
            "doctype": "Madar Delivery Batch Order",
            "delivery_batch": batch_name,
            "madar_order": order_name,
            "delivery_status_snapshot": _get_value(order, "delivery_status"),
        }
    )
    link.insert(ignore_permissions=True)
    return link


def _list_batches(frappe_module, filters, limit):
    rows = frappe_module.get_all(
        "Madar Delivery Batch",
        filters=filters,
        fields=BATCH_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_QUEUE_LIMIT), MAX_QUEUE_LIMIT)),
    )
    return [_serialize_batch(row, frappe_module, include_orders=False) for row in rows]


def _get_batch(frappe_module, batch_name):
    try:
        return frappe_module.get_doc("Madar Delivery Batch", batch_name)
    except Exception:
        return None


def _orders_for_batch(frappe_module, batch_name):
    links = frappe_module.get_all(
        "Madar Delivery Batch Order",
        filters={"delivery_batch": batch_name},
        fields=BATCH_ORDER_FIELDS,
        order_by="modified asc",
        limit=MAX_QUEUE_LIMIT,
    )
    orders = []
    for link in links:
        order = _get_order(frappe_module, _get_value(link, "madar_order"))
        if order:
            orders.append(order)
    return orders


def _can_access_batch(user, roles, permissions, batch):
    if has_permission(roles, UPDATE_PERMISSION) or _has_full_access(permissions):
        return True
    return has_permission(roles, VIEW_PERMISSION) and _get_value(batch, "driver_user") == user


def _serialize_batch(batch, frappe_module, include_orders=True):
    data = {
        "name": _get_value(batch, "name"),
        "batch_number": _get_value(batch, "batch_number") or _get_value(batch, "name"),
        "batch_type": _get_value(batch, "batch_type"),
        "destination_branch": _get_value(batch, "destination_branch"),
        "driver_user": _get_value(batch, "driver_user"),
        "status": _get_value(batch, "status"),
        "created_by_user": _get_value(batch, "created_by_user"),
        "picked_up_at": _string_or_none(_get_value(batch, "picked_up_at")),
        "out_for_delivery_at": _string_or_none(_get_value(batch, "out_for_delivery_at")),
        "delivered_at": _string_or_none(_get_value(batch, "delivered_at")),
        "returned_at": _string_or_none(_get_value(batch, "returned_at")),
        "return_reason": _get_value(batch, "return_reason"),
    }
    if include_orders:
        data["orders"] = [_serialize_order(order) for order in _orders_for_batch(frappe_module, data["name"])]
    return data


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
        "paid_amount": _float(_get_value(order, "paid_amount")),
        "remaining_amount": _float(_get_value(order, "remaining_amount")),
        "payment_status": _get_value(order, "payment_status") or "unpaid",
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
