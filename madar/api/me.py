import frappe
from frappe.utils import get_fullname

from madar.permissions.checks import build_user_context
from madar.services.employee_context import get_employee_context


@frappe.whitelist()
def get_context():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)

    return build_user_context(
        user=user,
        full_name=get_fullname(user),
        roles=frappe.get_roles(user),
        employee=get_employee_context(user),
    )
