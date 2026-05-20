from datetime import datetime

from madar.permissions.checks import has_permission
from madar.services.employee_context import get_employee_context


CHECK_IN_PERMISSION = "attendance.check_in"
CHECK_OUT_PERMISSION = "attendance.check_out"
DUPLICATE_WINDOW_SECONDS = 60
HISTORY_LIMIT = 20


def get_status(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    employee = _get_linked_employee(user, frappe_module)
    if not employee:
        return _error("EMPLOYEE_NOT_LINKED", "لا يوجد موظف مرتبط بالمستخدم الحالي.")

    if not _employee_checkin_available(frappe_module):
        return _error("EMPLOYEE_CHECKIN_UNAVAILABLE", "سجل الحضور غير متاح في نظام الموارد البشرية.")

    last_checkin = _get_last_checkin(frappe_module, employee["name"])
    state = _state_from_log_type(_get_value(last_checkin, "log_type"))
    last_time = _get_value(last_checkin, "time")
    return _ok(
        {
            "employee": employee,
            "state": state,
            "current_state": state,
            "last_log_type": _get_value(last_checkin, "log_type"),
            "last_time": str(last_time) if last_time else None,
            "last_checkin": _serialize_checkin(last_checkin),
        }
    )


def get_history(user, frappe_module=None, limit=HISTORY_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    employee = _get_linked_employee(user, frappe_module)
    if not employee:
        return _error("EMPLOYEE_NOT_LINKED", "لا يوجد موظف مرتبط بالمستخدم الحالي.")

    if not _employee_checkin_available(frappe_module):
        return _error("EMPLOYEE_CHECKIN_UNAVAILABLE", "سجل الحضور غير متاح في نظام الموارد البشرية.")

    safe_limit = max(1, min(int(limit or HISTORY_LIMIT), HISTORY_LIMIT))
    rows = _get_checkins(frappe_module, employee["name"], limit=safe_limit)
    return _ok(
        {
            "items": [_serialize_history_item(row) for row in rows],
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
    if duplicate and _within_duplicate_window(_get_value(duplicate, "time"), now, frappe_module):
        return _error("DUPLICATE_CHECKIN", "تم تسجيل نفس الحركة قبل لحظات.")

    last_checkin = _get_last_checkin(frappe_module, employee["name"])
    current_state = _state_from_log_type(_get_value(last_checkin, "log_type"))
    invalid_error = _invalid_session_error(current_state, log_type)
    if invalid_error:
        return invalid_error

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
    rows = _get_checkins(frappe_module, employee_name, limit=1)
    return rows[0] if rows else None


def _get_checkins(frappe_module, employee_name, limit):
    return frappe_module.get_all(
        "Employee Checkin",
        filters={"employee": employee_name},
        fields=["name", "employee", "time", "log_type"],
        order_by="time desc",
        limit=limit,
    )


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


def _within_duplicate_window(previous_time, now, frappe_module=None):
    if not isinstance(previous_time, datetime):
        return False
    return 0 <= (now - previous_time).total_seconds() <= _duplicate_window_seconds(frappe_module)


def _duplicate_window_seconds(frappe_module):
    try:
        from madar.services import settings_service

        return int(
            settings_service.get_setting_value(
                "attendance.duplicate_window_seconds",
                frappe_module=frappe_module,
            )
        )
    except Exception:
        return DUPLICATE_WINDOW_SECONDS


def _server_now(frappe_module):
    return frappe_module.utils.now_datetime()


def _state_from_log_type(log_type):
    if log_type == "IN":
        return "in_work"
    if log_type == "OUT":
        return "out_of_work"
    return "unknown"


def _invalid_session_error(current_state, log_type):
    if current_state == "in_work" and log_type == "IN":
        return _error("ALREADY_CHECKED_IN", "أنت مسجل حضور بالفعل.")
    if current_state == "out_of_work" and log_type == "OUT":
        return _error("ALREADY_CHECKED_OUT", "أنت مسجل انصراف بالفعل.")
    return None


def _serialize_checkin(checkin):
    if not checkin:
        return None
    return {
        "name": _get_value(checkin, "name"),
        "employee": _get_value(checkin, "employee"),
        "time": str(_get_value(checkin, "time")),
        "log_type": _get_value(checkin, "log_type"),
    }


def _serialize_history_item(checkin):
    log_type = _get_value(checkin, "log_type")
    return {
        "log_type": log_type,
        "time": str(_get_value(checkin, "time")),
        "state": _state_from_log_type(log_type),
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
