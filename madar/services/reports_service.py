import json
from datetime import date, datetime, time, timedelta

from madar.permissions.checks import get_permissions_for_roles
from madar.permissions.scopes import get_context_scopes
from madar.services.employee_context import get_employee_context


FULL_ACCESS = "system.full_access"
MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 20
MAX_QUERY_LIMIT = 10000


def get_orders_report(user, filters=None, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    context = _context(user, frappe_module)
    if not _can(context, {"orders.create", "orders.approve"}):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض تقرير الطلبات.")

    raw_filters = _normalize_filters(filters)
    rows = _load_rows(
        frappe_module,
        "Madar Order",
        [
            "name",
            "customer_name",
            "assigned_branch",
            "branch",
            "destination_branch",
            "order_status",
            "production_status",
            "delivery_status",
            "payment_status",
            "subtotal",
            "paid_amount",
            "remaining_amount",
            "creation",
        ],
        _query_filters(
            raw_filters,
            "creation",
            {
                "order_status": "order_status",
                "delivery_status": "delivery_status",
                "production_status": "production_status",
                "payment_status": "payment_status",
            },
            frappe_module,
        ),
    )
    rows = [
        row
        for row in rows
        if _branch_allowed(row, context, raw_filters.get("branch"))
    ]
    items = [
        _pick(
            row,
            {
                "name": "name",
                "customer_name": "customer_name",
                "branch": "branch",
                "destination_branch": "destination_branch",
                "order_status": "order_status",
                "production_status": "production_status",
                "delivery_status": "delivery_status",
                "payment_status": "payment_status",
                "subtotal": "subtotal",
                "paid_amount": "paid_amount",
                "remaining_amount": "remaining_amount",
                "created_date": "creation",
            },
        )
        for row in rows
    ]
    return _report(items, raw_filters, amount_field="subtotal")


def get_payments_report(user, filters=None, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    context = _context(user, frappe_module)
    if not _can(context, {"payments.collect", "accounting.view_sync_logs"}):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض تقرير المدفوعات.")

    raw_filters = _normalize_filters(filters)
    rows = _load_rows(
        frappe_module,
        "Madar Payment",
        [
            "name",
            "madar_order",
            "amount",
            "payment_method",
            "payment_status",
            "collection_context",
            "collected_by_user",
            "collected_at",
            "erp_sync_status",
            "erp_payment_entry",
            "modified",
        ],
        _query_filters(
            raw_filters,
            "collected_at",
            {
                "payment_method": "payment_method",
                "payment_status": "payment_status",
                "collection_context": "collection_context",
                "collected_by_user": "collected_by_user",
            },
            frappe_module,
        ),
    )
    if not _has_accounting_scope(context):
        rows = [row for row in rows if _get(row, "collected_by_user") == user]
    items = [
        _pick(
            row,
            {
                "name": "name",
                "order": "madar_order",
                "amount": "amount",
                "payment_method": "payment_method",
                "payment_status": "payment_status",
                "collection_context": "collection_context",
                "collected_by_user": "collected_by_user",
                "collected_at": "collected_at",
                "erp_sync_status": "erp_sync_status",
                "erp_payment_entry": "erp_payment_entry",
            },
        )
        for row in rows
    ]
    return _report(items, raw_filters, amount_field="amount")


def get_production_report(user, filters=None, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    context = _context(user, frappe_module)
    if not _can(context, {"production.view_work_orders"}):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض تقرير الإنتاج.")

    raw_filters = _normalize_filters(filters)
    rows = _load_rows(
        frappe_module,
        "Madar Work Order",
        [
            "name",
            "madar_order",
            "production_center",
            "production_department",
            "status",
            "accepted_at",
            "started_at",
            "ready_at",
            "delayed_at",
            "delay_reason",
            "creation",
        ],
        _query_filters(
            raw_filters,
            "creation",
            {
                "production_center": "production_center",
                "production_department": "production_department",
                "status": "status",
            },
            frappe_module,
        ),
    )
    rows = [
        row
        for row in rows
        if _department_allowed(row, context, raw_filters.get("production_department"))
    ]
    items = [
        _pick(
            row,
            {
                "name": "name",
                "order": "madar_order",
                "production_center": "production_center",
                "production_department": "production_department",
                "status": "status",
                "accepted_at": "accepted_at",
                "started_at": "started_at",
                "ready_at": "ready_at",
                "delayed_at": "delayed_at",
                "delay_reason": "delay_reason",
            },
        )
        for row in rows
    ]
    return _report(items, raw_filters)


def get_delivery_report(user, filters=None, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    context = _context(user, frappe_module)
    if not _can(context, {"delivery.view_assigned_batches", "delivery.update_batch"}):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض تقرير التوصيل.")

    raw_filters = _normalize_filters(filters)
    rows = _load_rows(
        frappe_module,
        "Madar Delivery Batch",
        [
            "name",
            "batch_type",
            "driver_user",
            "destination_branch",
            "status",
            "picked_up_at",
            "out_for_delivery_at",
            "delivered_at",
            "returned_at",
            "creation",
        ],
        _query_filters(
            raw_filters,
            "creation",
            {
                "batch_type": "batch_type",
                "status": "status",
                "driver_user": "driver_user",
                "destination_branch": "destination_branch",
            },
            frappe_module,
        ),
    )
    if FULL_ACCESS not in context["permissions"]:
        rows = [row for row in rows if _get(row, "driver_user") == user]
    items = [
        _pick(
            row,
            {
                "name": "name",
                "batch_type": "batch_type",
                "driver_user": "driver_user",
                "destination_branch": "destination_branch",
                "status": "status",
                "picked_up_at": "picked_up_at",
                "out_for_delivery_at": "out_for_delivery_at",
                "delivered_at": "delivered_at",
                "returned_at": "returned_at",
            },
        )
        for row in rows
    ]
    return _report(items, raw_filters)


def get_cashbox_report(user, filters=None, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    context = _context(user, frappe_module)
    if not _can(context, {"cashbox.view_own", "cashbox.review", "accounting.view_sync_logs"}):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض تقرير الصناديق.")

    raw_filters = _normalize_filters(filters)
    rows = _load_rows(
        frappe_module,
        "Madar Cashbox",
        [
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
        ],
        _query_filters(
            raw_filters,
            "cashbox_date",
            {
                "status": "status",
                "user": "user",
            },
            frappe_module,
            date_only=True,
        ),
    )
    if not _has_cashbox_review_scope(context):
        rows = [row for row in rows if _get(row, "user") == user]
    items = [
        _pick(
            row,
            {
                "name": "name",
                "user": "user",
                "cashbox_date": "cashbox_date",
                "status": "status",
                "expected_cash": "expected_cash",
                "submitted_cash": "submitted_cash",
                "difference": "difference",
                "submitted_at": "submitted_at",
                "reviewed_by": "reviewed_by",
                "reviewed_at": "reviewed_at",
            },
        )
        for row in rows
    ]
    return _report(items, raw_filters, amount_field="expected_cash")


def get_erp_sync_errors_report(user, filters=None, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    context = _context(user, frappe_module)
    if not _can(context, {"accounting.view_sync_logs"}):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية عرض تقرير أخطاء ERP.")

    raw_filters = _normalize_filters(filters)
    requested_entity = (raw_filters.get("entity_type") or "").strip()
    requested_status = (raw_filters.get("status") or "failed").strip()
    items = []
    if not requested_entity or requested_entity in {"Madar Order", "order"}:
        items.extend(
            _order_sync_errors(
                frappe_module,
                raw_filters,
                "erp_sync_status",
                "erp_sync_error",
                "erp_sales_order",
                requested_status,
            )
        )
        items.extend(
            _order_sync_errors(
                frappe_module,
                raw_filters,
                "erp_invoice_sync_status",
                "erp_invoice_sync_error",
                "erp_sales_invoice",
                requested_status,
            )
        )
    if not requested_entity or requested_entity in {"Madar Payment", "payment"}:
        rows = _load_rows(
            frappe_module,
            "Madar Payment",
            ["name", "erp_sync_status", "erp_sync_error", "erp_payment_entry", "modified"],
            _query_filters(
                raw_filters,
                "modified",
                {"status": "erp_sync_status"},
                frappe_module,
            ),
        )
        for row in rows:
            status = _get(row, "erp_sync_status")
            if status != requested_status:
                continue
            items.append(
                {
                    "entity_type": "Madar Payment",
                    "entity_name": _get(row, "name"),
                    "sync_status": status,
                    "safe_error": _safe_error_text(_get(row, "erp_sync_error")),
                    "reference": _get(row, "erp_payment_entry"),
                    "updated_at": _get(row, "modified"),
                }
            )
    return _report(items, raw_filters)


def _order_sync_errors(frappe_module, raw_filters, status_field, error_field, reference_field, wanted_status):
    rows = _load_rows(
        frappe_module,
        "Madar Order",
        ["name", status_field, error_field, reference_field, "modified"],
        _query_filters(
            raw_filters,
            "modified",
            {"status": status_field},
            frappe_module,
        ),
    )
    items = []
    for row in rows:
        status = _get(row, status_field)
        if status != wanted_status:
            continue
        items.append(
            {
                "entity_type": "Madar Order",
                "entity_name": _get(row, "name"),
                "sync_status": status,
                "safe_error": _safe_error_text(_get(row, error_field)),
                "reference": _get(row, reference_field),
                "updated_at": _get(row, "modified"),
            }
        )
    return items


def _context(user, frappe_module):
    roles = frappe_module.get_roles(user)
    permissions = set(get_permissions_for_roles(roles))
    employee = get_employee_context(user, frappe_module=frappe_module)
    return {
        "user": user,
        "roles": roles,
        "permissions": permissions,
        "employee": employee,
        "scopes": get_context_scopes(employee, permissions),
    }


def _query_filters(raw_filters, date_field, simple_map, frappe_module, date_only=False):
    filters = {}
    for source, target in simple_map.items():
        value = raw_filters.get(source)
        if value not in (None, ""):
            filters[target] = value
    start, end = _date_range(raw_filters, frappe_module, date_only=date_only)
    filters[date_field] = ["between", [start, end]]
    return filters


def _date_range(raw_filters, frappe_module, date_only=False):
    now = frappe_module.utils.now_datetime()
    today = now.date()
    start_date = _parse_date(raw_filters.get("date_from")) or (today - timedelta(days=6))
    end_date = _parse_date(raw_filters.get("date_to")) or today
    if date_only:
        return start_date, end_date
    return datetime.combine(start_date, time.min), datetime.combine(end_date, time.max)


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _load_rows(frappe_module, doctype, fields, filters):
    try:
        return frappe_module.get_all(
            doctype,
            filters=filters,
            fields=fields,
            order_by="modified desc",
            limit=MAX_QUERY_LIMIT,
        )
    except Exception:
        return []


def _report(items, raw_filters, amount_field=None):
    page, page_size = _pagination(raw_filters)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    summary = {"count": total}
    if amount_field:
        summary["total_amount"] = sum(_float(_get(item, amount_field)) for item in items)
    else:
        summary["total_amount"] = 0
    return _ok(
        {
            "items": [_serialize_item(item) for item in page_items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "filters": _public_filters(raw_filters),
            "summary": summary,
        }
    )


def _pagination(raw_filters):
    try:
        page = max(1, int(raw_filters.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(raw_filters.get("page_size") or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    return page, max(1, min(page_size, MAX_PAGE_SIZE))


def _branch_allowed(row, context, requested_branch=None):
    row_branch = _get(row, "assigned_branch") or _get(row, "branch") or _get(row, "destination_branch")
    scopes = context["scopes"].get("branch_names") or []
    if requested_branch and row_branch != requested_branch:
        return False
    if FULL_ACCESS in context["permissions"] or scopes == ["*"]:
        return True
    return bool(row_branch and row_branch in scopes)


def _department_allowed(row, context, requested_department=None):
    department = _get(row, "production_department")
    scopes = context["scopes"].get("department_names") or []
    if requested_department and department != requested_department:
        return False
    if FULL_ACCESS in context["permissions"] or scopes == ["*"]:
        return True
    return bool(department and department in scopes)


def _can(context, permission_keys):
    permissions = context["permissions"]
    return FULL_ACCESS in permissions or bool(permissions.intersection(permission_keys))


def _has_accounting_scope(context):
    permissions = context["permissions"]
    return FULL_ACCESS in permissions or "accounting.view_sync_logs" in permissions


def _has_cashbox_review_scope(context):
    permissions = context["permissions"]
    return (
        FULL_ACCESS in permissions
        or "cashbox.review" in permissions
        or "accounting.view_sync_logs" in permissions
    )


def _normalize_filters(filters):
    if filters is None:
        return {}
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except ValueError:
            return {}
    if not isinstance(filters, dict):
        return {}
    return {str(key): value for key, value in filters.items() if value not in (None, "")}


def _public_filters(filters):
    blocked = {"password", "api_key", "api_secret", "sid"}
    return {key: value for key, value in filters.items() if key not in blocked}


def _pick(row, mapping):
    return {public: _get(row, field) for public, field in mapping.items()}


def _serialize_item(item):
    return {key: _serialize_value(value) for key, value in item.items()}


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _safe_error_text(value):
    text = str(value or "").strip()
    if not text:
        return ""
    safe_lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and "traceback" not in line.lower() and "secret" not in line.lower()
    ]
    safe = safe_lines[-1] if safe_lines else "فشل في المزامنة"
    return safe[:240]


def _get(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


def _float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {
        "ok": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
    }
