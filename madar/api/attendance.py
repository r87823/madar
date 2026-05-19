import frappe

from madar.services import attendance_service


@frappe.whitelist()
def get_status():
    user = _authenticated_user()
    return attendance_service.get_status(user)


@frappe.whitelist()
def get_history():
    user = _authenticated_user()
    return attendance_service.get_history(user)


@frappe.whitelist()
def check_in():
    user = _authenticated_user()
    return attendance_service.check_in(user)


@frappe.whitelist()
def check_out():
    user = _authenticated_user()
    return attendance_service.check_out(user)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
