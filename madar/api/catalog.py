import frappe

from madar.services import catalog_service


@frappe.whitelist()
def list_products(search=""):
    user = _authenticated_user()
    return catalog_service.list_products(user, search=search)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
