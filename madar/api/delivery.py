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


@frappe.whitelist()
def create_delivery_batch(order_names):
    user = _authenticated_user()
    return delivery_service.create_delivery_batch(user, order_names)


@frappe.whitelist()
def assign_driver(batch_name, driver_user):
    user = _authenticated_user()
    return delivery_service.assign_driver(user, batch_name, driver_user)


@frappe.whitelist()
def list_delivery_batches():
    user = _authenticated_user()
    return delivery_service.list_delivery_batches(user)


@frappe.whitelist()
def get_delivery_batch(batch_name):
    user = _authenticated_user()
    return delivery_service.get_delivery_batch(user, batch_name)


@frappe.whitelist()
def list_my_delivery_batches():
    user = _authenticated_user()
    return delivery_service.list_my_delivery_batches(user)


@frappe.whitelist()
def mark_batch_picked_up(batch_name):
    user = _authenticated_user()
    return delivery_service.mark_batch_picked_up(user, batch_name)


@frappe.whitelist()
def mark_batch_out_for_delivery(batch_name):
    user = _authenticated_user()
    return delivery_service.mark_batch_out_for_delivery(user, batch_name)


@frappe.whitelist()
def mark_batch_delivered(batch_name):
    user = _authenticated_user()
    return delivery_service.mark_batch_delivered(user, batch_name)


@frappe.whitelist()
def mark_batch_returned(batch_name, reason):
    user = _authenticated_user()
    return delivery_service.mark_batch_returned(user, batch_name, reason)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
