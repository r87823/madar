import frappe

from madar.services import erp_sync_service


@frappe.whitelist()
def list_sync_orders():
    user = _authenticated_user()
    return erp_sync_service.list_sync_orders(user)


@frappe.whitelist()
def get_sync_order(order_name):
    user = _authenticated_user()
    return erp_sync_service.get_sync_order(user, order_name)


@frappe.whitelist()
def retry_sync_order(order_name):
    user = _authenticated_user()
    return erp_sync_service.retry_sync_order(user, order_name)


@frappe.whitelist()
def submit_erp_sales_order(order_name):
    user = _authenticated_user()
    return erp_sync_service.submit_erp_sales_order_for_user(user, order_name)


@frappe.whitelist()
def list_invoice_sync_orders():
    user = _authenticated_user()
    return erp_sync_service.list_invoice_sync_orders(user)


@frappe.whitelist()
def get_invoice_sync_order(order_name):
    user = _authenticated_user()
    return erp_sync_service.get_invoice_sync_order(user, order_name)


@frappe.whitelist()
def retry_invoice_sync(order_name):
    user = _authenticated_user()
    return erp_sync_service.retry_invoice_sync(user, order_name)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
