from madar.permissions.checks import get_permissions_for_roles, has_permission
from madar.permissions.scopes import get_context_scopes
from madar.services import notification_service
from madar.services.employee_context import get_employee_context


CREATE_PERMISSION = "orders.create"
SUBMIT_PERMISSION = "orders.submit_for_approval"
APPROVE_PERMISSION = "orders.approve"
FULL_ACCESS_PERMISSION = "system.full_access"
ORDER_FIELDS = [
    "name",
    "customer_name",
    "customer_phone",
    "branch",
    "assigned_branch",
    "fulfillment_method",
    "destination_branch",
    "order_status",
    "created_by_user",
    "notes",
    "subtotal",
    "items_count",
    "submitted_at",
    "cancelled_at",
    "approved_at",
    "approved_by",
    "returned_at",
    "rejected_at",
    "approval_reason",
    "production_status",
    "production_ready_at",
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
    "erp_sync_status",
    "erp_sync_error",
    "erp_sales_order",
    "erp_sales_order_docstatus",
    "erp_sales_invoice",
    "erp_sales_invoice_docstatus",
    "erp_invoice_sync_status",
    "erp_invoice_sync_error",
    "erp_invoice_created_at",
    "accounting_status",
    "accounting_review_notes",
    "accounting_reviewed_by",
    "accounting_reviewed_at",
    "accounting_finalized_at",
    "accounting_finalized_by",
    "accounting_finalization_error",
    "creation",
    "modified",
]
MAX_LIST_LIMIT = 50


def create_draft(
    user,
    customer_name,
    customer_phone="",
    notes="",
    fulfillment_method="branch_pickup",
    destination_branch=None,
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, CREATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إنشاء الطلبات.")

    employee = _employee(user, frappe_module)
    scopes = get_context_scopes(employee, permissions)
    branch = _default_branch(scopes, employee)
    fulfillment_method = (fulfillment_method or "branch_pickup").strip()
    if fulfillment_method not in {"branch_pickup", "customer_delivery"}:
        return _error("FULFILLMENT_METHOD_REQUIRED", "طريقة التسليم مطلوبة.")
    destination_branch = _resolve_destination_branch(
        fulfillment_method,
        destination_branch,
        branch,
        scopes,
        permissions,
    )
    if isinstance(destination_branch, dict):
        return destination_branch
    now = _server_now(frappe_module)
    doc = frappe_module.get_doc(
        {
            "doctype": "Madar Order",
            "naming_series": "MADAR-ORD-.YYYY.-",
            "customer_name": (customer_name or "").strip(),
            "customer_phone": (customer_phone or "").strip(),
            "notes": (notes or "").strip(),
            "branch": branch,
            "assigned_branch": destination_branch or branch,
            "fulfillment_method": fulfillment_method,
            "destination_branch": destination_branch,
            "order_status": "draft",
            "created_by_user": user,
            "subtotal": 0,
            "paid_amount": 0,
            "remaining_amount": 0,
            "payment_status": "unpaid",
            "items_count": 0,
            "delivery_status": "not_ready",
        }
    ).insert(ignore_permissions=True)
    _audit(doc, "create_draft", user, now)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def _resolve_destination_branch(fulfillment_method, requested_branch, default_branch, scopes, permissions):
    if fulfillment_method == "customer_delivery":
        return None
    branch_names = scopes.get("branch_names") or []
    requested_branch = (requested_branch or "").strip()
    if not requested_branch and default_branch:
        requested_branch = default_branch
    if not requested_branch:
        return _error("DESTINATION_BRANCH_REQUIRED", "فرع الاستلام مطلوب.")
    if FULL_ACCESS_PERMISSION in set(permissions or []) or branch_names == ["*"]:
        return requested_branch
    if requested_branch not in branch_names:
        return _error("OUT_OF_SCOPE", "فرع الاستلام خارج نطاقك.")
    return requested_branch


def list_orders(user, frappe_module=None, limit=MAX_LIST_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permissions = _user_permissions(user, frappe_module)
    filters = _scope_filters(user, permissions, _employee(user, frappe_module))
    rows = frappe_module.get_all(
        "Madar Order",
        filters=filters,
        fields=ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_LIST_LIMIT), MAX_LIST_LIMIT)),
    )
    return _ok({"items": [_serialize_order(row) for row in rows]})


