import frappe

from madar.services import work_order_service


@frappe.whitelist()
def create_work_orders_from_order(order_name):
    user = _authenticated_user()
    return work_order_service.create_work_orders_from_order(user, order_name)


@frappe.whitelist()
def list_work_orders():
    user = _authenticated_user()
    return work_order_service.list_work_orders(user)


@frappe.whitelist()
def get_work_order(work_order_name):
    user = _authenticated_user()
    return work_order_service.get_work_order(user, work_order_name)


@frappe.whitelist()
def accept_work_order(work_order_name):
    user = _authenticated_user()
    return work_order_service.accept_work_order(user, work_order_name)


@frappe.whitelist()
def start_work_order(work_order_name):
    user = _authenticated_user()
    return work_order_service.start_work_order(user, work_order_name)


@frappe.whitelist()
def mark_work_order_ready(work_order_name):
    user = _authenticated_user()
    return work_order_service.mark_work_order_ready(user, work_order_name)


@frappe.whitelist()
def mark_work_order_delayed(work_order_name, reason):
    user = _authenticated_user()
    return work_order_service.mark_work_order_delayed(user, work_order_name, reason)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
