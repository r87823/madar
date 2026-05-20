import frappe

from madar.services import settings_service


@frappe.whitelist()
def get_settings():
    user = _authenticated_user()
    return settings_service.get_settings(user)


@frappe.whitelist()
def get_setting_metadata():
    user = _authenticated_user()
    return settings_service.get_setting_metadata(user)


@frappe.whitelist()
def update_setting(setting_key, value):
    user = _authenticated_user()
    return settings_service.update_setting(user, setting_key, value)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
