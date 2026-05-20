import frappe

from madar.services import notification_service


@frappe.whitelist()
def list_notifications():
    user = _authenticated_user()
    return notification_service.list_notifications(user)


@frappe.whitelist()
def get_unread_count():
    user = _authenticated_user()
    return notification_service.get_unread_count(user)


@frappe.whitelist()
def mark_notification_read(notification_name):
    user = _authenticated_user()
    return notification_service.mark_read(user, notification_name)


@frappe.whitelist()
def mark_all_notifications_read():
    user = _authenticated_user()
    return notification_service.mark_all_read(user)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
