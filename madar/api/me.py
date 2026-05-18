import frappe
from frappe.utils import get_fullname

from madar.permissions.checks import build_user_context, get_permissions_for_roles
from madar.permissions.scopes import get_context_scopes
from madar.services.branch_context import get_branch_context
from madar.services.employee_context import get_employee_context


@frappe.whitelist()
def get_context():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)

    full_name = get_fullname(user)
    roles = frappe.get_roles(user)
    employee = get_employee_context(user)
    permissions = get_permissions_for_roles(roles)

    return build_user_context(
        user=user,
        full_name=full_name,
        roles=roles,
        employee=employee,
        branch=get_branch_context(employee),
        scopes=get_context_scopes(employee=employee, permissions=permissions),
    )
