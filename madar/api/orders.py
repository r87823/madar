import frappe

from madar.services import order_service


@frappe.whitelist()
def create_draft(
    customer_name,
    customer_phone="",
    notes="",
    fulfillment_method="branch_pickup",
    destination_branch=None,
):
    user = _authenticated_user()
    return order_service.create_draft(
        user,
        customer_name=customer_name,
        customer_phone=customer_phone,
        notes=notes,
        fulfillment_method=fulfillment_method,
        destination_branch=destination_branch,
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


@frappe.whitelist()
def list_approval_queue():
    user = _authenticated_user()
    return order_service.list_approval_queue(user)


@frappe.whitelist()
def approve_order(order_name):
    user = _authenticated_user()
    return order_service.approve_order(user, order_name)


@frappe.whitelist()
def return_order_for_edit(order_name, reason):
    user = _authenticated_user()
    return order_service.return_order_for_edit(user, order_name, reason)


@frappe.whitelist()
def reject_order(order_name, reason):
    user = _authenticated_user()
    return order_service.reject_order(user, order_name, reason)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
