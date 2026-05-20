import frappe

from madar.services import reports_service


@frappe.whitelist()
def get_orders_report(filters=None, **kwargs):
    user = _authenticated_user()
    return reports_service.get_orders_report(user, _filters(filters, kwargs))


@frappe.whitelist()
def get_payments_report(filters=None, **kwargs):
    user = _authenticated_user()
    return reports_service.get_payments_report(user, _filters(filters, kwargs))


@frappe.whitelist()
def get_production_report(filters=None, **kwargs):
    user = _authenticated_user()
    return reports_service.get_production_report(user, _filters(filters, kwargs))


@frappe.whitelist()
def get_delivery_report(filters=None, **kwargs):
    user = _authenticated_user()
    return reports_service.get_delivery_report(user, _filters(filters, kwargs))


@frappe.whitelist()
def get_cashbox_report(filters=None, **kwargs):
    user = _authenticated_user()
    return reports_service.get_cashbox_report(user, _filters(filters, kwargs))


@frappe.whitelist()
def get_erp_sync_errors_report(filters=None, **kwargs):
    user = _authenticated_user()
    return reports_service.get_erp_sync_errors_report(user, _filters(filters, kwargs))


def _filters(filters, kwargs):
    if filters:
        return filters
    return kwargs or {}


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
