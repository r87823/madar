import frappe

from madar.services import accounting_finalization_service


@frappe.whitelist()
def get_finalization_status(order_name):
    user = _authenticated_user()
    return accounting_finalization_service.get_finalization_status(user, order_name)


@frappe.whitelist()
def submit_sales_invoice(order_name):
    user = _authenticated_user()
    return accounting_finalization_service.submit_sales_invoice(user, order_name)


@frappe.whitelist()
def submit_payment_entries(order_name):
    user = _authenticated_user()
    return accounting_finalization_service.submit_payment_entries_for_order(user, order_name)


@frappe.whitelist()
def finalize_order_accounting(order_name):
    user = _authenticated_user()
    return accounting_finalization_service.finalize_order_accounting(user, order_name)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
