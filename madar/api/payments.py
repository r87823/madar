import frappe

from madar.services import payment_service


@frappe.whitelist()
def collect_payment(order_name, amount, payment_method, reference_no="", notes=""):
    user = _authenticated_user()
    return payment_service.collect_payment(
        user,
        order_name,
        amount,
        payment_method,
        reference_no=reference_no,
        notes=notes,
    )


@frappe.whitelist()
def list_order_payments(order_name):
    user = _authenticated_user()
    return payment_service.list_order_payments(user, order_name)


@frappe.whitelist()
def get_payment(payment_name):
    user = _authenticated_user()
    return payment_service.get_payment(user, payment_name)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
