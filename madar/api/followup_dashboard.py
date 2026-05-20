import frappe

from madar.services import followup_dashboard_service


@frappe.whitelist()
def get_summary():
    user = _authenticated_user()
    return followup_dashboard_service.get_summary(user)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