def get_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    _roles, permissions = _user_permissions(user, frappe_module)
    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    return _ok(_serialize_order(doc))


def submit_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, SUBMIT_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إرسال الطلب.")

    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    if _get_value(doc, "order_status") not in {"draft", "returned_for_edit"}:
        return _error("INVALID_ORDER_TRANSITION", "يمكن إرسال الطلبات المسودة أو المعادة للتعديل فقط.")
    if int(_float(_get_value(doc, "items_count"))) <= 0:
        return _error("ORDER_HAS_NO_ITEMS", "لا يمكن إرسال طلب بدون أصناف.")

    now = _server_now(frappe_module)
    doc.order_status = "submitted"
    doc.submitted_at = now
    doc.save(ignore_permissions=True)
    _audit(doc, "submit_order", user, now)
    _notify_order_submitted(doc, frappe_module)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def list_approval_queue(user, frappe_module=None, limit=MAX_LIST_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, APPROVE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية اعتماد الطلبات.")

    filters = _scope_filters(user, permissions, _employee(user, frappe_module))
    filters["order_status"] = "submitted"
    rows = frappe_module.get_all(
        "Madar Order",
        filters=filters,
        fields=ORDER_FIELDS,
        order_by="modified desc",
        limit=max(1, min(int(limit or MAX_LIST_LIMIT), MAX_LIST_LIMIT)),
    )
    return _ok({"items": [_serialize_order(row) for row in rows]})


def approve_order(user, order_name, frappe_module=None):
    return _approval_transition(
        user=user,
        order_name=order_name,
        next_status="approved",
        action="approve_order",
        frappe_module=frappe_module,
    )


def return_order_for_edit(user, order_name, reason, frappe_module=None):
    return _approval_transition(
        user=user,
        order_name=order_name,
        next_status="returned_for_edit",
        action="return_order_for_edit",
        reason=reason,
        frappe_module=frappe_module,
    )


def reject_order(user, order_name, reason, frappe_module=None):
    return _approval_transition(
        user=user,
        order_name=order_name,
        next_status="rejected",
        action="reject_order",
        reason=reason,
        frappe_module=frappe_module,
    )


def cancel_order(user, order_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, CREATE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية إلغاء الطلب.")

    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    if _get_value(doc, "order_status") != "draft":
        return _error("INVALID_ORDER_TRANSITION", "يمكن إلغاء الطلبات المسودة فقط.")

    now = _server_now(frappe_module)
    doc.order_status = "cancelled"
    doc.cancelled_at = now
    doc.save(ignore_permissions=True)
    _audit(doc, "cancel_order", user, now)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def _approval_transition(user, order_name, next_status, action, reason="", frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles, permissions = _user_permissions(user, frappe_module)
    if not has_permission(roles, APPROVE_PERMISSION):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية اعتماد الطلبات.")
    if next_status in {"returned_for_edit", "rejected"} and not (reason or "").strip():
        return _error("REASON_REQUIRED", "سبب الإجراء مطلوب.")

    doc = _get_scoped_order(user, order_name, permissions, frappe_module)
    if not doc:
        return _error("ORDER_NOT_FOUND", "الطلب غير موجود أو خارج نطاقك.")
    if _get_value(doc, "order_status") != "submitted":
        return _error("INVALID_ORDER_TRANSITION", "يمكن معالجة الطلبات المرسلة للاعتماد فقط.")

    now = _server_now(frappe_module)
    doc.order_status = next_status
    if next_status == "approved":
        doc.approved_at = now
        doc.approved_by = user
        doc.erp_sync_status = "pending"
        doc.erp_sync_error = None
        doc.erp_sales_order = None
        doc.erp_sales_order_docstatus = None
        doc.erp_sales_invoice = None
        doc.erp_sales_invoice_docstatus = None
        doc.erp_invoice_sync_status = "pending"
        doc.erp_invoice_sync_error = None
        doc.erp_invoice_created_at = None
        doc.accounting_status = "not_ready"
        doc.accounting_review_notes = None
        doc.accounting_reviewed_by = None
        doc.accounting_reviewed_at = None
        doc.accounting_finalized_at = None
        doc.accounting_finalized_by = None
        doc.accounting_finalization_error = None
    elif next_status == "returned_for_edit":
        doc.returned_at = now
        doc.approval_reason = (reason or "").strip()
    elif next_status == "rejected":
        doc.rejected_at = now
        doc.approval_reason = (reason or "").strip()
    doc.save(ignore_permissions=True)
    _audit(doc, action, user, now, reason=reason)
    _notify_approval_transition(doc, next_status, reason, frappe_module)
    frappe_module.db.commit()
    return _ok(_serialize_order(doc))


def _notify_order_submitted(order, frappe_module):
    order_name = _get_value(order, "name")
    recipients = notification_service.users_with_permission(
        APPROVE_PERMISSION,
        frappe_module=frappe_module,
    )
    notification_service.safe_notify_users(
        recipients,
        title="طلب جديد بانتظار الاعتماد",
        message=f"تم إرسال الطلب {order_name} للاعتماد.",
        event_type="order_submitted",
        entity_type="Madar Order",
        entity_name=order_name,
        priority="normal",
        frappe_module=frappe_module,
    )


def _notify_approval_transition(order, next_status, reason, frappe_module):
    order_name = _get_value(order, "name")
    creator = _get_value(order, "created_by_user")
    if next_status == "returned_for_edit":
        notification_service.safe_notify_user(
            creator,
            title="تم إرجاع الطلب للتعديل",
            message=f"تم إرجاع الطلب {order_name} للتعديل. السبب: {(reason or '').strip()}",
            event_type="order_returned_for_edit",
            entity_type="Madar Order",
            entity_name=order_name,
            priority="normal",
            frappe_module=frappe_module,
        )
    elif next_status == "rejected":
        notification_service.safe_notify_user(
            creator,
            title="تم رفض الطلب",
            message=f"تم رفض الطلب {order_name}. السبب: {(reason or '').strip()}",
            event_type="order_rejected",
            entity_type="Madar Order",
            entity_name=order_name,
            priority="high",
            frappe_module=frappe_module,
        )
    elif next_status == "approved":
        notification_service.safe_notify_user(
            creator,
            title="تم اعتماد الطلب",
            message=f"تم اعتماد الطلب {order_name}.",
            event_type="order_approved",
            entity_type="Madar Order",
            entity_name=order_name,
            priority="normal",
            frappe_module=frappe_module,
        )
        notification_service.safe_notify_users(
            notification_service.users_with_permission(
                "production.view_work_orders",
                frappe_module=frappe_module,
            ),
            title="تم اعتماد الطلب",
            message=f"تم اعتماد الطلب {order_name}.",
            event_type="order_approved",
            entity_type="Madar Order",
            entity_name=order_name,
            priority="normal",
            frappe_module=frappe_module,
        )


def _get_scoped_order(user, order_name, permissions, frappe_module):
    try:
        doc = frappe_module.get_doc("Madar Order", order_name)
    except Exception:
        return None
    if not _is_visible(doc, user, permissions, _employee(user, frappe_module)):
        return None
    return doc


def _is_visible(order, user, permissions, employee):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return True
    if _get_value(order, "created_by_user") == user:
        return True
    scopes = get_context_scopes(employee, permissions)
    branch_names = scopes.get("branch_names") or []
    return _get_value(order, "assigned_branch") in branch_names or _get_value(order, "branch") in branch_names


def _scope_filters(user, permissions, employee):
    if FULL_ACCESS_PERMISSION in set(permissions or []):
        return {}
    scopes = get_context_scopes(employee, permissions)
    branch_names = scopes.get("branch_names") or []
    if branch_names:
        return {"assigned_branch": ["in", branch_names]}
    return {"created_by_user": user}


def _default_branch(scopes, employee):
    branch_names = scopes.get("branch_names") or []
    if branch_names and branch_names != ["*"]:
        return branch_names[0]
    return _get_value(employee, "branch")


def _user_permissions(user, frappe_module):
    roles = frappe_module.get_roles(user)
    return roles, get_permissions_for_roles(roles)


def _employee(user, frappe_module):
    return get_employee_context(user, frappe_module=frappe_module)


def _server_now(frappe_module):
    return frappe_module.utils.now_datetime()


def _audit(doc, action, user, now, reason=""):
    if hasattr(doc, "add_comment"):
        suffix = f" reason={reason}" if reason else ""
        doc.add_comment("Info", f"{action} by {user} at {now}{suffix}")


def _serialize_order(order):
    return {
        "name": _get_value(order, "name"),
        "customer_name": _get_value(order, "customer_name"),
        "customer_phone": _get_value(order, "customer_phone"),
        "branch": _get_value(order, "branch"),
        "assigned_branch": _get_value(order, "assigned_branch"),
        "fulfillment_method": _get_value(order, "fulfillment_method") or "branch_pickup",
        "destination_branch": _get_value(order, "destination_branch"),
        "order_status": _get_value(order, "order_status"),
        "created_by_user": _get_value(order, "created_by_user"),
        "notes": _get_value(order, "notes"),
        "subtotal": _float(_get_value(order, "subtotal")),
        "items_count": int(_float(_get_value(order, "items_count"))),
        "submitted_at": _string_or_none(_get_value(order, "submitted_at")),
        "cancelled_at": _string_or_none(_get_value(order, "cancelled_at")),
        "approved_at": _string_or_none(_get_value(order, "approved_at")),
        "approved_by": _get_value(order, "approved_by"),
        "returned_at": _string_or_none(_get_value(order, "returned_at")),
        "rejected_at": _string_or_none(_get_value(order, "rejected_at")),
        "approval_reason": _get_value(order, "approval_reason"),
        "production_status": _get_value(order, "production_status") or "not_started",
        "production_ready_at": _string_or_none(_get_value(order, "production_ready_at")),
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
        "erp_sync_status": _get_value(order, "erp_sync_status"),
        "erp_sync_error": _get_value(order, "erp_sync_error"),
        "erp_sales_order": _get_value(order, "erp_sales_order"),
        "erp_sales_order_docstatus": int(_float(_get_value(order, "erp_sales_order_docstatus")))
        if _get_value(order, "erp_sales_order_docstatus") not in {None, ""}
        else None,
        "erp_sales_invoice": _get_value(order, "erp_sales_invoice"),
        "erp_sales_invoice_docstatus": int(_float(_get_value(order, "erp_sales_invoice_docstatus")))
        if _get_value(order, "erp_sales_invoice_docstatus") not in {None, ""}
        else None,
        "erp_invoice_sync_status": _get_value(order, "erp_invoice_sync_status"),
        "erp_invoice_sync_error": _get_value(order, "erp_invoice_sync_error"),
        "erp_invoice_created_at": _string_or_none(_get_value(order, "erp_invoice_created_at")),
        "accounting_status": _get_value(order, "accounting_status"),
        "accounting_review_notes": _get_value(order, "accounting_review_notes"),
        "accounting_reviewed_by": _get_value(order, "accounting_reviewed_by"),
        "accounting_reviewed_at": _string_or_none(_get_value(order, "accounting_reviewed_at")),
        "accounting_finalized_at": _string_or_none(_get_value(order, "accounting_finalized_at")),
        "accounting_finalized_by": _get_value(order, "accounting_finalized_by"),
        "accounting_finalization_error": _get_value(order, "accounting_finalization_error"),
        "creation": _string_or_none(_get_value(order, "creation")),
        "modified": _string_or_none(_get_value(order, "modified")),
    }


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
    return {
        "ok": True,
        "data": data,
        "error": None,
    }


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }
