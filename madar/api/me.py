import frappe

from madar.permissions.checks import build_user_context


@frappe.whitelist()
def get_context():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)

    return build_user_context(
        user=user,
        full_name=frappe.get_fullname(user),
        roles=frappe.get_roles(user),
    )

