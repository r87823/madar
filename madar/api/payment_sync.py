import frappe

from madar.services import payment_erp_sync_service


@frappe.whitelist()
def list_payment_sync_items():
    user = _authenticated_user()
    return payment_erp_sync_service.list_payment_sync_items(user)


@frappe.whitelist()
def get_payment_sync_item(payment_name):
    user = _authenticated_user()
    return payment_erp_sync_service.get_payment_sync_item(user, payment_name)


@frappe.whitelist()
def retry_payment_sync(payment_name):
    user = _authenticated_user()
    return payment_erp_sync_service.retry_payment_sync(user, payment_name)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
