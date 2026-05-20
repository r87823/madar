import frappe

from madar.services import accounting_review_service


@frappe.whitelist()
def get_order_accounting_summary(order_name):
    user = _authenticated_user()
    return accounting_review_service.get_order_accounting_summary(user, order_name)


@frappe.whitelist()
def list_orders_for_accounting_review():
    user = _authenticated_user()
    return accounting_review_service.list_orders_for_accounting_review(user)


@frappe.whitelist()
def mark_accounting_reviewed(order_name):
    user = _authenticated_user()
    return accounting_review_service.mark_accounting_reviewed(user, order_name)


@frappe.whitelist()
def mark_accounting_needs_attention(order_name, notes):
    user = _authenticated_user()
    return accounting_review_service.mark_accounting_needs_attention(user, order_name, notes)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
