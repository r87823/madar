import frappe

from madar.services import cashbox_service


@frappe.whitelist()
def get_my_cashbox():
    user = _authenticated_user()
    return cashbox_service.get_my_cashbox(user)


@frappe.whitelist()
def list_my_cashbox_entries(cashbox_name=None):
    user = _authenticated_user()
    return cashbox_service.list_my_cashbox_entries(user, cashbox_name=cashbox_name)


@frappe.whitelist()
def submit_my_cashbox(submitted_cash):
    user = _authenticated_user()
    return cashbox_service.submit_my_cashbox(user, submitted_cash)


@frappe.whitelist()
def list_cashboxes_for_review():
    user = _authenticated_user()
    return cashbox_service.list_cashboxes_for_review(user)


@frappe.whitelist()
def get_cashbox(cashbox_name):
    user = _authenticated_user()
    return cashbox_service.get_cashbox(user, cashbox_name)


@frappe.whitelist()
def approve_cashbox(cashbox_name):
    user = _authenticated_user()
    return cashbox_service.approve_cashbox(user, cashbox_name)


@frappe.whitelist()
def return_cashbox(cashbox_name, reason):
    user = _authenticated_user()
    return cashbox_service.return_cashbox(user, cashbox_name, reason)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
