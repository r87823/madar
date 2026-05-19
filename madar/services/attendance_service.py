from datetime import datetime

from madar.permissions.checks import has_permission
from madar.services.employee_context import get_employee_context


CHECK_IN_PERMISSION = "attendance.check_in"
CHECK_OUT_PERMISSION = "attendance.check_out"
DUPLICATE_WINDOW_SECONDS = 60


def get_status(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    employee = _get_linked_employee(user, frappe_module)
    if not employee:
        return _error("EMPLOYEE_NOT_LINKED", "لا يوجد موظف مرتبط بالمستخدم الحالي.")

    if not _employee_checkin_available(frappe_module):
        return _error("EMPLOYEE_CHECKIN_UNAVAILABLE", "سجل الحضور غير متاح في نظام الموارد البشرية.")

    last_checkin = _get_last_checkin(frappe_module, employee["name"])
    return _ok(
        {
            "employee": employee,
            "state": _state_from_log_type(_get_value(last_checkin, "log_type")),
            "last_checkin": _serialize_checkin(last_checkin),
        }
    )


def check_in(user, frappe_module=None):
    return _create_checkin(
        user=user,
        log_type="IN",
        permission_key=CHECK_IN_PERMISSION,
        frappe_module=frappe_module,
    )


def check_out(user, frappe_module=None):
    return _create_checkin(
        user=user,
        log_type="OUT",
        permission_key=CHECK_OUT_PERMISSION,
        frappe_module=frappe_module,
    )


def _create_checkin(user, log_type, permission_key, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    roles = frappe_module.get_roles(user)
    if not has_permission(roles, permission_key):
        return _error("PERMISSION_DENIED", "ليست لديك صلاحية تنفيذ هذا الإجراء.")

    employee = _get_linked_employee(user, frappe_module)
    if not employee:
        return _error("EMPLOYEE_NOT_LINKED", "لا يوجد موظف مرتبط بالمستخدم الحالي.")

    if not _employee_checkin_available(frappe_module):
        return _error("EMPLOYEE_CHECKIN_UNAVAILABLE", "سجل الحضور غير متاح في نظام الموارد البشرية.")

    now = _server_now(frappe_module)
    duplicate = _get_recent_same_log(frappe_module, employee["name"], log_type)
    if duplicate and _within_duplicate_window(_get_value(duplicate, "time"), now):
        return _error("DUPLICATE_CHECKIN", "تم تسجيل نفس الحركة قبل لحظات.")

    created = frappe_module.get_doc(
        {
            "doctype": "Employee Checkin",
            "employee": employee["name"],
            "time": now,
            "log_type": log_type,
        }
    ).insert(ignore_permissions=True)
    frappe_module.db.commit()

    return _ok(
        {
            "employee": employee,
            "state": _state_from_log_type(log_type),
            "last_checkin": _serialize_checkin(created),
        }
    )


def _get_linked_employee(user, frappe_module):
    employee = get_employee_context(user, frappe_module=frappe_module)
    if not employee or not employee.get("name"):
        return None
    return employee


def _employee_checkin_available(frappe_module):
    try:
        meta = frappe_module.get_meta("Employee Checkin")
        return meta.has_field("employee") and meta.has_field("time") and meta.has_field("log_type")
    except Exception:
        return False


def _get_last_checkin(frappe_module, employee_name):
    rows = frappe_module.get_all(
        "Employee Checkin",
        filters={"employee": employee_name},
        fields=["name", "employee", "time", "log_type"],
        order_by="time desc",
        limit=1,
    )
    return rows[0] if rows else None


def _get_recent_same_log(frappe_module, employee_name, log_type):
    rows = frappe_module.get_all(
        "Employee Checkin",
        filters={"employee": employee_name},
        fields=["name", "employee", "time", "log_type"],
        order_by="time desc",
        limit=1,
    )
    if not rows:
        return None
    latest = rows[0]
    if _get_value(latest, "log_type") != log_type:
        return None
    return latest


def _within_duplicate_window(previous_time, now):
    if not isinstance(previous_time, datetime):
        return False
    return 0 <= (now - previous_time).total_seconds() <= DUPLICATE_WINDOW_SECONDS


def _server_now(frappe_module):
    return frappe_module.utils.now_datetime()


def _state_from_log_type(log_type):
    if log_type == "IN":
        return "in_work"
    if log_type == "OUT":
        return "out_of_work"
    return "unknown"


def _serialize_checkin(checkin):
    if not checkin:
        return None
    return {
        "name": _get_value(checkin, "name"),
        "employee": _get_value(checkin, "employee"),
        "time": str(_get_value(checkin, "time")),
        "log_type": _get_value(checkin, "log_type"),
    }


def _get_value(source, field):
    if not source:
        return None
    if isinstance(source, dict):
        return source.get(field)
    return getattr(source, field, None)


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

