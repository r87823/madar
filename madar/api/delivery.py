import frappe

from madar.services import delivery_service


@frappe.whitelist()
def list_dispatch_queue():
    user = _authenticated_user()
    return delivery_service.list_dispatch_queue(user)


@frappe.whitelist()
def mark_dispatched_to_branch(order_name):
    user = _authenticated_user()
    return delivery_service.mark_dispatched_to_branch(user, order_name)


@frappe.whitelist()
def mark_received_at_branch(order_name):
    user = _authenticated_user()
    return delivery_service.mark_received_at_branch(user, order_name)


@frappe.whitelist()
def mark_ready_for_customer_pickup(order_name):
    user = _authenticated_user()
    return delivery_service.mark_ready_for_customer_pickup(user, order_name)


@frappe.whitelist()
def mark_customer_picked_up(order_name):
    user = _authenticated_user()
    return delivery_service.mark_customer_picked_up(user, order_name)


@frappe.whitelist()
def mark_dispatched_to_customer(order_name):
    user = _authenticated_user()
    return delivery_service.mark_dispatched_to_customer(user, order_name)


@frappe.whitelist()
def mark_delivered_to_customer(order_name):
    user = _authenticated_user()
    return delivery_service.mark_delivered_to_customer(user, order_name)


@frappe.whitelist()
def mark_failed_delivery(order_name, reason):
    user = _authenticated_user()
    return delivery_service.mark_failed_delivery(user, order_name, reason)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user

