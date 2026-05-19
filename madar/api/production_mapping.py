import frappe

from madar.services import production_mapping_service


@frappe.whitelist()
def list_production_centers():
    user = _authenticated_user()
    return production_mapping_service.list_production_centers(user)


@frappe.whitelist()
def list_production_departments(production_center=None):
    user = _authenticated_user()
    return production_mapping_service.list_production_departments(
        user,
        production_center=production_center,
    )


@frappe.whitelist()
def list_item_department_mappings():
    user = _authenticated_user()
    return production_mapping_service.list_item_department_mappings(user)


@frappe.whitelist()
def create_or_update_production_center(center_name, center_code, is_active=1):
    user = _authenticated_user()
    return production_mapping_service.create_or_update_production_center(
        user,
        center_name=center_name,
        center_code=center_code,
        is_active=is_active,
    )


@frappe.whitelist()
def create_or_update_production_department(
    department_name,
    department_code,
    production_center,
    is_active=1,
):
    user = _authenticated_user()
    return production_mapping_service.create_or_update_production_department(
        user,
        department_name=department_name,
        department_code=department_code,
        production_center=production_center,
        is_active=is_active,
    )


@frappe.whitelist()
def create_or_update_item_department_mapping(
    item_code,
    production_center,
    production_department,
    is_active=1,
):
    user = _authenticated_user()
    return production_mapping_service.create_or_update_item_department_mapping(
        user,
        item_code=item_code,
        production_center=production_center,
        production_department=production_department,
        is_active=is_active,
    )


@frappe.whitelist()
def validate_order_department_mappings(order_name):
    user = _authenticated_user()
    return production_mapping_service.validate_order_department_mappings(user, order_name)


def _authenticated_user():
    user = frappe.session.user
    if user == "Guest":
        frappe.throw("Authentication required", frappe.AuthenticationError)
    return user
