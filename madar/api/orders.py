import frappe

from madar.services import order_service


@frappe.whitelist()
def create_draft(customer_name, customer_phone="", notes=""):
    user = _authenticated_user()
    return order_service.create_draft(
        user,
        customer_name=customer_name,
        customer_phone=customer_phone,
        notes=notes,
    )


@frappe.whitelist()
def list_orders():
    user = _authenticated_user()
    return order_service.list_orders(user)


@frappe.whitelist()
def get_order(order_name):
    user = _authenticated_user()
    return order_service.get_order(user, order_name)


@frappe.whitelist()
def submit_order(order_name):
    user = _authenticated_user()
    return order_service.submit_order(user, order_name)


@frappe.whitelist()
def cancel_order(order_name):
    user = _authenticated_user()
    return order_service.cancel_order(user, order_name)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
