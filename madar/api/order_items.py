import frappe

from madar.services import order_item_service


@frappe.whitelist()
def list_order_items(order_name):
    user = _authenticated_user()
    return order_item_service.list_order_items(user, order_name)


@frappe.whitelist()
def add_item(order_name, item_code, qty, notes=""):
    user = _authenticated_user()
    return order_item_service.add_item(
        user,
        order_name=order_name,
        item_code=item_code,
        qty=qty,
        notes=notes,
    )


@frappe.whitelist()
def update_item_qty(order_name, item_name, qty):
    user = _authenticated_user()
    return order_item_service.update_item_qty(
        user,
        order_name=order_name,
        item_name=item_name,
        qty=qty,
    )


@frappe.whitelist()
def remove_item(order_name, item_name):
    user = _authenticated_user()
    return order_item_service.remove_item(
        user,
        order_name=order_name,
        item_name=item_name,
    )


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
