from madar.permissions.checks import get_permissions_for_roles


NOTIFICATION_FIELDS = [
    "name",
    "recipient_user",
    "title",
    "message",
    "event_type",
    "entity_type",
    "entity_name",
    "is_read",
    "read_at",
    "created_at",
    "priority",
    "modified",
]
MAX_NOTIFICATION_LIMIT = 50
VALID_PRIORITIES = {"low", "normal", "high"}


def notify_user(
    recipient_user,
    title,
    message,
    event_type,
    entity_type=None,
    entity_name=None,
    priority="normal",
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    recipient_user = (recipient_user or "").strip()
    if not recipient_user:
        return _error("RECIPIENT_REQUIRED", "مستلم الإشعار مطلوب.")
    now = _server_now(frappe_module)
    priority = priority if priority in VALID_PRIORITIES else "normal"
    doc = frappe_module.get_doc(
        {
            "doctype": "Madar Notification",
            "naming_series": "MADAR-NOTIF-.YYYY.-",
            "recipient_user": recipient_user,
            "title": (title or "").strip(),
            "message": (message or "").strip(),
            "event_type": (event_type or "").strip(),
            "entity_type": (entity_type or "").strip() if entity_type else "",
            "entity_name": (entity_name or "").strip() if entity_name else "",
            "is_read": 0,
            "read_at": None,
            "created_at": now,
            "priority": priority,
        }
    ).insert(ignore_permissions=True)
    _commit(frappe_module)
    return _ok(_serialize_notification(doc))


def notify_users(
    recipient_users,
    title,
    message,
    event_type,
    entity_type=None,
    entity_name=None,
    priority="normal",
    frappe_module=None,
):
    if frappe_module is None:
        import frappe as frappe_module

    created = []
    for user in _unique_users(recipient_users):
        result = notify_user(
            user,
            title=title,
            message=message,
            event_type=event_type,
            entity_type=entity_type,
            entity_name=entity_name,
            priority=priority,
            frappe_module=frappe_module,
        )
        if result.get("ok"):
            created.append(result["data"]["name"])
    return _ok({"created": len(created), "notifications": created})


def safe_notify_user(*args, **kwargs):
    try:
        return notify_user(*args, **kwargs)
    except Exception as exc:
        frappe_module = kwargs.get("frappe_module")
        _log_notification_error(frappe_module, exc)
        return _error("NOTIFICATION_CREATE_FAILED", "تعذر إنشاء الإشعار.")


def safe_notify_users(*args, **kwargs):
    try:
        return notify_users(*args, **kwargs)
    except Exception as exc:
        frappe_module = kwargs.get("frappe_module")
        _log_notification_error(frappe_module, exc)
        return _error("NOTIFICATION_CREATE_FAILED", "تعذر إنشاء الإشعار.")


def list_notifications(user, frappe_module=None, limit=MAX_NOTIFICATION_LIMIT):
    if frappe_module is None:
        import frappe as frappe_module

    rows = frappe_module.get_all(
        "Madar Notification",
        filters={"recipient_user": user},
        fields=NOTIFICATION_FIELDS,
        order_by="created_at desc",
        limit=max(1, min(int(limit or MAX_NOTIFICATION_LIMIT), MAX_NOTIFICATION_LIMIT)),
    )
    return _ok({"items": [_serialize_notification(row) for row in rows]})


def get_unread_count(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    rows = frappe_module.get_all(
        "Madar Notification",
        filters={"recipient_user": user, "is_read": 0},
        fields=["name"],
        limit=1000,
    )
    return _ok({"unread_count": len(rows)})


def mark_read(user, notification_name, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    doc = _get_notification(frappe_module, notification_name)
    if not doc or _get_value(doc, "recipient_user") != user:
        return _error("NOTIFICATION_NOT_FOUND", "الإشعار غير موجود.")
    if not bool(_get_value(doc, "is_read")):
        doc.is_read = 1
        doc.read_at = _server_now(frappe_module)
        doc.save(ignore_permissions=True)
        _commit(frappe_module)
    return _ok(_serialize_notification(doc))


def mark_all_read(user, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    rows = frappe_module.get_all(
        "Madar Notification",
        filters={"recipient_user": user, "is_read": 0},
        fields=["name"],
        limit=1000,
    )
    updated = 0
    now = _server_now(frappe_module)
    for row in rows:
        doc = _get_notification(frappe_module, _get_value(row, "name"))
        if doc and _get_value(doc, "recipient_user") == user and not bool(_get_value(doc, "is_read")):
            doc.is_read = 1
            doc.read_at = now
            doc.save(ignore_permissions=True)
            updated += 1
    if updated:
        _commit(frappe_module)
    return _ok({"updated": updated})


def users_with_permission(permission_key, frappe_module=None):
    if frappe_module is None:
        import frappe as frappe_module

    users = frappe_module.get_all(
        "User",
        filters={"enabled": 1},
        fields=["name"],
        limit=1000,
    )
    recipients = []
    for user in users:
        user_name = _get_value(user, "name")
        if user_name in {"Guest", "Administrator"}:
            continue
        permissions = get_permissions_for_roles(frappe_module.get_roles(user_name))
        if permission_key in permissions or "system.full_access" in permissions:
            recipients.append(user_name)
    return sorted(_unique_users(recipients))


def _get_notification(frappe_module, notification_name):
    try:
        return frappe_module.get_doc("Madar Notification", notification_name)
    except Exception:
        return None


def _serialize_notification(notification):
    return {
        "name": _get_value(notification, "name"),
        "recipient_user": _get_value(notification, "recipient_user"),
        "title": _get_value(notification, "title"),
        "message": _get_value(notification, "message"),
        "event_type": _get_value(notification, "event_type"),
        "entity_type": _get_value(notification, "entity_type"),
        "entity_name": _get_value(notification, "entity_name"),
        "is_read": bool(_get_value(notification, "is_read")),
        "read_at": _string_or_none(_get_value(notification, "read_at")),
        "created_at": _string_or_none(_get_value(notification, "created_at")),
        "priority": _get_value(notification, "priority") or "normal",
    }


def _unique_users(users):
    seen = set()
    result = []
    for user in users or []:
        value = (user or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _log_notification_error(frappe_module, exc):
    if frappe_module is None:
        try:
            import frappe as frappe_module
        except Exception:
            return
    if hasattr(frappe_module, "log_error"):
        frappe_module.log_error(title="NOTIFICATION_CREATE_FAILED", message=str(exc)[:500])


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


def _ok(data):
    return {"ok": True, "data": data, "error": None}


def _error(code, message):
    return {"ok": False, "data": None, "error": {"code": code, "message": message}}
