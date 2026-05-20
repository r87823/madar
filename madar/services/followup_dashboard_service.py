from datetime import time

from madar.permissions.checks import get_permissions_for_roles
from madar.permissions.scopes import get_context_scopes
from madar.services.employee_context import get_employee_context


FULL_ACCESS = "system.full_access"
MAX_COUNT_LIMIT = 10000


def get_summary(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles = frappe_module.get_roles(user)
    permissions = set(get_permissions_for_roles(roles))
    employee = get_employee_context(user, frappe_module=frappe_module)
    scopes = get_context_scopes(employee, permissions)
    cards = []
    alerts = []

    _add_orders_today(cards, user, permissions, scopes, frappe_module)
    _add_pending_approval(cards, permissions, scopes, frappe_module)
    _add_production_cards(cards, alerts, permissions, scopes, frappe_module)
    _add_delivery_cards(cards, user, permissions, frappe_module)
    _add_payment_card(cards, user, permissions, frappe_module)
    _add_cashbox_review_card(cards, alerts, permissions, frappe_module)
    _add_erp_failed_card(cards, alerts, permissions, frappe_module)
    _add_accounting_ready_card(cards, alerts, permissions, frappe_module)
    _add_unread_notifications(cards, user, frappe_module)
    _add_attendance_state(cards, permissions)

    return _ok({"cards": cards, "alerts": alerts})


def _add_orders_today(cards, user, permissions, scopes, frappe_module):
    if not _has_any(permissions, {"orders.create", "orders.approve"}):
        return
    filters = _today_filters(frappe_module)
    filters.update(_branch_filter(scopes))
    cards.append(
        _card(
            "orders_today",
            "طلبات اليوم",
            _count("Madar Order", filters, frappe_module),
            "حسب نطاقك",
            route_key="orders_list",
        )
    )


def _add_pending_approval(cards, permissions, scopes, frappe_module):
    if not _has_any(permissions, {"orders.approve"}):
        return
    filters = {"order_status": "submitted"}
    filters.update(_branch_filter(scopes))
    cards.append(
        _card(
            "orders_pending_approval",
            "طلبات بانتظار الاعتماد",
            _count("Madar Order", filters, frappe_module),
            "حسب نطاقك",
            route_key="approval_queue",
        )
    )


def _add_production_cards(cards, alerts, permissions, scopes, frappe_module):
    if not _has_any(permissions, {"production.view_work_orders"}):
        return
    filters = _department_filter(scopes)
    in_progress_filters = dict(filters)
    in_progress_filters["status"] = ["in", ["accepted", "in_production"]]
    delayed_filters = dict(filters)
    delayed_filters["status"] = "delayed"
    in_progress = _count("Madar Work Order", in_progress_filters, frappe_module)
    delayed = _count("Madar Work Order", delayed_filters, frappe_module)
    cards.append(
        _card(
            "production_in_progress",
            "طلبات قيد الإنتاج",
            in_progress,
            "حسب نطاقك",
            route_key="production_queue",
        )
    )
    cards.append(
        _card(
            "production_delayed",
            "إنتاج متأخر",
            delayed,
            "حسب نطاقك",
            priority="high" if delayed > 0 else "normal",
            route_key="production_queue",
        )
    )
    if delayed > 0:
        alerts.append(
            _alert(
                "production_delayed",
                "إنتاج متأخر",
                f"يوجد {delayed} أوامر إنتاج متأخرة",
                "high",
                "production_queue",
            )
        )


def _add_delivery_cards(cards, user, permissions, frappe_module):
    if not _has_any(permissions, {"delivery.view_assigned_batches", "delivery.update_batch"}):
        return
    ready = _count("Madar Order", {"delivery_status": "ready_for_dispatch"}, frappe_module)
    batch_filters = {"status": ["in", ["assigned", "picked_up", "out_for_delivery", "partially_completed"]]}
    if FULL_ACCESS not in permissions:
        batch_filters["driver_user"] = user
    active = _count("Madar Delivery Batch", batch_filters, frappe_module)
    route = "dispatch_queue" if "delivery.update_batch" in permissions and FULL_ACCESS in permissions else "my_delivery_batches"
    cards.append(
        _card(
            "ready_for_dispatch",
            "جاهز للإرسال",
            ready,
            "طلبات جاهزة للتوصيل",
            route_key="dispatch_queue",
        )
    )
    cards.append(
        _card(
            "active_delivery_batches",
            "دفعات توصيل نشطة",
            active,
            "حسب التكليف",
            route_key=route,
        )
    )


def _add_payment_card(cards, user, permissions, frappe_module):
    if not _has_any(permissions, {"payments.collect", "accounting.view_sync_logs"}):
        return
    filters = _today_filters(frappe_module)
    if "accounting.view_sync_logs" not in permissions and FULL_ACCESS not in permissions:
        filters["collected_by_user"] = user
    cards.append(
        _card(
            "payments_today",
            "مدفوعات اليوم",
            _count("Madar Payment", filters, frappe_module),
            "عمليات التحصيل",
            route_key="none",
        )
    )


def _add_cashbox_review_card(cards, alerts, permissions, frappe_module):
    if not _has_any(permissions, {"cashbox.review", "accounting.view_sync_logs"}):
        return
    value = _count("Madar Cashbox", {"status": "submitted"}, frappe_module)
    cards.append(
        _card(
            "cashboxes_waiting_review",
            "صناديق بانتظار المراجعة",
            value,
            "صناديق مرسلة",
            priority="high" if value > 0 else "normal",
            route_key="cashbox_review",
        )
    )
    if value > 0:
        alerts.append(
            _alert(
                "cashboxes_waiting_review",
                "صناديق بانتظار المراجعة",
                f"يوجد {value} صناديق تحتاج مراجعة",
                "high",
                "cashbox_review",
            )
        )


def _add_erp_failed_card(cards, alerts, permissions, frappe_module):
    if not _has_any(permissions, {"accounting.view_sync_logs"}):
        return
    value = (
        _count("Madar Order", {"erp_sync_status": "failed"}, frappe_module)
        + _count("Madar Order", {"erp_invoice_sync_status": "failed"}, frappe_module)
        + _count("Madar Payment", {"erp_sync_status": "failed"}, frappe_module)
    )
    cards.append(
        _card(
            "erp_sync_failed",
            "أخطاء مزامنة ERP",
            value,
            "تحتاج مراجعة",
            priority="high" if value > 0 else "normal",
            route_key="erp_sync_review",
        )
    )
    if value > 0:
        alerts.append(
            _alert(
                "erp_sync_failed",
                "أخطاء مزامنة ERP",
                f"يوجد {value} عناصر تحتاج مراجعة",
                "high",
                "erp_sync_review",
            )
        )


def _add_accounting_ready_card(cards, alerts, permissions, frappe_module):
    if not _has_any(permissions, {"accounting.view_sync_logs"}):
        return
    value = _count("Madar Order", {"accounting_status": "ready_for_review"}, frappe_module)
    cards.append(
        _card(
            "accounting_ready_for_review",
            "جاهز للمراجعة المحاسبية",
            value,
            "طلبات مكتملة",
            priority="high" if value > 0 else "normal",
            route_key="accounting_review",
        )
    )
    if value > 0:
        alerts.append(
            _alert(
                "accounting_ready_for_review",
                "جاهز للمراجعة المحاسبية",
                f"يوجد {value} طلبات جاهزة للمراجعة",
                "normal",
                "accounting_review",
            )
        )


def _add_unread_notifications(cards, user, frappe_module):
    cards.append(
        _card(
            "unread_notifications",
            "إشعارات غير مقروءة",
            _count("Madar Notification", {"recipient_user": user, "is_read": 0}, frappe_module),
            "حسابك الحالي",
            route_key="notifications",
        )
    )


def _add_attendance_state(cards, permissions):
    if not _has_any(permissions, {"attendance.check_in", "attendance.check_out"}):
        return
    cards.append(
        _card(
            "attendance_state",
            "حالة الحضور",
            "غير معروف",
            "من سجل الحضور",
            route_key="attendance",
        )
    )


def _today_filters(frappe_module):
    now = frappe_module.utils.now_datetime()
    start = datetime_combine(now, time.min)
    end = datetime_combine(now, time.max)
    return {"creation": ["between", [start, end]]}


def datetime_combine(now, clock):
    return now.__class__.combine(now.date(), clock)


def _branch_filter(scopes):
    branches = scopes.get("branch_names") or []
    if not branches or branches == ["*"]:
        return {}
    return {"assigned_branch": ["in", branches]}


def _department_filter(scopes):
    departments = scopes.get("department_names") or []
    if not departments or departments == ["*"]:
        return {}
    return {"production_department": ["in", departments]}


def _count(doctype, filters, frappe_module):
    try:
        rows = frappe_module.get_all(
            doctype,
            filters=filters,
            fields=["name"],
            limit=MAX_COUNT_LIMIT,
        )
        return len(rows)
    except Exception:
        return 0


def _has_any(permissions, wanted):
    permissions = set(permissions or [])
    return FULL_ACCESS in permissions or bool(permissions.intersection(wanted))


def _card(key, title, value, subtitle, priority="normal", route_key="none", route_params=None):
    return {
        "key": key,
        "title": title,
        "value": value,
        "subtitle": subtitle,
        "priority": priority,
        "route_key": route_key,
        "route_params": route_params or {},
    }


def _alert(key, title, message, priority, route_key, route_params=None):
    return {
        "key": key,
        "title": title,
        "message": message,
        "priority": priority,
        "route_key": route_key,
        "route_params": route_params or {},
    }


def _ok(data):
    return {"ok": True, "data": data, "error": None}
